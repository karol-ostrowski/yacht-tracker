from kafka import KafkaConsumer
from datetime import datetime
import logging
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

KAFKA_BROKER = "broker:9092"
TOPIC_NAME = "integer-stream"
GROUP_ID = "int-stream-consumer-group"

def create_consumer():
    try:
        consumer = KafkaConsumer(
            TOPIC_NAME,
            bootstrap_servers=[KAFKA_BROKER],
            auto_offset_reset="earliest",
            enable_auto_commit=True,
            auto_commit_interval_ms=2000,
            group_id=GROUP_ID,
            value_deserializer=lambda x: json.loads(x.decode("utf-8"))
        )
        logger.info(f"Connected to Kafka broker at {KAFKA_BROKER}")
        return consumer
    except Exception as e:
        logger.error(f"Failed to create consumer: {e}")
        raise

def consumer_data(consumer):
    try:
        logger.info("Starting consuming messages...")
        for message in consumer:
            value = message.value
            timestamp = datetime.fromtimestamp(value["timestamp"]/1000).strftime("%Y-%m-%d %H:%M:%S")
            logger.info(
                f"Received integer: {value["integer"]}"
                f"Timestamp: {timestamp}"
                f"Partition: {message.partition}"
                f"Offset: {message.offset}"
            )

    except KeyboardInterrupt:
        logger.info("Consumer interrupted")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
    finally:
        consumer.close()

if __name__ == "__main__":
    consumer = create_consumer()
    consumer_data(consumer)