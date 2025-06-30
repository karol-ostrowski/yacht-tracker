from kafka import KafkaConsumer

KAFKA_BROKER = "localhost:29092"
IN_TOPIC_NAME = "raw_sensor_data"
GROUP_ID = "raw_data_consumers"
OUT_TOPIC_NAME = "enriched_data"

# Create a Kafka consumer
consumer = KafkaConsumer(
    OUT_TOPIC_NAME,
    bootstrap_servers=KAFKA_BROKER,
    group_id=GROUP_ID,
    auto_offset_reset='latest',          # Start at the latest message
    value_deserializer=lambda m: m.decode('utf-8')  # Decode bytes to string
)

print(f"Listening to topic: {IN_TOPIC_NAME}")
try:
    for message in consumer:
        print(f"Received message: {message.value}")
except KeyboardInterrupt:
    print("Consumer interrupted. Exiting.")
finally:
    consumer.close()