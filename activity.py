from data_object import DataObject
from duration import Duration
from failure import Failure
from resource import ResourceRequirement


class Activity:
    # Activities contained in process models

    ALLOWED_PRIORITIES = ['low', 'normal', 'high']

    def __init__(self, id, name, distribution=None, data_input=None, resources=None, failure_rate=0, retries=0, timeout=None, priority='normal'):
        self.id = id
        self.name = name
        self.duration = Duration(distribution)
        self.data_input = DataObject.from_list(data_input)
        self.data_output = DataObject.from_list(data_input)
        self.resources = ResourceRequirement.from_list(resources)
        self.failure = Failure(failure_rate if failure_rate is not None else 0)
        self.retries = retries if retries is not None else 0
        self.timeout = timeout
        if priority is None:
            self.priority = 'normal'
        elif priority.lower() in Activity.ALLOWED_PRIORITIES:
            self.priority = priority.lower()
        else:
            # TODO: Add more helpful error messages.
            print('Priority value not allowed.')
            raise TypeError

    def generate_duration(self):
        # Returns an instance of the randomly generated duration time
        return self.duration.generate()

    def generate_failure(self):
        return self.failure.check()

    def __repr__(self):
        return "Id:%s, Name:%s" % (self.id, self.name)
