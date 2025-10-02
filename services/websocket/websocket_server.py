"""WebSocket Kafka bridge using FastAPI.

This module implements a FastAPI application that:
- Consumes messages from a Kafka topic asynchronously.
- Broadcasts Kafka messages to connected WebSocket clients.
- Handles connections and disconnects.
- Provides a health-check endpoint.
"""
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from aiokafka import AIOKafkaConsumer
from contextlib import asynccontextmanager
import asyncio
import uvicorn
from logging_setup import logger
from config import IN_TOPIC_NAME, KAFKA_BROKER, GROUP_ID

active_connections = []

def create_consumer() -> AIOKafkaConsumer:
    """Creates an asynchronous Kafka consumer.
    
    Returns:
        consumer (AIOKafkaConsumer): Asynchronous Kafka consumer connected to the broker,
        topic and group specified in the config file. 
    """
    consumer = AIOKafkaConsumer(
        IN_TOPIC_NAME,
        bootstrap_servers=KAFKA_BROKER,
        group_id=GROUP_ID,
        auto_offset_reset="latest",
        value_deserializer=lambda x: x.decode("utf-8")
    )

    logger.info(f"Connected a consumer to {KAFKA_BROKER}")

    return consumer

async def consume_messages() -> None:
    """Asynchronous loop sending data from Kafka topic to the websocket until stopped."""
    consumer = create_consumer()
    await consumer.start()

    try:
        async for message in consumer:
            if active_connections:
                # Copy to avoid modifications made by asynchronous code when inside the loop.
                connections_copy = active_connections.copy()
                for connection in connections_copy:
                    try:
                        await connection.send_text(message.value)
                        logger.info(f"Sent message: {message.value}")
                    except Exception as e:
                        logger.error(f"Failed to deliver a message: {e}")
                        if connection in active_connections:
                            active_connections.remove(connection)

    finally:
        await consumer.stop()
        logger.info("Kafka consumer stopped.")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Defines the on startup (before yield) and on shutdown logic (after yield).
    
    Args:
        app (FastAPI): Instance of the FastAPI application.
    """
    consume_task = asyncio.create_task(consume_messages())
    yield
    for connection in active_connections:
        active_connections.remove(connection)
    logger.info("Closed all connections.")
    consume_task.cancel()
    try:
        await consume_task
    except asyncio.CancelledError:
        pass

app = FastAPI(lifespan=lifespan)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """Accepts websocket connections, tracks them and handles errors.
    
    Args:
        websocket (WebSocket): Instance of a WebSocket connection. Provided by the client when accessing.
    """
    await websocket.accept()
    active_connections.append(websocket)
    logger.info(f"A client has connected.")

    try:
        while True:
            # to keep the connection alive and not bother the CPU too much
            await asyncio.sleep(3600)
    except WebSocketDisconnect as e:
        logger.error(f"Websocket disconnected: {e}")
    except Exception as e:
        logger.error(f"Connection failed: {e}")

@app.get("/health")
async def status() -> dict[str, str]:
    """Endpoint for checking if a connection can be established."""
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)