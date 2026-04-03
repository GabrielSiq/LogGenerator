import time
from activity import Activity
from config import DAYS, RESOURCE_TYPES
from gateway import Gateway
from log import LogWriter, LogItem
from model_builder import ModelBuilder
from datetime import datetime, timedelta
from random import randint
from process import Process
from execution_queue import PriorityQueue, QueueItem


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
        self.pending_merges = dict()
        self.running_processes = dict()
        self._waiting_queues = {}  # dict[tuple, PriorityQueue] keyed by (org, dept, role) or ('physical', type)

    # Public methods
    def simulate(self, name=None, resource_limit=None):
        model = ModelBuilder()
        self.models, self.rm, self.dm = model.build_all(resource_limit=resource_limit)

        self._initialize_queue()

        simulation = time.time()
        while not self.execution_queue.is_empty():
            current = self.execution_queue.pop()
            if current.start > self.end:
                break
            self._simulate(current)
        print('Simulation time: ' + str(time.time() - simulation))

        LogWriter.write(self.log_queue, name=name)

    # Private methods
    def _simulate(self, item: QueueItem) -> None:
        if isinstance(item.element, Activity):
            self._simulate_activity(item)
        elif isinstance(item.element, Gateway):
            self._simulate_gateway(item)

    def _simulate_activity(self, item: QueueItem) -> None:
        # TODO: Refactor this function.
        activity = item.element
        duration = item.leftover_duration if item.leftover_duration is not None else activity.generate_duration()
        timeout = item.leftover_timeout if item.leftover_timeout is not None else activity.timeout
        max_duration = min(duration, timeout)
        # data is read at the beginning and written at the end.
        data = self.dm.read_requirements(item.process_id, item.process_instance_id, requirements_list=activity.data_input) if item.data is None else item.data
        input = {k: dict(v) for k, v in data.items()} if data is not None else None
        # TODO: Adapt for physical resources.
        assigned = None
        if activity.resources is not None:
            date, assigned = self.rm.assign_resources(activity.resources, item.process_id, item.process_instance_id, item.element_id, item.element_instance_id, start_time=item.start, duration=max_duration)
            if date < item.start + timedelta(seconds=max_duration):
                if not assigned:
                    # No resources available — park in role-specific wait queue instead of main queue.
                    if not item.waiting:
                        self.log_queue.push(
                            LogItem(item.start, item.process_id, item.process_instance_id, item.element_id,
                                    item.element_instance_id,
                                    'waiting_resource'))
                    role_key = self._resource_key(activity.resources[0])
                    if role_key not in self._waiting_queues:
                        self._waiting_queues[role_key] = PriorityQueue()
                    item.waiting = True
                    self._waiting_queues[role_key].push(item)
                    return
                else:
                    # resources were assigned but weren't enough to complete the activity. create a log and push back into queue with new duration when we finish this execution.
                    self.log_queue.push(
                        LogItem(item.start, item.process_id, item.process_instance_id, item.element_id,
                                item.element_instance_id,
                                'start_activity', resource=assigned, data_input=input))
                    self.log_queue.push(
                        LogItem(date, item.process_id, item.process_instance_id,
                                item.element_id, item.element_instance_id,
                                'pause_activity', resource=assigned))
                    self._wake_waiting_for(assigned, date)
                    self._push_to_execution(item.leftover(duration, (date - item.start).total_seconds(), data))
                    return

        self.log_queue.push(
            LogItem(item.start, item.process_id, item.process_instance_id, item.element_id, item.element_instance_id,
                    'start_activity', resource=assigned, data_input=input))

        end_time = item.start + timedelta(seconds=max_duration)
        # Failed
        if activity.failure.check_failure():
            # Failed
            self.log_queue.push(
                LogItem(end_time, item.process_id, item.process_instance_id,
                        item.element_id, item.element_instance_id,
                        'failed', resource=assigned))
            if assigned:
                self._wake_waiting_for(assigned, end_time)
            if item.attempt < activity.retries:
                self._push_to_execution(item.repeat(max_duration + 1))
        else:
            # Completed activity

            # Gets updated data from the activity, and updates it in the data manager
            output = None
            if activity.data_output is not None:
                output = activity.process_data(data)
                for id, fields in output.items():
                    self.dm.update_object(id, item.process_id, item.process_instance_id, fields)
            if assigned:
                self._wake_waiting_for(assigned, end_time)
            if duration > timeout:
                self.log_queue.push(
                    LogItem(end_time, item.process_id, item.process_instance_id,
                            item.element_id, item.element_instance_id,
                            'timeout', resource=assigned))
            else:
                self.log_queue.push(
                    LogItem(end_time, item.process_id, item.process_instance_id,
                            item.element_id, item.element_instance_id,
                            'end_activity', resource=assigned, data_output=output))
                # add next to queue
                element, gate, delay = item.running_process.process_reference.get_next(source=activity.id)
                if element is not None:
                    self._push_to_execution(item.successor(element, duration=duration, delay=delay), current_gate=gate)

    def _resource_key(self, requirement) -> tuple:
        if requirement.class_type == RESOURCE_TYPES['human']:
            return (requirement.org, requirement.dept, requirement.role)
        else:
            return ('physical', requirement.physical_type)

    def _wake_waiting_for(self, assigned: dict, new_start: datetime) -> None:
        # Find role keys for all freed resources and re-queue any parked waiting items.
        role_keys = set()
        for rid in assigned:
            if rid in self.rm.human_resources:
                r = self.rm.human_resources[rid]
                role_keys.add((r.org, r.dept, r.role))
            elif rid in self.rm.physical_resources:
                r = self.rm.physical_resources[rid]
                role_keys.add(('physical', r.type))
        for key in role_keys:
            if key in self._waiting_queues:
                q = self._waiting_queues[key]
                while not q.is_empty():
                    waiting_item = q.pop()
                    waiting_item.start = new_start
                    waiting_item.waiting = False
                    self.execution_queue.push(waiting_item)

    def _simulate_gateway(self, item: QueueItem) -> None:
        gateway = item.element
        data = self.dm.read_all(item.process_id, item.process_instance_id)
        gates = gateway.get_gate(input_data=data)
        for gate in gates:
            element, gt, delay = item.running_process.process_reference.get_next(source=gateway.id, gate=gate)
            self._push_to_execution(item.successor(element, delay=delay), current_gate=gt)

    def _push_to_execution(self, item: QueueItem, current_gate=None):
        if isinstance(item.element, Gateway) and item.element.type == 'merge':
            # Special case for merges
            instance = self.pending_merges[item.process_id][item.process_instance_id]
            if item.element_id not in instance:
                # Create a record for this gateway if not exists
                instance[item.element_id] = dict()
            if item.element_instance_id not in instance[item.element_id]:
                # Create a record for this gateway instance if not exists
                instance[item.element_id][item.element_instance_id] = dict((gate, None) for gate in item.element.merge_inputs)
            instance[item.element_id][item.element_instance_id][current_gate] = item.start
            if all(date is not None for gate, date in instance[item.element_id][item.element_instance_id].items()):
                # If all gates are fulfilled
                item.start = max(list(instance[item.element_id][item.element_instance_id].values())) + timedelta(seconds=1)
                self.execution_queue.push(item)
                self.running_processes[item.process_id][item.process_instance_id].last_activities[item.element_id] += 1
        else:
            self.execution_queue.push(item)

    def _initialize_queue(self) -> None:
        self.execution_queue = PriorityQueue()
        for model in self.models:
            first_hour = self.start.replace(microsecond=0, second=0, minute=0)
            second_hour = first_hour+timedelta(hours=1)
            remaining_minutes = second_hour - self.start
            self.pending_merges[model.id] = dict()
            self.running_processes[model.id] = dict()
            self._initialize_hour(model, first_hour, first_hour=remaining_minutes.total_seconds())
            hour = first_hour
            while hour + timedelta(hours=1) < self.end.replace(microsecond=0, second=0, minute=0):
                hour += timedelta(hours=1)
                self._initialize_hour(model, hour)
            last_hour = hour + timedelta(hours=1)
            remaining_minutes = self.end - last_hour
            self._initialize_hour(model, last_hour, last_hour=remaining_minutes.total_seconds())

    def _initialize_hour(self, model: Process, time: datetime, first_hour: float = None, last_hour: float = None) -> None:
        arrival_rate = model.get_arrival_rate(DAYS[time.weekday()], time.hour)
        arrivals = sorted([timedelta(minutes=randint(0, 59)) for i in range(arrival_rate)])
        for item in arrivals:
            if (first_hour is None and last_hour is None) or (first_hour is not None and item.total_seconds() >= (3600 - first_hour)) or (last_hour is not None and item.total_seconds() <= last_hour):
                instance = model.new()
                self.pending_merges[instance.process_id].update({instance.process_instance_id: dict()})
                for data in instance.process_reference.data_objects:
                    self.dm.create_instance(data.id, instance.process_id, instance.process_instance_id)
                self.running_processes[instance.process_id][instance.process_instance_id] = instance
                act = instance.process_reference.get_first_activity()[0]
                self.execution_queue.push(
                    QueueItem(instance, act.id, instance.get_element_instance_id(act.id), time + item, act))










