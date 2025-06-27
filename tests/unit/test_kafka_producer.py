"""Test module for the fake data generator producer."""
import pytest
import data_generator.kafka_producer
from unittest.mock import MagicMock, patch
from data_generator.sailboat_data_simulator import Sailboat

