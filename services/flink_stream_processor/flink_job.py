"""Flink job for enriching the sensor data and creating metrics."""
from pyflink.common.typeinfo import Types
from pyflink.common.watermark_strategy import WatermarkStrategy
from pyflink.common.typeinfo import Types
from transformations import ParseAndFilter, LateMetrics, CalculateInstSpeed, OnTimeEventCounter, OnTimeTotalTimeCounter
from pyflink.common.serialization import SimpleStringSchema
from pyflink.common.typeinfo import Types
from pyflink.datastream.connectors.kafka import KafkaSource, KafkaOffsetsInitializer, KafkaSink, KafkaRecordSerializationSchema
from pyflink.datastream.formats.json import JsonRowSerializationSchema
from pyflink.common import Configuration
from pyflink.datastream import StreamExecutionEnvironment, RuntimeExecutionMode
from utils import LATE_DATA_TAG
from config import KAFKA_BROKER, GROUP_ID, IN_TOPIC_NAME, OUT_TOPIC_NAME, PARALLELISM
from logging_setup import logger

def main() -> None:
    """Holds main pipeline execution steps."""
    config = Configuration()
    config.set_string("python.fn-execution.bundle.size", "1")
    config.set_string("python.fn-execution.bundle.time", "0")
    config.set_string("metrics.latency.interval", "10000")
    config.set_string("python.executable", "/usr/bin/python3.9")
    logger.info(f"Creating a stream execution environment.")
    env = StreamExecutionEnvironment.get_execution_environment(config)
    env.add_python_file("config.py")
    env.add_python_file("__init__.py")
    env.add_python_file("logging_setup.py")
    env.add_python_file("transformations.py")
    env.add_python_file("utils.py")
    env.set_runtime_mode(RuntimeExecutionMode.STREAMING)
    env.set_parallelism(PARALLELISM)

    logger.info(f"Building a Kafka source.")
    kafka_source = KafkaSource.builder() \
        .set_starting_offsets(KafkaOffsetsInitializer.latest()) \
        .set_bootstrap_servers(KAFKA_BROKER) \
        .set_topics(IN_TOPIC_NAME) \
        .set_group_id(GROUP_ID) \
        .set_value_only_deserializer(SimpleStringSchema()) \
        .build()

    logger.info(f"Building a record serialized.")
    serialization_schema = JsonRowSerializationSchema \
        .builder() \
        .with_type_info(
            type_info=Types.ROW_NAMED(
                ["id", "x", "y", "timestamp", "inst_speed", "time_taken"],
                [Types.INT(), Types.FLOAT(), Types.FLOAT(), Types.DOUBLE(), Types.FLOAT(), Types.FLOAT()]
            )
        ).build()
    record_serializer = KafkaRecordSerializationSchema.builder() \
        .set_topic(OUT_TOPIC_NAME) \
        .set_value_serialization_schema(serialization_schema) \
        .build()
    logger.info(f"Building a Kafka sink.")
    kafka_sink = KafkaSink.builder() \
        .set_bootstrap_servers(KAFKA_BROKER) \
        .set_record_serializer(record_serializer) \
        .build()

    ds = env.from_source(source=kafka_source,
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
    
    late_data_ds.process(
        func=LateMetrics()
    )
    
    enriched_ds = keyed_parsed_ds.flat_map(
            func=CalculateInstSpeed(),
            output_type=Types.ROW_NAMED(
                ["id", "x", "y", "timestamp", "inst_speed", "time_taken"],
                [Types.INT(), Types.FLOAT(), Types.FLOAT(), Types.DOUBLE(), Types.FLOAT(), Types.FLOAT()]
            )
        )
    
    keyed_parsed_ds.process(
        func=OnTimeEventCounter()
    )

    enriched_ds.process(
        func=OnTimeTotalTimeCounter()
    )

    enriched_ds.sink_to(kafka_sink)
    logger.info(f"Executing the environment.")
    env.execute()
    

if __name__ == "__main__":
    main()