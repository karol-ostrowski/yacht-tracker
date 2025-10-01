"""Test module for the custom pyflink transformations and metrics."""
from unittest.mock import Mock, MagicMock, patch
from types import ModuleType
import json
import sys
import pytest

class MockRow:
    """Replacement for pyflink.table.Row."""
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)
    
class MockProcessFunction():
    """Needed for transformations to inherit from."""
    pass

class MockKeyedProcessFunction():
    """Needed for transformations to inherit from."""
    pass

class MockFlatMapFunction():
    """Needed for a tranformation to inherit from."""
    pass

class MockListState():
    """Replacement forthea list_state attribute."""
    def __init__(self, values: list[MockRow]):
        self.values = values

    def get(self) -> list[MockRow]:
        return self.values
    
    def update(self, items: list) -> None:
        self.values = items

class MockCtx():
    """Replacement for the runtime context."""
    def __init__(self, key: int = 0):
        self.key = key
    
    def get_current_key(self) -> int:
        return self.key
    
class MockCounter():
    """Replacement for a method of context.get_metric_group()"""
    def __init__(self):
        self.count = 0

    def inc(self, inc: int = 1) -> None:
        self.count += inc

class MockMetricGroup():
    """Replacement for a method of the runtime context."""
    def counter(self, _: str) -> MockCounter:
        return MockCounter()
    
class MockOutputTag():
    """Replacement for OutputTag"""
    def __repr__(self):
        return "OutputTag"
    
datastream = ModuleType("pyflink.datastream")
datastream.ProcessFunction = MockProcessFunction
datastream.RuntimeContext = MockCtx
datastream.OutputTag = Mock(return_value="OutputTag")

table = ModuleType("pyflink.table")
table.Row = MockRow

functions = ModuleType("pyflink.functions")
functions.FlatMapFunction = MockFlatMapFunction
functions.KeyedProcessFunction = MockKeyedProcessFunction

sys.modules['pyflink'] = MagicMock()
sys.modules['pyflink.common'] = MagicMock()
sys.modules['pyflink.common.typeinfo'] = MagicMock()
sys.modules['pyflink.table'] = table
sys.modules['pyflink.datastream'] = datastream
sys.modules['pyflink.datastream.state'] = MagicMock()
sys.modules['pyflink.datastream.functions'] = functions

from services.flink_stream_processor.transformations import (
    CalculateInstSpeed,
    LateMetrics,
    ParseAndFilter,
    OnTimeEventCounter,
    OnTimeTotalTimeCounter
)

@pytest.fixture
def mock_message():
    """Mock message for processing."""
    return {
        "id": 1,
        "x": 22.2,
        "y": 33.3,
        "timestamp": 1234567890.0
    }

def test_ParseAndFilter(mock_message):
    """Test if an on-time event is correctly parsed and filtered."""
    json_event = json.dumps(mock_message)
    result = next(ParseAndFilter().process_element(json_event, None))
    assert isinstance(result, MockRow)
    assert result.__dict__ == mock_message

def test_ParseAndFilter_late(mock_message):
    """Test if a late event is correctly parsed and filtered."""
    json_event = json.dumps(mock_message)
    transformation = ParseAndFilter()
    _ = next(transformation.process_element(json_event, None))
    late_result = next(transformation.process_element(json_event, None))
    
    assert isinstance(late_result, tuple)
    assert isinstance(late_result[1], MockRow)
    assert late_result[1].__dict__ == mock_message
    assert late_result[0] == "OutputTag"

@patch('time.time')
def test_CalculateInstSpeed(mock_time):
    """Test instantaneous speed calcualtion."""
    mock_time.return_value = 5
    transformation = CalculateInstSpeed()
    transformation.list_state = MockListState([
        MockRow(**{"id": 1, "x": 1, "y": 1, "timestamp": 1})
    ])
    event = MockRow(**{"id": 2, "x": 2, "y": 1, "timestamp": 2})
    result = next(transformation.flat_map(event))
    
    assert isinstance(result, MockRow)
    assert result.inst_speed == 111320
    assert result.time_taken == mock_time.return_value - event.timestamp

def test_OnTimeEventCounter():
    """Test on-time event counter metric."""
    event_counter = OnTimeEventCounter()
    event_counter.metric_group = MockMetricGroup()
    event_counter.total_on_time_events_counter = MockCounter()
    ctx1 = MockCtx(1)
    ctx2 = MockCtx(2)
    event_counter.process_element(None, ctx1)
    event_counter.process_element(None, ctx2)
    event_counter.process_element(None, ctx2)

    assert event_counter.total_on_time_events_counter.count == 3
    assert event_counter.id_counters[1].count == 1
    assert event_counter.id_counters[2].count == 2

def test_OnTimeTotalTimeCounter():
    """Test on-time total time taken counter metric."""
    time_counter = OnTimeTotalTimeCounter()
    time_counter.event_counter = MockCounter()
    time_counter.time_counter = MockCounter()
    event1 = MockRow(**{"time_taken": 1})
    event2 = MockRow(**{"time_taken": 2})
    time_counter.process_element(event1, None)
    assert time_counter.time_counter.count == event1.time_taken * 1000

    time_counter.process_element(event2, None)
    assert time_counter.time_counter.count == (event1.time_taken + event2.time_taken) * 1000

def test_LateMetrics():
    """Test correctness of late events metrics."""
    event_counter = LateMetrics()
    event_counter.metric_group = MockMetricGroup()
    event_counter.total_late_events_counter = MockCounter()
    ctx1 = MockCtx(1)
    ctx2 = MockCtx(2)
    event_counter.process_element(None, ctx1)
    event_counter.process_element(None, ctx2)
    event_counter.process_element(None, ctx2)

    assert event_counter.id_counters[1].count == 1
    assert event_counter.id_counters[2].count == 2
    assert event_counter.total_late_events_counter.count == 3