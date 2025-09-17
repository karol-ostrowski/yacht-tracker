"""Test module for the data generator script."""
import pytest
import json
import sys
from unittest.mock import Mock, patch, MagicMock
from types import ModuleType

class MockKafkaProducer():
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

kafka = ModuleType("kafka")
kafka.KafkaProducer = MockKafkaProducer

sys.modules["pathlib"] = MagicMock()
sys.modules["logging"] = MagicMock()
sys.modules["logging.handlers"] = MagicMock()
sys.modules["kafka"] = kafka

from data_generator.kafka_producer import (
    create_producer, 
    generate_sailboats, 
    produce_data
)


@pytest.fixture
def mock_sailboat():
    """Mock sailboat fixture."""
    sailboat = Mock()
    sailboat.id = 1
    sailboat.x = 22.2
    sailboat.y = 33.3
    return sailboat


def test_create_producer():
    """Test successful creation of a Kafka producer."""
    result = create_producer()
    assert result.__dict__["bootstrap_servers"] == ["broker:9092"]

    serializer = result.__dict__["value_serializer"]
    assert serializer({"k": "v"}) == json.dumps({"k": "v"}).encode("utf-8")


@patch('data_generator.kafka_producer.Sailboat')
def test_generate_sailboats(mock_sailboat_class,
                            mock_sailboat):
    """Test generating given number of sailboats."""
    mock_sailboat_class.return_value = mock_sailboat
    num_of_boats = 10

    result = generate_sailboats(num_of_sailboats=num_of_boats)

    assert len(result) == num_of_boats
    assert result[num_of_boats // 2] == mock_sailboat_class.return_value


@patch('data_generator.kafka_producer.Sailboat')
def test_generate_sailboats_default_value(mock_sailboat_class,
                                          mock_sailboat):
    """Test generating default number of sailboats."""
    mock_sailboat_class.return_value = mock_sailboat

    result = generate_sailboats()

    assert len(result) == 1
    assert result[0] == mock_sailboat_class.return_value


@patch('time.sleep')
@patch('time.time')
@patch('random.uniform')
@patch('data_generator.kafka_producer.generate_sailboats')
def test_produce_data(mock_generate_sailboats,
                      mock_uniform,
                      mock_time,
                      mock_sleep,
                      mock_sailboat):
    """Test produce_data function for a single iteration."""

    mock_generate_sailboats.return_value = [mock_sailboat]
    mock_time.return_value = 1234567890.0
    mock_uniform.side_effect = [0.1, 0.55]
    mock_producer = Mock()
    
    # break the loop after one iteration
    iteration_count = 0
    def side_effect_sleep(_):
        nonlocal iteration_count
        iteration_count += 1
        if iteration_count >= 1:
            raise KeyboardInterrupt()
    
    mock_sleep.side_effect = side_effect_sleep
    
    with pytest.raises(KeyboardInterrupt):
        produce_data(mock_producer, len(mock_generate_sailboats.return_value))
    
    call_args = mock_producer.send.call_args
    assert call_args[1]["topic"] == "raw_sensor_data"

    message = call_args[1]["value"]
    assert message["id"] == 1
    assert message["x"] == 22.2
    assert message["y"] == 33.3
    assert message["timestamp"] == 1234567890.0


@patch('time.sleep')
@patch('time.time')
@patch('random.uniform')
@patch('data_generator.kafka_producer.generate_sailboats')
def test_produce_data_produce_late_event(mock_generate_sailboats,
                      mock_uniform,
                      mock_time,
                      mock_sleep,
                      mock_sailboat):
    """Test producing a late event."""

    mock_generate_sailboats.return_value = [mock_sailboat]
    mock_time.return_value = 1234567890.0
    mock_uniform.side_effect = [0.01, 0.55]
    mock_producer = Mock()
    
    # break the loop after one iteration
    iteration_count = 0
    def side_effect_sleep(_):
        nonlocal iteration_count
        iteration_count += 1
        if iteration_count >= 1:
            raise KeyboardInterrupt()
    
    mock_sleep.side_effect = side_effect_sleep
    
    with pytest.raises(KeyboardInterrupt):
        produce_data(mock_producer, len(mock_generate_sailboats.return_value))
    
    call_args = mock_producer.send.call_args
    assert call_args[1]["topic"] == "raw_sensor_data"
    
    call_args = mock_producer.send.call_args
    assert call_args[1]["topic"] == "raw_sensor_data"
    message = call_args[1]["value"]
    assert message["id"] == 1
    assert message["x"] == 22.2
    assert message["y"] == 33.3
    assert message["timestamp"] == 1234567890.0 - 5