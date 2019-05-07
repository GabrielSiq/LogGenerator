from heapq import heappush, heappop

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
        self.models = model.create_process_model()
        # print("\nTesting data manager:")
        self.rm, self.dm = model.build_all()

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

        current = self.execution_queue.pop()
        while current.start <= self.end and not self.execution_queue.is_empty():
            self._simulate(current)
            current = self.execution_queue.pop()

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
        activity = item.element
        duration = min(activity.generate_duration(), activity.timeout)
        if activity.resources is not None:
            assigned = self.rm.assign_resource(activity.resources, item.process_id, item.process_instance_id, item.element_id, item.element_instance_id, start_time=item.start, duration=duration)
            if not assigned:
                # check when resources will be available and set the date to it
                pass
        # add next to queue
        # TODO: CHECK cases where timeout or no resources or retries
        element, delay = item.running_process.process_reference.get_next(source=activity.id)
        self.execution_queue.push(item.successor(element, duration=duration, delay=delay))
        self.log_queue.push(LogItem(item.start, item.process_id, item.process_instance_id, item.element_id, item.element_instance_id, 'start_activity'))
        self.log_queue.push(
            LogItem(item.start + timedelta(seconds=duration), item.process_id, item.process_instance_id, item.element_id, item.element_instance_id,
                    'end_activity'))

    def _simulate_gateway(self, item):
        # TODO: Missing merge logic.
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
                self.running_processes.append(instance)
                act = instance.process_reference.get_first_activity()[0]
                self.execution_queue.push(QueueItem(instance, act.id, 0, time + item, act))


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
    def __init__(self, process, element_id, element_instance_id, start, element):
        self.process_id = process.process_id
        self.process_instance_id = process.process_instance_id
        self.element_id = element_id
        self.element_instance_id = element_instance_id
        self.start = start
        self.priority = element.priority if isinstance(element, Activity) else PRIORITY_VALUES['high']
        self.element = element
        self.running_process = process

    def successor(self, element, duration=0, delay=0):
        return QueueItem(self.running_process, element.id, self.running_process.get_element_instance_id(element.id), self.start + timedelta(seconds=duration + delay), element)

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


sim = SimulationManager(start=datetime.now(), end=datetime.now() + timedelta(hours=1))
sim.main()









