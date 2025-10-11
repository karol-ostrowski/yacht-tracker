"""Config file for variables used during creation of a asynchronous Kafka consumer
broadcasting messages to FastAPI WebSocket."""
KAFKA_BROKER = "broker:9092"
IN_TOPIC_NAME = "enriched_data"
GROUP_ID = "websocket_consumers"