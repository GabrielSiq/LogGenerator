from __future__ import annotations
from datetime import timedelta, datetime
from heapq import heappush, heappop
from typing import Union, Dict, Any
from process import ProcessInstance
from activity import Activity
from config import PRIORITY_VALUES
from gateway import Gateway


class PriorityQueue:
    # Initialization and instance variables
    def __init__(self) -> None:
        self.queue = []

    # Public methods
    def push(self, item: Any) -> None:
        heappush(self.queue, item)

    def pop(self) -> Any:
        try:
            return heappop(self.queue)
        except IndexError:
            return None

    def is_empty(self) -> bool:
        return len(self.queue) == 0

    # Private Methods
    def __repr__(self):
        return ', '.join("%s: %s" % item for item in vars(self).items())


class QueueItem:
    def __init__(self, process: ProcessInstance, element_id: str, element_instance_id: int, start: datetime, element: Union[Activity, Gateway], duration: int = None, timeout: int = None, data: Dict[str, dict] = None, attempt: int = 0, waiting: bool = False) -> None:
        self.process_id = process.process_id
        self.process_instance_id = process.process_instance_id
        self.element_id = element_id
        self.element_instance_id = element_instance_id
        self.start = start
        self.priority = element.priority if isinstance(element, Activity) else PRIORITY_VALUES['high']
        self.element = element
        self.running_process = process
        self.leftover_duration = duration
        self.leftover_timeout = timeout
        self.data = data
        self.attempt = attempt
        self.waiting = waiting

    def successor(self, element: Union[Activity, Gateway], duration: int = 0, delay: int = 0) -> QueueItem:
        return QueueItem(self.running_process, element.id, self.running_process.get_element_instance_id(element.id), self.start + timedelta(seconds=duration + delay), element)

    def repeat(self, duration: int) -> QueueItem:
        self.start = self.start + timedelta(seconds=duration)
        self.attempt = self.attempt + 1
        return self

    def leftover(self, original_duration: int, actual_duration: int, data: Dict[str, dict]) -> QueueItem:
        self.leftover_duration = self.leftover_duration - actual_duration if self.leftover_duration is not None else original_duration - actual_duration
        self.leftover_timeout = self.leftover_timeout - actual_duration if self.leftover_timeout is not None else self.element.timeout - actual_duration
        self.data = data
        self.start = self.start + timedelta(seconds=actual_duration)
        return self

    def postpone(self, new_start: datetime) -> QueueItem:
        self.start = new_start
        self.waiting = True
        return self

    def __lt__(self, other: QueueItem) -> bool:
        if self.start < other.start:
            # If the start date is smaller, then it's automatically smaller
            return True
        elif self.start == other.start:
            # If they have same start date, we check priority and process instance id
            if self.priority < other.priority:
                return True
            elif self.priority == other.priority and self.process_id == other.process_id and self.process_instance_id > other.process_instance_id:
                return True
            else:
                return False
        else:
            return False

    # Private Methods
    def __repr__(self):
        return ', '.join("%s: %s" % item for item in vars(self).items())