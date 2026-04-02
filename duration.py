from typing import Union, Optional
from numpy import random


class Duration:
    # Initialization and instance variables
    def __init__(self, distribution: Union[dict, int]) -> None:
        if type(distribution) is dict:
            distribution = dict(distribution)
            self.type = distribution.pop('type').lower()
            self.parameters = distribution
        else:
            self.type = 'const'
            self.parameters = {'value': distribution if distribution is not None else 0}

    # Public methods
    def generate(self) -> Optional[int]:
        if self.type == 'normal':
            dur = round(random.normal(loc=self.parameters['mean'], scale=self.parameters['std']))
        elif self.type == 'uniform':
            dur = round(random.uniform(low=self.parameters['low'], high=self.parameters['high']))
        elif self.type == 'triangular':
            dur = round(random.triangular(left=self.parameters['left'], mode=self.parameters['mode'], right=self.parameters['right']))
        elif self.type == 'beta':
            dur = round(random.beta(a=self.parameters['a'], b=self.parameters['b']))
        elif self.type == 'const':
            dur = int(self.parameters['value'])
        else:
            dur = None

        return max(0, dur) if dur is not None else None

    # Private Methods
    def __repr__(self):
        return ', '.join("%s: %s" % item for item in vars(self).items())
