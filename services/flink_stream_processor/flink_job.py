"""Flink job for enriching the sensor data."""
import logging
import json
import time
from collections import deque
from typing import Iterable, Tuple
from pathlib import Path
from pyflink.common.serialization import SimpleStringSchema
from pyflink.common.watermark_strategy import WatermarkStrategy
from pyflink.common.typeinfo import Types
from pyflink.datastream import StreamExecutionEnvironment, RuntimeExecutionMode
from pyflink.datastream.connectors.kafka import KafkaSource, KafkaOffsetsInitializer, KafkaSink, KafkaRecordSerializationSchema, FlinkKafkaProducer
from pyflink.datastream import MapFunction, RuntimeContext, ProcessFunction, OutputTag
from pyflink.datastream.state import ListStateDescriptor, ListState
from pyflink.datastream.functions import FlatMapFunction, SinkFunction
from pyflink.table import Row, StreamTableEnvironment

KAFKA_BROKER = "localhost:29092"
IN_TOPIC_NAME = "raw_sensor_data"
OUT_TOPIC_NAME = "enriched_data"
GROUP_ID = "raw_data_consumers"

# TODO
# export custom functions and classes to a different file
LATE_DATA_TAG = OutputTag(
    tag_id="late_data",
    type_info=Types.ROW_NAMED(
        ["id", "x", "y", "timestamp"],
        [Types.INT(), Types.FLOAT(), Types.FLOAT(), Types.DOUBLE()]
    )
)

logger = logging.getLogger("Flink job")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

class RealTimePrint(SinkFunction):
    def invoke(self, event, ctx):
        print(event, flush=True)

class ParseAndFilter(ProcessFunction):
    """Parse the event and filter out if out of order.
    Filtering is needed for ensuring correct behaviour of future transformations."""
    def __init__(self):
        self.most_recent_timestamp = 0
        
    def process_element(self, event: str, ctx: ProcessFunction.Context):
        try:
            d = json.loads(event)
            if d["timestamp"] > self.most_recent_timestamp:
                self.most_recent_timestamp = d["timestamp"]
                yield Row(release_time = time.time())
                '''yield Row(
                    id = d["id"],
                    x = d["x"],
                    y = d["y"],
                    timestamp=d["timestamp"],
                    tt = (time.time() - d["timestamp"])
                )'''

            else:
                yield \
                    LATE_DATA_TAG, \
                    Row(
                        id = d["id"],
                        x = d["x"],
                        y = d["y"],
                        timestamp=d["timestamp"]
                    )
                
        except json.JSONDecodeError as e:
            logger.error(f"An error occured when parsing an event ({event}): {e}")

class RowToJson(MapFunction):
        def map(self, value: Row) -> str:
            return json.dumps(value.as_dict())


# "State TTL is still not supported in PyFlink DataStream API." ~ Flink docs ;cccc
class CalculateAvgSpeed(FlatMapFunction):
    def __init__(self):
        self.list_state: ListState = None

    def open(self, ctx: RuntimeContext):
        descriptor = ListStateDescriptor(
            name="list_state",
            elem_type_info=Types.ROW_NAMED(
                ["id", "x", "y", "timestamp"],
                [Types.INT(), Types.FLOAT(), Types.FLOAT(), Types.DOUBLE()]
            )
        )
        self.list_state = ctx.get_list_state(descriptor)

    def flat_map(self, event: Row):
        queue = []
        for e in reversed(list(self.list_state.get())):
            if event.timestamp - e.timestamp <= 5:
                queue.append(e)
            else:
                break
        try:
            time_diff = event.timestamp - queue[-1].timestamp
            if time_diff >= 1:
                distance = ((event.x - queue[-1].x) ** 2 \
                         +  (event.y - queue[-1].y) ** 2) ** 0.5
                speed = distance / time_diff
                queue.append(event)
                self.list_state.update(queue)
                yield Row(
                    id = event.id,
                    x = event.x,
                    y = event.y,
                    timestamp = event.timestamp,
                    avg_speed = speed,
                    time_taken = (time.time() - event.timestamp)
                )
            else:
                queue.append(event)
                self.list_state.update(queue)

        except IndexError:
            self.list_state.add(event)




        '''if not queue:
            self.list_state.add(event)
            return
        
        while queue:
            leftmost_event: Row = queue[0]
            time_diff = event.timestamp - leftmost_event.timestamp
            if time_diff >= 5:
                del queue[0]
            
            elif 1 < time_diff < 5:
                distance = ((event.x - leftmost_event.x) ** 2 \
                         +  (event.y - leftmost_event.y) ** 2) ** 0.5
                avg_speed = distance / time_diff
                queue.append(event)
                self.list_state.update(queue)
                yield Row(
                    id = event.id,
                    x = event.x,
                    y = event.y,
                    timestamp = event.timestamp,
                    speed = avg_speed
                )

            elif time_diff <= 1:
                queue.append(event)
                self.list_state.update(queue)
                return'''

def main() -> None:
    """Holds main pipeline execution steps."""
    env = StreamExecutionEnvironment.get_execution_environment()
    env.set_runtime_mode(RuntimeExecutionMode.STREAMING)
    env.set_buffer_timeout(0)
    env.set_parallelism(1)
    flink_connector_name = "flink-sql-connector-kafka-4.0.0-2.0.jar"
    kafka_jar = Path(__file__).resolve().parent / flink_connector_name
    env.add_jars(kafka_jar.as_uri())

    source = KafkaSource.builder() \
        .set_starting_offsets(KafkaOffsetsInitializer.latest()) \
        .set_bootstrap_servers(KAFKA_BROKER) \
        .set_topics(IN_TOPIC_NAME) \
        .set_group_id(GROUP_ID) \
        .set_value_only_deserializer(SimpleStringSchema()) \
        .set_property("fetch.min.bytes", "1") \
        .set_property("fetch.max.wait.ms", "10") \
        .set_property("max.poll.records", "100") \
        .build()
    
    record_serializer = KafkaRecordSerializationSchema.builder() \
        .set_topic(OUT_TOPIC_NAME) \
        .set_value_serialization_schema(SimpleStringSchema()) \
        .build()
    sink = KafkaSink.builder() \
        .set_bootstrap_servers(KAFKA_BROKER) \
        .set_record_serializer(record_serializer) \
        .build()

    ds = env.from_source(source=source,
                         watermark_strategy=WatermarkStrategy.no_watermarks(),
                         source_name="raw_data_source")
    
    parsed_ds = ds.process(
        func=ParseAndFilter(),
        output_type=Types.ROW_NAMED(
            ["release_time"],
            [Types.DOUBLE()]
        )
    )
    '''parsed_ds = ds.process(
        func=ParseAndFilter(),
        output_type=Types.ROW_NAMED(
            ["id", "x", "y", "timestamp", "tt"],
            [Types.INT(), Types.FLOAT(), Types.FLOAT(), Types.DOUBLE(), Types.DOUBLE()]
        )
    )'''

    # TODO
    # add aggregating tumbling window, count late data per id, use watermark mechanism
    # late_data_ds = parsed_ds.get_side_output(LATE_DATA_TAG)

    # enriched_ds = parsed_ds \
    #     .key_by(
    #         key_selector=(lambda event: event.id),
    #         key_type=Types.INT()
    #     ) \
    #     .flat_map(
    #         func=CalculateAvgSpeed(),
    #         output_type=Types.ROW_NAMED(
    #             ["id", "x", "y", "timestamp", "avg_speed", "time_taken"],
    #             [Types.INT(), Types.FLOAT(), Types.FLOAT(), Types.DOUBLE(), Types.FLOAT(), Types.DOUBLE()]
    #         )
    #     )

    # window = parsed_ds \
    # .key_by(lambda v: v[0]) \
    # .window(TumblingEventTimeWindows.of(Time(50))) \
    # .process(MyProcessWindowFunction())

    parsed_ds.map(RowToJson(), output_type=Types.STRING()).sink_to(sink)
    env.execute()
    

if __name__ == "__main__":
    main()

