import logging
from shutil import copyfile
from os.path import isfile
from uuid import uuid4

from kromatography.model.simulation import Simulation
from kromatography.solve.simulation_job_utils import walk_dataelement_editable

logger = logging.getLogger(__name__)


class LazyLoadingSimulation(Simulation):
    """ Simulation object, where the output is lazy loaded from CADET file JIT.

    This is useful when massive amounts of simulations are created because it
    doesn't require keeping the SimulationResults in memory.
    """

    #: The output isn't held by any (instance) attribute in a LazySimulation
    output = None

    @classmethod
    def from_simulation(cls, sim):
        """ Create a LazyLoadingSimulation from a regular simulation.

        Copy all attributes including run ones, except for the output. To
        replace the output, the source cadet file is copied into the target
        simulation unless the cadet file has been
        erased.
        """
        new_sim = cls(name=sim.name)
        new_sim.copy_traits(sim, copy="deep")
        new_sim.uuid = uuid4()

        if sim.has_run:
            source_file = sim.cadet_filepath
            if isfile(source_file):
                copyfile(source_file, new_sim.cadet_filepath)
                new_sim.set_as_run()
            else:
                new_sim.set_as_not_run()

        return new_sim

    def to_simulation(self):
        """ Export the current simulation to a regular simulation with its
        results data in memory.
        """
        new_sim = Simulation(name=self.name)
        new_sim.copy_traits(self)
        new_sim.uuid = uuid4()
        if self.has_run:
            new_sim.output = self.output
            new_sim.set_as_run()
        return new_sim

    def __getattribute__(self, attr_name):
        """ Attribute getter that does lazy loading of result file for output.
        """
        if attr_name == "output":
            if isfile(self.cadet_filepath):
                try:
                    output = self.load_results()
                    # Since sim has run, output should not be editable
                    walk_dataelement_editable(output, False,
                                              skip_traits=['source_experiment'])  # noqa
                except Exception as e:
                    msg = "Failed to retrieve the output data from CADET " \
                          "file. Error was {}".format(e)
                    logger.info(msg)
                    output = None
            else:
                output = None

            return output
        else:
            return super(LazyLoadingSimulation, self).__getattribute__(
                attr_name
            )

    def __setattribute__(self, attr_name, value):
        """ Do nothing when trying to set the output since getter ignores it.
        """
        if attr_name == "output":
            return
        else:
            super(LazyLoadingSimulation, self).__setattribute__(attr_name,
                                                                value)

    def _name_changed(self):
        # No listener needed in this lazy case since the output will be loaded
        # upon request
        pass


def is_lazy(sim):
    """ Evaluate if the provided simulation is of type LazyLoading or not.
    """
    if not isinstance(sim, Simulation):
        msg = "is_lazy can only be called on a simulation."
        logger.exception(msg)
        raise ValueError(msg)

    return isinstance(sim, LazyLoadingSimulation)
