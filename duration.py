from typing import Union, Optional
from numpy import random


class Duration:
    # Initialization and instance variables
    def __init__(self, distribution: Union[dict, int]) -> None:
        if type(distribution) is dict:
            self.type = distribution['type'].lower()
            distribution.pop('type')
            self.parameters = distribution
        else:
            self.type = 'const'
            self.parameters = {'value': distribution if distribution is not None else 0}

    # Public methods
    def generate(self) -> Optional[int]:
        if self.type == 'normal':
            return int(random.normal(loc=self.parameters['mean'], scale=self.parameters['variance']))
        elif self.type == 'uniform':
            return int(random.uniform(low=self.parameters['low'], high=self.parameters['high']))
        elif self.type == 'triangular':
            return int(random.triangular(left=self.parameters['left'], mode=self.parameters['mode'], right=self.parameters['right']))
        elif self.type == 'beta':
            return int(random.beta(a=self.parameters['a'], b=self.parameters['b']))
        elif self.type == 'const':
            return int(self.parameters['value'])
        else:
            return None

    # Private Methods
    def __repr__(self):
        return ', '.join("%s: %s" % item for item in vars(self).items())
