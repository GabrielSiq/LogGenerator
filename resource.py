class Resource:

    def __init__(self, id, quantity):
        self.id = id
        self.quantity = quantity

    @classmethod
    def from_list(cls, resource_list):
        class_list = []
        for item in resource_list:
            class_list.append(cls(item.key, item.value))
        return class_list
