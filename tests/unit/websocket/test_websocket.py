"""Test module for the Kafka WebSocket bridge."""
from types import ModuleType
from unittest.mock import MagicMock, patch
import sys
import json
import asyncio

class MockAIOKafkaConsumer():
    """Mock AIOKafkaConsumer object.
    
    Args:
        topic (Any): Topic attribute.

        **kwargs (Any): kwargs.
    """
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
sys.modules["fastapi"] = MagicMock()
sys.modules["uvicorn"] = MagicMock()

from services.websocket.websocket.websocket_server import (
    create_consumer,
    consume_messages,
    KAFKA_BROKER,
    GROUP_ID,
    IN_TOPIC_NAME
)

def test_create_consumer():
    """Test consumer creation."""
    consumer = create_consumer()
    assert consumer.topic == IN_TOPIC_NAME
    assert consumer.bootstrap_servers == KAFKA_BROKER
    assert consumer.group_id == GROUP_ID
    assert consumer.auto_offset_reset == "latest"
    x = json.dumps({"k": "v"}).encode("utf-8")
    assert consumer.value_deserializer(x) == x.decode("utf-8")

def test_consume_messages():
    """Test forwarding messages to the WebSocket."""
    consumer = create_consumer()
    mock_connection = MagicMock()
    mock_connections = [mock_connection]
    with patch("services.websocket.websocket.websocket_server.active_connections", mock_connections):
        asyncio.run(consume_messages(consumer))
    mock_connection.send_text.assert_called_once()