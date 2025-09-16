import pytest
from unittest.mock import Mock, patch
import json

class FakeRow:
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

with patch('services.flink_stream_processor.logging_setup.logger') as mock_logger, \
     patch('pyflink.common.typeinfo.Types') as mock_types, \
     patch('pyflink.table.Row', side_effect=lambda **kwargs: FakeRow(**kwargs)) as mock_row, \
     patch('pyflink.datastream.RuntimeContext') as mock_ctx, \
     patch('pyflink.datastream.ProcessFunction', MockProcessFunction), \
     patch('pyflink.datastream.state.ListStateDescriptor') as mock_list_state_descriptor, \
     patch('pyflink.datastream.state.ListState') as mock_list_state, \
     patch('pyflink.datastream.functions.FlatMapFunction', MockFlatMapFunction), \
     patch('pyflink.datastream.functions.KeyedProcessFunction', MockKeyedProcessFunction), \
     patch('pyflink.datastream.OutputTag', return_value="OutputTag") as mock_output_tag:
    from services.flink_stream_processor.transformations import (
        CalculateInstSpeed,
        LateMetrics,
        ParseAndFilter,
        OnTimeEventCounter,
        OnTimeTotalTimeCounter
    )

class MockListState():
    def __init__(self, values: list[FakeRow]):
        self.values = values

    def get(self) -> list[FakeRow]:
        return self.values
    
    def update(self, list: list) -> None:
        self.values = list

class MockCtx():
    def __init__(self, key: int):
        self.key = key
    
    def get_current_key(self) -> int:
        return self.key
    
class MockCounter():
    def __init__(self):
        self.count = 0

    def inc(self, inc = 1) -> None:
        self.count += inc

class MockMetricGroup():
    def counter(self, _: str) -> MockCounter:
        return MockCounter()

@pytest.fixture
def mock_message():
    """Mock message."""
    return {
        "id" : 1,
        "x" : 22.2,
        "y" : 33.3,
        "timestamp" : 1234567890.0
    }

def test_ParseAndFilter(mock_message):
    """Test if an on-time event is correctly parsed and filtered."""
    json_event = json.dumps(mock_message)
    result = next(ParseAndFilter().process_element(json_event, None))
    assert isinstance(result, FakeRow)
    assert result.__dict__ == mock_message

def test_ParseAndFilter_late(mock_message):
    """Test if a late event is correctly parsed and filtered."""
    json_event = json.dumps(mock_message)
    transformation = ParseAndFilter()
    _ = next(transformation.process_element(json_event, None))
    late_result = next(transformation.process_element(json_event, None))
    
    assert isinstance(late_result, tuple)
    assert isinstance(late_result[1], FakeRow)
    assert late_result[1].__dict__ == mock_message
    assert late_result[0] == "OutputTag"

@patch('time.time')
def test_CalculateInstSpeed(mock_time):
    mock_time.return_value = 5
    transformation = CalculateInstSpeed()
    transformation.list_state = MockListState([
        FakeRow(**{"id" : 1, "x" : 1, "y" : 1, "timestamp" : 1})
    ])
    event = FakeRow(**{"id" : 2, "x" : 2, "y" : 1, "timestamp" : 2})
    result = next(transformation.flat_map(event))
    
    assert isinstance(result, FakeRow)
    assert result.inst_speed == 1
    assert result.time_taken == mock_time.return_value - event.timestamp

def test_OnTimeEventCounter():
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
    time_counter = OnTimeTotalTimeCounter()
    time_counter.event_counter = MockCounter()
    time_counter.time_counter = MockCounter()
    event1 = FakeRow(**{"time_taken" : 1})
    event2 = FakeRow(**{"time_taken" : 2})
    time_counter.process_element(event1, None)
    assert time_counter.time_counter.count == event1.time_taken * 1000

    time_counter.process_element(event2, None)
    assert time_counter.time_counter.count == (event1.time_taken + event2.time_taken) * 1000

def test_LateMetrics():
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