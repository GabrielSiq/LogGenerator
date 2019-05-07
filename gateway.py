from numpy import random
from config import GATEWAY_TYPES


class Gateway:
    # Initialization and instance variables
    def __init__(self, id, name, type, gates, distribution=None, rule=None):
        self.id = id
        self.name = name
        self.type = type
        self.merge_inputs = []
        if self.type == GATEWAY_TYPES['choice']:
            if rule is not None:
                self.decider = GateRule(gates, rule)
            elif distribution is not None:
                self.decider = GateDistribution(gates, distribution)
            else:
                raise ValueError("For choice gateways, either rule or distribution must be present.")
        elif self.type == GATEWAY_TYPES['parallel']:
            self.decider = None
        else:
            raise ValueError("Value %s is not a valid gateway type." % self.type)
        self.gates = gates

    # Public methods
    def get_gate(self):
        if self.type == GATEWAY_TYPES['parallel']:
            return self.gates
        else:
            return [self.decider.get_gate()]

    # Private methods
    def __repr__(self):
        return ', '.join("%s: %s" % item for item in vars(self).items())


class GateRule:
    # TODO: Implement gate rule.
    # Initialization and instance variables
    def __init__(self, gates, rule):
        a = rule
        pass

    # Private methods
    def __repr__(self):
        return ', '.join("%s: %s" % item for item in vars(self).items())


class GateDistribution:
    # TODO: Check types in initialization, for public functions
    # Initialization and instance variables
    def __init__(self, gates, pdf):
        # gates is a list of the gate ids
        # pdf is a list of probabilities ordered by gates
        self.gates = gates
        self.pdf = list(map(float, pdf))
        if sum(self.pdf) != 1:
            raise ValueError("Probabilities don't add to 1.")

    # Public methods
    def get_gate(self):
        return random.choice(self.gates, p=self.pdf)

    # Private methods
    def __repr__(self):
        return ', '.join("%s: %s" % item for item in vars(self).items())
