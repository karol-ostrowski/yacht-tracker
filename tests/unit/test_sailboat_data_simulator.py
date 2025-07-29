"""Test module for the fake data generator."""
import pytest
from unittest.mock import patch
from data_generator.Sailboat import Sailboat

@pytest.fixture
def sailboat():
    """Create a standard sailboat for testing."""
    return Sailboat(id = 1)

def test_sailboat_init(sailboat):
    """Checks if the object initialization works as expected."""
    assert sailboat.id == 1
    assert 50 <= sailboat.x <= 950
    assert 50 <= sailboat.y <= 950
    assert -1 <= sailboat.horizontal_speed <= 1
    assert -1 <= sailboat.vertical_speed <= 1

def test_sailboat_move(sailboat):
    """Checks if the move() method updates location."""
    init_x = sailboat.x
    init_y = sailboat.y
    sailboat.horizontal_speed = 0.5
    sailboat.vertical_speed = 0.5
    sailboat.move()
    assert sailboat.x != init_x
    assert sailboat.y != init_y

@patch("random.uniform", return_value=0.9)
def test_sailboat_speedup(sailboat):
    """Check if move() method can successfully change the speed."""
    sailboat.horizontal_speed = 0.5
    init_speed = sailboat.horizontal_speed
    sailboat.move()
    assert sailboat.horizontal_speed != init_speed

def test_horizontal_boundary_direction_change(sailboat):
    """Check if the sailboat correctly changes the direction upon reaching the horizontal boundary."""
    sailboat.x = 949.9
    sailboat.horizontal_speed = 0.7
    sailboat.move()
    assert sailboat.horizontal_speed == -0.7
    
def test_vertical_boundary_direction_change(sailboat):
    """Check if the sailboat correctly changes the direction upon reaching the vertical boundary."""
    sailboat.y = 949.9
    sailboat.vertical_speed = 0.7
    sailboat.move()
    assert sailboat.vertical_speed == -0.7
