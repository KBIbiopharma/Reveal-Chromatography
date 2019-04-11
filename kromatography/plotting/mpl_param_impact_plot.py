from matplotlib import pyplot as plt
from numpy import arange
import pandas as pd

from app_common.mpl_tools.mpl_style_description import PltStyleDescription

PARAM_LABELS = {
    "column.bed_height_actual": "Bed height",
    "method.method_steps[0].volume": "Load volume",
    "method.method_steps[1].volume": "Wash volume",
    "method.method_steps[2].volume": "Elut. volume",
    "method.method_steps[0].flow_rate": "Load flow rate",
    "method.method_steps[1].flow_rate": "Wash flow rate",
    "method.method_steps[2].flow_rate": "Elut. flow rate",
    'method.initial_buffer.pH': "Equil. pH",
    "method.method_steps[0].solutions[0].pH": "Load pH",
    "method.method_steps[1].solutions[0].pH": "Wash pH",
    "method.method_steps[2].solutions[1].pH": "Elution pH",
    "method.collection_criteria.start_collection_target": "Start collect",
    "method.collection_criteria.stop_collection_target": "Stop collect",
    "column.resin.average_bead_diameter": "Bead diam.",
    "column.resin.ligand_density": "Ligand density",
    'method.initial_buffer.chemical_component_concentrations[1]': 'Equil. cation conc.',  # noqa
    'method.method_steps[2].solutions[1].chemical_component_concentrations[1]': 'Elution cation conc.',  # noqa
    'method.method_steps[1].solutions[0].chemical_component_concentrations[1]': 'Wash cation conc.'  # noqa
}


def plot_performance_as_tornado_plot(data, perf_name, cp_perf=None,
                                     select_cols=None, filepath="",
                                     **plt_style):
    """ Make a tornado/Pareto plot to show how a performance parameter changes
    with and around a set of input parameters.

    Parameters
    ----------
    data : DataFrame
        Table of impacts of parameters (columns) on a set of performances
        (rows). The impact is described as the difference between the
        performance for a certain value of a parameter and the value of that
        performance at a reference parameter value (or reference simulation).
        These columns are expected to be sorted from the most impactful to the
        least. See :func:`extract_perf_data` to generate this dataframe from a
        list of simulation grids.

    perf_name : str
        Name of the performance to plot the impact of parameters on. For
        display in title only.

    cp_perf : float [OPTIONAL]
        Value of the reference simulation, used to reset all other data. For
        display in title only.

    select_cols : int [OPTIONAL]
        Number of parameters to display the impact of. By default, don't skip
        anything.

    filepath : str [OPTIONAL]
        Path to the file to save the plot into, if any. Leave blank to skip
        saving to file.

    plt_style : dict
        General styling keyword for a Matplotlib plot. Supports all attributes
        of a :class:`app_common..mpl_tools.mpl_style_description.PltStyleDescription`.  # noqa

    Examples
    --------
    >>> print(data)
                              Stop collect               Start collect
    low1                          3.411318                    1.003988
    high1                        -4.069830                   -0.740883
    low2                          6.179353                    3.698790
    high2                        -9.043037                   -5.305777
    set point                     0.000000                    0.000000
    >>> perf_name = 'Step Yield'
    >>> cp_perf = 69.80
    >>> plot_performance_as_tornado_plot(data, perf_name, cp_perf=cp_perf,
                                         title_fontsize=24)
    """
    plt_desc = PltStyleDescription(**plt_style)

    if select_cols:
        data = data.iloc[:, :select_cols]

    sorted_params = data.columns
    pos = arange(len(sorted_params)) + .5

    if len(data) == 7:
        style = "6_points"
    elif len(data) == 5:
        style = "or_cr"
    else:
        msg = "Data shape unsupported!"
        raise NotImplementedError(msg)

    highs1 = data.loc["high1", :]
    lows1 = data.loc["low1", :]
    highs2 = data.loc["high2", :]
    lows2 = data.loc["low2", :]
    if style == "6_points":
        highs3 = data.loc["high3", :]
        lows3 = data.loc["low3", :]

    plt.figure()
    if style == "6_points":
        width = 0.2  # the width of the bars: can also be len(x) sequence
        second_alpha = 0.6
    else:
        width = 0.4
        second_alpha = 0.5

    pos1 = pos
    pos2 = pos + width
    p1 = plt.bar(pos1, highs1, width, color='red')
    p2 = plt.bar(pos1, lows1, width, color='blue')
    p3 = plt.bar(pos2, highs2, width, color='red', alpha=second_alpha)
    p4 = plt.bar(pos2, lows2, width, color='blue', alpha=second_alpha)
    if style == "6_points":
        pos3 = pos + 2 * width
        p5 = plt.bar(pos3, highs3, width, color='red', alpha=0.3)
        p6 = plt.bar(pos3, lows3, width, color='blue', alpha=0.3)

    plt.ylabel('Impact on {}'.format(perf_name), fontsize=plt_desc.y_fontsize)
    plt.yticks(fontsize=plt_desc.y_fontsize-2)
    if cp_perf:
        plt.title("Set Point {}: {:.5f}".format(perf_name, cp_perf),
                  fontsize=plt_desc.title_fontsize)
    plt.xticks(pos2+width/2., sorted_params)
    plt.xticks(rotation=30, fontsize=plt_desc.x_fontsize)
    if plt_desc.include_legend:
        if style == "6_points":
            plt.legend((p1[0], p2[0], p3[0], p4[0], p5[0], p6[0]),
                       ('High param @ NOR', 'Low param @ NOR',
                        'High param @ 2xNOR', 'Low param @ 2xNOR',
                        'High param @ 3xNOR', 'Low param @ 3xNOR'),
                       loc=plt_desc.legend_loc,
                       fontsize=plt_desc.legend_fontsize)
        else:
            plt.legend((p1[0], p2[0], p3[0], p4[0]),
                       ('High param @ NOR', 'Low param @ NOR',
                        'High param @ CR', 'Low param @ CR'),
                       loc=plt_desc.legend_loc,
                       fontsize=plt_desc.legend_fontsize)

    plt.grid(plt_desc.include_grid)

    if filepath:
        plt.savefig(filepath)


def extract_perf_data(param_grids, perf_name, index_desc, param_labels=None,
                      param_list=None):
    """ Convert a dictionary of grid data, aggregate it and sort
    it to prepare it for :func:`plot_performance_as_tornado_plot`.

    Parameters
    ----------
    param_grids : dict
        Dictionary mapping scanned parameter names to the grid's group_data
        contained in 5-point or 7-point simulation grids, each scanning 1
        parameter, to study their impact on performances.

    perf_name : str
        Name of the performance to extract data for.

    index_desc : list
        List of descriptions of the index. Depending on how the grid was
        created, the location of the low, center and high value in the index
        may differ. Typical values are ["low1", "high1", "low2", "high2",
        "set point"] and ["low2", "low1", "set point", "high1", "high2"].

    param_labels : dict, [OPTIONAL]
        Mapping between parameters scanned and a shortened/pretty version to
        display in output DF. Defaults to standards stored in this module.

    param_list : dict, [OPTIONAL]
        Mapping between parameter scanned and a description of how it was
        scanned: center value, the difference(s) with the values explored, and
        a string representation of the unit of the center value. No pretty
        display of unit/range information in the results if not provided.
    """
    if param_labels is None:
        param_labels = PARAM_LABELS

    data = {param: df[perf_name] for param, df in param_grids.items()}
    data = pd.DataFrame(data)
    if param_list:
        col_names = []
        for col in data.columns:
            if len(param_list[col]) == 3:
                center, diff, units = param_list[col]
                large_diff = 3 * diff
            elif len(param_list[col]) == 4:
                center, diff, diff_cr, units = param_list[col]
                large_diff = diff_cr
            else:
                msg = "Unexpected length for param_list for {}".format(col)
                raise NotImplementedError(msg)

            # \u00B1 is unicode for +/- symbol
            range_desc = u"\n[\u00B1 {}/\u00B1 {}]{}".format(diff, large_diff,
                                                             units)
            name = param_labels[col] + range_desc
            col_names.append(name)
        data.columns = col_names
    else:
        data.columns = [param_labels[col] for col in data.columns]

    for col in data:
        data[col] = data[col].astype(float)

    if len(index_desc) == 7:
        largest_range = "low3", "high3"
    elif len(index_desc) == 5:
        largest_range = "low2", "high2"
    else:
        raise NotImplementedError("Unexpected index length")

    data.index = index_desc

    # Rescale the data to be differences compared to the set point:
    set_point_perf = data.loc["set point", :][0]
    data = data - data.loc["set point"]

    # Sort the parameters based on the sum of their impact, in both the
    # negative and the positive direction:
    unsorted_lows = data.loc[largest_range[0], :]
    unsorted_highs = data.loc[largest_range[1], :]
    perf_sum = (unsorted_highs**2 + unsorted_lows**2)
    impact_level = perf_sum.sort(inplace=False, ascending=False)
    sorted_params = impact_level.index
    data = data[sorted_params]
    return data, set_point_perf
