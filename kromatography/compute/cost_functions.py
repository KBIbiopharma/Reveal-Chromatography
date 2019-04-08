""" Default cost function for optimizing parameters of a simulation to match an
experiment or a set of experiment **taken in the SAME conditions**.
"""
import logging
from numpy import all, array, float64, isnan, nan, nansum, newaxis
import pandas as pd

from scimath.units.api import convert_str
from traits.api import Array, Bool, Float, HasStrictTraits, Instance, List, \
    on_trait_change, Str

from kromatography.model.api import Experiment, Simulation
from kromatography.compute.cost_function_calcs import calc_peak_timing, \
    calc_trailing_slope

logger = logging.getLogger(__name__)

SIM_COL_NAME = "Simulation"

# Default cost function weights
DEFAULT_PEAK_TIME_WEIGHT = 10.
DEFAULT_PEAK_HEIGHT_WEIGHT = 5.
DEFAULT_PEAK_SLOPE_WEIGHT = 0.5

# Shape of the costs
COST_ELEMENT_AXIS = 0
EXP_AXIS = 1
PROD_COMP_AXIS = 2


class CostFunction(HasStrictTraits):
    def __call__(self):
        raise NotImplementedError


class CostFunction0(CostFunction):
    """ Default cost "function" for optimizing a simulation against a
    (set of) experiment(s).

    The cost is defined by a linear combination of the peak location, peak
    height and peak shape (trailing slope). To use this class, create an
    instance, optionally specify the target experiments and weights. Then call
    it like a function, providing the list of simulation to compute the cost
    for. The target experiments and weights can also be provided at call time.

    Note: The list of experiments provided will be used in the following way:
    all metrics will be collected for all these experiments, but these metrics
    will be AVERAGED, in effect treating these experiments as 1. To compute the
    distance between multiple sets of simulations/experiments, this function
    must be called multiple times.

    Example
    -------
    Assuming that `exp` is an :class:`Experiment` and s1 and s2 are
    :class:`Simulation` instances::

        >>> weights = np.array([1, 2, 3])
        >>> func = CostFunction0(target_experiments=[exp],
        ...                      weights=weights)
        >>> func([s1, s2])
                                       Product_1
        Simulation Name
        Sim 0_Constant Binding Group  123.252989
        Sim 0_Constant Binding Group  123.252989
    """
    #: Allowed to use UV continuous data to compute cost? Useful for pure
    #: protein and no fraction data. Ignored if fraction data is present.
    use_uv_for_cost = Bool(False)

    #: Relative importance of peak_time, peak_height and peak_slope respect.
    weights = Array(dtype="float64")

    #: Output computed costs
    cost_data = Instance(pd.DataFrame)

    # Individual weights (ignored if weights array provided) ------------------

    #: Weight (relative importance) of the peak time location
    peak_time_weight = Float(DEFAULT_PEAK_TIME_WEIGHT)

    #: Weight (relative importance) of the height of the peak
    peak_height_weight = Float(DEFAULT_PEAK_HEIGHT_WEIGHT)

    #: Weight (relative importance) of the peak's back slope
    peak_slope_weight = Float(DEFAULT_PEAK_SLOPE_WEIGHT)

    # Parameters that can be pass at call time --------------------------------

    #: List of experiments to *combine* to compute the distance of a simulation
    target_experiments = List(Instance(Experiment))

    #: Component whose peak we are trying to fit
    target_components = List(Str)

    # Additional cost computation parameters ----------------------------------

    peak_slope_low_trigger_fraction = Float(0.2)

    peak_slope_high_trigger_fraction = Float(0.8)

    peak_height_max_cost = Float(30)

    peak_slope_max_cost = Float(20)

    # Cached data to allow recomputation for in-memory objects ----------------

    #: Metrics/data for the current target experiments
    cached_exp_data = Array

    #: Metrics/data for the current target simulations
    cached_sim_data = Array

    #: List of the currently analyzed simulations
    cached_simulations = List(Simulation)

    def __call__(self, simulation_list, target_exps=None, weights=None):
        """ Collect data and compute costs for the provided simulations.

        Parameters
        ----------
        simulation_list : list(Simulation)
            List of simulations to compute the distance to experiment for.

        target_exps : list(Experiment)
            List of experiments to compute the distance to.

        weights : array [OPTIONAL]
            Array of weights to overwrite the defaults if needed.

        Returns
        -------
        DataFrame containing the cost for each simulation and each product
        component.
        """
        if target_exps is not None:
            if isinstance(target_exps, Experiment):
                self.target_experiments = [target_exps]
            else:
                self.target_experiments = target_exps

        self.cached_exp_data = self.collect_experiment_targets()
        self.cached_simulations = simulation_list
        self.cached_sim_data = self.collect_sim_data(simulation_list)
        return self.compute_costs(weights=weights)

    def collect_experiment_targets(self):
        """ Collect target metrics for each experiments, and each component.

        FIXME: for now, the targets the costs will be computed with is the
        average of targets for all experiments.
        """
        return self.collect_metrics(self.target_experiments,
                                    self.get_expt_data)

    def collect_sim_data(self, simulation_list):
        """ Collect simulation metrics to compute costs from.
        """
        return self.collect_metrics(simulation_list, self.get_sim_data)

    def collect_metrics(self, base_experiments, data_collector):
        """ Collect metrics for a list of simulations or experiments.
        """
        peak_times = []
        peak_heights = []
        trailing_slopes = []

        for exp in base_experiments:
            results = exp.output

            exp_peak_times = []
            exp_peak_heights = []
            exp_trailing_slopes = []
            for component in self.target_components:
                if not results:
                    peak_time = nan
                    peak_height = nan
                    trailing_slope = nan
                else:
                    x_data, y_data = data_collector(results, component)
                    peak_time = calc_peak_timing(x_data, y_data)
                    peak_height = y_data.max()
                    trailing_slope = calc_trailing_slope(
                        x_data, y_data,
                        self.peak_slope_low_trigger_fraction,
                        self.peak_slope_high_trigger_fraction
                    )

                exp_peak_heights.append(peak_height)
                exp_peak_times.append(peak_time)
                exp_trailing_slopes.append(trailing_slope)

            peak_times.append(exp_peak_times)
            peak_heights.append(exp_peak_heights)
            trailing_slopes.append(exp_trailing_slopes)

        return array([peak_times, peak_heights, trailing_slopes])

    def compute_costs(self, weights=None):
        """ Compute the costs for each simulation and each component compared
        to the average target value across all experiments.

        Parameters
        ----------
        observed_data : Array
            Array of the metrics for all the components and all the
            simulations.

        targets : list(Experiment)
            List of experiments to compare the simulations to.

        simulation_names : List(str)
            List of simulation names used to populate the index of the returned
            dataframe.

        weights : 1D-array (optional)
            Array of weights, one for each of the elements of a cost.

        Returns
        -------
        DataFrame containing the cost for each simulation and each product
        component.
        """
        if weights is None:
            weights = self.weights
        else:
            self.weights = array(weights, dtype=float64)

        # Normalize the weights
        weights = weights / weights.sum()

        observed_data = self.cached_sim_data
        targets = self.cached_exp_data

        # Structure of the errors intermediate array:
        num_params, num_sim, num_comp = observed_data.shape

        if all(isnan(observed_data)):
            msg = "No data found in provided simulations"
            logger.exception(msg)
            raise ValueError(msg)

        # Average across all experiments and repeat data by the number sims to
        # compare each of the sims to the average experiment
        targets = targets.mean(axis=EXP_AXIS)
        targets = targets[:, newaxis, :].repeat(num_sim, axis=EXP_AXIS)
        # Duplicate weights across all simulations and all components:
        weights = weights[:, newaxis, newaxis]
        weights = weights.repeat(num_sim, axis=EXP_AXIS)
        weights = weights.repeat(num_comp, axis=PROD_COMP_AXIS)

        # Cost = \Sum weight * relative_error**2
        # FIXME: dividing by the observed values because the targets can be 0.
        # TODO: investigate why trailing slope can be 0...
        errors = abs((observed_data - targets)/targets)
        # Scale the costs by factor 100 now that normal values are normalized:
        costs = 100 * nansum(errors * weights, axis=COST_ELEMENT_AXIS)
        self.package_costs(costs)
        return self.cost_data

    def package_costs(self, costs):
        """ Package the 2D array of costs into a dataframe with labels.

        The index is the list of simulations. the columns are the target
        components for which the costs are computed.
        """
        sim_names = [sim.name for sim in self.cached_simulations]
        costs_df = pd.DataFrame(costs, index=sim_names,
                                columns=list(self.target_components))
        costs_df.index.name = SIM_COL_NAME
        self.cost_data = costs_df

    def get_expt_data(self, results, component):
        """ Extract x and y data for provided experiment and component name.
        """
        try:
            data = results.fraction_data[component]
        except KeyError:
            if self.use_uv_for_cost:
                from kromatography.utils.string_definitions import UV_DATA_KEY
                data = results.continuous_data[UV_DATA_KEY]
            else:
                raise

        return data.x_data, data.y_data

    def get_sim_data(self, results, component):
        """ Extract x and y data for provided experiment and component name.
        """
        # FIXME: Remove this and make sims use the same component names...
        component += "_Sim"
        xy_data = results.continuous_data[component]
        factor = convert_str(1, xy_data.x_metadata['units'], "min")
        x_data = xy_data.x_data * factor
        y_data = xy_data.y_data
        return x_data, y_data

    # Traits listeners --------------------------------------------------------

    @on_trait_change('peak_height_weight, peak_slope_weight, peak_time_weight')
    def rebuild_weights(self):
        self.weights = array([self.peak_time_weight, self.peak_height_weight,
                              self.peak_slope_weight], dtype=float64)

    # Traits initialization methods -------------------------------------------

    def _weights_default(self):
        return array([self.peak_time_weight, self.peak_height_weight,
                      self.peak_slope_weight], dtype=float64)

    def _target_components_default(self):
        exp = self.target_experiments[0]
        all_comps = exp.product.product_component_names
        return all_comps


ALL_COST_FUNCTIONS = {"Position/height/Back-Slope": CostFunction0}
