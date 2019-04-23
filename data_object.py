from collections import OrderedDict


class DataRequirement:
    def __init__(self, id):
        self.id = id

    @classmethod
    def from_list(cls, data_list):
        if data_list is None:
            return None
        class_list = []
        for item in data_list:
            class_list.append(cls(item))
        return class_list

    def __repr__(self):
        return ', '.join("%s: %s" % item for item in vars(self).items())


class DataObject:
    def __init__(self, id):
        self.id = id

    def __repr__(self):
        return ', '.join("%s: %s" % item for item in vars(self).items())


class Form(DataObject):

    type = 'form'

    def __init__(self, id, name, fields):
        DataObject.__init__(self, id)
        self.name = name

        if isinstance(fields, OrderedDict):
            self.fields = fields
        else:
            raise TypeError("Wrong type for 'fields' variable supplied")


