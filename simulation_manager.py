from activity import Activity
from config import DAYS
from gateway import Gateway
from log import LogWriter, LogItem
from model_builder import ModelBuilder
from datetime import datetime, timedelta
from random import randint

from process import Process
from queue import PriorityQueue, QueueItem


class SimulationManager:
    # Initialization and instance variables
    def __init__(self, start: datetime, end: datetime) -> None:
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
        #TODO: Remove unnecessary prints. (15 min)
        model = ModelBuilder()
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
    def _simulate(self, item: QueueItem) -> bool:
        if isinstance(item.element, Activity):
            return self._simulate_activity(item)
        elif isinstance(item.element, Gateway):
            return self._simulate_gateway(item)

    def _simulate_activity(self, item: QueueItem) -> bool:
        # TODO: Add data and resource information to log. (1h)
        # TODO: Decide what does this return. (30min)
        activity = item.element
        duration = item.leftover_duration if item.leftover_duration is not None else activity.generate_duration()
        timeout = item.leftover_timeout if item.leftover_timeout is not None else activity.timeout
        max_duration = min(duration, timeout)
        # data is read at the beginning and written at the end.
        data = self.dm.read_all(item.process_id, item.process_instance_id, requirements_list=activity.data_input) if item.data is None else item.data
        # TODO: What about physical resources? The same logic doesn't apply... (1h)
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
                    return True
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
                    self.execution_queue.push(item.leftover(duration, (date - item.start).total_seconds(), data))
                    return True

        self.log_queue.push(
            LogItem(item.start, item.process_id, item.process_instance_id, item.element_id, item.element_instance_id,
                    'start_activity'))

        # Failed
        if activity.failure.check_failure():
            # Failed
            self.log_queue.push(
                LogItem(item.start + timedelta(seconds=max_duration), item.process_id, item.process_instance_id,
                        item.element_id, item.element_instance_id,
                        'failed'))
            if item.attempt < activity.retries:
                self.execution_queue.push(item.repeat(max_duration + 1))
        else:
            # Completed activity

            # Gets updated data from the activity, and updates it in the data manager
            if activity.process_data is not None:
                output = activity.process_data(data)
                for id, fields in output.items():
                    self.dm.update_object(id, item.process_id, item.process_instance_id, fields)
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
        return True

    def _simulate_gateway(self, item: QueueItem) -> bool:
        # TODO: Missing merge logic. (1h)

        gateway = item.element
        data = self.dm.read_all(item.process_id, item.process_instance_id)
        gates = gateway.get_gate(input_data=data)
        for gate in gates:
            element, delay = item.running_process.process_reference.get_next(source=gateway.id, gate=gate)
            self.execution_queue.push(item.successor(element, delay=delay))
        self.log_queue.push(LogItem(item.start, item.process_id, item.process_instance_id, item.element_id, item.element_instance_id, 'decision'))
        return True

    def _initialize_queue(self) -> None:
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

    def _initialize_hour(self, model: Process, time: datetime, minutes: timedelta = None) -> None:
        arrival_rate = model.get_arrival_rate(DAYS[time.weekday()], time.hour)
        arrivals = sorted([timedelta(minutes=randint(0, 59)) for i in range(arrival_rate)])
        for item in arrivals:
            if minutes is None or item <= minutes:
                instance = model.new()
                for data in instance.process_reference.data_objects:
                    self.dm.create_instance(data.id, instance.process_id, instance.process_instance_id)
                self.running_processes.append(instance)
                act = instance.process_reference.get_first_activity()[0]
                self.execution_queue.push(
                    QueueItem(instance, act.id, instance.get_element_instance_id(act.id), time + item, act))


sim = SimulationManager(start=datetime.now(), end=datetime.now() + timedelta(days=30))
sim.main()









