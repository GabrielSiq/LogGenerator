from numpy import random


class Failure:
    # Defines if an activity has failed or not.

    # Initialization and instance variables
    def __init__(self, failure_rate: float) -> None:
        self.rate = float(failure_rate)

    # Public methods
    def check_failure(self) -> bool:
        # Returns True if failed, False if not.
        return random.choice([True, False], p=[self.rate, 1-self.rate])

    # Private methods
    def __repr__(self):
        return ', '.join("%s: %s" % item for item in vars(self).items())
