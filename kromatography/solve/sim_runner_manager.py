import logging

from traits.api import Dict, HasStrictTraits, List, Set

logger = logging.getLogger(__name__)


class SimulationRunnerManager(HasStrictTraits):
    """ Class to manager multiple simulation runners, and connect a sim to its
    runner.
    """
    #: Set of runner uuids in the _runner_list
    known_runners = Set

    _runner_list = List

    _sim_work_item_map = Dict

    _work_item_sim_map = Dict

    def add_runner(self, runner, index_sims=False):
        """ Add a new runner to the manager.

        Parameters
        ----------
        runner : SimulationRunner
            Simulation runner to keep track of.

        index_sims : bool [OPTIONAL, default=False]
            Whether all sims submitted to the runner should be added to the
            internal maps for quick retrieval.
        """
        if runner.uuid not in self.known_runners:
            self._runner_list.append(runner)
            self.known_runners.add(runner.uuid)

        if index_sims:
            self.index_all_sims([runner])

    def index_all_sims(self, runner_list=None):
        """ Rebuild maps for all simulations submitted to a list of runners.
        """
        if runner_list is None:
            runner_list = self._runner_list

        for runner in runner_list:
            sims = runner.simulation_list
            for sim, work_item in zip(runner.work_item_ids, sims):
                self._work_item_sim_map[(runner.job_id, work_item)] = sim.uuid
                self._sim_work_item_map[sim.uuid] = (runner.job_id, work_item)
