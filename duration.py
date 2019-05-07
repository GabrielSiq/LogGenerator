from numpy import random


class Duration:
    # Initialization and instance variables
    def __init__(self, distribution):
        if type(distribution) is dict:
            self.type = distribution['type'].lower()
            distribution.pop('type')
            self.parameters = distribution
        else:
            self.type = 'const'
            self.parameters = {'value': int(distribution) if distribution is not None else 0}

    # Public methods
    def generate(self):
        if self.type == 'normal':
            return int(random.normal(loc=int(self.parameters['mean']), scale=int(self.parameters['variance'])))
        elif self.type == 'uniform':
            return int(random.uniform(low=int(self.parameters['low']), high=int(self.parameters['high'])))
        elif self.type == 'triangular':
            return int(random.triangular(left=int(self.parameters['left']), mode=int(self.parameters['mode']), right=int(self.parameters['right'])))
        elif self.type == 'beta':
            return int(random.beta(a=int(self.parameters['a']), b=int(self.parameters['b'])))
        elif self.type == 'const':
            return int(self.parameters['value'])
        else:
            return None

    # Private Methods
    def __repr__(self):
        return ', '.join("%s: %s" % item for item in vars(self).items())
