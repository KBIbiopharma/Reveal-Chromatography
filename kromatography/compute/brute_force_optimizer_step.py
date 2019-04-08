""" Driver class and supporting utilities to build optimal simulations
given a (set of) experiments, using the brute force approach of minimizing 1 or
more simulation grids.
"""
from __future__ import division, print_function

import re
from collections import defaultdict
import logging
import pandas as pd
import numpy as np

from traits.api import Bool, Callable, Constant, Dict, Enum, Instance, Int, \
    List, on_trait_change, Property, Str
from scimath.units.api import UnitScalar

from app_common.encore.job_manager import JobManager

from ..model.simulation_group import SimulationGroup
from ..model.factories.simulation_group import param_scans_to_sim_group
from ..model.parameter_scan_description import ParameterScanDescription
from ..utils.app_utils import get_preferences
from .experiment_optimizer_step import ALL_COST_COL_NAME, \
    ExperimentOptimizerStep
from .cost_functions import ALL_COST_FUNCTIONS, SIM_COL_NAME

logger = logging.getLogger(__name__)

OPTIMIZER_STEP_TYPE = "Brute-force optimizer step"


class BruteForceOptimizerStep(ExperimentOptimizerStep):
    """ Optimize a set of simulation parameters to model the provided
    experiment using the grid search (brute force) approach.

    If sim_group_max_size is 0, the step creates 1 simulation grid around a
    simulation built to model each target experiment. if sim_group_max_size is
    a positive integer, all simulations for a target experiments are split into
    groups of size less or equal to sim_group_max_size.

    When a simulation grid is fully run, the cost of each simulation to the
    corresponding target experiment is computed using the cost function
    attribute. The cost data from each simulation grid is stored in the
    group_cost_data dict and combined into the step's cost_data once the
    simulation names are stripped.
    """
    # General step traits -----------------------------------------------------

    #: Type of the optimizer step
    optimizer_step_type = Constant(OPTIMIZER_STEP_TYPE)

    #: List of parameter objects to scan
    parameter_list = List(ParameterScanDescription)

    #: List of parameter names to scan
    scanned_param_names = Property(List(Str), depends_on="parameter_list[]")

    # SimulationGroup related traits ------------------------------------------

    #: List of simulation groups, scanning desired parameters, 1 per target exp
    # Built from start_point_simulation and scanned_params if not provided.
    simulation_groups = List(Instance(SimulationGroup))

    #: Cost function to minimize, one per simulation group
    group_cost_functions = Dict(Str, Callable)

    #: Maximum size for each of the simulation groups in the step
    # if the step needs a larger grid, it will be split into SimGroups of size
    # less or equal to this
    sim_group_max_size = Int

    #: Number of the next simulation group to run
    _next_group_to_run = Int(0)

    #: Local storage of the job_manager to run subsequent groups
    _job_manager = Instance(JobManager)

    #: Make the run call blocking?
    _wait_on_run = Bool

    # Run related traits ------------------------------------------------------

    # Total number of simulations involved in the optimization step
    size = Property(Int, depends_on="simulation_groups[]")

    #: Number of simulations already run
    size_run = Property(Int, depends_on="simulation_groups.size_run")

    #: Percentage of the optimizer that has already run
    percent_run = Property(Str, depends_on="size_run")

    # Output related traits ---------------------------------------------------

    #: Aggregation method to combine costs for all components & all experiments
    cost_agg_func = Enum("sum", "mean")

    #: Dict mapping each simulation group to its cost data.
    _group_cost_data = Dict

    #: Dict mapping each component to a list of the best simulations
    optimal_simulation_for_comp = Dict

    # Run related methods -----------------------------------------------------

    def run(self, job_manager, wait=False):
        """ Run optimization step by running all simulation groups it contains.
        """
        # Initialize run parameters
        super(BruteForceOptimizerStep, self).run(job_manager, wait=wait)
        if not self.simulation_groups:
            self.initialize_sim_group()

        first_group = self.simulation_groups[0]
        runner = first_group.run(job_manager, wait=wait)

        self._job_manager = job_manager
        self._next_group_to_run = 1
        self._wait_on_run = wait

        return runner

    def wait(self):
        """ Wait for currently known simulation groups to finish running.
        """
        for group in self.simulation_groups:
            msg = "Waiting for {} to finish...".format(group.name)
            logger.debug(msg)
            group.wait()

    def initialize_sim_group(self):
        """ Initialize simulation groups with one based on self attribute.

        Depending on the group_max_size, there may be multiple simulation
        groups to target a given experiment.
        """
        for exp, start_point_sim in zip(self.target_experiments,
                                        self.starting_point_simulations):
            name = "Grid {}_{}".format(exp.name, self.name)
            groups = param_scans_to_sim_group(
                name, self.parameter_list, start_point_sim,
                max_size=self.sim_group_max_size
            )
            self.simulation_groups.extend(groups)

    # Cost related methods ----------------------------------------------------

    def recompute_costs_for_weights(self, new_weights):
        """ Assume new weights for all cost functions.

        Also recompute costs for all groups if they have already been computed.
        """
        if not self.has_run:
            self.cost_func_kw["weights"] = new_weights
            return

        # Otherwise, recompute all costs data (using cached metrics stored in
        # cost functions:
        self.invalidate_group_cost_data()
        for group in self.simulation_groups:
            # Rebuild the simulations so that we can recover parameter values
            # for the cost data dataframe:
            if not group.simulations:
                group.initialize_simulations(use_output_cache=True)

            group_name = group.name
            cost_func = self.group_cost_functions[group_name]
            cost_func.weights = new_weights
            cost_data = cost_func.compute_costs()
            # Don't aggregate yet, to avoid triggering listeners until all
            # cost_data recomputed:
            self.update_cost_data_dict(group, cost_data, skip_aggregate=True)

        # Now we are ready to compute the step's cost_data:
        self.aggregate_cost_data()

    def compute_costs(self, sim_group, cost_function=None):
        """ Compute the costs of one of the SimulationGroups of the step.

        Also cache the cost_function for each sim_group, so that costs can be
        recomputed if weights are changed.

        Parameters
        ----------
        sim_group : SimulationGroup
            Group for which to compute costs.

        cost_function : Callable [OPTIONAL]
            Target cost function to use to compute costs. Optional: if a
            cost_function_type has been provided at step creation, and this is
            None, a cost_function will be created.
        """
        if cost_function is None:
            klass = ALL_COST_FUNCTIONS[self.cost_function_type]
            cost_function = klass(**self.cost_func_kw)

        target_exp = sim_group.center_point_simulation.source_experiment
        cost_data = cost_function(sim_group.simulations,
                                  target_exps=target_exp)
        self.group_cost_functions[sim_group.name] = cost_function
        self.update_cost_data_dict(sim_group, cost_data)

    def update_cost_data_dict(self, group, cost_data, skip_aggregate=False):
        """ Collect all cost_function cost data for all sim groups.

        Also aggregates all into the step's cost_data if the step has finished
        running. The step's cost data will aggregate data from all simulation
        groups, sum/average it over all components, and display the scanned
        parameters values along side with the aggregate cost.
        """
        if cost_data is None:
            return

        # Copy to avoid modifying the cost function object which has a hold on
        # the cost_data
        cost_data = cost_data.copy()
        simulations = group.simulations

        # Aggregate the cost function data
        df_agg_method = getattr(cost_data, self.cost_agg_func)
        cost_data[ALL_COST_COL_NAME] = df_agg_method(axis=1)

        # Add the values of the scanned parameters
        self.append_param_values(cost_data, simulations)

        # Collect the group's cost data with the rest of the data targeting the
        # same experiment if any:
        exp_name = group.center_point_simulation.source_experiment.name
        if exp_name in self._group_cost_data:
            existing = self._group_cost_data[exp_name]
            self._group_cost_data[exp_name] = pd.concat([existing, cost_data])
        else:
            self._group_cost_data[exp_name] = cost_data

        if self.has_run and not skip_aggregate:
            self.aggregate_cost_data()

    def invalidate_group_cost_data(self):
        """ Past cost_data are invalid. Delete them.
        """
        self._group_cost_data = {}

    def aggregate_cost_data(self):
        """ Aggregate cost data over all target experiment.

        The step's cost data will aggregate data from all simulation groups,
        sum/average it over all components, and display the scanned parameters
        values along side with the aggregate cost.
        """
        # Remove the column name from the final cost_data since there may be
        # more than 1 simulation for a given parameter setup, one per target
        # experiment:
        cost_data_list = [data.drop(SIM_COL_NAME, axis=1)
                          for data in self._group_cost_data.values()]
        average_cost_data = sum(cost_data_list)
        if self.cost_agg_func == "mean":
            average_cost_data /= len(self.target_experiments)

        self.cost_data = average_cost_data

    def append_param_values(self, costs_df, simulations):
        """ Evaluate parameters for provided sims and reset as cost DF index.
        """
        for param_name in self.scanned_param_names:
            expr = "sim.{}".format(param_name)
            costs_df[param_name] = [eval(expr, {"sim": sim})
                                    for sim in simulations]
            first_val = costs_df[param_name][0]
            if isinstance(first_val, UnitScalar):
                costs_df[param_name] = costs_df[param_name].apply(float)
            elif is_squeezable(first_val):
                # FIXME: WHEN DOES THIS HAPPEN?
                costs_df[param_name] = costs_df[param_name].apply(float)
            elif is_repeating_array(first_val):
                # This can happen when a parameter is a slice of an array:
                # replace with the first value if all the same because we can't
                # index with an array (unhashable).
                costs_df[param_name] = costs_df[param_name].apply(
                    lambda x: x[0]
                )

        costs_df.reset_index(inplace=True)
        costs_df.set_index(self.scanned_param_names, inplace=True)

    # Optimal simulation methods ----------------------------------------------

    def update_optimal_simulation_for_comp(self):
        """ Extract the best simulation for each product component.
        """
        best_simulations = defaultdict(list)
        for comp in self.target_components:
            for group_cost_data in self._group_cost_data.values():
                data = group_cost_data[comp]
                try:
                    idx = data.argmin(axis=0)
                    sim_name = group_cost_data.loc[idx, SIM_COL_NAME]
                    sim = self._get_sim_from_name(sim_name)
                    best_simulations[comp].append(sim)
                except Exception as e:
                    msg = "Failing to find the simulation with minimal cost " \
                          "for component {}. Data was {}. (Exception was {})"
                    logger.error(msg.format(comp, data, e))

        self.optimal_simulation_for_comp = best_simulations

    def get_optimal_sims(self, exp_name, num_sims):
        """ Collect optimal num_sims simulations matching specific experiment.
        """
        if len(self.cost_data) == 0:
            return []

        # Make sure we are not trying to extract more optimal simulations that
        # the total number of available simulations (for a given experiment)

        sorted_data = self.cost_data.sort_values(by=ALL_COST_COL_NAME)
        optim_sim_idx = sorted_data.index[:num_sims]
        # This assumes that self.cost_data and elements of
        # self._group_cost_data are indexed on the same columns:
        group_data = self._group_cost_data[exp_name]
        sim_names = group_data.loc[optim_sim_idx, SIM_COL_NAME].tolist()
        return [self._get_sim_from_name(name) for name in sim_names]

    # Private interface -------------------------------------------------------

    def _get_sim_from_name(self, sim_name):
        """ Find a simulation ran in the step in the simulation sim groups.

        Raises
        ------
        ValueError
            If the simulation isn't found.
        """
        pattern = "Sim (\d+)_(.+)"
        match = re.match(pattern, sim_name)
        target_sim_num, target_group_name = match.groups()
        group = self._get_group_from_name(target_group_name)
        try:
            sim = group.get_simulation(int(target_sim_num))
            if sim.name != sim_name:
                msg = "Logical error: the simulation's name isn't what was " \
                      "expected!"
                logger.exception(msg)
                raise ValueError(msg)

            return sim
        except (IndexError, AssertionError) as e:
            msg = "Simulation with name {} not found in step's simulation " \
                  "groups. Error was {}."
            msg = msg.format(sim_name, e)
            logger.error(msg)
            raise ValueError(msg)

    def _get_group_from_name(self, group_name):
        """ Return the simulation group with provided name.
        """
        for group in self.simulation_groups:
            if group.name.startswith(group_name):
                return group

        msg = "SimulationGroup with name {} not found in step's groups. " \
              "Known names are {}"
        known_group_names = [group.name for group in self.simulation_groups]
        msg = msg.format(group_name, known_group_names)
        logger.error(msg)
        raise ValueError(msg)

    def _get_step_has_run(self):
        if not self.simulation_groups:
            return False
        return all([group.has_run for group in self.simulation_groups])

    # Traits listeners --------------------------------------------------------

    @on_trait_change("simulation_groups:has_run")
    def optimize_costs(self, sim_group, attr_name, group_has_run):
        self.has_run = self._get_step_has_run()
        if group_has_run:
            msg = "Group {} has finished running: updating costs."
            msg = msg.format(sim_group.name)
            logger.info(msg)

            self.compute_costs(sim_group)
            if self.has_run:
                self.update_optimal_simulation_for_comp()
            else:
                self._run_next_sim_group()

            # Save memory by throwing away simulations: they can be rebuilt
            # from the simulation diffs.
            sim_group.release_simulation_list()
            self.data_updated = True

    def _run_next_sim_group(self):
        """ A simGroup has finished running: run the next one.
        """
        next_group = self.simulation_groups[self._next_group_to_run]
        msg = "Now submitting {} to run...".format(next_group.name)
        logger.debug(msg)
        next_group.run(self._job_manager, wait=self._wait_on_run)
        self._next_group_to_run += 1

    # Traits property getters -------------------------------------------------

    def _get_size(self):
        return sum([group.size for group in self.simulation_groups])

    def _get_size_run(self):
        return sum([group.size_run for group in self.simulation_groups])

    def _get_percent_run(self):
        if self.size:
            percent_run = self.size_run / self.size * 100.
        else:
            percent_run = np.nan

        return "{:.2f} %".format(percent_run)

    def _get_scanned_param_names(self):
        step_params = []
        for param in self.parameter_list:
            p_name = param.name
            parallel_params = hasattr(param, "parallel_parameters") and \
                len(param.parallel_parameters) > 0
            if parallel_params:
                step_params.extend([p.name for p in param.parallel_parameters])

            step_params.append(p_name)

        return step_params

    # Traits initialization methods -------------------------------------------

    def _cost_data_default(self):
        cols = self.target_components + [ALL_COST_COL_NAME]
        data = {name: [] for name in cols}
        return pd.DataFrame(data, index=[])

    def _sim_group_max_size_default(self):
        preferences = get_preferences()
        return preferences.optimizer_preferences.optimizer_step_chunk_size


def is_repeating_array(val):
    return isinstance(val, np.ndarray) and not isinstance(val, UnitScalar) \
        and np.all(val == val[0])


def is_squeezable(val):
    list_like = (list, np.ndarray)
    return isinstance(val, list_like) and not isinstance(val, UnitScalar) \
        and len(val) == 1
