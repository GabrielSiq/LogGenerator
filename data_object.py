class DataObject:
    def __init__(self, id):
        self.id = id

    @classmethod
    def from_list(cls, data_list):
        class_list = []
        for item in data_list:
            class_list.append(cls(item))
        return class_list
