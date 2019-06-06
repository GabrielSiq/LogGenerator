from typing import Union, Tuple
from duration import Duration


class Transition:
    # Initialization and instance variables
    def __init__(self, source: str, destination: str, sgate: str = None, dgate: str = None, distribution: Union[dict, int] = 0) -> None:
        self.source = source
        self.source_gate = sgate
        self.destination = destination
        self.destination_gate = dgate
        self.delay = Duration(distribution)

    # Public methods
    def get_next(self) -> Tuple[str, str, int]:
        return self.destination, self.destination_gate, self.delay.generate()

    # Private methods
    def __repr__(self):
        return ', '.join("%s: %s" % item for item in vars(self).items())
