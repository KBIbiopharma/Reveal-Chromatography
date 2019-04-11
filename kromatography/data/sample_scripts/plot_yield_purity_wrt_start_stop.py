"""
Reveal script to build contour plots of purity and yield as a function of start
and stop collect for a loaded experiment.
"""
# Script inputs ---------------------------------------------------------------

EXP_NAME = "<YOUR EXPERIMENT NAME HERE>"

# Target values to scan (will be linearly spaced between LOW and HIGH)
# (unit is % if type='Percent Peak Max', and AU/cm if type='Fixed Absorbance'):
START_COLLECT_SCAN_LOW = 10
START_COLLECT_SCAN_HIGH = 50
START_COLLECT_SCAN_NUM_VALUES = 9

STOP_COLLECT_SCAN_LOW = 10
STOP_COLLECT_SCAN_HIGH = 50
STOP_COLLECT_SCAN_NUM_VALUES = 9

# Imports ---------------------------------------------------------------------

from numpy import arange, array, linspace, meshgrid
import matplotlib.pyplot as plt
from matplotlib import cm
from itertools import product

from kromatography.compute.experiment_performance_parameters import \
    calculate_experiment_performance_data


# Supporting functions --------------------------------------------------------

def scan_start_stop_criteria(exp, start_value_range, stop_value_range):
    """ Scan start/stop criteria and compute yield and purities as 2D arrays.
    """
    product_comps = exp.product.product_components
    yields = []
    purity_map = {comp.name: [] for comp in product_comps}

    for start, stop in product(start_value_range, stop_value_range):
        exp.method.collection_criteria.start_collection_target = start
        exp.method.collection_criteria.stop_collection_target = stop

        perf_data = calculate_experiment_performance_data(exp)
        step_yield = perf_data.step_yield
        purities = perf_data.pool.product_component_purities
        yields.append(step_yield.tolist())
        for comp, purity in zip(product_comps, purities):
            purity_map[comp.name].append(purity)

    starts, stops = meshgrid(start_value_range, stop_value_range)
    starts, stops = starts.T, stops.T
    shape = (len(start_value_range), len(stop_value_range))
    yields = array(yields).reshape(shape)
    for key, data in purity_map.items():
        purity_map[key] = array(data).reshape(shape)

    return starts, stops, yields, purity_map


def plot_yield_purity_as_heatmaps(method, start_vals, stop_vals, yields,
                                  purity_map, ticks_downsampling=1):
    """ Create a heatmap of the computed yields, and purities displayed against
    the start and stop values
    """
    start_type = method.collection_criteria.start_collection_type
    stop_type = method.collection_criteria.stop_collection_type
    if start_type == "Fixed Absorbance":
        start_unit = "AU/cm"
    elif start_type == "Percent Peak Maximum":
        start_unit = "%"
    else:
        raise ValueError("Unsupported start collection type.")

    if stop_type == "Fixed Absorbance":
        stop_unit = "AU/cm"
    elif stop_type == "Percent Peak Maximum":
        stop_unit = "%"
    else:
        raise ValueError("Unsupported start collection type.")

    colormap = cm.cool

    plt.imshow(yields, cmap=colormap)
    plt.colorbar()
    plt.title("Yield in %")
    plt.xlabel("Stop collect in {}".format(stop_unit))
    plt.ylabel("Start collect in {}".format(start_unit))

    stop_ticks = stop_vals[::ticks_downsampling]
    stop_ticks_text = ["{:.2f}".format(val) for val in stop_ticks]
    start_ticks = start_vals[::ticks_downsampling]
    start_ticks_text = ["{:.2f}".format(val) for val in start_ticks]
    stop_ticks_position = arange(len(stop_vals))[::ticks_downsampling]
    start_ticks_position = arange(len(start_vals))[::ticks_downsampling]
    plt.xticks(stop_ticks_position, stop_ticks_text)
    plt.yticks(start_ticks_position, start_ticks_text)

    for key, data in purity_map.items():
        plt.figure()
        plt.imshow(data, cmap=colormap)
        plt.colorbar()
        plt.title("Purity for {} in %".format(key))
        plt.xlabel("Stop collect in {}".format(stop_unit))
        plt.ylabel("Start collect in {}".format(start_unit))

        plt.xticks(stop_ticks_position, stop_ticks_text)
        plt.yticks(start_ticks_position, start_ticks_text)

    plt.show()


# Start of script -------------------------------------------------------------

# Collect experiment
study = task.project.study

run_1_exp = study.search_experiment_by_name(EXP_NAME)

# Plot performances for a grid of configurations
start_values = linspace(START_COLLECT_SCAN_LOW, START_COLLECT_SCAN_HIGH,
                        START_COLLECT_SCAN_NUM_VALUES)
stop_values = linspace(STOP_COLLECT_SCAN_LOW, STOP_COLLECT_SCAN_HIGH,
                       STOP_COLLECT_SCAN_NUM_VALUES)
data = scan_start_stop_criteria(run_1_exp, start_values, stop_values)
starts, stops, yields, purity_map = data
method = run_1_exp.method
plot_yield_purity_as_heatmaps(method, start_values, stop_values, yields,
                              purity_map, ticks_downsampling=2)

# End of script ---------------------------------------------------------------
