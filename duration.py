from numpy import random


class Duration:

    def __init__(self, distribution):
        self.type = distribution['type']
        distribution.pop('type')
        self.parameters = distribution

    def generate(self):
        if self.type == 'normal':
            return random.normal(loc=self.parameters['mean'], scale=self.parameters['variance'])
        elif self.type == 'uniform':
            return random.uniform(low=self.parameters['low'], high=self.parameters['high'])
        elif self.type == 'triangular':
            return random.triangular(left=self.parameters['left'], mode=self.parameters['mode'], right=self.parameters['right'])
        elif self.type == 'beta':
            return random.beta(a=self.parameters['a'], b=self.parameters['b'])
        else:
            return None
