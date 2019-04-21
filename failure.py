import random


class Failure:
    # Defines if an activity has failed or not.

    def __init__(self, failure_rate):
        self.rate = failure_rate

    def check(self):
        chance = random.random()
        return chance < self.rate

    def __repr__(self):
        return ', '.join("%s: %s" % item for item in vars(self).items())
