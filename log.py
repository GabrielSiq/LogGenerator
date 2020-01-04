from __future__ import annotations
import json
from collections import OrderedDict
from datetime import datetime
from pathlib import Path
from config import DEFAULT_PATHS, SUPPORTED_FORMATS
from execution_queue import PriorityQueue


class LogItem:

    def __init__(self, date: datetime, process_id: str, process_instance_id: int, activity_id: str, activity_instance_id: int, status: str, resource=None, data_input=None, data_output=None) -> None:
        self.timestamp = int(date.timestamp())
        self.date = date.strftime("%m/%d/%Y-%H:%M:%S")
        self.process_id = process_id
        self.process_instance_id = process_instance_id
        self.activity_id = activity_id
        self.activity_instance_id = activity_instance_id
        self.status = status
        self.resource = resource
        self.data_input = data_input
        self.data_output = data_output

    # Private methods
    def __lt__(self, other: LogItem) -> bool:
        return self.timestamp < other.timestamp or (self.timestamp == other.timestamp and self.process_id < self.process_id)


class LogWriter:
    # Public methods
    @staticmethod
    def write(log: PriorityQueue, location: str = DEFAULT_PATHS['log'], name: str = None, format: str = 'json') -> None:
        data_folder = Path(location)
        LogWriter._create_output_path(data_folder)
        # hardcoded Yan's output for Ran. Useless for the future.
        if True:
            LogWriter._write_yan(log, data_folder, name)
        elif format == SUPPORTED_FORMATS['json']:
            LogWriter._write_json(log, data_folder, name)

    # Private methods

    @staticmethod
    def _write_yan(log_list: PriorityQueue, location: Path, name: str) -> None:
        file_to_open = LogWriter._unique_path(location, name, '.txt')
        output = []
        lsn = 1
        count = {}
        with file_to_open.open(mode='w') as f:
            while not log_list.is_empty():
                item = log_list.pop()
                if item.status == 'end_activity':
                    if item.process_instance_id not in count.keys():
                        count[item.process_instance_id] = 1
                    wid = item.process_instance_id
                    is_lsn = count[item.process_instance_id]
                    t = item.activity_id
                    entry = str(lsn) + ' ' + str(wid) + ' ' + str(is_lsn) + " " + t
                    if item.resource is not None:
                        for key, value in item.resource.items():
                            entry += ' ' + key + '=' + str(value)
                    if item.data_input is not None:
                        for name, data_object in item.data_input.items():
                            for key, value in data_object.items():
                                entry += ' ' + key + '=' + str(value)
                    entry += ' #'
                    if item.data_output is not None:
                        for name, data_object in item.data_output.items():
                            for key, value in data_object.items():
                                entry += ' ' + key + '=' + str(value)

                    entry += '\n'
                    f.write(entry)
                    count[item.process_instance_id] += 1
                    lsn += 1



    @staticmethod
    def _write_json(log_list: PriorityQueue, location: Path, name: str) -> None:
        file_to_open = LogWriter._unique_path(location, name, '.json')
        output = []
        lid = 0
        while not log_list.is_empty():
            log = OrderedDict({'log_id': lid})
            log.update(LogWriter._parse_event(log_list.pop()))
            output.append(log)
            lid += 1
        with file_to_open.open(mode='w') as f:
            json.dump(output, f, indent=2)

    @staticmethod
    def _parse_event(item: LogItem) -> dict:
        return {k: v for k, v in item.__dict__.items() if v is not None}

    @staticmethod
    def _unique_path(location: Path, name: str, suffix: str) -> Path:
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
    def _create_output_path(location: Path) -> None:
        location.mkdir(parents=True, exist_ok=True)







