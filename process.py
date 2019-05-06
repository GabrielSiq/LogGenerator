class ProcessManager:
    # Initialization and instance variables
    def __init__(self):
        pass


class ProcessInstance:
    def __init__(self, pid, piid, process_reference):
        self.process_id = pid
        self.process_instance_id = piid
        self.process_reference = process_reference

    # Private methods
    def __repr__(self):
        return ', '.join("%s: %s" % item for item in vars(self).items())


class Process:
    # Class variables
    instance = 0

    # Initialization and instance variables
    def __init__(self, id, name, arrival_rate, deadline, activities, gateways, transitions):
        self.id = id
        self.name = name
        self.arrival_rate = arrival_rate
        self.deadline = deadline
        self.activities = activities
        self.gateways = dict()
        for gate in gateways:
            self.gateways[gate.id] = gate
        self.transitions = transitions
        # self.data_objects = data_objects if isinstance(data_objects[0], DataRequirement)else DataRequirement.from_list(data_objects)
        # self.resources = resources

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
        Process.instance += 1
        return ProcessInstance(self.id, self.instance, self)

    def get_next(self, source, gate=None):
        # returns next activity or gateway id and the delay of the transition
        # For list structure
        for transition in self.transitions:
            if transition.source == source and (gate is None or transition.gate == gate):
                (act, delay) = transition.get_next()
                return self.activities[act], delay
        # For dict structure
        # if gate is None:
        #     return self.transitions[source].get_next()
        # else:
        #     return self.transitions[source][gate].get_next()

    # Private methods
    def __repr__(self):
        return ', '.join("%s: %s" % item for item in vars(self).items())
