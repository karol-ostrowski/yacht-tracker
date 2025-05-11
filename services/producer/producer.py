from kafka import KafkaProducer
import time
import logging
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

KAFKA_BROKER = "broker:9092"
TOPIC_NAME = "integer-stream"

def create_producer():
    try:
        producer = KafkaProducer(
            bootstrap_servers=[KAFKA_BROKER],
            value_serializer= lambda x: json.dumps(x).encode("utf-8"),
            retries = 3
        )
        logger.info(f"Connected to Kafka broker at {KAFKA_BROKER}")
        return producer
    except Exception as e:
        logger.error(f"Falied to create a producer: {e}")
        raise

def on_delivery_success(record_metadata):
    logger.info(f"Delivered message to {record_metadata.topic} (partition: {record_metadata.partition}, offset: {record_metadata.offset})")

def on_delivery_failure(e):
    logger.error(f"Failed to deliver message: {e}")

def produce_data(producer):
    counter = 0
    try:
        while True:
            message = {
                "integer" : counter,
                "timestamp" : int(time.time() * 1000)
            }

            producer.send(
                TOPIC_NAME,
                value=message,
            ).add_callback(on_delivery_success).add_errback(on_delivery_failure)

            logger.debug(f"Sent integer : {counter}")
            counter += 1
            time.sleep(2)
    except KeyboardInterrupt:
        logger.info("Producer interrupted")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
    finally:
        producer.flush()
        producer.close()

if __name__ == "__main__":
    producer = create_producer()
    produce_data(producer)