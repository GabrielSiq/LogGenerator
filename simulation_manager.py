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
        log_list = []
        log_list.append(LogItem(datetime.now(),1,1,5,1,'start'))
        log_list.append(LogItem(datetime.now()+timedelta(minutes=3), 1, 2, 3, 1, 'start'))
        log_list.append(LogItem(datetime.now()+timedelta(minutes=6), 2, 1, 5, 1, 'start'))
        log_list.append(LogItem(datetime.now()+timedelta(minutes=9), 1, 1, 5, 1, 'end'))
        log_list.append(LogItem(datetime.now()+timedelta(minutes=12), 2, 1, 5, 1, 'end'))

        LogWriter.write(log_list, name='banana')

        self._initialize_queue()
        while not self.queue.is_empty():
            item = self.queue.pop()
            print(str(item[0]), item[1], item[2])

    def _initialize_queue(self):
        # TODO: improve variable names in this function
        self.queue = ExecutionQueue()
        for model in self.models:
            zero_hour = self.start.replace(microsecond=0, second=0, minute=0)
            first_hour = zero_hour+timedelta(hours=1)
            first_time = first_hour - self.start
            self._initialize_hour(model, zero_hour, first_time)
            while zero_hour + timedelta(hours=1) < self.end.replace(microsecond=0, second=0, minute=0):
                zero_hour += timedelta(hours=1)
                self._initialize_hour(model, zero_hour)
            last_hour = zero_hour + timedelta(hours=1)
            last_time = self.end - last_hour
            self._initialize_hour(model, last_hour, last_time)

    def _initialize_hour(self, model, time, minutes=None):
        arrival_rate = model.get_arrival_rate(DAYS[time.weekday()], time.hour)
        arrivals = [timedelta(minutes=randint(0, 59)) for i in range(arrival_rate)]
        for item in arrivals:
            if minutes is None or item <= minutes:
                self.queue.push((time + item, 'Normal', model.get_first_activity()[0]))



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


sim = SimulationManager(start=datetime.now()+timedelta(days=2), end=datetime.now() + timedelta(days=4))
sim.main()









