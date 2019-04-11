import numpy as np
import logging

from scimath.units.api import convert_str, UnitArray, UnitScalar
from scimath.units.dimensionless import fraction, percent

from kromatography.utils.chromatography_units import convert_units
from kromatography.model.solution_with_product import SolutionWithProduct
from kromatography.model.chromatography_results import PerformanceData
from kromatography.utils.units_utils import time_to_volume
from kromatography.utils.simulation_utils import calculate_step_start_times

logger = logging.getLogger(__name__)

MISSING_UNITTED_VALUE = UnitScalar(np.nan, units="")


def calculate_performance_data(sim, continuous_data):
    """ Calculates the performance results based on continuous_data.

    Parameters
    ----------
    sim : Simulation
        Simulation object we are computing the performance for. Used to collect
        information about the product it models and the collection criteria.

    continuous_data : dict
        Dictionary of continuous data that was simulated by CADET.

    Returns
    -------
    PerformanceData or None
        Returns None if no collection criteria was specified in the
        simulation's method.
    """
    # Use the section_times from the continuous data to set the time to start
    # looking for the start collection criteria
    col_criteria = sim.method.collection_criteria
    if col_criteria is None:
        msg = "Skipping performance data for sim {} since no collection " \
              "criteria was set.".format(sim.name)
        logger.debug(msg)

        no_performance_data = PerformanceData(
            name=sim.name,
            # Parameters to be displayed in the perf param pane:
            start_collect_time=MISSING_UNITTED_VALUE,
            stop_collect_time=MISSING_UNITTED_VALUE,
            pool_volume=MISSING_UNITTED_VALUE,
            step_yield=MISSING_UNITTED_VALUE,
            pool_concentration=MISSING_UNITTED_VALUE,
        )

        return no_performance_data

    sim_data = continuous_data['Total_Sim']
    pooling_step_num = sim.method.collection_step_number
    start_times = calculate_step_start_times(sim)
    pooling_start = start_times[pooling_step_num]
    pooling_stop = start_times[pooling_step_num+1]

    start_stop_collect_data = calculate_start_stop_collect(
        sim_data, col_criteria, step_start=pooling_start,
        step_stop=pooling_stop
    )

    start_collect_time, start_collect_idx, stop_collect_time, stop_collect_idx\
        = start_stop_collect_data

    # The flow rate of collecting the pool is the flow rate during the elution
    # or pooling step in general (that is the step creating the pool):
    pooling_step = sim.method.method_steps[pooling_step_num]
    yield_flow_rate = pooling_step.flow_rate
    pool_volume = calculate_pool_volume(start_collect_time, stop_collect_time,
                                        yield_flow_rate, sim.column)

    product_component_concentrations = calculate_component_concentrations(
        sim.product, continuous_data, start_collect_idx, stop_collect_idx
    )

    pool_concentration = calculate_pool_concentration(
        product_component_concentrations
    )

    load_step = sim.method.load
    step_yield = calculate_step_yield(pool_concentration, pool_volume,
                                      load_step)

    # This is a partial solution object because the pH, conductivity, and
    # chemical concentrations are not computed by CADET.
    pool = SolutionWithProduct(
        name='{}_Pool'.format(sim.name),
        source="Simulation",
        lot_id="unknown",
        solution_type="Pool",
        product=sim.product,
        product_concentration=pool_concentration,
        product_component_concentrations=product_component_concentrations
    )

    performance_data = PerformanceData(
        name=sim.name,
        pool=pool,
        # Parameters to be displayed in the perf param pane:
        start_collect_time=start_collect_time,
        stop_collect_time=stop_collect_time,
        pool_volume=pool_volume,
        step_yield=step_yield,
        pool_concentration=pool_concentration,
    )

    return performance_data


def calculate_start_stop_collect(absorb_data, col_criteria, step_start,
                                 step_stop):
    """ Find the times and array indices corresponding to start & stop collect.

    Parameters
    ----------
    absorb_data : XYData
        Data container for the time and measurement values for absorbance data.

    col_criteria : CollectionCriteria
        Pool collection criteria describing when to start and stop collecting.

    step_start : UnitScalar
        Start time of the step creating the pool, in minutes.

    step_stop : UnitScalar
        Stop time of the step creating the pool, in minutes.

    Returns
    -------
    UnitScalar, int, UnitScalar, int
        Time to start collecting at and corresponding index in the arrays and
        time to stop collecting at and corresponding index.
    """
    x_units = absorb_data.x_metadata["units"]
    factor = convert_str(1., x_units, "min")
    x_data = absorb_data.x_data * factor
    in_step_mask = (x_data >= float(step_start)) & (x_data <= float(step_stop))
    y_data = absorb_data.y_data

    start_collect_time, start_idx = _calculate_start_collect(
        x_data, y_data, in_step_mask, col_criteria
    )

    stop_collect_time, stop_idx = _calculate_stop_collect(
        x_data, y_data, in_step_mask, col_criteria
    )

    return start_collect_time, start_idx, stop_collect_time, stop_idx


def _calculate_start_collect(x_data, y_data, in_step_mask, col_criteria):
    """ Compute the time and index at which to start collecting.
    """
    start_collect_value = col_criteria.start_collection_target
    start_collect_type = col_criteria.start_collection_type
    start_collect_while = col_criteria.start_collection_while

    step_y_data = y_data[in_step_mask]

    if start_collect_type == "Fixed Absorbance":
        threshold = start_collect_value
    elif start_collect_type == "Percent Peak Maximum":
        peak_max = step_y_data.max()
        threshold = start_collect_value * peak_max / 100.
    else:
        msg = ("Stop collect type {} not supported. Choose 'Fixed Absorbance'"
               " or 'Percent Peak Maximum'.".format(start_collect_type))
        logger.exception(msg)
        raise ValueError(msg)

    if start_collect_while == "Ascending":
        threshold_mask = y_data > threshold
        collect_mask = threshold_mask & in_step_mask
    else:
        # Compute the max during pooling and find the (global) index of it
        peak_max_idx = step_y_data.argmax() + np.where(in_step_mask)[0][0]
        threshold_mask = y_data < threshold
        after_peak_mask = x_data > x_data[peak_max_idx]
        collect_mask = threshold_mask & in_step_mask & after_peak_mask

    collect_indexes = np.where(collect_mask)[0]
    if len(collect_indexes) == 0:
        msg = "No collection data found, at the intersection between step " \
              "time and satisfying the collection criteria."
        logger.warning(msg)
        start_collect_time = UnitScalar(np.nan, units="min")
        start_idx = 0
    else:
        start_idx = collect_indexes[0]
        start_collect_time = UnitScalar(x_data[start_idx], units="min")

    return start_collect_time, start_idx


def _calculate_stop_collect(x_data, y_data, in_step_mask, col_criteria):
    """ Compute time at which to stop collecting, using continuous data.
    """
    stop_collect_value = col_criteria.stop_collection_target
    stop_collect_type = col_criteria.stop_collection_type
    stop_collect_while = col_criteria.stop_collection_while

    step_y_data = y_data[in_step_mask]
    peak_max_idx = step_y_data.argmax() + np.where(in_step_mask)[0][0]

    if stop_collect_type == "Fixed Absorbance":
        threshold = stop_collect_value
    elif stop_collect_type == "Percent Peak Maximum":
        peak_max = step_y_data.max()
        threshold = stop_collect_value * peak_max / 100.
    else:
        msg = ("Stop collect type {} not supported. Choose 'Fixed Absorbance'"
               " or 'Percent Peak Maximum'.".format(stop_collect_type))
        logger.exception(msg)
        raise ValueError(msg)

    if stop_collect_while == "Descending":
        after_peak_mask = x_data > x_data[peak_max_idx]
        below_threshold = y_data < threshold
        collect_mask = in_step_mask & after_peak_mask & below_threshold
    else:
        above_threshold = y_data > threshold
        collect_mask = in_step_mask & above_threshold

    valid_idx = np.where(collect_mask)[0]
    if len(valid_idx) == 0:
        msg = "Stop collect threshold ({}) never reached after the max! " \
              "Revise stop criteria.".format(threshold)
        logger.warning(msg)
        stop_collect_time = UnitScalar(np.nan, units="min")
        stop_idx = 0
    else:
        stop_idx = valid_idx[0]
        stop_collect_time = UnitScalar(x_data[stop_idx], units="min")

    return stop_collect_time, stop_idx


def calculate_pool_volume(start_collect_time, stop_collect_time, flow_rate,
                          column):
    """ Calculates pool volume in CVs.
    """
    flow_time = stop_collect_time - start_collect_time
    pool_volume = time_to_volume(flow_time, flow_rate, column, to_unit="CV")
    return pool_volume


def calculate_pool_concentration(comp_concentrations):
    """Calculates total pool concentration in g/liter by summing individual
    component concentrations.
    """
    if not isinstance(comp_concentrations, UnitArray):
        msg = "The component concentrations are expected to be passed as a " \
              "UnitArray."
        logger.exception(msg)
        raise ValueError(msg)

    pool_concentration = UnitScalar(float(np.sum(comp_concentrations)),
                                    units=comp_concentrations.units)
    pool_concentration = convert_units(pool_concentration, tgt_unit="g/L")
    return pool_concentration


def calculate_step_yield(pool_concentration, pool_volume, load_step):
    """ Calculates protein yield, in percent of the mass of protein
    loaded (at load step).

    Parameters
    ----------
    pool_concentration : UnitScalar
        Concentration of the pool extracted.

    pool_volume : UnitScalar
        Volume of the pool.

    load_step : MethodStep
        Step describing the load of the protein.
    """
    # Make sure that both volumes are in the same unit
    load_mass = load_step.volume * load_step.solutions[0].product_concentration
    pool_mass = pool_concentration * pool_volume
    step_yield = pool_mass / load_mass
    if step_yield.units != fraction:
        msg = "Computation of step_yield: the formula doesn't provide a " \
              "fraction (step_yield={!r}). Check the units.".format(step_yield)
        logger.error(msg)
        return np.nan

    step_yield = convert_units(step_yield, tgt_unit=percent)
    return step_yield


def calculate_component_concentrations(product, comp_absorb_data,
                                       start_collect_idx, stop_collect_idx):
    """ Calculate the concentration of each component in the pool in g/L.

    The volume of a component is defined as the integral of its absorbance data
    between the start and the stop collect.
    """
    comp_concentrations = []
    for i, comp in enumerate(product.product_components):
        # Collect component attributes:
        comp_name = comp.name
        ext_coeff = comp.extinction_coefficient

        collect_idx = range(start_collect_idx, stop_collect_idx)
        absorb_data = comp_absorb_data[comp_name + '_Sim']
        x = absorb_data.x_data[collect_idx]
        y = absorb_data.y_data[collect_idx]

        comp_conc = np.trapz(y, x) / \
            (absorb_data.x_data[stop_collect_idx] -
             absorb_data.x_data[start_collect_idx]) / ext_coeff

        comp_concentrations.append(comp_conc)

    product_component_concentrations = UnitArray(comp_concentrations,
                                                 units='g/L')
    return product_component_concentrations


# Utilities -------------------------------------------------------------------


def _get_step_index(step_list, step_name):
    """ Returns the index of the step with name step_name in the provided list
    of steps.
    """
    for i, step in enumerate(step_list):
        if step.name == step_name:
            return i

    msg = "No step called {} in list {}".format(step_name, step_list)
    raise ValueError(msg)
