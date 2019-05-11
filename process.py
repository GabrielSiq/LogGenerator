from __future__ import annotations
from activity import Activity
from data import DataRequirement
from typing import List, Union, Tuple, Dict

from gateway import Gateway
from transition import Transition


class ProcessInstance:
    def __init__(self, pid: str, piid: int, process_reference: Process) -> None:
        self.process_id = pid
        self.process_instance_id = piid
        self.process_reference = process_reference
        self.last_activities = dict((activity, 1) for activity in {**self.process_reference.activities, **self.process_reference.gateways})

    def get_element_instance_id(self, id: str) -> int:
        if id == "END":
            return 0
        self.last_activities[id] += 1
        return self.last_activities[id] - 1

    # Private methods
    def __repr__(self):
        return ', '.join("%s: %s" % item for item in vars(self).items())


class Process:
    # Class variables
    instance = 0

    # Initialization and instance variables
    def __init__(self, id: str, name: str, arrival_rate: dict, deadline: int, activities: Dict[str, Activity], gateways: List[Gateway], transitions: List[Transition], data_objects: Union[List[DataRequirement], List[dict]]) -> None:
        self.id = id
        self.name = name
        self.arrival_rate = arrival_rate
        self.deadline = deadline
        self.activities = activities
        self.gateways = dict((gate.id, gate) for gate in gateways)
        self.transitions = transitions
        self.data_objects = data_objects if isinstance(data_objects[0], DataRequirement)else DataRequirement.from_list(data_objects)

    # Public methods

    def get_arrival_rate(self, day: str, hour: int) -> int:
        # TODO: Improve modeling of arrival rate to allow for various levels of granularity
        # For now, arrival rate is only represented in terms of instances per hour.
        try:
            return self.arrival_rate[day][hour]
        except KeyError:
            return 0

    def get_first_activity(self) -> Union[Tuple[Activity, int], Tuple[Gateway, int]]:
        return self.get_next('START')

    def new(self) -> ProcessInstance:
        Process.instance += 1
        return ProcessInstance(self.id, self.instance, self)

    def get_next(self, source: str, gate: str = None) -> Union[Tuple[Activity, int], Tuple[Gateway, int], Tuple[None, None]]:
        # returns next activity or gateway id and the delay of the transition
        # For list structure
        for transition in self.transitions:
            if transition.source == source and (gate is None or transition.gate == gate):
                (act, delay) = transition.get_next()
                if act in self.activities:
                    return self.activities[act], delay
                elif act in self.gateways:
                    return self.gateways[act], delay
                elif act == "END":
                    return Activity.end(), delay
                else:
                    raise ValueError(f"Activity or gateway {act} can't be found")
        return None, None

    # Private methods
    def __repr__(self):
        return ', '.join("%s: %s" % item for item in vars(self).items())
