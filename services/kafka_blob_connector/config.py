import os

KAFKA_BROKER = "broker:9092"
IN_TOPIC_NAME = "raw_sensor_data"
GROUP_ID = "kafka_blob_connector"

MAX_BUFFER = 200

AZURE_CONTAINER_NAME = os.environ["AZURE_CONTAINER_NAME"]
AZURE_CONNECTION_STRING = os.environ["AZURE_CONNECTION_STRING"]