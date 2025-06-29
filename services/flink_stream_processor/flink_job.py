"""Flink job for enriching the sensor data."""
import logging
import json
import time
from typing import Iterable, Tuple
from pathlib import Path
from pyflink.common.serialization import SimpleStringSchema
from pyflink.common.watermark_strategy import WatermarkStrategy
from pyflink.common.typeinfo import Types
from pyflink.datastream import StreamExecutionEnvironment
from pyflink.datastream.connectors.kafka import KafkaSource, KafkaOffsetsInitializer
from pyflink.datastream import MapFunction, RuntimeContext
from pyflink.datastream.state import ListStateDescriptor, StateTtlConfig, Time
from pyflink.datastream.functions import FlatMapFunction

KAFKA_BROKER = "localhost:29092"
IN_TOPIC_NAME = "raw_sensor_data"
GROUP_ID = "raw_data_consumers"

logger = logging.getLogger("Flink job")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

def safe_parse(x: str):
    """Makes sure the script keeps running if parsing fails."""
    try:
        d = json.loads(x)
        return {
            "id": str(d["id"]),
            "x": str(d["x"]),
            "y": str(d["y"]),
            "timestamp": str(d["timestamp"])
        }
    except json.JSONDecodeError as e:
        logger.error(f"An error occured during parsing: {e}")
        return {
            "id": "999",
            "x": "0",
            "y": "0",
            "timestamp": f"{time.time()}"
        }

# class MyProcessWindowFunction(ProcessWindowFunction):

#     def process(self, key: str, context: ProcessWindowFunction.Context,
#                 elements: Iterable[Tuple[str, int]]) -> Iterable[str]:
#         count = 0
#         for _ in elements:
#             count += 1
#         yield "Window:` {} count: {}".format(context.window(), count)

# "State TTL is still not supported in PyFlink DataStream API." ~ Flink docs ;cccc
# Code below works as expected but the elements from the message_buffer are never removed.
# Decided to try a different appraoch (and keep this code for later, maybe will they patch it).
'''class CalculateAvgSpeed(MapFunction):
    def open(self, ctx: RuntimeContext):
        ttl_config = StateTtlConfig \
            .new_builder(Time.seconds(5)) \
            .set_update_type(StateTtlConfig.UpdateType.OnCreateAndWrite) \
            .set_state_visibility(StateTtlConfig.StateVisibility.NeverReturnExpired) \
            .build()
        descriptor = ListStateDescriptor(
            "message_buffer",
            Types.PICKLED_BYTE_ARRAY()
        )
        descriptor.enable_time_to_live(ttl_config)

        self.message_buffer = ctx.get_list_state(descriptor)

    def map(self, message):
        
        self.message_buffer.add(message)
        windowed_messaged = list(self.message_buffer.get())
        try:
            if float(message["timestamp"]) - float(windowed_messaged[0]["timestamp"]) > 0.5:
                distance = (float(message["x"]) - float(windowed_messaged[0]["x"])) ** 2 \
                         + (float(message["y"]) - float(windowed_messaged[0]["y"])) ** 2
                time_delta = float(message["timestamp"]) - float(windowed_messaged[0]["timestamp"])
                speed = distance / time_delta
                message["speed"] = str(speed)
                message["len"] = str(len(windowed_messaged))
                message["time delta"] = str(time_delta)
                return message
            
            logger.info(f"Unable to calculate the speed due to out of order data.")
            message["speed"] = "0"
            return message
        
        except ZeroDivisionError:
            logger.error(f"Unable to calculate the speed due to the division by zero.")
            message["speed"] = "0"
            return message'''

def main() -> None:
    """Holds main pipeline execution steps."""
    env = StreamExecutionEnvironment.get_execution_environment()
    flink_connector_name = "flink-sql-connector-kafka-4.0.0-2.0.jar"
    kafka_jar = Path(__file__).resolve().parent / flink_connector_name
    env.add_jars(kafka_jar.as_uri())

    source = KafkaSource.builder() \
        .set_starting_offsets(KafkaOffsetsInitializer.latest()) \
        .set_bootstrap_servers(KAFKA_BROKER) \
        .set_topics(IN_TOPIC_NAME) \
        .set_group_id(GROUP_ID) \
        .set_value_only_deserializer(SimpleStringSchema()) \
        .build()
    
    ds = env.from_source(source=source,
                         watermark_strategy=WatermarkStrategy.no_watermarks(),
                         source_name="raw_data_source")
    
    parsed_ds = ds.map(
        func=safe_parse,
        output_type=Types.MAP(
            key_type_info=Types.STRING(),
            value_type_info=Types.STRING()
        )
    )

    enriched_ds = parsed_ds \
        .key_by(
            key_selector=(lambda x: x["id"]),
            key_type=Types.STRING()
        ) \
        .map(
            func=CalculateAvgSpeed(),
            output_type=Types.MAP(
                key_type_info=Types.STRING(),
                value_type_info=Types.STRING()
            )
        )

    # window = parsed_ds \
    # .key_by(lambda v: v[0]) \
    # .window(TumblingEventTimeWindows.of(Time(50))) \
    # .process(MyProcessWindowFunction())

    enriched_ds.print()

    env.execute()
    

if __name__ == "__main__":
    main()