"""Tests for the data generator script."""
import pytest
import json
from unittest.mock import Mock, patch
with patch("pathlib.Path.mkdir") as mock_mkdir, \
     patch("logging.handlers.TimedRotatingFileHandler") as mock_handler:
    from data_generator.kafka_producer import (
        create_producer, 
        generate_sailboats, 
        produce_data
    )

@pytest.fixture
def mock_producer():
    """Mock Kafka producer fixture."""
    producer = Mock()
    future = Mock()
    producer.send.return_value = future
    future.add_callback.return_value = future
    future.add_errback.return_value = future
    return producer

@pytest.fixture
def mock_sailboat():
    """Mock sailboat fixture."""
    sailboat = Mock()
    sailboat.id = 1
    sailboat.x = 22.2
    sailboat.y = 33.3
    return sailboat

@patch('data_generator.kafka_producer.KafkaProducer')
def test_create_producer_success(mock_kafka_producer):
    """Test successful creation of Kafka producer."""
    mock_producer_instance = Mock()
    mock_kafka_producer.return_value = mock_producer_instance

    result = create_producer()

    called_kwargs = mock_kafka_producer.call_args[1]
    assert called_kwargs["bootstrap_servers"] == ["broker:9092"]

    serializer = called_kwargs["value_serializer"]
    assert serializer({"k": "v"}) == json.dumps({"k": "v"}).encode("utf-8")

    assert result is mock_producer_instance

@patch('data_generator.kafka_producer.Sailboat')
def test_generate_sailboats(mock_sailboat_class):
    """Test generating given number of sailboats."""
    
    num_of_boats = 10

    result = generate_sailboats(num_of_sailboats=num_of_boats)

    assert len(result) == num_of_boats
    assert isinstance(result[num_of_boats // 2], Mock)

@patch('data_generator.kafka_producer.Sailboat')
def test_generate_sailboats_default_value(mock_sailboat_class):
    """Test generating default number of sailboats."""

    result = generate_sailboats()

    assert len(result) == 1
    assert isinstance(result[0], Mock)

@patch('time.sleep')
@patch('time.time')
@patch('random.uniform')
@patch('data_generator.kafka_producer.generate_sailboats')
def test_produce_data(mock_generate_sailboats,
                      mock_uniform,
                      mock_time,
                      mock_sleep,
                      mock_sailboat,
                      mock_producer):
    """Test produce_data function for a single iteration."""

    mock_generate_sailboats.return_value = [mock_sailboat]
    mock_time.return_value = 1234567890.0
    mock_uniform.side_effect = [0.1, 0.55]
    
    # break the loop after one iteration
    iteration_count = 0
    def side_effect_sleep(*args, **kwargs):
        nonlocal iteration_count
        iteration_count += 1
        if iteration_count >= 1:
            raise KeyboardInterrupt()
    
    mock_sleep.side_effect = side_effect_sleep
    
    with pytest.raises(KeyboardInterrupt):
        produce_data(mock_producer, 1)
    
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
def test_produce_data_delayed(mock_generate_sailboats,
                              mock_uniform,
                              mock_time,
                              mock_sleep,
                              mock_sailboat,
                              mock_producer):
    """Test produce_data function for a single iteration."""

    mock_generate_sailboats.return_value = [mock_sailboat]
    mock_time.return_value = 1234567890.0
    mock_uniform.side_effect = [0.01, 0.55]
    
    # break the loop after one iteration
    iteration_count = 0
    def side_effect_sleep(*args, **kwargs):
        nonlocal iteration_count
        iteration_count += 1
        if iteration_count >= 1:
            raise KeyboardInterrupt()
    
    mock_sleep.side_effect = side_effect_sleep
    
    with pytest.raises(KeyboardInterrupt):
        produce_data(mock_producer, 1)
    
    call_args = mock_producer.send.call_args
    assert call_args[1]["topic"] == "raw_sensor_data"
    message = call_args[1]["value"]
    assert message["id"] == 1
    assert message["x"] == 22.2
    assert message["y"] == 33.3
    assert message["timestamp"] == 1234567890.0 - 5