""" Brute force implementation of a binding model optimizer.
"""
import logging
import numpy as np

from traits.api import Bool, Constant, Enum, Instance, Int, List, \
    on_trait_change, Range

from kromatography.model.api import BindingModel
from kromatography.compute.constant_binding_model_optimizer_step import \
    ConstantBruteForceBindingModelOptimizerStep
from kromatography.compute.brute_force_binding_model_optimizer_step import \
    BruteForceBindingModelOptimizerStep
from kromatography.compute.brute_force_optimizer import BruteForceOptimizer
from kromatography.model.parameter_scan_description import \
    extract_short_name_from_param_scan, ParameterScanDescription
from kromatography.utils.string_definitions import MULTI_SIM_RUNNER_CREATED

logger = logging.getLogger(__name__)

# Default values for refining grid properties
DEFAULT_REFINING_GRID_SIZE_FACTOR = 10

DEFAULT_REFINING_GRID_NUM_VALUES = 5

BRUTE_FORCE_2STEP_OPTIMIZER_TYPE = "Self-refining cross-component SMA " \
                                   "optimizer"


class BruteForce2StepBindingModelOptimizer(BruteForceOptimizer):
    """ 2 step brute force (grid search based) optimizer to optimize binding
    model parameters.

    Optimization strategy contains 2 steps:
    1. Assume the same binding parameters for all simulations, and explore
    a wide grid of values, to try and find decent values for each
    component.
    2. Then scan a grid of values around these starting points for each
    component. Since there are interactions between peaks, the result
    depends on the order with which components are scanned. That leads to 2
    optimizer steps for a 1-component product and N+1 optimizer steps for an
    N-componment product.
    """
    # BruteForce2StepBindingModelOptimizer interface --------------------------

    #: Switch to allow/disallow the refinement steps after the constant scan
    do_refine = Bool(True)

    #: Spacing for step 1 and up (which refine component parameters)
    refining_step_spacing = Enum("Best", "Linear", "Log")

    #: Size of scanning grid for refining step
    refining_step_num_values = Int(DEFAULT_REFINING_GRID_NUM_VALUES)

    #: Control length of refined grid in % of previous grid's spacing size
    refining_factor = Range(value=DEFAULT_REFINING_GRID_SIZE_FACTOR, low=1,
                            high=100)

    #: Best binding model globally
    optimal_models = List(Instance(BindingModel))

    # ExperimentOptimizer interface -------------------------------------------

    #: Type of optimizer
    type = Constant(BRUTE_FORCE_2STEP_OPTIMIZER_TYPE)

    # BruteForce2StepBindingModelOptimizer methods ----------------------------

    def __init__(self, **traits):
        constant_step_traits = {}
        if "constant_step_parameter_list" in traits:
            # Collect step parameters
            constant_step_traits["parameter_list"] = \
                traits.pop("constant_step_parameter_list")

            if not constant_step_traits["parameter_list"]:
                msg = ("Unable to create a Brute-Force optimizer without "
                       "parameters to scan.")
                logger.exception(msg)
                raise ValueError(msg)

        # Skipping the immediate parent's __init__ since this replaces it.
        # Still need the grand parent, for the HasTraits hookups.
        super(BruteForceOptimizer, self).__init__(**traits)

        if not self.steps:
            # These step creations done during the __init__ instead of
            # _steps_default because the has_run property forces a request of
            # self.steps during __init__, because the target_experiments have
            # been assigned.
            self.create_steps(**constant_step_traits)

    def create_steps(self, **constant_step_traits):
        """ Create all optimization steps: constant scan and refining steps.
        """
        # First step uses the same binding parameters for all components
        step0 = ConstantBruteForceBindingModelOptimizerStep(
            name="{}: step 0".format(self.name),
            target_experiments=self.target_experiments,
            cost_function_type=self.cost_function_type,
            starting_point_simulations=self.starting_point_simulations,
            **constant_step_traits
        )
        step0.initialize_sim_group()
        self.steps.append(step0)

        if self.do_refine:
            for i, comp in enumerate(step0.component_names):
                # Make a refining step for each component, to refine that
                # component's binding parameter (build_parameter_list to
                # compute what scan will occur):
                step = BruteForceBindingModelOptimizerStep(
                    name="{}: step {}".format(self.name, i+1),
                    target_experiments=self.target_experiments,
                    cost_function_type=self.cost_function_type,
                )
                self.steps.append(step)

    def update_step(self, step_idx=1, from_step=0):
        """ Initialize a step's simulation group(s) from an already run step.
        """
        self.update_starting_point_simulations(step_idx, from_step=from_step)
        self.build_parameter_list(step_idx)
        step = self.steps[step_idx]
        step.initialize_sim_group()

    def update_starting_point_simulations(self, step_idx=1, from_step=0):
        """ Build the center point simulations from the optimal model for each
        component at the previous step.
        """
        prev_step = self.steps[from_step]
        step = self.steps[step_idx]

        # Create all starting points...
        cp_simulations = [sim.copy() for sim in
                          prev_step.starting_point_simulations]
        for cp_sim in cp_simulations:
            center_binding_model = cp_sim.binding_model

            #  ... and update from the best model for each component
            short_param_names = [extract_short_name_from_param_scan(param)
                                 for param in prev_step.parameter_list]
            for i, comp in enumerate(step.target_components):
                optim_model = prev_step.optimal_model_for_comp[comp]
                for attr in short_param_names:
                    getattr(center_binding_model, attr)[i+1] = \
                        getattr(optim_model, attr)[i+1]

        step.starting_point_simulations = cp_simulations

    def build_parameter_list(self, step_idx=1, from_step=0):
        """ Build the list of scanned parameters from the list of scanned
        parameters at the previous step. They should scan the binding model
        parameters for the ith product component.
        """
        prev_step = self.steps[from_step]
        step = self.steps[step_idx]
        comp_arr_idx = step_idx

        parameter_list = []
        for param in prev_step.parameter_list:
            short_name_param = extract_short_name_from_param_scan(param)
            low, high = self._compute_refined_param_range(param, comp_arr_idx,
                                                          prev_step)
            # Build new binding model param name
            name = "binding_model.{}[{}]".format(short_name_param,
                                                 comp_arr_idx)
            # Build new param spacing strategy
            if self.refining_step_spacing == "Best":
                if high / low < 1e2:
                    refining_step_spacing = "Linear"
                else:
                    refining_step_spacing = "Log"
            else:
                refining_step_spacing = self.refining_step_spacing

            # Build new param
            new_param = ParameterScanDescription(
                name=name, low=low, high=high,
                num_values=self.refining_step_num_values,
                spacing=refining_step_spacing
            )
            parameter_list.append(new_param)

        step.parameter_list = parameter_list

    # Traits listeners --------------------------------------------------------

    @on_trait_change('steps:data_updated')
    def setup_run_refining_steps(self):
        """ Update & run one of the refining steps once constant step has run.
        """
        if not self.steps[0].has_run:
            return

        for i in range(1, self.num_steps):
            if self.steps[i].status == MULTI_SIM_RUNNER_CREATED:
                self.update_step(step_idx=i, from_step=0)
                self.run_step(step_idx=i, wait=self._wait_on_step_run)
                return

    @on_trait_change('cost_data, num_optimal_simulations', post_init=True)
    def update_optimal_simulation_map(self, obj, attr_name, old, new):
        """ Collect best num_optimal_simulations simulations with lowest costs.
        """
        super_klass = super(BruteForce2StepBindingModelOptimizer, self)
        super_klass.update_optimal_simulation_map(obj, attr_name, old, new)

        # Collect optimal binding models from optimal simulations
        self.optimal_models[:] = [sim.binding_model
                                  for sim in self.optimal_simulations]

    # Traits property getters/setters -----------------------------------------

    def _get_size(self):
        step0 = self.steps[0]
        num_refining_steps = len(self.steps) - 1
        num_params = len(step0.parameter_list)
        refining_step_size = (self.refining_step_num_values**num_params *
                              num_refining_steps)
        return step0.size + refining_step_size

    # Private interface -------------------------------------------------------

    def _compute_refined_param_range(self, param, comp_arr_idx, prev_step):
        """ Build low and high ParamScan parameters for a step from previous
        step's grid using the values around the best value.
        """
        target_comp_name = prev_step.component_names[comp_arr_idx-1]
        short_name_param = extract_short_name_from_param_scan(param)
        best_model = prev_step.optimal_model_for_comp[target_comp_name]

        center_arr = getattr(best_model, short_name_param)
        center_val = center_arr[comp_arr_idx]
        scanned_vals = np.array(param.scanned_values)
        center_val_loc = np.where(np.abs(scanned_vals - center_val) < 1e-9)
        center_val_loc = center_val_loc[0][0]  # extract index from where
        before_loc = max(center_val_loc - 1, 0)
        before = scanned_vals[before_loc]
        after_loc = min(center_val_loc + 1, len(scanned_vals) - 1)
        after = scanned_vals[after_loc]

        edge_msg = ("The best value for {} ({}) was found close to the edge of"
                    " the initial step grid. Consider expanding the grid in "
                    "the future...")
        if before_loc == 0 or after_loc == len(scanned_vals) - 1:
            logger.warning(edge_msg.format(short_name_param, center_val))

        # Potentially asymetrical delta to respect log scans.
        if abs(after - center_val) > 1e-10:
            delta_plus = after - center_val
        else:
            # The best value is 'on' the grid edge. Use the distance to the
            # value before
            delta_plus = center_val - before

        if abs(center_val - before) > 1e-10:
            delta_minus = center_val - before
        else:
            # The best value is 'on' the grid edge. Use the distance to the
            # value after
            delta_minus = after - center_val

        low = center_val - delta_minus * self.refining_factor / 100.
        high = center_val + delta_plus * self.refining_factor / 100.
        return low, high
