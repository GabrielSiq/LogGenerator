import json
from datetime import datetime
from pathlib import Path
from config import DEFAULT_PATHS, SUPPORTED_FORMATS


class LogItem:
    log_id = 0
    def __init__(self, date, process_id, process_instance_id, activity_id, activity_instance_id, status):
        self.log_id = LogItem.log_id
        LogItem.log_id += 1 # warning: NOT thread safe
        self.timestamp = date.timestamp()
        self.process_id = process_id
        self.process_instance_id = process_instance_id
        self.activity_id = activity_id
        self.activity_instance_id = activity_instance_id
        self.status = status
        self.resource = []
        self.data_input = []
        self.data_output = []

    # Private methods
    def __lt__(self, other):
        return self.timestamp < other.timestamp


class LogWriter:
    # Public methods
    @staticmethod
    def write(log, location=DEFAULT_PATHS['log'], name=None, format='json'):
        data_folder = Path(location)
        LogWriter._create_output_path(data_folder)
        if format == SUPPORTED_FORMATS['json']:
            LogWriter._write_json(log, data_folder, name)

    # Private methods
    @staticmethod
    def _write_json(log_list, location, name):
        file_to_open = LogWriter._unique_path(location, name, '.json')
        output = []
        while log_list:
            output.append(LogWriter._parse_event(log_list.pop(0)))
        with file_to_open.open(mode='w') as f:
            json.dump(output, f, indent=4)

    @staticmethod
    def _parse_event(item):
        return item.__dict__

    @staticmethod
    def _unique_path(location, name, suffix):
        if name is not None:
            file_to_open = (location / name).with_suffix(suffix)
            if file_to_open.exists():
                i = 2
                stem = file_to_open.stem
                file_to_open = file_to_open.with_name(stem + ' (' + str(i) + ')').with_suffix(suffix)
                while file_to_open.exists():
                    i += 1
                    file_to_open = file_to_open.with_name(stem + ' (' + str(i) + ')').with_suffix(suffix)
        else:
            file_to_open = (location / datetime.now().strftime("%Y%m%d-%H%M%S")).with_suffix(suffix)
        return file_to_open

    @staticmethod
    def _create_output_path(location):
        location.mkdir(parents=True, exist_ok=True)







