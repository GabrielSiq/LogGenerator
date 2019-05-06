from duration import Duration


class Transition:
    # Initialization and instance variables
    def __init__(self, source, destination, gate=None, distribution=0):
        self.source = source
        self.gate = gate
        self.destination = destination
        self.delay = Duration(distribution)

    # Public methods
    def get_next(self):
        return self.destination, self.delay.generate()

    # Private methods
    def __repr__(self):
        return ', '.join("%s: %s" % item for item in vars(self).items())
