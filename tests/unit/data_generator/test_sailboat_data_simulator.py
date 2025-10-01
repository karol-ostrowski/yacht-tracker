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
    assert 21.020602 <= sailboat.x <= 21.043111
    assert 52.439085 <= sailboat.y <= 52.456344
    assert -0.00005 <= sailboat.horizontal_speed <= 0.00005
    assert -0.00005 <= sailboat.vertical_speed <= 0.00005

def test_sailboat_move(sailboat):
    """Checks if the move() method updates location."""
    init_x = sailboat.x
    init_y = sailboat.y
    sailboat.horizontal_speed = 0.00004
    sailboat.vertical_speed = 0.00004
    sailboat.move()
    assert sailboat.x != init_x
    assert sailboat.y != init_y

@patch("random.uniform", return_value=0.999)
def test_sailboat_speedup(_, sailboat):
    """Check if move() method can successfully change the speed."""
    sailboat.horizontal_speed = 0.00001
    init_speed = sailboat.horizontal_speed
    sailboat.move()
    assert sailboat.horizontal_speed != init_speed

@patch("random.uniform", return_value=0.5)
def test_horizontal_boundary_direction_change(_, sailboat):
    """Check if the sailboat correctly changes the direction upon reaching the horizontal boundary."""
    sailboat.x = 21.043110
    sailboat.horizontal_speed = 0.00001
    sailboat.move()
    assert sailboat.horizontal_speed == -0.00001
    
@patch("random.uniform", return_value=0.5)
def test_vertical_boundary_direction_change(_, sailboat):
    """Check if the sailboat correctly changes the direction upon reaching the vertical boundary."""
    sailboat.y = 52.456344
    sailboat.vertical_speed = 0.00001
    sailboat.move()
    assert sailboat.vertical_speed == -0.00001
