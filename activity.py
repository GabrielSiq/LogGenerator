import math
from config import PRIORITY_VALUES
from data_object import DataRequirement
from duration import Duration
from failure import Failure
from resource import ResourceRequirement


class Activity:
    # Activities contained in process models

    # Initialization and instance variables
    def __init__(self, id, name, distribution=0, data_input=None, data_output=None, resources=None, failure_rate=0, retries=0, timeout=None, priority='normal'):
        self.id = id
        self.name = name
        self.duration = Duration(distribution)
        self.data_input = DataRequirement.from_list(data_input)
        self.data_output = DataRequirement.from_list(data_output)
        self.resources = ResourceRequirement.from_list(resources)
        self.failure = Failure(failure_rate if failure_rate is not None else 0)
        self.retries = retries if retries is not None else 0
        self.timeout = int(timeout) if timeout is not None else math.inf
        if priority is None:
            self.priority = PRIORITY_VALUES['normal']
        elif priority.lower() in PRIORITY_VALUES:
            self.priority = PRIORITY_VALUES[priority.lower()]
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

    @staticmethod
    def end():
        return Activity("END", "END")

    # Private methods
    def __repr__(self):
        return ', '.join("%s: %s" % item for item in vars(self).items())
