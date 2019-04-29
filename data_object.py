from collections import OrderedDict


class DataManager:
    def __init__(self, data_list):
        self.data_store = {}

        for data in data_list:
            self.data_store[data.id] = data

    def read_object(self, object_id, fields=None):
        if fields is not None:
            return {k: self.data_store[object_id].get_fields()[k] for k in fields}
        return self.data_store[object_id].get_fields()

    def update_object(self, object_id, updated_fields):
        for field, value in updated_fields.items():
            self.data_store[object_id].set_field(field, value)

    def create_object(self, type, id, name, fields):
        if id in self.data_store:
            raise ValueError("An object with this ID already exists.")
        if type == 'form':
            new = Form(id, name, fields)
        else:
            raise ValueError("Object type not supported!")
        self.data_store[id] = new

    def delete_object(self, id):
        try:
            self.data_store.pop(id)
        except KeyError:
            raise KeyError("No object found with given ID.")

    def __repr__(self):
        return ', '.join("%s: %s" % item for item in vars(self).items())


class DataRequirement:
    def __init__(self, id):
        self.id = id

    @classmethod
    def from_list(cls, data_list):
        if data_list is None or data_list == []:
            return None
        class_list = []
        for item in data_list:
            class_list.append(cls(item['id']))
        return class_list

    def __repr__(self):
        return ', '.join("%s: %s" % item for item in vars(self).items())


class DataObject:
    def __init__(self, id, name):
        self.id = id
        self.name = name

    def __repr__(self):
        return ', '.join("%s: %s" % item for item in vars(self).items())


class Form(DataObject):

    type = 'form'

    def __init__(self, id, name, fields):
        DataObject.__init__(self, id, name)

        if isinstance(fields, OrderedDict):
            self.fields = fields
        elif isinstance(fields, list):
            self.fields = OrderedDict()
            for field in fields:
                self.fields[field] = None
        else:
            raise TypeError("Wrong type for 'fields' variable supplied")

    def get_fields(self):
        return self.fields

    def get_field(self, field_id):
        return self.fields[field_id]

    def set_field(self, field_id, field_value):
        self.fields[field_id] = field_value



