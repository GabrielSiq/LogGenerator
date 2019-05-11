import importlib.util
from numpy import random
from config import GATEWAY_TYPES, MERGE_OUTPUT, DEFAULT_PATHS
from typing import List, Dict

RULE_MODULE = importlib.import_module(DEFAULT_PATHS['rules_function'])


class Gateway:
    # Initialization and instance variables
    def __init__(self, id: str, name: str, type: str, gates: List[str], distribution: List[float] = None, rule: str = None) -> None:
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
    def get_gate(self, input_data: Dict[str, dict] = None) -> List[str]:
        if self.type == GATEWAY_TYPES['parallel'] or self.type == GATEWAY_TYPES['merge']:
            return self.gates
        elif self.type == GATEWAY_TYPES['choice']:
            return [self.decider.get_gate()]
        else:
            # Rule
            return [self.decider.get_gate(input_data)]

    def get_inputs(self) -> List[str]:
        if self.type == GATEWAY_TYPES['merge']:
            return self.merge_inputs

    # Private methods
    def __repr__(self):
        return ', '.join("%s: %s" % item for item in vars(self).items())


class GateRule:
    # Initialization and instance variables
    def __init__(self, gates: List[str], rule: str) -> None:
        self.gates = gates
        self.decision = getattr(RULE_MODULE, rule)

    def get_gate(self, input_data: Dict[str, dict] = None) -> str:
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
    # TODO: Add type hints to all functions
    # Initialization and instance variables
    def __init__(self, gates: List[str], pdf: List[float]) -> None:
        self.gates = gates
        self.pdf = pdf
        if sum(self.pdf) != 1:
            raise ValueError("Probabilities don't add to 1.")

    # Public methods
    def get_gate(self) -> str:
        return random.choice(self.gates, p=self.pdf)

    # Private methods
    def __repr__(self):
        return ', '.join("%s: %s" % item for item in vars(self).items())
