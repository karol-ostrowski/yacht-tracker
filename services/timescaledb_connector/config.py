"""Config file for variables used during creation of a Kafka consumer
for the custom TimescaleDB connector."""

KAFKA_BROKER = "broker:9092"
IN_TOPIC_NAME = "enriched_data"
GROUP_ID = "enriched_data_consumers"