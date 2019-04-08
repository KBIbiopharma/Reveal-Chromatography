""" Driver class and supporting utilities to build the optimal simulations
given an experiment and a transport model.
"""
import logging
import pandas as pd

from traits.api import Bool, Dict, Enum, Event, Instance, List, \
    on_trait_change, Str

from app_common.model_tools.data_element import DataElement

from kromatography.model.experiment import Experiment
from kromatography.model.simulation import Simulation
from kromatography.compute.cost_functions import ALL_COST_FUNCTIONS
from kromatography.utils.string_definitions import MULTI_SIM_RUNNER_CREATED, \
    MULTI_SIM_RUNNER_FINISHED, MULTI_SIM_RUNNER_RUNNING

logger = logging.getLogger(__name__)

ALL_COST_COL_NAME = "Cost (All selected comps)"

EXP_OPTIMIZER_STEP_TYPE = "Experiment optimizer step"


class ExperimentOptimizerStep(DataElement):
    """ Driver to build an optimal simulation to match (an) experiment(s).

    TODO: add the ability to do a smart run, and use initial results from
    simulation runs to trim the parameter space.
    """
    # General step traits -----------------------------------------------------

    #: Type of the optimizer step
    optimizer_step_type = EXP_OPTIMIZER_STEP_TYPE

    #: Target experiment to simultaneously minimize the distance to
    target_experiments = List(Instance(Experiment))

    #: List of all target component names we are trying to fit simulations to
    target_components = List(Str)

    #: Initial starting points for the optimizer, one for each target exp
    starting_point_simulations = List(Instance(Simulation))

    #: Type of cost function to minimize
    cost_function_type = Str("Position/height/Back-Slope")

    #: Allowed to use UV continuous data to compute cost? Useful for pure
    #: protein and no fraction data.
    use_uv_for_cost = Bool(False)

    #: Set when optimizer has run, before cost data is updated.
    # Not a property so that it can be reset to false when running again
    has_run = Bool

    #: Status of the optimizer as a string
    status = Enum([MULTI_SIM_RUNNER_CREATED, MULTI_SIM_RUNNER_RUNNING,
                   MULTI_SIM_RUNNER_FINISHED])

    #: Event emitted once output data has been aggregated once run is finished
    data_updated = Event

    #: Series mapping all simulations to their costs for each component
    cost_data = Instance(pd.DataFrame)

    #: Keyword arguments for the cost function creation
    cost_func_kw = Dict

    def __init__(self, **traits):
        # Input validation
        provided_1_exp = "target_experiments" in traits and \
                         isinstance(traits["target_experiments"], Experiment)
        if provided_1_exp:
            traits["target_experiments"] = [traits["target_experiments"]]

        # HasTraits
        super(ExperimentOptimizerStep, self).__init__(**traits)

    def run(self, job_manager, wait=False):
        """ Build and run a SimulationGroup around each center simulation.
        """
        self.has_run = False
        self.status = MULTI_SIM_RUNNER_RUNNING

    # Traits listeners --------------------------------------------------------

    def _use_uv_for_cost_changed(self, new):
        self.cost_func_kw['use_uv_for_cost'] = new

    @on_trait_change('target_experiments[]')
    def assert_all_experiments_valid(self):
        self.assert_all_exp_have_output()
        self.assert_all_exp_for_same_product()

    def _has_run_changed(self):
        if self.has_run:
            self.status = MULTI_SIM_RUNNER_FINISHED
        else:
            self.status = MULTI_SIM_RUNNER_CREATED

    # Validation related methods ----------------------------------------------

    def assert_all_exp_have_output(self):
        for exp in self.target_experiments:
            if exp.output is None:
                msg = ("Target experiments provided must have outputs, but {} "
                       "doesn't.".format(exp.name))
                logger.exception(msg)
                raise ValueError(msg)

    def assert_all_exp_for_same_product(self):
        for i, exp in enumerate(self.target_experiments[1:]):
            if not self._valid_product(exp.product):
                msg = ("Experiment {} doesn't have a the same product, as "
                       "experiment 0.".format({i+1}))
                logger.exception(msg)
                raise ValueError(msg)

    def _valid_product(self, prod):
        target_product = self.target_experiments[0].product
        comp_names = prod.product_component_names
        if target_product.product_component_names != comp_names:
            return False
        elif target_product.name != prod.name:
            return False

        return True

    # Traits initialization methods -------------------------------------------

    def _cost_func_kw_default(self):
        cost_func_kw = {"target_components": self.target_components,
                        "use_uv_for_cost": self.use_uv_for_cost}
        klass = ALL_COST_FUNCTIONS[self.cost_function_type]
        # Collect default values for cost weights:
        cost_function = klass()
        all_weights = ['peak_height_weight', 'peak_slope_weight',
                       'peak_time_weight']
        for weight in all_weights:
            cost_func_kw[weight] = getattr(cost_function, weight)
        return cost_func_kw

    def _target_components_default(self):
        exp = self.target_experiments[0]
        return exp.product.product_component_names
