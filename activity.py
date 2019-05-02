from config import PRIORITY_TYPES, GATEWAY_TYPES
from data_object import DataRequirement
from duration import Duration
from failure import Failure
from resource import ResourceRequirement
from numpy import random


class ProcessManager:
    # Initialization and instance variables
    def __init__(self):
        pass


class Process:
    # Initialization and instance variables
    def __init__(self, id, name, arrival_rate, deadline, activities, gateways, transitions):
        self.id = id
        self.name = name
        self.arrival_rate = arrival_rate
        self.deadline = deadline
        self.activities = activities
        self.gateways = {}
        for gate in gateways:
            self.gateways[gate.id] = gate
        self.transitions = transitions
        # self.data_objects = data_objects if isinstance(data_objects[0], DataRequirement)else DataRequirement.from_list(data_objects)
        # self.resources = resources

    # Public methods
    def get_next(self, source, gate=None):
        # returns next activity or gateway id and the delay of the transition
        if gate is None:
            return self.transitions[source].get_next()
        else:
            return self.transitions[source][gate].get_next()

    # Private methods
    def __repr__(self):
        return ', '.join("%s: %s" % item for item in vars(self).items())


class Gateway:
    # Initialization and instance variables
    def __init__(self, id, name, type, gates, distribution=None, rule=None):
        self.id = id
        self.name = name
        self.type = type
        self.merge_inputs = []
        if self.type == GATEWAY_TYPES['choice']:
            if rule is not None:
                self.decider = GateRule(gates, rule)
            elif distribution is not None:
                self.decider = GateDistribution(gates, distribution)
            else:
                raise ValueError("For choice gateways, either rule or distribution must be present.")
        elif self.type == GATEWAY_TYPES['parallel']:
            self.decider = None
        else:
            raise ValueError("Value %s is not a valid gateway type." % self.type)
        self.gates = gates

    # Public methods
    def get_gate(self):
        if self.type == GATEWAY_TYPES['parallel']:
            return self.gates
        else:
            return self.decider.get_gate()

    # Private methods
    def __repr__(self):
        return ', '.join("%s: %s" % item for item in vars(self).items())


class GateRule:
    # TODO: Implement gate rule.
    # Initialization and instance variables
    def __init__(self, gates, rule):
        a = rule
        pass

    # Private methods
    def __repr__(self):
        return ', '.join("%s: %s" % item for item in vars(self).items())


class GateDistribution:
    # TODO: Check types in initialization, for public functions
    # Initialization and instance variables
    def __init__(self, gates, pdf):
        # gates is a list of the gate ids
        # pdf is a list of probabilities ordered by gates
        self.gates = gates
        self.pdf = list(map(float, pdf))
        if sum(self.pdf) != 1:
            raise ValueError("Probabilities don't add to 1.")

    # Public methods
    def get_gate(self):
        return random.choice(self.gates, p=self.pdf)

    # Private methods
    def __repr__(self):
        return ', '.join("%s: %s" % item for item in vars(self).items())


class Transition:
    # Initialization and instance variables
    def __init__(self, source, destination, gate=None, distribution=0):
        self.source = source
        self.gate = gate
        self.destination = destination
        self.delay = Duration(distribution)

    # Public methods
    def get_next(self):
        return self.destination, self.delay.generate()

    # Private methods
    def __repr__(self):
        return ', '.join("%s: %s" % item for item in vars(self).items())


class Activity:
    # Activities contained in process models
    # TODO: add instance ids to all classes (or maybe only when they're on the queue running, maybe thats better)
    # Initialization and instance variables
    def __init__(self, id, name, distribution=0, data_input=None, data_output=None, resources=None, failure_rate=0, retries=0, timeout=None, priority=PRIORITY_TYPES['normal']):
        self.id = id
        self.name = name
        self.duration = Duration(distribution)
        self.data_input = DataRequirement.from_list(data_input)
        self.data_output = DataRequirement.from_list(data_output)
        self.resources = ResourceRequirement.from_list(resources)
        self.failure = Failure(failure_rate if failure_rate is not None else 0)
        self.retries = retries if retries is not None else 0
        self.timeout = timeout
        if priority is None:
            self.priority = PRIORITY_TYPES['normal']
        elif priority.lower() in PRIORITY_TYPES.values():
            self.priority = priority.lower()
        else:
            raise TypeError('Value %s is not supported for priority.' % priority)

    # Public methods
    def generate_duration(self):
        # Returns an instance of the randomly generated duration time
        return self.duration.generate()

    def generate_failure(self):
        return self.failure.check_failure()

    def update(self, fields):
        for key, value in fields.items():
            setattr(self, key, value)

    # Private methods
    def __repr__(self):
        return ', '.join("%s: %s" % item for item in vars(self).items())
