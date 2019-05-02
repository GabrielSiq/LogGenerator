class LogItem:
    def __init__(self, date, process_id, process_instance_id, activity_id, activity_instance_id, status):
        self.log_id = id(self)
        self.timestamp = date.timestamp()
        self.process_id = process_id
        self.process_instance_id = process_instance_id
        self.activity_id = activity_id
        self.activity_instance_id = activity_instance_id
        self.status = status
        self.resource = []
        self.data_input = []
        self.data_output = []

    def __lt__(self, other):
        return self.timestamp < other.timestamp

class LogWriter:
    def __init__(self, location, format):


