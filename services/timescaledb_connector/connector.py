"""Custom connector forwarding data from a Kafka broekr to TimescaleDB."""
from kafka import KafkaConsumer
import psycopg
from config import IN_TOPIC_NAME, GROUP_ID, KAFKA_BROKER
from logging_setup import logger

