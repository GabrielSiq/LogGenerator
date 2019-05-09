from heapq import heappush, heappop
import math
from activity import Activity
from config import DAYS, PRIORITY_VALUES
from gateway import Gateway
from log import LogWriter, LogItem
from model_builder import ModelBuilder
from datetime import datetime, timedelta
from random import randint


class SimulationManager:
    # Initialization and instance variables
    def __init__(self, start, end):
        self.log = list()
        self.dm = None
        self.rm = None
        self.models = list()
        self.start = start
        self.end = end
        self.execution_queue = PriorityQueue()
        self.log_queue = PriorityQueue()
        self.running_processes = list()
        print(str(start), str(end))

    # Public methods
    def main(self):
        model = ModelBuilder()
        # print("\nParsing activities:")
        # list_of_activities = model.create_activities()
        # for activity in list_of_activities:
        #     print(activity)
        # print("\nParsing resources:")
        # list_of_resources = model.create_resources()
        # for resource in list_of_resources:
        #     print(resource)
        # print("\nParsing data:")
        # list_of_data = model.create_data()
        # for data in list_of_data:
        #     print(data)
        # print("\nParsing models:")
        # list_of_models = model.create_process_model()
        # for process in list_of_models:
        #     print(process)
        # print("\nTesting data manager:")
        self.models, self.rm, self.dm = model.build_all()

        req = model.activities['quality'].resources[0]

        # print(rm.get_available(req, datetime.now() - timedelta(hours=3), datetime.now() - timedelta(hours=2)))
        # log_list = [
        #     LogItem(datetime.now(), 1, 1, 5, 1, 'start'),
        #     LogItem(datetime.now() + timedelta(minutes=3), 1, 2, 3, 1, 'start'),
        #     LogItem(datetime.now() + timedelta(minutes=6), 2, 1, 5, 1, 'start'),
        #     LogItem(datetime.now() + timedelta(minutes=9), 1, 1, 5, 1, 'end'),
        #     LogItem(datetime.now() + timedelta(minutes=12), 2, 1, 5, 1, 'end')
        # ]
        #
        # LogWriter.write(log_list, name='banana')

        print("\nTesting queue:")
        self._initialize_queue()
        # while not self.execution_queue.is_empty():
        #     item = self.execution_queue.pop()
        #     print(item.start)

        # return

        act = self.models[0].activities['verify']
        para = self.models[0].gateways['parallelTest']
        merge = self.models[0].gateways['mergeTest']
        rule = self.models[0].gateways['checklistCompleted']
        choice = self.models[0].gateways['qualityPassed']

        # for i in range(10):
        #     print(para.get_gate(), merge.get_gate(),rule.get_gate(),choice.get_gate())

        while not self.execution_queue.is_empty():
            current = self.execution_queue.pop()
            if current.start > self.end:
                break
            self._simulate(current)

        LogWriter.write(self.log_queue)
        while not self.execution_queue.is_empty():
            item = self.execution_queue.pop()
            if item.start < self.end:
                print('unused items in queue')

    # Private methods
    def _simulate(self, item):
        if isinstance(item.element, Activity):
            return self._simulate_activity(item)
        elif isinstance(item.element, Gateway):
            return self._simulate_gateway(item)

    def _simulate_activity(self, item):
        # TODO: Decide what does this return.
        activity = item.element
        duration = item.leftover_duration if item.leftover_duration is not None else activity.generate_duration()
        timeout = item.leftover_timeout if item.leftover_timeout is not None else activity.timeout
        max_duration = min(duration, timeout)
        # TODO: What about physical resources? The same logic doesn't apply...
        if activity.resources is not None:
            date, assigned = self.rm.assign_resources(activity.resources, item.process_id, item.process_instance_id, item.element_id, item.element_instance_id, start_time=item.start, duration=max_duration)
            if date < item.start + timedelta(seconds=max_duration):
                if not assigned:
                    # When there are no resources available. Register the occurence and try again when next resource is available.
                    new_start = self.rm.when_available(activity.resources, item.start, item.start + timedelta(seconds=max_duration))
                    self.log_queue.push(
                        LogItem(item.start, item.process_id, item.process_instance_id, item.element_id,
                                item.element_instance_id,
                                'waiting_resource'))
                    self.execution_queue.push(item.postpone(new_start))
                    return
                else:
                    # resources were assigned but weren't enough to complete the activity. create a log and push back into queue with new duration when we finish this execution.
                    self.log_queue.push(
                        LogItem(item.start, item.process_id, item.process_instance_id, item.element_id,
                                item.element_instance_id,
                                'start_activity'))
                    self.log_queue.push(
                        LogItem(date, item.process_id, item.process_instance_id,
                                item.element_id, item.element_instance_id,
                                'pause_activity'))
                    self.execution_queue.push(item.leftover(duration, (date - item.start).total_seconds()))
                    return

        # TODO: CHECK cases where no resources or retries/fails
        # Completed activity
        self.log_queue.push(
            LogItem(item.start, item.process_id, item.process_instance_id, item.element_id, item.element_instance_id,
                    'start_activity'))
        if duration > timeout:
            self.log_queue.push(
                LogItem(item.start + timedelta(seconds=max_duration), item.process_id, item.process_instance_id,
                        item.element_id, item.element_instance_id,
                        'timeout'))
        else:
            self.log_queue.push(
                LogItem(item.start + timedelta(seconds=max_duration), item.process_id, item.process_instance_id,
                        item.element_id, item.element_instance_id,
                        'end_activity'))
            # add next to queue
            element, delay = item.running_process.process_reference.get_next(source=activity.id)
            if element is not None:
                self.execution_queue.push(item.successor(element, duration=duration, delay=delay))

    def _simulate_gateway(self, item):
        # TODO: Missing merge and rule logic.

        #TODO: For rule: send together a dict with all data objects tied to that process execution. Then, the decision code should figure it out. Come back and test it.
        gateway = item.element
        gates = gateway.get_gate()
        for gate in gates:
            element, delay = item.running_process.process_reference.get_next(source=gateway.id, gate=gate)
            self.execution_queue.push(item.successor(element, delay=delay))
        self.log_queue.push(LogItem(item.start, item.process_id, item.process_instance_id, item.element_id, item.element_instance_id, 'decision'))

    def _initialize_queue(self):
        self.execution_queue = PriorityQueue()
        for model in self.models:
            first_hour = self.start.replace(microsecond=0, second=0, minute=0)
            second_hour = first_hour+timedelta(hours=1)
            remaining_minutes = second_hour - self.start
            self._initialize_hour(model, first_hour, remaining_minutes)
            hour = first_hour
            while hour + timedelta(hours=1) < self.end.replace(microsecond=0, second=0, minute=0):
                hour += timedelta(hours=1)
                self._initialize_hour(model, hour)
            last_hour = hour + timedelta(hours=1)
            remaining_minutes = self.end - last_hour
            self._initialize_hour(model, last_hour, remaining_minutes)

    def _initialize_hour(self, model, time, minutes=None):
        arrival_rate = model.get_arrival_rate(DAYS[time.weekday()], time.hour)
        arrivals = sorted([timedelta(minutes=randint(0, 59)) for i in range(arrival_rate)])
        for item in arrivals:
            if minutes is None or item <= minutes:
                instance = model.new()
                for data in instance.process_reference.data_objects:
                    self.dm.create_instance(data.id, instance.process_id, instance.process_instance_id)
                self.running_processes.append(instance)
                act = instance.process_reference.get_first_activity()[0]
                self.execution_queue.push(QueueItem(instance, act.id, instance.get_element_instance_id(act.id), time + item, act))


class PriorityQueue:
    # Initialization and instance variables
    def __init__(self):
        self.queue = []

    # Public methods
    def push(self, item):
        heappush(self.queue, item)

    def pop(self):
        try:
            return heappop(self.queue)
        except IndexError:
            return None

    def is_empty(self):
        return len(self.queue) == 0

    # Private Methods
    def __repr__(self):
        return ', '.join("%s: %s" % item for item in vars(self).items())


class QueueItem:
    def __init__(self, process, element_id, element_instance_id, start, element, duration=None, timeout=None):
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

    def successor(self, element, duration=0, delay=0):
        return QueueItem(self.running_process, element.id, self.running_process.get_element_instance_id(element.id), self.start + timedelta(seconds=duration + delay), element)

    def leftover(self, original_duration, actual_duration):
        leftover_duration = self.leftover_duration - actual_duration if self.leftover_duration is not None else original_duration - actual_duration
        leftover_timeout = self.leftover_timeout - actual_duration if self.leftover_timeout is not None else self.element.timeout - actual_duration
        return QueueItem(self.running_process, self.element_id, self.element_instance_id, self.start + timedelta(seconds=actual_duration), self.element, duration=leftover_duration, timeout=leftover_timeout)

    def postpone(self, new_start):
        # TODO: Decide if timeout is activity running time or if it's deadline after it starts. It possibly makes more sense to be deadline after it starts, so this logic will have to change a bit. postponing will reduce from leftover timeout if the activity has already started. change resources as well. Maybe we could record the original start time.
        return QueueItem(self.running_process, self.element_id, self.element_instance_id,
                         new_start, self.element, duration=self.leftover_duration, timeout=self.leftover_timeout)

    def __lt__(self, other):
        if self.start < other.start:
            return True
        elif self.start == other.start:
            if (isinstance(self.element, Activity) and isinstance(other.element, Gateway)) or self.priority < other.priority:
                return True
        else:
            return False
        return self.start < other.start or (self.start == other.start and self.priority < other.priority)

    # Private Methods
    def __repr__(self):
        return ', '.join("%s: %s" % item for item in vars(self).items())


sim = SimulationManager(start=datetime.now(), end=datetime.now() + timedelta(days=30))
sim.main()









