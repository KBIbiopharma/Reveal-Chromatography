""" Class for brute force optimizers.
"""
from __future__ import division, print_function

import logging
import numpy as np

from traits.api import Bool, Constant, Event, Instance, Int, List, Property, \
    Str

from kromatography.compute.brute_force_optimizer_step import \
    BruteForceOptimizerStep
from kromatography.compute.experiment_optimizer import ExperimentOptimizer
from app_common.encore.job_manager import JobManager

GRID_BASED_OPTIMIZER_TYPE = "Grid-search Optimizer"

COMPLETION_PRECISION = 2

logger = logging.getLogger(__name__)


class BruteForceOptimizer(ExperimentOptimizer):
    """ An optimizer class stringing simulation grid based steps to find 1 or
    more optimal parameters to fit an experiment or a set of experiments.
    """
    #: Optimizer type
    type = Constant(GRID_BASED_OPTIMIZER_TYPE)

    #: Succession of steps to complete the optimization process
    steps = List(Instance(BruteForceOptimizerStep))

    # Run related attributes --------------------------------------------------

    #: Event to request the solver to execute the optimizer, listened to by app
    cadet_request = Event

    #: Number of simulations already run
    size_run = Property(Int, depends_on="steps.size_run")

    #: Percentage of the optimizer that has already run
    percent_run = Property(Str, depends_on="size_run")

    #: Should running be synchronous?
    _wait_on_step_run = Bool(False)

    #: Job manager to run to run subsequent steps if any
    _job_manager = Instance(JobManager)

    def __init__(self, **traits):
        param_list = traits.pop('parameter_list', [])
        super(BruteForceOptimizer, self).__init__(**traits)

        if not self.steps:
            # These step creations done during the __init__ instead of
            # _steps_default because the has_run property forces a request of
            # self.steps during __init__, because the target_experiments have
            # been assigned.
            self.create_steps(param_list)

    def create_steps(self, param_list):
        """ Create all optimization steps: constant scan and refining steps.
        """
        step = BruteForceOptimizerStep(
            name="step {}_{}".format(len(self.steps), self.name),
            target_experiments=self.target_experiments,
            cost_function_type=self.cost_function_type,
            target_components=self.target_components,
            starting_point_simulations=self.starting_point_simulations,
            parameter_list=param_list,
        )
        step.initialize_sim_group()
        self.steps.append(step)

    def run(self, job_manager, wait=False):
        """ Run of the optimizer: run first step and set run attributes.
        """
        super(BruteForceOptimizer, self).run(job_manager)
        self._wait_on_step_run = wait
        self._job_manager = job_manager

        runner = None
        if not self.steps[0].has_run:
            # Run the first step as a blocking call since the update requires
            # to know the outcome of the first step:
            runner = self.run_step(step_idx=0)

        if wait:
            self.wait()
        return runner

    def wait(self):
        """ Wait until all currently known optimization steps have finished
        running.
        """
        for step in self.steps:
            step.wait()

    def run_step(self, step_idx, wait=False):
        """ Run optimization steps with index step_idx.s
        """
        super(BruteForceOptimizer, self).run_step()
        step = self.steps[step_idx]
        runner = step.run(job_manager=self._job_manager, wait=wait)
        return runner

    def recompute_costs_for_weights(self, new_weights):
        """ Propagate a change in desired cost function weights to steps.
        """
        for step in self.steps:
            step.recompute_costs_for_weights(new_weights)

    # Property getters/setters ------------------------------------------------

    def _get_size_run(self):
        return sum([step.size_run for step in self.steps])

    def _get_percent_run(self):
        if self.size:
            percent_run = self.size_run / self.size * 100.
        elif self.has_run:
            # has_run is stored in project files, but size_run is lost:
            percent_run = 100.
        else:
            percent_run = np.nan

        pattern = "{:." + str(COMPLETION_PRECISION) + "f} %"
        return pattern.format(percent_run)
