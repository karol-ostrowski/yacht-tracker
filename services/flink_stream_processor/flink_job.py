"""Flink job for enriching the sensor data and creating metrics."""
import logging
import json
import time
from collections import defaultdict
from pathlib import Path
from pyflink.common import Configuration
from pyflink.common.serialization import SimpleStringSchema
from pyflink.common.watermark_strategy import WatermarkStrategy, TimestampAssigner
from pyflink.common.typeinfo import Types
from pyflink.datastream import StreamExecutionEnvironment, RuntimeExecutionMode
from pyflink.datastream.connectors.kafka import KafkaSource, KafkaOffsetsInitializer, KafkaSink, KafkaRecordSerializationSchema
from pyflink.datastream import RuntimeContext, ProcessFunction, OutputTag
from pyflink.datastream.state import ListStateDescriptor, ListState, Time
from pyflink.datastream.functions import FlatMapFunction, AggregateFunction, CoMapFunction
from pyflink.datastream.window import TumblingProcessingTimeWindows
from pyflink.table import Row
from side_output_functions import create_default_statistic

KAFKA_BROKER = "broker:9092"
IN_TOPIC_NAME = "raw_sensor_data"
OUT_TOPIC_NAME = "enriched_data"
GROUP_ID = "raw_data_consumers"
METRIC_AGGREGATION_WINDOW_SIZE = 10 # in seconds

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

class ParseAndFilter(ProcessFunction):
    """Parses the event and filter out if out of order. Yields Row objects."""
    def __init__(self):
        self.most_recent_timestamp = 0

    def process_element(self, event: str, _):
        try:
            d = json.loads(event)
            if d["timestamp"] > self.most_recent_timestamp:
                self.most_recent_timestamp = d["timestamp"]
                yield Row(
                    id = d["id"],
                    x = d["x"],
                    y = d["y"],
                    timestamp=d["timestamp"]
                )

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

# "State TTL is still not supported in PyFlink DataStream API." ~ Flink docs ;cccc
# TODO
# replace current ttl mechanism with redis
class CalculateInstSpeed(FlatMapFunction):
    """Yields Row a object with added value of the instantaneous speed calculated
    using distance/time_diff formula based on the current event and the least recent
    event 5 seconds back event time. Assumes data is ordered by time."""
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

    def flat_map(self, current_event: Row):
        queue = []
        for event in reversed(list(self.list_state.get())):
            if current_event.timestamp - event.timestamp <= 5:
                queue.append(event)
            else:
                break
        try:
            time_diff = current_event.timestamp - queue[-1].timestamp
            oldest_available_event = queue[-1]
            if time_diff >= 1:
                distance = ((current_event.x - oldest_available_event.x) ** 2 \
                         +  (current_event.y - oldest_available_event.y) ** 2) ** 0.5
                speed = distance / time_diff
                queue.append(current_event)
                self.list_state.update(queue)
                yield Row(
                    id = current_event.id,
                    x = current_event.x,
                    y = current_event.y,
                    timestamp = current_event.timestamp,
                    inst_speed = speed,
                    time_taken = (time.time() - current_event.timestamp)
                )
            else:
                queue.append(current_event)
                self.list_state.update(queue)

        except IndexError:
            self.list_state.add(current_event)
    
class AggregateEvents(AggregateFunction):
    """Aggregates events of specific id."""
    def create_accumulator(self) -> tuple[int, int]:
        return 0, 0
    
    def add(self, event: Row, accumulator: tuple[int, int]) -> tuple[int, int]:
        return event.id, accumulator[1] + 1
    
    def get_result(self, accumulator: tuple[int, int]) -> tuple[int, int]:
        return accumulator
    
    def merge(self, acc_a: tuple[int, int], acc_b: tuple[int, int]) -> tuple[int, int]:
        return acc_a[0], acc_a[1] + acc_b[1]
    
class LateOnTimeAggregator(CoMapFunction):
    def map1(self, on_time_event: tuple[int, int]) -> tuple[int, int]:
        return on_time_event[0], on_time_event[1]
    
    def map2(self, late_event: tuple[int, int]) -> tuple[int, int]:
        return -late_event[0], late_event[1]

class CreateLateOnTimeStatistic(AggregateFunction):
    """Returns a JSON string containing the accumulated count of late and on-time events for each id."""
    def create_accumulator(self) -> defaultdict[int, dict[str, int]]:
        return defaultdict(create_default_statistic)
    
    def add(self, event: tuple[int, int], accumulator: defaultdict[int, dict[str, int]]) \
        -> defaultdict[int, dict[str, int]]:
        if event[0] > 0:
            accumulator[event[0]]["on_time"] += event[1]
        else:
            accumulator[-event[0]]["late"] += event[1]
        return accumulator
    
    def get_result(self, accumulator: defaultdict[int, dict[str, int]]) -> str:
        return json.dumps(accumulator)
    
    def merge(self, acc_a: defaultdict[int, dict[str, int]], acc_b: defaultdict[int, dict[str, int]]) \
        -> defaultdict[int, dict[str, int]]:
        """Adds the count from acc_b to acc_a. Makes sure that keys present only in acc_b are accounted for."""
        set_a, set_b = set(acc_a), set(acc_b)
        for key in acc_a:
            acc_a[key]["on_time"] += acc_b[key]["on_time"]
            acc_a[key]["late"] += acc_b[key]["late"]
        for key in set_b - set_a:
            acc_a[key]["on_time"] += acc_b[key]["on_time"]
            acc_a[key]["late"] += acc_b[key]["late"]
        return acc_a

def main() -> None:
    """Holds main pipeline execution steps."""
    # TODO
    # probably i can set up config with docker compose file instead of this code below
    config = Configuration()
    config.set_string("python.fn-execution.bundle.size", "1")
    config.set_string("python.fn-execution.bundle.time", "0")
    config.set_string("metrics.latency.interval", "2000")
    config.set_string("python.executable", "/usr/bin/python3.9")
    env = StreamExecutionEnvironment.get_execution_environment(config)
    env.set_runtime_mode(RuntimeExecutionMode.STREAMING)
    env.set_parallelism(1)
    # flink_connector_name = "flink-sql-connector-kafka-4.0.0-2.0.jar"
    # prom_metrics_name = "flink-metrics-prometheus-2.0.0.jar"
    # kafka_jar = Path(__file__).resolve().parent / flink_connector_name
    # prom_jar = Path(__file__).resolve().parent / prom_metrics_name
    # kafka_jar = Path("/opt/flink") / flink_connector_name
    # prom_jar = Path("/opt/flink") / prom_metrics_name
    # env.add_jars(",".join([kafka_jar.as_uri(), prom_jar.as_uri()]))

    source = KafkaSource.builder() \
        .set_starting_offsets(KafkaOffsetsInitializer.latest()) \
        .set_bootstrap_servers(KAFKA_BROKER) \
        .set_topics(IN_TOPIC_NAME) \
        .set_group_id(GROUP_ID) \
        .set_value_only_deserializer(SimpleStringSchema()) \
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
    
    parsed_ds = ds \
        .process(
            func=ParseAndFilter(),
            output_type=Types.ROW_NAMED(
                ["id", "x", "y", "timestamp"],
                [Types.INT(), Types.FLOAT(), Types.FLOAT(), Types.DOUBLE()]
            )
        )
    
    keyed_parsed_ds = parsed_ds \
        .key_by(
            key_selector=(lambda event: event.id),
            key_type=Types.INT()
        )

    late_data_ds = parsed_ds \
        .get_side_output(LATE_DATA_TAG) \
        .key_by(
            key_selector=(lambda event: event.id),
            key_type=Types.INT()
        )
    
    aggregated_on_time_data_count = keyed_parsed_ds \
    .window(TumblingProcessingTimeWindows.of(size=Time.seconds(METRIC_AGGREGATION_WINDOW_SIZE))) \
    .aggregate(
            aggregate_function=AggregateEvents(),
            accumulator_type=Types.TUPLE([
                Types.INT(),
                Types.INT()
            ]),
            output_type=Types.TUPLE([
                Types.INT(),
                Types.INT()
            ])
        )
    
    aggregated_late_data_count = late_data_ds \
        .window(TumblingProcessingTimeWindows.of(size=Time.seconds(METRIC_AGGREGATION_WINDOW_SIZE))) \
        .aggregate(
            aggregate_function=AggregateEvents(),
            accumulator_type=Types.TUPLE([
                Types.INT(),
                Types.INT()
            ]),
            output_type=Types.TUPLE([
                Types.INT(),
                Types.INT()
            ])
        )
    
    aggregated_count_combined = aggregated_on_time_data_count \
        .connect(aggregated_late_data_count) \
        .map(
            func=(LateOnTimeAggregator()),
            output_type=Types.TUPLE([
                Types.INT(),
                Types.INT()
            ])
        )
    
    late_on_time_metric = aggregated_count_combined \
        .window_all(TumblingProcessingTimeWindows.of(size=Time.seconds(METRIC_AGGREGATION_WINDOW_SIZE))) \
        .aggregate(
            aggregate_function=CreateLateOnTimeStatistic(),
            accumulator_type=Types.PICKLED_BYTE_ARRAY(),
            output_type=Types.STRING()
        )
    
    enriched_ds = keyed_parsed_ds.flat_map(
            func=CalculateInstSpeed(),
            output_type=Types.ROW_NAMED(
                ["id", "x", "y", "timestamp", "inst_speed", "time_taken"],
                [Types.INT(), Types.FLOAT(), Types.FLOAT(), Types.DOUBLE(), Types.FLOAT(), Types.DOUBLE()]
            )
        )
    # TODO
    # add time constrains for each metrics window
    # TODO
    # make kafka the sink for all outputs, develop a way of keeping track of the time taken for the processing
    late_on_time_metric.print()
    enriched_ds.print()
    env.execute()
    

if __name__ == "__main__":
    main()

