""" Base class for binding model optimizers.
"""
import pandas as pd
import logging
import time

from traits.api import Bool, Dict, Enum, Float, Instance, Int, List, \
    on_trait_change, Property, Str

from app_common.model_tools.data_element import DataElement

from kromatography.model.simulation import Simulation
from kromatography.compute.experiment_optimizer_step import ALL_COST_COL_NAME,\
    ExperimentOptimizerStep
from kromatography.model.experiment import Experiment
from kromatography.utils.string_definitions import MULTI_SIM_RUNNER_CREATED, \
    MULTI_SIM_RUNNER_FINISHED, MULTI_SIM_RUNNER_RUNNING

OPTIMIZER_TYPE = "ExperimentOptimizer"

DEFAULT_NUM_OPTIMAL_SIMULATIONS = 3

logger = logging.getLogger(__name__)


class ExperimentOptimizer(DataElement):
    """ A base optimizer class stringing optimization steps to find
    the optimal simulations to fit an experiment or a set of experiments.
    """
    #: Optimizer name
    name = Str('New optimizer')

    #: Optimizer type
    type = OPTIMIZER_TYPE

    #: List of experiments to simultaneously minimize the distance to
    target_experiments = List(Instance(Experiment))

    #: List of experiment names to minimize the distance to
    target_experiment_names = Property(List(Str),
                                       depends_on="target_experiments")

    #: Target product components to compute the cost for
    target_components = List(Str)

    #: Initial starting points for the optimizer, one for each target exp
    starting_point_simulations = List(Instance(Simulation))

    #: Type of target cost function to minimize
    cost_function_type = Str("Position/height/Back-Slope")

    #: Allowed to use UV continuous data to compute cost? Useful for pure
    #: protein and no fraction data.
    use_uv_for_cost = Bool(False)

    # Run related traits ------------------------------------------------------

    #: Timestamp of starting to run
    run_start = Float

    #: Timestamp of starting to run
    run_stop = Float

    #: Succession of steps to complete the optimization process
    steps = List(Instance(ExperimentOptimizerStep))

    #: Number of steps
    num_steps = Property(Int, depends_on="steps[]")

    #: Number of simulations used during optimization
    size = Property(Int, depends_on="steps[]")

    #: Has all simulation groups of all optimizer steps run?
    has_run = Bool

    #: Status of the optimizer as a string
    status = Enum([MULTI_SIM_RUNNER_CREATED, MULTI_SIM_RUNNER_RUNNING,
                   MULTI_SIM_RUNNER_FINISHED])

    # Parameters scanned and not ----------------------------------------------

    #: Parameters that are optimized over
    scanned_param_names = Property(List(Str), depends_on="steps[]")

    # Outputs from optimizations ----------------------------------------------

    #: Number of models to collect as optimal models
    num_optimal_simulations = Int(DEFAULT_NUM_OPTIMAL_SIMULATIONS)

    #: Best simulations globally
    optimal_simulations = List(Instance(Simulation))

    #: Best simulations, grouped by target experiment
    optimal_simulation_map = Dict

    #: Collected averaged costs for each combination of the scanned parameters
    cost_data = Instance(pd.DataFrame)

    #: Ordered list of columns for the cost_data DF
    cost_data_cols = Property(List)

    # ExperimentOptimizer interface -------------------------------------------

    def run(self, job_manager, **kwargs):
        self.has_run = False
        self.status = MULTI_SIM_RUNNER_RUNNING
        self.run_start = time.time()

    def run_step(self, **kwargs):
        self.status = MULTI_SIM_RUNNER_RUNNING

    # Trait listeners ---------------------------------------------------------

    def _use_uv_for_cost_changed(self, new):
        for step in self.steps:
            step.use_uv_for_cost = new

    @on_trait_change('cost_data, num_optimal_simulations', post_init=True)
    def update_optimal_simulation_map(self, obj, attr_name, old, new):
        """ Collect best num_optimal_simulations simulations with lowest costs.
        """
        if len(self.cost_data) == 0:
            return

        # If there are enough optimal simulations available, truncate.
        # Not a new assignment to avoid tree editor loosing track of the object
        num_optim_sims_changed = attr_name == 'num_optimal_simulations'
        if num_optim_sims_changed and old > new:
            to_remove = old - new
            for exp_name in self.optimal_simulation_map:
                self.optimal_simulation_map[exp_name][-to_remove:] = []

        else:
            # Find the last run step
            # FIXME: We should replace this by a more solid way to identify the
            # step containing each of the optimal simulations when we support
            # multi-step optimizers.
            for step in self.steps[::-1]:
                if step.has_run:
                    last_run_step = step
                    break
            else:
                msg = "No step has run yet. No optimal simulation is to be " \
                      "found. Aborting."
                logger.info(msg)
                return

            for exp in self.target_experiments:
                sims = last_run_step.get_optimal_sims(
                    exp.name, self.num_optimal_simulations
                )
                self.optimal_simulation_map[exp.name] = sims

        self.update_optimal_simulations()

    def update_optimal_simulations(self):
        """ Interleave the best simulations for each target experiment.
        """
        num_optim_sims = self.num_optimal_simulations
        # If there are enough optimal simulations available, truncate.
        # Not a new assignment to avoid tree editor loosing track of the object
        current_num = len(self.optimal_simulations)
        if current_num > num_optim_sims:
            to_remove = current_num - num_optim_sims
            self.optimal_simulations[-to_remove:] = []
        else:
            self.optimal_simulations[:] = []
            num_optim_sims = len(self.optimal_simulation_map.values()[0])
            for i in range(num_optim_sims):
                for exp_name in self.optimal_simulation_map:
                    sim_i = self.optimal_simulation_map[exp_name][i]
                    self.optimal_simulations.append(sim_i)

    @on_trait_change("steps.cost_data")
    def rebuild_cost_data(self):
        all_cost_dfs = [self._filter_df_cols(step.cost_data)
                        for step in self.steps if step.has_run]
        if all_cost_dfs:
            # reset_index again to renumber when there are multiple DFs
            cost_data = pd.concat(all_cost_dfs)
            cost_data = cost_data.sort_values(by=ALL_COST_COL_NAME)
            # Sort columns, without assuming that all params are available in
            # the data from steps already run:
            param_cols = set(cost_data.columns) - {ALL_COST_COL_NAME}
            sorted_cols = sorted(list(param_cols)) + [ALL_COST_COL_NAME]
            self.cost_data = cost_data[sorted_cols].reset_index(drop=True)
        else:
            self.cost_data = self._build_empty_cost_df()

    @on_trait_change('steps:has_run')
    def update_has_run(self):
        self.has_run = all([step.has_run for step in self.steps])
        if self.has_run:
            self.status = MULTI_SIM_RUNNER_FINISHED
            self.run_stop = time.time()
            duration = (self.run_stop - self.run_start) / 60.
            msg = "[TIMING] Optimizer {} ran in {:.2f} min".format(self.name,
                                                                   duration)
            logger.debug(msg)

    # Traits initialization methods -------------------------------------------

    def _cost_data_default(self):
        return self._build_empty_cost_df()

    # Traits property getters/setters -----------------------------------------

    def _get_num_steps(self):
        return len(self.steps)

    def _get_size(self):
        return sum([step.size for step in self.steps])

    def _get_target_experiment_names(self):
        return [exp.name for exp in self.target_experiments]

    def _get_scanned_param_names(self):
        """ Collect the names of parameters being scanned in steps already set.
        """
        param_names = []
        for step in self.steps:
            param_names += step.scanned_param_names
        return sorted(param_names)

    def _get_cost_data_cols(self):
        """ Ordered list of columns the cost data DF is made with. """
        return self.scanned_param_names + [ALL_COST_COL_NAME]

    # Private interface -------------------------------------------------------

    def _build_empty_cost_df(self):
        """ Build an empty version of the future cost_data dataframe.

        It should contain a column for each of the parameters scanned (sorted
        by their name) and the cost column.
        """
        df = pd.DataFrame({col: [] for col in self.cost_data_cols}, index=[])
        # Sort inputs and add cost column last:
        df = df[self.cost_data_cols]
        return df

    def _filter_df_cols(self, step_cost_data):
        """ Reset the index to show the parameter values as regular cols and
        remove individual product component costs.
        """
        data = step_cost_data.reset_index()
        for col in data:
            if col not in self.cost_data_cols:
                data = data.drop(col, axis=1)
        return data

    def _optimal_simulation_map_default(self):
        return {exp.name: [] for exp in self.target_experiments}

    def _target_components_default(self):
        exp = self.target_experiments[0]
        all_comps = exp.product.product_component_names
        return all_comps
