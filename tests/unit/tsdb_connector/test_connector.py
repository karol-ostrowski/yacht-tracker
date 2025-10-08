"""Test module for the TimescaleDB connector."""
from types import ModuleType
from unittest.mock import MagicMock, patch
import sys
import json
import asyncio

class MockAIOKafkaConsumer():
    def __init__(self, topic, **kwargs):
        self.topic = topic
        for key, value in kwargs.items():
            setattr(self, key, value)

        self.messages = [MagicMock()]

    def __aiter__(self):
        return self

    async def __anext__(self):
        if self.messages:
            return self.messages.pop(0)
        else:
            raise StopAsyncIteration
        
    async def start(self):
        pass
    
    async def stop(self):
        pass


aiokafka = ModuleType("aiokafka")
aiokafka.AIOKafkaConsumer = MockAIOKafkaConsumer

sys.modules["aiokafka"] = aiokafka
sys.modules["logging"] = MagicMock()
sys.modules["logging.handlers"] = MagicMock()
sys.modules["pathlib"] = MagicMock()
sys.modules["psycopg"] = MagicMock()

from services.timescaledb_connector.timescaledb_connector.connector import (
    create_consumer,
    consume_messages,
    KAFKA_BROKER,
    GROUP_ID,
    IN_TOPIC_NAME,
    MAX_BUFFER
)

def test_create_consumer():
    """Test consumer creation."""
    consumer = create_consumer()
    assert consumer.topic == IN_TOPIC_NAME
    assert consumer.bootstrap_servers == KAFKA_BROKER
    assert consumer.group_id == GROUP_ID
    assert consumer.auto_offset_reset == "earliest"
    x = json.dumps({"k": "v"}).encode("utf-8")
    assert consumer.value_deserializer(x) == json.loads(x.decode("utf-8"))

def test_consume_messages_batching():
    """Test if the function batches messages before releasing the semaphore."""
    consumer = create_consumer()
    queue = MagicMock()
    semaphore = MagicMock()
    asyncio.run(consume_messages(
        consumer, queue, semaphore
    ))
    semaphore.release.assert_not_called()

def test_consume_messages_full_batch():
    """Test if the function releases the semaphore when buffer is full."""
    consumer = create_consumer()
    queue = MagicMock()
    semaphore = MagicMock()
    mock_buffer = MagicMock()
    mock_buffer.__len__.return_value = MAX_BUFFER
    with patch("builtins.list", return_value=mock_buffer):
        asyncio.run(consume_messages(
            consumer, queue, semaphore
        ))
    semaphore.release.assert_called_once()