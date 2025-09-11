import time
import json
from pyflink.common.typeinfo import Types
from pyflink.table import Row
from pyflink.datastream import RuntimeContext, ProcessFunction
from pyflink.datastream.state import ListStateDescriptor, ListState
from pyflink.datastream.functions import FlatMapFunction, KeyedProcessFunction
from logging_setup import logger
from utils import LATE_DATA_TAG

class ParseAndFilter(ProcessFunction):
    """Parses the event and filter out if out of order. Yields Row objects."""
    def __init__(self):
        self.most_recent_timestamp = 0

    def process_element(self, event: str, _):
        try:
            d = json.loads(event)
            if d["timestamp"] > self.most_recent_timestamp:
                self.most_recent_timestamp = d["timestamp"]
                yield Row(
                    id = d["id"],
                    x = d["x"],
                    y = d["y"],
                    timestamp=d["timestamp"]
                )

            else:
                yield \
                    LATE_DATA_TAG, \
                    Row(
                        id = d["id"],
                        x = d["x"],
                        y = d["y"],
                        timestamp=d["timestamp"]
                    )
                
        except json.JSONDecodeError as e:
            logger.error(f"An error occured when parsing an event ({event}): {e}")

# "State TTL is still not supported in PyFlink DataStream API." ~ Flink docs ;cccc
# TODO
# replace current ttl mechanism with redis
class CalculateInstSpeed(FlatMapFunction):
    """Yields Row a object with added value of the instantaneous speed calculated
    using distance/time_diff formula based on the current event and the least recent
    event 5 seconds back event time. Assumes data is ordered by time."""
    def __init__(self):
        self.list_state: ListState = None

    def open(self, ctx: RuntimeContext):
        descriptor = ListStateDescriptor(
            name="list_state",
            elem_type_info=Types.ROW_NAMED(
                ["id", "x", "y", "timestamp"],
                [Types.INT(), Types.FLOAT(), Types.FLOAT(), Types.DOUBLE()]
            )
        )
        self.list_state = ctx.get_list_state(descriptor)

    def flat_map(self, current_event: Row):
        queue = []
        for event in reversed(list(self.list_state.get())):
            if current_event.timestamp - event.timestamp <= 5:
                queue.append(event)
            else:
                break
        try:
            time_diff = current_event.timestamp - queue[-1].timestamp
            oldest_available_event = queue[-1]
            if time_diff >= 1:
                distance = ((current_event.x - oldest_available_event.x) ** 2 \
                         +  (current_event.y - oldest_available_event.y) ** 2) ** 0.5
                speed = distance / time_diff
                queue.append(current_event)
                self.list_state.update(queue)
                yield Row(
                    id = current_event.id,
                    x = current_event.x,
                    y = current_event.y,
                    timestamp = current_event.timestamp,
                    inst_speed = speed,
                    time_taken = (time.time() - current_event.timestamp)
                )
            else:
                queue.append(current_event)
                self.list_state.update(queue)

        except IndexError:
            self.list_state.add(current_event)

class OnTimeEventCounter(KeyedProcessFunction):
    """Counts all on-time events and calculated their total time taken, counts on-time events by device ID.
    Makes the metrics available for scraping at the /metrics endpoint."""
    def __init__(self):
        self.id_counters = {}
        self.total_on_time_events_counter = None

    def open(self, ctx):
        self.metric_group = ctx.get_metrics_group()
        self.total_on_time_events_counter = ctx \
            .get_metrics_group() \
            .counter("total_on_time_events")

    def process_element(self, _, ctx):
        key = ctx.get_current_key()
        metric_name = f"on_time_device_{key}"
        if key not in self.id_counters:
            self.id_counters[key] = self.metric_group.counter(metric_name)
        self.id_counters[key].inc()
        self.total_on_time_events_counter.inc()

class OnTimeTotalTimeAndEventCounter(ProcessFunction):
    """Counts all on-time events and calculates their total time taken, counts on-time events by device ID.
    Makes the metrics available for scraping at the /metrics endpoint."""
    def __init__(self):
        self.time_counter = None
        self.event_counter = None

    def open(self, ctx):
        metrics_group = ctx.get_metrics_group()
        self.time_counter = metrics_group.counter("time_counter_ms")
        self.event_counter = metrics_group.counter("on_time_event_counter")

    def process_element(self, current_event, _):
        self.time_counter.inc(current_event.time_taken*1000)
        self.event_counter.inc()

class LateMetrics(KeyedProcessFunction):
    """Counts late events by device ID and exposed them at the /metrics endpoint."""
    def __init__(self):
        self.id_counters = {}

    def open(self, ctx):
        self.metric_group = ctx.get_metrics_group()

    def process_element(self, _, ctx):
        key = ctx.get_current_key()
        metric_name = f"late_device_{key}"
        if key not in self.id_counters:
            self.id_counters[key] = self.metric_group.counter(metric_name)
        self.id_counters[key].inc()