from numpy import random


class Duration:

    def __init__(self, distribution):
        if type(distribution) is dict:
            self.type = distribution['type']
            distribution.pop('type')
            self.parameters = distribution
        else:
            self.type = 'const'
            self.parameters = {'value', distribution}

    def generate(self):
        if self.type == 'normal':
            return random.normal(loc=self.parameters['mean'], scale=self.parameters['variance'])
        elif self.type == 'uniform':
            return random.uniform(low=self.parameters['low'], high=self.parameters['high'])
        elif self.type == 'triangular':
            return random.triangular(left=self.parameters['left'], mode=self.parameters['mode'], right=self.parameters['right'])
        elif self.type == 'beta':
            return random.beta(a=self.parameters['a'], b=self.parameters['b'])
        elif self.type == 'const':
            return self.parameters['value']
        else:
            return None

    def __repr__(self):
        return ', '.join("%s: %s" % item for item in vars(self).items())
