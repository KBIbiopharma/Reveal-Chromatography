""" Classes and utilities to create a SimulationGroup around a center point
simulation.
"""
from __future__ import division

import logging
from itertools import chain, product
from numpy import random

from scimath.units.api import UnitScalar

from kromatography.utils.app_utils import get_preferences
from kromatography.model.simulation_group import SingleParamSimulationDiff
from kromatography.model.parameter_scan_description import \
    ParameterScanDescription
from kromatography.model.random_parameter_scan_description import \
    RandomParameterScanDescription
from kromatography.model.simulation_group import SIM_GROUP_GRID_TYPE, \
    SIM_GROUP_MC_TYPE, SimulationGroup
from kromatography.model.lazy_simulation import LazyLoadingSimulation

logger = logging.getLogger(__name__)

DEFAULT_MC_GROUP = "New MC group"

DISTRIBUTION_MAP = {"Gaussian": random.normal,
                    "Uniform": random.uniform}


# API functions ---------------------------------------------------------------


def param_scans_to_sim_group(group_name, parameter_scans, center_sim,
                             lazy_loading=False, max_size=None,
                             group_type=SIM_GROUP_GRID_TYPE, group_size=-1,
                             auto_delete_run_sims=False):
    """ Returns simulation grid from a list of regular parameter scans.

    Parameters
    ----------
    group_name : str
        Target group name.

    parameter_scans : list(ParameterScanDescription)
        List of parameter scan descriptions.

    center_sim : Simulation
        Center point simulation from which to create all simulations in the
        future group.

    group_type : str [OPTIONAL]
        Type of the future group(s) to be created. Should be one of the values
        allowed for the :attr:`simulation_group.SimulationGroup.type`
        attribute. Set to a regular grid by default.

    lazy_loading : bool (default: False)
        Save memory by making the output group of the lazy loading kind.

    max_size : None or int [OPTIONAL]
        Max size of the group(s) created. If a non-zero value is specified, a
        list of simulation group is returned, each with a number of simulation
        diffs smaller or equal to max_size.

    group_size : int [OPTIONAL]
        Size of the resulting group, used only if of Monte-Carlo type. Size is
        computed from parameter scan descriptions for the grid type.

    auto_delete_run_sims : bool [OPTIONAL, default=False]
        Delete CADET files and in memory simulations once they run?

    Returns
    -------
    SimulationGroup or list(SimulationGroup)
        SimulationGroup created from the list of parameter scans the group
        should explore. If a max_size is provided, returns a list of
        SimulationGroup instances collectively scanning the entire parameter
        space described by parameter_scans, each with  0 < size <= max_size.
    """
    # Override the number of threads per run from preferences in case it has
    # changed. Do it on the center sim to avoid having to do it on each
    # simulation of the group:
    prefs = get_preferences()
    target_nthreads = prefs.solver_preferences.cadet_num_threads

    if lazy_loading and not isinstance(center_sim, LazyLoadingSimulation):
        center_sim = LazyLoadingSimulation.from_simulation(center_sim)
        center_sim.solver.nthreads = target_nthreads
    else:
        # if the nthreads will be overridden, make a copy to avoid modifying
        # the source simulation
        if center_sim.solver.nthreads != target_nthreads:
            center_sim = center_sim.copy()
            center_sim.solver.nthreads = target_nthreads

    if group_type == SIM_GROUP_GRID_TYPE:
        simulation_diffs = sim_diffs_from_grid_parameter_scans(parameter_scans)
    elif group_type == SIM_GROUP_MC_TYPE:
        simulation_diffs = sim_diffs_from_random_parameter_scans(
            parameter_scans, group_size
        )
    else:
        msg = "Unsupported group type: {}".format(group_type)
        logger.exception(msg)
        raise ValueError(msg)

    return build_group_or_groups(group_name, center_sim, simulation_diffs,
                                 max_size, group_type=group_type,
                                 auto_delete_run_sims=auto_delete_run_sims)


# Scripting API functions -----------------------------------------------------


def build_random_simulation_group(center_sim, param_names, group_size=200,
                                  dist_types="uniform", dist_desc=None,
                                  lazy_loading=False, max_block_size=None,
                                  group_name=DEFAULT_MC_GROUP,
                                  adtl_params=None):
    """ Build a simulation group around a center point scanning a list of
    parameters randomly. Useful for scripting tools.

    Parameters
    ----------
    center_sim : Simulation
        Simulation around which to build the grid.

    param_names : List
        List of parameters to scan in the grid.

    group_size : int [OPTIONAL, default=200]
        Number of simulations to generate to explore the space.

    dist_types : str or list of str [OPTIONAL, default="uniform"]
        Type(s) of sampling distributions for each parameter scanned. Supported
        values are "uniform", "normal".

    dist_desc : str or list of str
        Parameters of the sampling distributions for each parameter scanned, in
        the order of the constructor of the chosen distribution. That is the
        low (inclusive) and high (EXclusive) if "uniform" is chosen, and mean
        and standard deviation if "normal" is chosen.

    lazy_loading : bool
        Whether to force the center simulation to be a lazy loading simulation,
        to conserve RAM.

    max_block_size : int
        Maximum group size for the resulting group. If the needed group is
        larger, a list of groups will be created and returned.

    group_name : str
        Name of the resulting group.

    adtl_params : dict
        Map between parameters and adjustment parameters that must be changed
        at the same time.

    Returns
    -------
    SimulationGroup or list(SimulationGroup)
        SimulationGroup created from the list of parameter scans the group
        should explore. If a max_size is provided, returns a list of
        SimulationGroup instances collectively scanning the entire parameter
        space described by parameter_scans, each with  0 < size <= max_size.
    """
    if not param_names or not group_size:
        return

    if lazy_loading and not isinstance(center_sim, LazyLoadingSimulation):
        center_sim = LazyLoadingSimulation.from_simulation(center_sim)

    if isinstance(dist_types, str):
        dist_types = [dist_types] * len(param_names)

    assert len(dist_types) == len(dist_desc)

    param_scans = []
    for param, dist_type, desc in zip(param_names, dist_types, dist_desc):
        param_scan = RandomParameterScanDescription(
            name=param, distribution=dist_type, dist_param1=desc[0],
            dist_param2=desc[1], target_simulation=center_sim
        )
        param_scans.append(param_scan)

    sim_diff_list = sim_diffs_from_random_parameter_scans(
        param_scans, group_size, adtl_params=adtl_params
    )
    return build_group_or_groups(group_name, center_sim, sim_diff_list,
                                 max_block_size, group_type=SIM_GROUP_MC_TYPE)


def build_simulation_grid(sim, param_names, num_values=20, val_ranges=0.25,
                          lazy_loading=True):
    """ Build a grid around a center point scanning a list of parameters over a
    range. Useful for scripting tools.

    The resulting grid is built with linear spacing.

    Parameters
    ----------
    sim : Simulation
        Simulation around which to build the grid.

    param_names : List
        List of parameters to scan in the grid.

    num_values : int [OPTIONAL, default=20]
        Number of values to scan, *in each dimension*.

    val_ranges : float or list [OPTIONAL, default=0.25]
        If float, the range to scan is relative to the center value. By
        default, that range is 25%. If a list is specified, it must be the same
        length as the number of parameters to scan. A list of floats applies
        potentially different relative ranges for each parameter. A list of
        tuples must specify, for each parameter scanned, the low and high
        values to define the range.

    lazy_loading : bool
        Leave all simulation data/results on disk? Otherwise, the data is
        brought in memory.
    """
    parameter_scans = []
    center_values = []
    if isinstance(val_ranges, float):
        val_ranges = [val_ranges] * len(param_names)

    assert len(val_ranges) == len(param_names)

    for i, (name, val_range) in enumerate(zip(param_names, val_ranges)):
        cp_val = eval("sim.{}".format(name), {}, {"sim": sim})
        cp_val = float(cp_val)
        if isinstance(val_range, tuple):
            low, high = val_range
        elif isinstance(val_range, float):
            low = cp_val - val_range * cp_val
            high = cp_val + val_range * cp_val
        else:
            msg = "Unsupported type for element {} of val_ranges: {}"
            msg = msg.format(i, type(val_range))
            logger.exception(msg)
            raise ValueError(msg)

        p = ParameterScanDescription(name=name, low=low, high=high,
                                     num_values=num_values,
                                     target_simulation=sim)
        parameter_scans.append(p)
        center_values.append(cp_val)

    if len(param_names) == 2:
        group_name = "Scan {} and {}".format(*param_names)
    elif len(param_names) == 1:
        group_name = "Scan {}".format(param_names[0])
    else:
        msg = "Dimension of the param_names argument not supported. Should " \
              "be 1 or 2, but got {}".format(len(param_names))
        logger.exception(msg)
        raise ValueError(msg)

    grid = param_scans_to_sim_group(group_name, parameter_scans, sim,
                                    group_type=SIM_GROUP_GRID_TYPE,
                                    lazy_loading=lazy_loading)
    return grid


# Supporting functions --------------------------------------------------------


def build_group_or_groups(group_name, center_sim, simulation_diffs, max_size,
                          group_type=SIM_GROUP_GRID_TYPE,
                          auto_delete_run_sims=False):
    """ Build a group or a list of groups from simulation diffs based on the
    group size limit.


    Parameters
    ----------
    group_name

    center_sim: Simulation
        Simulation from which to build the group.

    simulation_diffs : list
        List of simulation differences to build the group's simulation from.

    max_size : int
        Max size of the future simulation group. If the resulting group will be
        bigger, a list of groups is returned rather than 1 group. Then, each
        group has a size less or equal to max_size.

    group_type : str [OPTIONAL, default="Multi-Param Grid"]
        Type of simulation group to build. Must be "Multi-Param Grid" or
        "Monte-Carlo Exploration".

    auto_delete_run_sims : bool [OPTIONAL, default=False]
        Delete CADET files and in memory simulations once they run?

    Returns
    -------
    SimulationGroup or list(SimulationGroup)
        SimulationGroup created from the list of parameter scans the group
        should explore. If a max_size is provided, returns a list of
        SimulationGroup instances collectively scanning the entire parameter
        space described by parameter_scans, each with  0 < size <= max_size.
    """
    group_traits = dict(center_point_simulation=center_sim, type=group_type,
                        auto_delete_run_sims=auto_delete_run_sims)
    if not max_size:
        group = SimulationGroup(
            name=group_name,
            simulation_diffs=simulation_diffs,
            **group_traits
        )
        return group
    else:
        # Split the simulation diffs into blocks of size at or below max_size
        groups = []
        # Compute the number of groups to split all diffs into:
        factor, mod = divmod(len(simulation_diffs), max_size)
        num_group = factor
        if mod:
            num_group += 1
        for i in range(num_group):
            block_sim_diffs = simulation_diffs[i*max_size:(i+1)*max_size]
            block_name = "Block_{}_".format(i) + group_name
            group = SimulationGroup(
                name=block_name,
                simulation_diffs=block_sim_diffs,
                **group_traits
            )
            groups.append(group)
        return groups


def sim_diffs_from_grid_parameter_scans(parameter_scans):
    # Docstring below...
    if len(parameter_scans) == 0:
        return []

    all_dim_diffs = []
    for scan in parameter_scans:
        if isinstance(scan, ParameterScanDescription) and \
                not scan.parallel_parameters:
            # In this dimension, only 1 parameter that changes at a time:
            scan = (scan,)
        else:
            # Convert to the tuple form if parallel parameters stored in the
            # parallel_parameters attribute:
            # Transform p1.parallel_parameters = [p2, p3]
            # into (p1, p2, p3)
            if isinstance(scan, ParameterScanDescription):
                scan = tuple([scan] + scan.parallel_parameters)

            # make sure parameter scans for a given dimension have the same
            # length
            for scan_i in scan[1:]:
                if scan_i.num_values != scan[0].num_values:
                    msg = "For parameters to be coupled, they must have the " \
                          "same number of values but {} has {} values and {} "\
                          " has {} values."
                    msg = msg.format(scan_i.name, scan_i.num_values,
                                     scan[0].name, scan[0].num_values)
                    logger.exception(msg)
                    raise ValueError(msg)

        # Generate a tuple of SimDiffs for this dimension
        dim_diffs = zip(*[param_desc.to_sim_diffs()
                          for param_desc in scan])
        all_dim_diffs.append(dim_diffs)

    # compute all difference combinations:
    simulation_diffs = list(product(*all_dim_diffs))
    # Flatten the results so that each SimDiff is a tuple of
    # SingleParamSimDiff, and not a tuple of tuples:
    simulation_diffs = [list(chain(*x)) for x in simulation_diffs]

    return simulation_diffs


sim_diffs_from_grid_parameter_scans.__doc__ = \
    """ Transform a list of ParameterScanDescription into a list of all
    possible SimulationDiffs to scan all combinations of parameter values.

    Parameters
    ----------
    parameter_scans : list
        List of ParameterScanDescriptions, each defining a different dimension
        being scanned by the future group. What is returned is all combinations
        of parameter values.

    Returns
    -------
    list
        List of tuples of SimulationDiff objects to build a SimulationGroup
        from.

    Notes
    -----
    Instead of 1 ParameterScanDescription per element in parameter_scans, it is
    possible to have a N-tuple of ParameterScanDescription. In that case, it is
    treated as the need for N parameters to be changed simultaneously. For
    example, this can be needed when scanning a proportion of a component, and
    needing to adjust another one every time to keep the total at 100%.

    Examples
    --------
    >>> parameters = [
        ParameterScanDescription(
            name="method.method_steps[2].flow_rate",
            low=50, high=100, num_values=2
        ),
        ParameterScanDescription(
            name="method.collection_criteria.start_collection_target",
            low=30, high=60, num_values=2
        ),
    ]
    >>> sim_diffs_from_grid_parameter_scans(parameters)
    [(SingleParamSimulationDiff(extended_attr='method.method_steps[2].flow_rate', val=50.0),
      SingleParamSimulationDiff(extended_attr='method.collection_criteria.start_collection_target', val=30.0)),
     (SingleParamSimulationDiff(extended_attr='method.method_steps[2].flow_rate', val=50.0),
      SingleParamSimulationDiff(extended_attr='method.collection_criteria.start_collection_target', val=60.0)),
     (SingleParamSimulationDiff(extended_attr='method.method_steps[2].flow_rate', val=100.0),
      SingleParamSimulationDiff(extended_attr='method.collection_criteria.start_collection_target', val=30.0)),
     (SingleParamSimulationDiff(extended_attr='method.method_steps[2].flow_rate', val=100.0),
      SingleParamSimulationDiff(extended_attr='method.collection_criteria.start_collection_target', val=60.0))]
    """  # noqa


def sim_diffs_from_random_parameter_scans(parameter_scans, group_size,
                                          adtl_params=None):
    """ Transform all RandomParameterScanDescription into a list of Simulation
    diffs.

    Parameters
    ----------
    parameter_scans : list
        List of RandomParameterScanDescription describing which parameters to
        scan and following which random distribution.

    group_size : int
        Number of random values to generate. Corresponds to the future size of
        the group.

    adtl_params : dict
        Map between scanned parameter names and a list of additional parameters
        that must be modified in the same simulation. If that's the case, the
        values must be lists of 2-tuples, containing the attribute path for the
        additional parameter that must change in sync and a callable which
        receives the random value of the source parameter and returns the value
        of the additional parameter.

        This advanced feature can be needed when scanning a proportion of a
        component, and needing to adjust another one every time to keep the
        total at 100%.

    Examples
    --------
    This will create a 100 size simulation group scanning uniformly the elution
    flow rate and the start collect::

    >>> parameters = [
        RandomParameterScanDescription(
            name="method.method_steps[2].flow_rate",
            distribution="uniform",
            dist_param1=50, dist_param2=100
        ),
        RandomParameterScanDescription(
            name="method.collection_criteria.start_collection_target",
            distribution="uniform",
            dist_param1=30, dist_param2=50
        ),
    ]

    >>> sim_diffs_from_random_parameter_scans(parameters, 100)
    [(SingleParamSimulationDiff...]
    """
    if adtl_params is None:
        adtl_params = {p.name: [] for p in parameter_scans}
    else:
        for p in parameter_scans:
            if p.name not in adtl_params:
                adtl_params[p.name] = []

    if len(parameter_scans) == 0:
        simulation_diffs = []
    else:
        # Generate the arrays of random values for each parameter
        all_param_values = {}
        for param in parameter_scans:
            func = DISTRIBUTION_MAP.get(param.distribution, None)
            if func is None:
                func = getattr(random, param.distribution)

            param_values = func(
                param.dist_param1, param.dist_param2, *param.additional_params,
                size=group_size
            )
            all_param_values[param] = param_values

        # Generate the simulation diffs from the random values
        simulation_diffs = []
        # FIXME: Inefficient! GET RID OF THIS FOR LOOP or cythonize it!
        for diff_num in range(group_size):
            sim_diff = []
            for param in parameter_scans:
                value = all_param_values[param][diff_num]
                if isinstance(param.center_value, UnitScalar):
                    units = param.center_value.units
                    value = UnitScalar(value, units=units)

                diff = SingleParamSimulationDiff(param.name, value)
                sim_diff.append(diff)
                for additional_param_desc in adtl_params[param.name]:
                    adtl_param_name, evaluator = additional_param_desc
                    diff = SingleParamSimulationDiff(adtl_param_name,
                                                     evaluator(value))
                    sim_diff.append(diff)

            simulation_diffs.append(tuple(sim_diff))

    return simulation_diffs


def build_5_point_groups_from_param_desc(cp_sim, param_list,
                                         param_labels=None):
    """ Build 5-point simulation groups from a list of parameters to study
    their impact on performances. Parameter descriptions specify their
    operational and characterization ranges.

    Parameters
    ----------
    cp_sim : Simulation
        Center point simulation around which to scan and compare to.

    param_list : dict
        Dictionary mapping parameter paths to scan to a tuple describing how to
        scan it. That tuple must be of length 4, containing respectively the
        low operating value, high operating value, low characterization value
        and high characterization value. All values must be in the unit the
        center point simulation has that parameter in, if applicable. Note that
        both keys and values can be replaced with tuples of paths and tuples of
        4-value tuples when multiple parameters must be scanned together.

    param_labels : dict [OPTIONAL]
        Map between a parameter path and a nice string representation for it.
        It will be used as the grid's name.

    Returns
    -------
    dict
        Map between the parameter path to explore (the first one in each
        dimension) and the corresponding simulation group to run.
    """
    from kromatography.plotting.mpl_param_impact_plot import PARAM_LABELS

    if param_labels is None:
        param_labels = PARAM_LABELS

    groups = {}
    for coupled_params, coupled_param_values in param_list.items():
        if isinstance(coupled_params, basestring):
            coupled_params = [coupled_params]
            coupled_param_values = [coupled_param_values]
        else:
            # Convert to list to be able to modify it:
            coupled_param_values = list(coupled_param_values)

        for i in range(len(coupled_params)):
            param_name = coupled_params[i]
            values = coupled_param_values[i]
            print("Exploring {} impact".format(param_name))
            if len(values) != 4:
                msg = "Format of param_list argument not supported: it should"\
                      " contain the following values: low_or, high_or, low_cr"\
                      ", high_cr."
                logger.exception(msg)
                raise ValueError(msg)

            # Replace values with unitted values if needed:
            cp_val = eval("sim.{}".format(param_name), {}, {"sim": cp_sim})
            if isinstance(cp_val, UnitScalar):
                coupled_param_values[i] = [UnitScalar(p, units=cp_val.units)
                                           for p in values]
                values = coupled_param_values[i]

            # Reorder to be low_cr, low_or, center, high_or, high_cr since
            # it is the plotting function default:
            coupled_param_values[i] = [values[2], values[0], values[1],
                                       values[3]]
            coupled_param_values[i].insert(2, cp_val)

        # Build all sim diffs for each parameter in the dimension
        diffs = [[SingleParamSimulationDiff(param, val) for val in vals]
                 for param, vals in zip(coupled_params, coupled_param_values)]
        # Regroup the coupled parameter diffs together:
        diffs = zip(*diffs)

        dimension_name = param_labels.get(coupled_params[0], coupled_params[0])
        group = SimulationGroup(
            name="Explore {}".format(dimension_name),
            center_point_simulation=cp_sim, simulation_diffs=diffs
        )
        groups[coupled_params[0]] = group

    return groups
