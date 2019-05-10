import importlib
from typing import Union

import math
from config import PRIORITY_VALUES, DEFAULT_PATHS
from data import DataRequirement
from duration import Duration
from failure import Failure
from resource import ResourceRequirement

DATA_MODULE = importlib.import_module(DEFAULT_PATHS['data_function'])


class Activity:
    # Activities contained in process models

    # Initialization and instance variables
    def __init__(self, id: str, name: str, distribution: Union[dict, int] = 0, data_input: list = None, data_output: list = None, resources: list = None, failure_rate: float = 0, retries: int = 0, timeout: int = None, priority: str = 'normal') -> None:
        self.id = id
        self.name = name
        self.duration = Duration(distribution)
        self.data_input = DataRequirement.from_list(data_input)
        self.data_output = DataRequirement.from_list(data_output)
        self.process_data = getattr(DATA_MODULE, self.id) if data_output is not None else None
        self.resources = ResourceRequirement.from_list(resources)
        self.failure = Failure(failure_rate if failure_rate is not None else 0)
        self.retries = retries if retries is not None else 0
        self.timeout = timeout if timeout is not None else math.inf
        if priority is None:
            self.priority = PRIORITY_VALUES['normal']
        elif priority.lower() in PRIORITY_VALUES:
            self.priority = PRIORITY_VALUES[priority.lower()]
        else:
            raise TypeError('Value %s is not supported for priority.' % priority)

    # Public methods
    def generate_duration(self) -> int:
        # Returns an instance of the randomly generated duration time
        return self.duration.generate()

    def generate_failure(self) -> bool:
        return self.failure.check_failure()

    def update(self, fields: dict) -> None:
        for key, value in fields.items():
            if key == 'data_input' or key == 'data_output':
                setattr(self, key, DataRequirement.from_list(value))
            elif key == 'duration':
                setattr(self, key, Duration(value))
            elif key == 'failure':
                setattr(self, key, Failure(value))
            elif key == 'priority':
                setattr(self, key, PRIORITY_VALUES[value.lower()])
            else:
                setattr(self, key, value)

    @staticmethod
    def end() -> 'Activity':
        return Activity("END", "END")

    # Private methods
    def __repr__(self):
        return ', '.join("%s: %s" % item for item in vars(self).items())
