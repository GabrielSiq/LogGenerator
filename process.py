from activity import Activity
from data import DataRequirement


class ProcessManager:
    # Initialization and instance variables
    def __init__(self):
        pass


class ProcessInstance:
    def __init__(self, pid, piid, process_reference):
        self.process_id = pid
        self.process_instance_id = piid
        self.process_reference = process_reference
        self.last_activities = dict()
        for activity in self.process_reference.activities:
            self.last_activities[activity] = 1
        for gateway in self.process_reference.gateways:
            self.last_activities[gateway] = 1

    def get_element_instance_id(self, id):
        if id == "END":
            return 0
        self.last_activities[id] += 1
        return self.last_activities[id] - 1

    # Private methods
    def __repr__(self):
        return ', '.join("%s: %s" % item for item in vars(self).items())


class Process:
    # Class variables
    instance = 0

    # Initialization and instance variables
    def __init__(self, id, name, arrival_rate, deadline, activities, gateways, transitions, data_objects):
        self.id = id
        self.name = name
        self.arrival_rate = arrival_rate
        self.deadline = deadline
        self.activities = activities
        self.gateways = dict()
        for gate in gateways:
            self.gateways[gate.id] = gate
        self.transitions = transitions
        self.data_objects = data_objects if isinstance(data_objects[0], DataRequirement)else DataRequirement.from_list(data_objects)

    # Public methods

    def get_arrival_rate(self, day, hour):
        # TODO: Improve modeling of arrival rate to allow for various levels of granularity
        # For now, arrival rate is only represented in terms of instances per hour.
        try:
            return int(self.arrival_rate[day][hour])
        except KeyError:
            return 0

    def get_first_activity(self):
        return self.get_next('START')

    def new(self):
        # TODO: Somehow initialize data objects. maybe the sim manager can call creation in the data manager.
        Process.instance += 1
        return ProcessInstance(self.id, self.instance, self)

    def get_next(self, source, gate=None):
        # returns next activity or gateway id and the delay of the transition
        # For list structure
        for transition in self.transitions:
            if transition.source == source and (gate is None or transition.gate == gate):
                (act, delay) = transition.get_next()
                if act in self.activities:
                    return self.activities[act], delay
                elif act in self.gateways:
                    return self.gateways[act], delay
                elif act == "END":
                    return Activity.end(), delay
                else:
                    raise ValueError(f"Activity or gateway {act} can't be found")
        return None, None

    # Private methods
    def __repr__(self):
        return ', '.join("%s: %s" % item for item in vars(self).items())
