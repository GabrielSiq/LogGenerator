import importlib.util
from numpy import random
from config import GATEWAY_TYPES, MERGE_OUTPUT, DEFAULT_PATHS

RULE_MODULE = importlib.import_module(DEFAULT_PATHS['rules_function'])


class Gateway:
    # Initialization and instance variables
    def __init__(self, id, name, type, gates, distribution=None, rule=None):
        self.id = id
        self.name = name
        self.type = type
        if self.type == GATEWAY_TYPES['choice']:
            if rule is not None:
                self.type = GATEWAY_TYPES['rule']
                self.decider = GateRule(gates, rule)
            elif distribution is not None:
                self.decider = GateDistribution(gates, distribution)
            else:
                raise ValueError("For choice gateways, either rule or distribution must be present.")
            self.gates = gates
        elif self.type == GATEWAY_TYPES['parallel']:
            self.decider = None
            self.gates = gates
        elif self.type == GATEWAY_TYPES['merge']:
            self.merge_inputs = gates
            self.gates = MERGE_OUTPUT
        else:
            raise ValueError("Value %s is not a valid gateway type." % self.type)

    # Public methods
    def get_gate(self, input_data=None):
        if self.type == GATEWAY_TYPES['parallel'] or self.type == GATEWAY_TYPES['merge']:
            return self.gates
        elif self.type == GATEWAY_TYPES['choice']:
            return [self.decider.get_gate()]
        else:
            # Rule
            return [self.decider.get_gate(input_data)]

    def get_inputs(self):
        if self.type == GATEWAY_TYPES['merge']:
            return self.merge_inputs

    # Private methods
    def __repr__(self):
        return ', '.join("%s: %s" % item for item in vars(self).items())


class GateRule:
    # Initialization and instance variables
    def __init__(self, gates, rule):
        self.gates = gates
        self.decision = getattr(RULE_MODULE, rule)

    def get_gate(self, input_data=None):
        if input_data is not None:
            gate = self.decision(input_data)
        else:
            gate = self.decision()
        if gate in self.gates:
            return gate
        else:
            raise RuntimeError("Gate provided by input rule function doesn't exist.")

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
