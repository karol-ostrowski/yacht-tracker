"""Custom connector sending batched data from a Kafka broker to an Azure Blob Storage instance."""
from aiokafka import AIOKafkaConsumer
from azure.storage.blob.aio import ContainerClient
from collections import deque
from datetime import datetime
import asyncio
import json
from services.kafka_blob_connector.kafka_blob_connector.config import(
    KAFKA_BROKER,
    GROUP_ID,
    IN_TOPIC_NAME,
    MAX_BUFFER,
    AZURE_CONTAINER_NAME,
    AZURE_CONNECTION_STRING
)
from services.kafka_blob_connector.kafka_blob_connector.logging_setup import logger

def create_consumer() -> AIOKafkaConsumer:
    """Creates an asynchronous Kafka consumer.
    
    Returns:
        consumer (AIOKafkaConsumer): Asynchronous Kafka consumer.
    """
    consumer = AIOKafkaConsumer(
        IN_TOPIC_NAME,
        bootstrap_servers=KAFKA_BROKER,
        group_id=GROUP_ID,
        auto_offset_reset="earliest",
        value_deserializer=lambda x: json.loads(x.decode("utf-8"))
    )
    return consumer

async def consume_messages(
    consumer: AIOKafkaConsumer,
    queue: deque,
    semaphore: asyncio.Semaphore
) -> None:
    """Consumes messages from Kafka topic and batches them.
    
    Args:
        consumer (AIOKafkaConsumer): Asynchronous Kafka consumer.

        queue (deque): Stores messages to be batched for sending.

        semaphore (Semaphore): A semaphore.
    """
    buffer = list()
    
    try:
        await consumer.start()
        logger.info("Consumer started.")
        
        async for message in consumer:
            buffer.append(message.value)

            if len(buffer) >= MAX_BUFFER:
                queue.append(buffer[:MAX_BUFFER])
                buffer = buffer[MAX_BUFFER:]
                semaphore.release()
                
    except asyncio.CancelledError:
        if buffer:
            queue.append(buffer)
            semaphore.release()
        raise
    finally:
        await consumer.stop()
        logger.info("Kafka consumer stopped.")


async def upload_to_blob(container_client: ContainerClient, batch: list) -> None:
    """Uploads a batch of messages to Azure Blob Storage.
    
    Args:
        container_client (ContainerClient): Azure Container client.

        batch (list): List of messages to upload.
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    blob_name = f"raw_data/{timestamp}.json"
    blob_client = container_client.get_blob_client(blob=blob_name)
    
    data = json.dumps(batch)
    await blob_client.upload_blob(data, overwrite=True)
    logger.info(f"Uploaded data to {blob_name}.")


async def main():
    """Contains the main logic."""
    queue = deque()
    semaphore = asyncio.Semaphore(value=0)
    consumer = create_consumer()
    
    try:
        async with ContainerClient.from_connection_string(
            AZURE_CONNECTION_STRING,
            container_name=AZURE_CONTAINER_NAME
        ) as container_client:
            logger.info(f"Connected to container {AZURE_CONTAINER_NAME}")
            
            consume_task = asyncio.create_task(
                consume_messages(consumer, queue, semaphore)
            )
            
            while True:
                await semaphore.acquire()
                if queue:
                    batch = queue.popleft()
                    try:
                        await upload_to_blob(container_client, batch)
                    except Exception as e:
                        logger.error(f"An error occurred during upload: {e}")
                        queue.appendleft(batch)
                        semaphore.release()
                        
    except KeyboardInterrupt:
        logger.info("Shutting down the Kafka to Azure Blob connector.")
    finally:
        consume_task.cancel()
        try:
            await consume_task
        except asyncio.CancelledError:
            pass

if __name__ == "__main__":
    asyncio.run(main())