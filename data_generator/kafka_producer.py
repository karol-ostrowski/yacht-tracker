"""A script for generating fake sensor data. For development purposes."""
import logging.handlers
from kafka import KafkaProducer
from Sailboat import Sailboat
import logging
import json
import time
import random
import argparse
from pathlib import Path

KAFKA_BROKER = "localhost:29092"
TOPIC_NAME = "raw_sensor_data"

handler = logging.handlers.TimedRotatingFileHandler(
    filename=Path(__file__).parent.parent / "logs" / "data_generator" / "data_generator.log",
    when="m",
    interval=5,
    backupCount=6
)

formatter = logging.Formatter(
    fmt="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

handler.setFormatter(formatter)

logger = logging.getLogger("data_generator")
logger.addHandler(handler)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"),

def create_producer() -> KafkaProducer:
    """Creates a Kafka producer.
    
    Returns:
        KafkaProducer: a Kafka producer connected to a broker specified in a global variable.
    """
    producer = KafkaProducer(
        bootstrap_servers = [KAFKA_BROKER],
        value_serializer = lambda x : json.dumps(x).encode("utf-8")
    )
    # TODO
    # this logger info is not that useful, improve it
    logger.info(f"Connected a producer to {KAFKA_BROKER}")
    return producer

def generate_sailboats(num_of_sailboats: int = 1) -> list[Sailboat]:
    """Creates a given number of Sailboat objects.

    Args:
        num_of_sailboats (int): Number of sailboats to be generated, defaults to 1.

    Returns:
        list[Sailboat]: List of Sailboat objects.
    """
    sailboats = []
    for i in range(num_of_sailboats):
        sailboats.append(Sailboat(i + 1))
    logger.info(f"Generated {num_of_sailboats} sailboats.")
    return sailboats

def on_delivery_success(record_metadata, message):
    """On delivery confirmation displays a logger info message."""
    logger.info(f"Delivered: id={message['id']} x={message['x']} y={message['y']} timestamp={message['timestamp']} topic={record_metadata.topic}")

def on_delivery_failure(e):
    """On delivery failure displays a logger error message."""
    logger.error(f"Failed to deliver a message: {e}")

def produce_data(producer: KafkaProducer, num_of_sailboats: int = 1) -> None:
    """Executes the loop sending fake sensor data to the Kafka broker.

    Makes a move with a Sailboat and sends the id, x-coordinate, 
    y-coordinate and current timestamp to the Kafka broker. 
    Randomly picks a Sailboat without returning, after moving
    all available Sailboats repopulates the list and cycles again.
    Sends a message 20-100 times a second. Loops until stopped manually.

    Args:
        producer (KafkaProducer): Kafka producer that should send the Sailboat data.
        num_of_sailboats (int): Number of sailboats to be generated, defaults to 1.
    """
    try:
        sailboats = generate_sailboats(num_of_sailboats)
        while True:
            shuffled_sailboats = sailboats.copy()
            random.shuffle(shuffled_sailboats)
            while shuffled_sailboats:
                moving_sailboard = shuffled_sailboats.pop()
                moving_sailboard.move()
                timestamp = time.time()
                if random.uniform(0, 1) > 0.50:
                    timestamp -= 5
                message = {
                    "id" : moving_sailboard.id,
                    "x" : moving_sailboard.x,
                    "y" : moving_sailboard.y,
                    "timestamp" : timestamp,
                }
                producer.send(
                    TOPIC_NAME,
                    value=message
                ) \
                .add_callback(lambda record_metadata: on_delivery_success(record_metadata, message)) \
                .add_errback(on_delivery_failure)
                # TODO
                # make this waiting mechanism not stupid
                time.sleep(random.uniform(0.1, 0.15))
    finally:
        logger.info("Flushing messages and closing the producer...")
        producer.flush()
        producer.close()
        logger.info("Producer correctly closed.")
        
def main():
    """Parses the possible command line argument, creates a predefined Kafka producer
    and starts producing and sending fake sensor data to the predefined Kafka broker.
    """
    parser = argparse.ArgumentParser("Fake sailboat data generator")
    parser.add_argument(
        "--sailboats", "-S", type=int, default=1, help="Number of fake sailboats."
        )
    args = parser.parse_args()
    producer = create_producer()
    produce_data(producer=producer, num_of_sailboats=args.sailboats)

if __name__ == "__main__":
    main()
