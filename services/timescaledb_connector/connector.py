"""Custom connector forwarding data from a Kafka broker to TimescaleDB."""
from aiokafka import AIOKafkaConsumer
from collections import deque
import psycopg
import asyncio
import json
from config import IN_TOPIC_NAME, GROUP_ID, KAFKA_BROKER
from logging_setup import logger

MAX_BUFFER = 20

def create_consumer() -> AIOKafkaConsumer:
    """Creates an asynchronous Kafka consumer.
    
    Returns:
        consumer (AIOKafkaConsumer): Asynchronous Kafka consumer.
    """
    consumer = AIOKafkaConsumer(
        IN_TOPIC_NAME,
        bootstrap_servers=KAFKA_BROKER,
        group_id=GROUP_ID,
        auto_offset_reset="latest",
        value_deserializer=lambda x: json.loads(x.decode("utf-8"))
    )
    logger.info(f"Connected a consumer to {KAFKA_BROKER}")
    return consumer

async def consume_messages(consumer: AIOKafkaConsumer, queue: deque, semaphore: asyncio.Semaphore) -> None:
    """Consumes messages from Kafka topic and batches them.
    
    Args:
        consumer (AIOKafkaConsumer): Asynchronous Kafka consumer.

        queue (collections.deque): Stores batched messages to be sent to the database.
        
        semaphore (asyncio.Semaphore): Semaphore.
    """
    buffer = []
    try:
        await consumer.start()
        logger.info("Consumer started")
        
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
    finally:
        await consumer.stop()
        logger.info("Kafka consumer stopped.")

async def main():
    """Contains the main logic."""
    queue = deque()
    semaphore = asyncio.Semaphore(value=0)
    consumer = create_consumer()
    
    try:
        async with await psycopg.AsyncConnection.connect(
            "dbname=tsdb user=karol password=pass host=tsdb port=5432"
        ) as aconn:
            consume_task = asyncio.create_task(
                consume_messages(consumer,
                                 queue,
                                 semaphore)
            )
            
            async with aconn.cursor() as cur:
                while True:
                    try:
                        await semaphore.acquire()
                        batch = queue.popleft()
                        
                        await cur.executemany(
                            """INSERT INTO readings 
                            (yacht_id, x, y, timestamp, inst_speed, time_taken) 
                            VALUES (%(id)s, %(x)s, %(y)s, to_timestamp(%(timestamp)s), %(inst_speed)s, %(time_taken)s)""",
                            batch
                        )
                        await aconn.commit()
                        
                    except Exception as e:
                        logger.error(f"An error occured: {e}")
                        await aconn.rollback()
                        
    except KeyboardInterrupt:
        logger.info("Shutting down the Kafka TimescaleDB connector.")
    finally:
        consume_task.cancel()
        try:
            await consume_task
        except asyncio.CancelledError:
            pass

if __name__ == "__main__":
    asyncio.run(main())