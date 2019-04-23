from numpy import random


class Failure:
    # Defines if an activity has failed or not.

    def __init__(self, failure_rate):
        self.rate = failure_rate

    def check_failure(self):
        # Returns True if failed, False if not.
        return random.choice([True, False], p=[self.rate, 1-self.rate])

    def __repr__(self):
        return ', '.join("%s: %s" % item for item in vars(self).items())
