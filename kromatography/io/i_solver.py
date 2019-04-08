from traits.api import Interface


class ISolver(Interface):

    def run(self):
        """ Returns a simulation object after a calling the solver
            and updating the simulation"""
