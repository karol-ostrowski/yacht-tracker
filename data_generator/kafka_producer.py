from kafka import KafkaProducer
from sailboat_data_simulator import Sailboat
import logging
import json
import time
import random
import argparse

logger = logging.getLogger("Data generator")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S")

KAFKA_BROKER = "broker:9092"
TOPIC_NAME = "raw_sensor_data"

def create_producer() -> KafkaProducer:
    producer = KafkaProducer(
        bootstrap_servers = KAFKA_BROKER,
        value_serializer = lambda x : json.dumps(x).encode("utf-8")
    )
    logger.info(f"Connected a producer to {KAFKA_BROKER}")
    return producer

def generate_sailboats(number_of_sailboats: int = 1) -> list[Sailboat]:
    sailboats = []
    for i in range(number_of_sailboats):
        sailboats.append(Sailboat(i))
    logger.info(f"Generated {number_of_sailboats} sailboats")
    return sailboats

def on_delivery_success(record_metadata):
    logger.info(f"Delivered a message to topic {record_metadata.topic}")

def on_delivery_failure(e):
    logger.error(f"Failed to deliver a message: {e}")

def produce_data(producer: KafkaProducer, number_of_sailboats: int = 1 ) -> None:
    try:
        sailboats = generate_sailboats(number_of_sailboats)
        while True:
            shuffled_sailboats = sailboats.copy()
            random.shuffle(shuffled_sailboats)
            while shuffled_sailboats:
                moving_sailboard = shuffled_sailboats.pop()
                moving_sailboard.move()
                message = {
                    "id" : moving_sailboard.id,
                    "x" : moving_sailboard.x,
                    "y" : moving_sailboard.y,
                    "timestamp" : int(time.time() * 1000)
                }
                producer.send(
                    TOPIC_NAME,
                    value=message
                ).add_callback(on_delivery_success).add_errback(on_delivery_failure)
                time.sleep(random.uniform(0.01, 0.05))
    finally:
        logger.info("Flushing messages and closing the producer...")
        producer.flush()
        producer.close()
        logger.info("Producer correctly closed")

if __name__ == "__main__":
    parser = argparse.ArgumentParser("Fake sailboat data generator")
    parser.add_argument("--sailboats", "-S", type=int, default=1, help="Number of fake sailboats")
    args = parser.parse_args()
    producer = create_producer()
    produce_data(producer=producer, number_of_sailboats=args.sailboats)