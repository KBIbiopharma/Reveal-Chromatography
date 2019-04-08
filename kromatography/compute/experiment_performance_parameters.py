""" Functions to compute the performance parameters and data for experiments.
"""
from __future__ import print_function
from logging import getLogger
from numpy import array, diff, isnan, nan, ones, searchsorted, trapz, where
from pandas import Series

from scimath.units.api import convert, unit_parser, UnitArray, UnitScalar
from scimath.units.time import minute

from kromatography.compute.performance_parameters import \
    calculate_pool_concentration, calculate_pool_volume, \
    calculate_start_stop_collect, calculate_step_yield
from kromatography.model.api import SolutionWithProduct
from kromatography.model.performance_data import PerformanceData
from kromatography.utils.string_definitions import UV_DATA_KEY
from kromatography.utils.units_utils import is_volumetric_flow_rate, \
    is_linear_flow_rate, linear_flow_rate_to_volumetric, \
    volumetric_CV_flow_rate_to_volumetric_flow_rate
from kromatography.utils.chromatography_units import absorption_unit, \
    convert_units
from kromatography.utils.string_definitions import FRACTION_TOTAL_DATA_KEY

logger = getLogger(__name__)


def compute_strip_fraction(experiment):
    """ Estimate the fraction of product eluting at/after the strip step.

    This fraction is computed from the ratio of the loaded product (with
    specified load concentration and load volume) to the product eluting
    between the start of the load and start of the strip. This is computed by
    integrating the chromatogram before the strip, applying the extinction
    coefficient from the component with the highest fraction.

    This allows to detect potential experimental data discrepancies between:

        #. the chromatogram, and in particular, its shape in the Strip part,
        #. the product's extinction coefficient,
        #. the mass of product loaded, or in other word, the load
           concentration.

    Parameters
    ----------
    experiment : Experiment
        Experiment object we are computing the strip fraction for.

    Returns
    -------
    UnitScalar
        Percentage of the loaded product that is found to elute during the
        strip step. Value set to nan if unable to compute.
    """
    from .strip_fraction_calculator import StripFractionCalculator
    calculator = StripFractionCalculator(experim=experiment)
    return calculator.strip_mass_fraction


def compute_mass_from_abs_data(absorb_data, ext_coeff, experim, t_start=None,
                               t_stop=None, t_start_idx=None, t_stop_idx=None):
    """ Compute total mass of a product component between start and stop times.

    The total mass is computed by integrating the specified chromatogram,
    between t_start and t_stop and using the specified extinction coefficient
    and flow rate at each time.

    Parameters
    ----------
    absorb_data : XYData
        Data (fraction or continuous) to integrate to compute the contained
        mass.

    ext_coeff : UnitScalar
        Extinction coefficient to use to convert the absorbance to a product
        concentration.

    experim : Experiment
        Experiment from which to extract the method (and therefore flow rate)
        information and the system's path length.

    t_start : UnitScalar
        Time at which to start integrating, in minutes. Leave as None to use
        the t_start_idx to specify the time range to integrate.

    t_stop : UnitScalar
        Time at which to stop integrating, in minutes. Leave as None to use
        the t_stop_idx to specify the time range to integrate.

    t_start_idx : Int or None
        Index in the x_data to start integrating at (inclusive).

    t_stop_idx : Int or None
        Index in the x_data to stop integrating at (exclusive). Leave as None
        to go all the way to the end.

    Returns
    -------
    UnitScalar
        Product mass, in grams, estimated to elute between t_start and t_stop.
    """
    all_x_data = absorb_data.x_data
    all_y_data = absorb_data.y_data

    # Convert time inputs into minutes:
    data_time_unit = unit_parser.parse_unit(absorb_data.x_metadata["units"])
    all_x_data = convert(all_x_data, from_unit=data_time_unit, to_unit=minute)

    if t_start is not None and t_stop is not None:
        t_start = convert_units(t_start, tgt_unit=minute)
        t_stop = convert_units(t_stop, tgt_unit=minute)

        t_start_idx = searchsorted(all_x_data, t_start)
        t_stop_idx = searchsorted(all_x_data, t_stop)
        if t_start_idx == t_stop_idx:
            msg = "Unable to compute the integral of the provided because" \
                  "t_start too close to t_stop."
            logger.warning(msg)
            return UnitScalar(0., units="gram")

    collect_idx = slice(t_start_idx, t_stop_idx)
    times = all_x_data[collect_idx]
    absorbances = all_y_data[collect_idx]

    #: Extract the flow rate from the experiment method:
    flow_rates = build_flow_rate_array(times, experim, to_unit="liter/minute")
    missing_flow_rates = where(isnan(flow_rates))[0]
    if len(missing_flow_rates) > 0:
        msg = "The time range requested to integrate results goes beyond the "\
              "known method steps, and will need to be cropped by {} values." \
              " Cropped values are {}.".format(len(missing_flow_rates),
                                               missing_flow_rates)
        logger.warning(msg)
        t_stop_idx = missing_flow_rates[0]
        collect_idx = slice(t_start_idx, t_stop_idx)
        times = all_x_data[collect_idx]
        absorbances = all_y_data[collect_idx]
        flow_rates = flow_rates[collect_idx]

    # Turn absorbances into AU/cm
    path_length = convert_units(experim.system.abs_path_length, "cm")[()]
    data_absorb_unit = unit_parser.parse_unit(absorb_data.y_metadata["units"])
    absorbances_au = convert(absorbances, from_unit=data_absorb_unit,
                             to_unit=absorption_unit)
    # Compute masses in grams
    masses = (absorbances_au*array(flow_rates)) / (path_length*ext_coeff[()])
    total_mass = trapz(masses, times)
    return UnitScalar(total_mass, units="gram")


def build_flow_rate_array(times, experiment, to_unit="liter/minute"):
    """ Build array of flow rates in liter/min at each time of 'times' array.

    Parameters
    ----------
    times : numpy.array
        Array of chromatogram times at which to extract the flow rates.

    experiment : Experiment
        Experiment to extract the flow rates from.

    to_unit : str
        Unit of the output.

    Returns
    -------
    UnitArray
        Array of flow rates at the times of the times array.
    """
    method_steps = experiment.method.method_steps
    step_boundary_times = experiment.method_step_boundary_times

    flow_rates = ones(times.shape) * nan
    for i, step in enumerate(method_steps):
        step_start_time = step_boundary_times[i]
        step_stop_time = step_boundary_times[i+1]
        mask = (times >= step_start_time) & (times < step_stop_time)
        if is_linear_flow_rate(step.flow_rate):
            diam = experiment.column.column_type.diameter
            flow_rate = linear_flow_rate_to_volumetric(step.flow_rate, diam,
                                                       to_unit=to_unit)
        elif is_volumetric_flow_rate(step.flow_rate):
            flow_rate = convert(step.flow_rate, from_unit=step.flow_rate.units,
                                to_unit=unit_parser.parse_unit(to_unit))
        else:
            flow_rate = volumetric_CV_flow_rate_to_volumetric_flow_rate(
                step.flow_rate, experiment.column, to_unit=to_unit
            )

        flow_rates[mask] = float(flow_rate)

    return UnitArray(flow_rates, units=to_unit)


def get_most_contributing_component(experim, exclude=None):
    """ Returns the component with the largest fraction in the experiment data.
    """
    if exclude is None:
        exclude = set([])

    if experim is None or experim.product is None:
        return

    product = experim.product
    components = [comp for comp in product.product_components
                  if comp.name not in exclude]

    if len(components) == 1:
        return components[0]

    if experim.output is None or not experim.output.fraction_data:
        return

    comp_contributions = {}
    old_total_name = "fraction_Total"
    for comp_name, frac_data in experim.output.fraction_data.items():
        names_to_skip = {FRACTION_TOTAL_DATA_KEY, old_total_name} | exclude
        if comp_name not in names_to_skip:
            comp_contributions[comp_name] = frac_data.y_data.max()

    comp_contributions = Series(comp_contributions)
    most_contributing_comp_name = comp_contributions.sort_values().index[-1]
    return experim.product.get_component_with_name(most_contributing_comp_name)


def calculate_experiment_performance_data(exp):
    """ Calculates the performance data based on continuous_data.
    Performance data includes the start and stop times from the start and stop
    collection criteria, the pool's concentrations, volume and purities, and
    the yield. Used to build the output of a simulation once the solver has
    run.

    Parameters
    ----------
    exp : Experiment
        Experiment object we are computing the performance for. Used to collect
        information about the product it models and the collection criteria.

    Returns
    -------
    PerformanceData or None
        Returns None if no collection criteria was specified in the
        simulation's method.
    """
    # Use the section_times from the continuous data to set the time to start
    # looking for the start collection criteria
    col_criteria = exp.method.collection_criteria
    if col_criteria is None:
        msg = "Skipping performance data for exp {} since no collection " \
              "criteria was set.".format(exp.name)
        logger.debug(msg)
        return None

    continuous_data = exp.output.continuous_data
    exp_data = continuous_data[UV_DATA_KEY]
    pooling_step_num = exp.method.collection_step_number
    # Collect pooling boundaries from fraction data times:
    fraction_data = exp.output.fraction_data
    pooling_start = fraction_data[FRACTION_TOTAL_DATA_KEY].x_data.min()
    pooling_stop = fraction_data[FRACTION_TOTAL_DATA_KEY].x_data.max()

    start_stop_collect_data = calculate_start_stop_collect(
        exp_data, col_criteria, step_start=pooling_start,
        step_stop=pooling_stop
    )

    start_collect_time, start_collect_idx, stop_collect_time, stop_collect_idx\
        = start_stop_collect_data

    # The flow rate of collecting the pool is the flow rate during the elution
    # or pooling step in general (that is the step creating the pool):
    pooling_step = exp.method.method_steps[pooling_step_num]
    yield_flow_rate = pooling_step.flow_rate
    pool_volume = calculate_pool_volume(start_collect_time, stop_collect_time,
                                        yield_flow_rate, exp.column)

    product_component_concentrations = \
        calculate_exp_component_concentrations(
            exp, exp.output.fraction_data, pooling_step.flow_rate,
            pool_volume, start_collect_time, stop_collect_time
        )

    pool_concentration = calculate_pool_concentration(
        product_component_concentrations
    )

    load_step = exp.method.load
    step_yield = calculate_step_yield(pool_concentration, pool_volume,
                                      load_step)

    pool = SolutionWithProduct(
        name='{}_Pool'.format(exp.name),
        source="{} {}".format(exp.__class__.__name__, exp.name),
        lot_id="unknown",
        solution_type="Pool",
        product=exp.product,
        product_concentration=pool_concentration,
        product_component_concentrations=product_component_concentrations
    )

    performance_data = PerformanceData(
        name=exp.name,
        pool=pool,
        # Parameters to be displayed in the perf param pane:
        start_collect_time=start_collect_time,
        stop_collect_time=stop_collect_time,
        pool_volume=pool_volume,
        step_yield=step_yield,
        pool_concentration=pool_concentration,
    )

    return performance_data


def calculate_exp_component_concentrations(exp, fraction_data, flow_rate,
                                           pool_volume, start_collect,
                                           stop_collect):
    """ Calculate the concentration of each component in the pool in g/L from
    experimentally measured fraction data.
    The mass of a component in the pool is its fraction at various times, times
    the product concentration integrated over duration of the pooling process.
    The pool component concentration is the
    """
    from kromatography.utils.units_utils import is_volumetric_flow_rate, \
        linear_flow_rate_to_volumetric
    from kromatography.utils.chromatography_units import column_volumes, \
        convert_units
    from kromatography.utils.units_utils import unitted_list_to_array

    if is_volumetric_flow_rate(flow_rate):
        pooling_flow_rate = flow_rate
    else:
        d = exp.column.column_type.diameter
        pooling_flow_rate = linear_flow_rate_to_volumetric(
            flow_rate, diam=d, to_unit="liter/minute"
        )

    comp_concentrations = []

    for i, comp in enumerate(exp.product.product_components):
        # Collect component attributes:
        comp_name = comp.name
        comp_fraction_data = fraction_data[comp_name]
        avail_x = comp_fraction_data.x_data

        start_collect_idx = searchsorted(avail_x, start_collect)
        stop_collect_idx = searchsorted(avail_x, stop_collect)
        collect_idx = range(start_collect_idx, stop_collect_idx)

        ext_coeff = comp.extinction_coefficient.tolist()
        fraction_comp_conc = comp_fraction_data.y_data[collect_idx] / ext_coeff
        fraction_comp_conc = UnitArray(fraction_comp_conc, units='g/L')

        # Integration of these concentrations over time to get the total mass
        # of the component:
        if stop_collect_idx+1 > len(comp_fraction_data.x_data):
            msg = "Computing the total mass of component {} cannot complete " \
                  "because there are no fractions specified after the " \
                  "pooling step. Please add at least 1 fraction to your " \
                  "fractions for experiment {}."
            msg = msg.format(comp.name, exp.name)
            logger.exception(msg)
            raise ValueError(msg)

        collect_idx_times = range(start_collect_idx, stop_collect_idx+1)
        times = comp_fraction_data.x_data[collect_idx_times]
        time_units = comp_fraction_data.x_metadata["units"]
        delta_times = UnitArray(list(diff(times)), units=time_units)
        frac_comp_masses = fraction_comp_conc * delta_times * pooling_flow_rate
        frac_mass = float(frac_comp_masses.sum())
        comp_mass = UnitScalar(frac_mass, units=frac_comp_masses.units)

        if pool_volume.units == column_volumes:
            pool_volume = float(pool_volume) * exp.column.volume

        comp_conc = comp_mass / pool_volume
        comp_concentrations.append(convert_units(comp_conc, 'g/L'))

    # Read off the units from the fraction tab in the Excel spreadsheet!
    product_component_concentrations = \
        unitted_list_to_array(comp_concentrations)

    return product_component_concentrations
