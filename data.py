from collections import OrderedDict
from copy import deepcopy

from config import DATA_TYPES


class DataManager:
    # Initialization and instance variables
    def __init__(self, data_list, process_list=None):
        self.reference_data = dict((data.id, data) for data in data_list)
        self.data_store = dict.fromkeys(process_list, dict()) if process_list is not None else dict()

    # Public methods
    def read_object(self, object_id, fields=None):
        if fields is not None:
            return {k: self.reference_data[object_id].get_fields()[k] for k in fields}
        return self.reference_data[object_id].get_fields()

    def update_object(self, object_id, updated_fields):
        for field, value in updated_fields.items():
            self.reference_data[object_id].set_field(field, value)

    def create_object(self, type, id, name, fields):
        if id in self.reference_data:
            raise ValueError("An object with ID %s already exists." % id)
        if type == DATA_TYPES['form']:
            new = Form(id, name, fields)
        else:
            raise ValueError("Object type %s not supported!" % type)
        self.reference_data[id] = new

    def create_instance(self, object_id, process_id, process_instance_id):
        # Currently, each process can only have one instance of each data object.
        if process_id in self.data_store:
            self.data_store[process_id][process_instance_id] = deepcopy(self.reference_data[object_id])

    def delete_object(self, id):
        try:
            self.reference_data.pop(id)
        except KeyError:
            raise KeyError("No object found with ID %s." % id)

    # Private methods
    def __repr__(self):
        return ', '.join("%s: %s" % item for item in vars(self).items())


class DataRequirement:
    # Initialization and instance variables
    def __init__(self, id, fields):
        self.id = id
        self.fields = fields

    # Public methods
    @classmethod
    def from_list(cls, data_list):
        if data_list is None or data_list == []:
            return None
        class_list = []
        for item in data_list:
            class_list.append(cls(item['id'], item['fields'] if 'fields' in item else []))
        return class_list

    # Private methods
    def __repr__(self):
        return ', '.join("%s: %s" % item for item in vars(self).items())


class DataObject:
    # Initialization and instance variables
    def __init__(self, id, name):
        self.id = id
        self.name = name

    # Private methods
    def __repr__(self):
        return ', '.join("%s: %s" % item for item in vars(self).items())


class Form(DataObject):
    # Class variables
    type = DATA_TYPES['form']

    # Initialization and instance variables
    def __init__(self, id, name, fields):
        DataObject.__init__(self, id, name)

        if isinstance(fields, OrderedDict):
            self.fields = fields
        elif isinstance(fields, list):
            self.fields = OrderedDict().fromkeys(fields, None)
        else:
            raise TypeError("Wrong type for 'fields' variable supplied")

    # Public methods
    def get_fields(self):
        return self.fields

    def get_field(self, field_id):
        return self.fields[field_id]

    def set_field(self, field_id, field_value):
        self.fields[field_id] = field_value


