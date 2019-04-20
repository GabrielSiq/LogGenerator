class Resource:

    def __init__(self, id, quantity):
        self.id = id
        self.quantity = quantity

    @classmethod
    def from_list(cls, resource_list):
        if not resource_list:
            return None
        class_list = []
        for item in resource_list:
            class_list.append(cls(item[0], item[1]))
        return class_list
