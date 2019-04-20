from duration import Duration
from failure import Failure
from resource import Resource



class Activity:
    # Activities contained in process models

    ALLOWED_PRIORITIES = ['low', 'normal', 'high']

    def __init__(self, id, name, distribution=None, data_input=None, resources=None, failure_rate=0, retries=0, timeout=None, priority='normal'):
        self.id = id
        self.name = name
        self.duration = Duration(distribution)
        self.data_input = DataObject(data_input)
        self.data_output = DataObject(data_input)
        self.resources = Resource.from_list(resources)
        self.failure = Failure(failure_rate)
        self.retries = retries
        self.timeout = timeout
        if priority.lower() in Activity.ALLOWED_PRIORITIES:
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
