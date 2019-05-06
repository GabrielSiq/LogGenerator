from heapq import heappush, heappop
from config import DAYS
from log import LogWriter, LogItem
from model_builder import ModelBuilder
from datetime import datetime, timedelta
from random import randint


class SimulationManager:
    # Initialization and instance variables
    def __init__(self, start, end):
        self.log = []
        self.dm = None
        self.rm = None
        self.models = []
        self.start = start
        self.end = end
        self.queue = ExecutionQueue()
        self.running_processes = []
        print(str(start), str(end))

    # Public methods
    def main(self):
        model = ModelBuilder()
        print("\nParsing activities:")
        list_of_activities = model.create_activities()
        for activity in list_of_activities:
            print(activity)
        print("\nParsing resources:")
        list_of_resources = model.create_resources()
        for resource in list_of_resources:
            print(resource)
        print("\nParsing data:")
        list_of_data = model.create_data()
        for data in list_of_data:
            print(data)
        print("\nParsing models:")
        list_of_models = model.create_process_model()
        for process in list_of_models:
            print(process)
        self.models = list_of_models
        print("\nTesting data manager:")
        rm, dm = model.build_all()

        req = model.activities['quality'].resources[0]

        print(rm.get_available(req, datetime.now() - timedelta(hours=3), datetime.now() - timedelta(hours=2)))
        log_list = [
            LogItem(datetime.now(), 1, 1, 5, 1, 'start'),
            LogItem(datetime.now() + timedelta(minutes=3), 1, 2, 3, 1, 'start'),
            LogItem(datetime.now() + timedelta(minutes=6), 2, 1, 5, 1, 'start'),
            LogItem(datetime.now() + timedelta(minutes=9), 1, 1, 5, 1, 'end'),
            LogItem(datetime.now() + timedelta(minutes=12), 2, 1, 5, 1, 'end')
        ]

        LogWriter.write(log_list, name='banana')

        print("\nTesting queue:")
        self._initialize_queue()

        while not self.queue.is_empty():
            item = self.queue.pop()
            print(str(item[0]), item[1], item[2])

    def _initialize_queue(self):
        # TODO: improve variable names in this function
        self.queue = ExecutionQueue()
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
        arrivals = [timedelta(minutes=randint(0, 59)) for i in range(arrival_rate)]
        for item in arrivals:
            if minutes is None or item <= minutes:
                self.running_processes.append(model.new())
                act = model.get_first_activity()[0]
                self.queue.push((time + item, act.priority, act))



class ExecutionQueue:
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


sim = SimulationManager(start=datetime.now()+timedelta(days=2), end=datetime.now() + timedelta(days=3))
sim.main()









