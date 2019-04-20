from duration import Duration
from failure import Failure
from resource import Resource


class Activity:
    # Activities contained in process models

    def __init__(self, id, name, distribution=None, data_input=None, resource=None, failure_rate=0, retries=0, timeout=None, priority='mid'):
        self.id = id
        self.name = name
        self.duration = Duration(distribution)
        self.data_input = DataObject(data_input)
        self.data_output = DataObject(data_input)
        self.resource = Resource(resource)
        self.failure = Failure(failure_rate)
        self.retries = retries
        self.timeout = timeout
        self.priority = priority

    def generate_duration(self):
        # Returns an instance of the randomly generated duration time
        return self.duration.generate()

    def generate_failure(self):
        return self.failure.check()
