""" Scripting functions to plot simulation grid performances using Matplotlib.
"""
import logging
from os.path import join
import matplotlib.pyplot as plt
import seaborn as sns
from pandas import DataFrame
from scipy import ndimage
from numpy import arange, ones

from app_common.std_lib.filepath_utils import string2filename
from app_common.mpl_tools.mpl_style_description import PltStyleDescription

from kromatography.model.simulation_group import SIM_COL_NAME

logger = logging.getLogger(__name__)

sns.set_style("whitegrid")


# API functions ---------------------------------------------------------------


def plot_sim_group_performances(group_data, param1, param2, show_plots=True,
                                save_plots=False, file_format=".png",
                                **kwargs):
    """ Plot all performance parameters as a function of 2 parameters scanned.

    Parameters
    ----------
    group_data : DataFrame
        SimulationGroup output data.

    param1, param2 : str
        Scanned parameters to plot the performances against. First parameter
        display along the index, second along the columns.

    show_plots : bool
        Plot all outputs as an interactive Matplotlib window?

    save_plots : bool
        Save all plots into a (separate) file?

    file_format : str
        File format to save the plots into. Supported formats: eps, jpeg, jpg,
        pdf, pgf, png, ps, raw, rgba, svg, svgz, tif, tiff. Ignored if
        save_to_file=False.

    kwargs : dict
        Additional plotting parameters. See :func:`plot_as_heatmap` for
        details.
    """
    _convert_df_dtypes(group_data)
    output_map = extract_output_data(group_data, [param1, param2])
    num_figs = plot_output_as_heatmaps(output_map, **kwargs)

    if save_plots:
        for output_name, fig_num in num_figs.items():
            plt.figure(fig_num)
            fname = "reveal_generated_plot_{}_against_{}_and_{}{}"
            fname = fname.format(output_name, param1, param2, file_format)
            fname = string2filename(fname)
            msg = "Saving output {} into file {}".format(output_name, fname)
            logger.warning(msg)
            print(msg)
            plt.savefig(fname)

    if show_plots:
        plt.show()


# Data transformation functions -----------------------------------------------


def filter_dataframe(group_data, filter_data):
    """ Filter DataFrame along the parameters (columns) specified.

    Parameters
    ----------
    group_data : DataFrame
        Data to filter.

    filter_data : dict
        Mapping between a parameter name and a 2-tuple of min and max values
        beyond which to remove data rows.
    """
    mask = ones(len(group_data), dtype=bool)

    for col in filter_data:
        min_val, max_val = filter_data[col]

        if min_val:
            mask *= group_data[col] >= min_val
        if max_val:
            mask *= group_data[col] < max_val

    return group_data.loc[mask, :]


def _convert_df_dtypes(group_data):
    """ Try and convert all columns of a DataFrame to float dtype.
    """
    for col in group_data:
        try:
            group_data[col] = group_data[col].astype("float64")
        except ValueError:
            pass


def extract_output_data(group_data, parameters, param_filter=None):
    """ Extract output data from grid data, and pivot them to prepare to plot.

    Parameters
    ----------
    group_data : DataFrame
        SimulationGroup output data.

    parameters : list
        List of the 2 parameter names to pivot along (first parameter display
        along the index, second along the columns). There can be more entries
        in the list, if filtering other parameters is needed.

    param_filter : dict [OPTIONAL]
        Additional parameters to filter on. The dict maps the additional
        parameters to the min/max values they need to be within.
    """
    if param_filter:
        group_data = filter_dataframe(group_data, param_filter)

    output_map = {}
    for col in group_data.columns:
        if col not in [SIM_COL_NAME] + parameters:
            pivoted = group_data.pivot_table(
                index=parameters[1], columns=parameters[0], values=col
            )
            output_map[col] = pivoted.sort_index(ascending=False)

    return output_map


# Plotting functions ----------------------------------------------------------


def plot_output_as_heatmaps(output_map, filepath='', **kwargs):
    """ Print the dictionary of outputs as 2D heatmaps.

    Returns the mapping between the figure created and the performance plotted
    on it, so that they can be recovered and saved as image files.

    Parameters
    ----------
    output_map : dict
        Dictionary of dataframes containing output parameters as a function of
        2 scanned parameters.

    filepath : str
        Folder path to save all produced plots into. Filename will be generated
        from each output plotted.

    kwargs : dict
        Additional plotting parameters. See :func:`plot_as_heatmap` for
        details.

    Returns
    -------
    Dict
        Mapping between the performance plotted and the figure number.
    """
    fig_map = {}
    for fig_num, (output, data) in enumerate(output_map.items()):
        title = output.replace("_", " ")
        if filepath:
            fname = string2filename(output) + ".jpg"
            kwargs["filepath"] = join(filepath, fname)
        try:
            plot_as_heatmap(data, title=title, **kwargs)
        except Exception as e:
            logger.exception(e)
        else:
            fig_map[title] = fig_num

    return fig_map


def plot_as_heatmap(data, title, add_cross_at=None, param_labels=None,
                    smooth="gauss", filepath='', **plt_style):
    """ Build a Matplotlib heatmap to display pivoted table of an output as a
    function of 2 scanned parameters.

    If smoothing is applied, 5 contours are drawn on top of the heatmaps.

    Parameters
    ----------
    data : DataFrame
        DataFrame containing output parameter as a function of 2 scanned
        parameters.

    title : str
        Name of the output

    add_cross_at : tuple [OPTIONAL]
        (x, y) coordinate of a red cross to be added. Leave as None to skip.

    param_labels : dict [OPTIONAL]
        Dictionary mapping parameter names to pretty names to use in plot
        labels.

    filepath : str
        Path to the file to save the plot to, if any.

    smooth : str [OPTIONAL, default="None"]
        What type of smoothing should be applied to the 2D matrix of data
        before plotting. Supported values are "None" and "gauss".

    plt_style : dict
        General styling keyword for a Matplotlib plot. Supports all attributes
        of a :class:`app_common..mpl_tools..mpl_style_description.PltStyleDescription`.  # noqa
    """
    plt_desc = PltStyleDescription(**plt_style)

    if param_labels is None:
        param_labels = {data.columns.name: data.columns.name,
                        data.index.name: data.index.name}

    if smooth == "gauss":
        data_to_plot = ndimage.filters.gaussian_filter(data, 2, mode='nearest')
        data_to_plot = DataFrame(data_to_plot, columns=data.columns,
                                 index=data.index)
        imshow_kw = {"interpolation": "gaussian"}
    else:
        data_to_plot = data
        imshow_kw = {"interpolation": "None"}

    plt.figure()
    plt.imshow(data_to_plot, cmap=plt_desc.colormap, **imshow_kw)
    plt.colorbar()
    plt.title(title.title(), fontsize=plt_desc.title_fontsize)
    plt.xlabel(param_labels[data_to_plot.columns.name],
               fontsize=plt_desc.x_fontsize)
    plt.ylabel(param_labels[data_to_plot.index.name],
               fontsize=plt_desc.y_fontsize)

    if plt_desc.include_contours:
        CS = plt.contour(data_to_plot, plt_desc.countour_num, colors='k',
                         linewidths=plt_desc.contour_linewidth, origin='lower')
        plt.clabel(CS, inline=1, fontsize=plt_desc.contour_fontsize)

    x_ticks_text, x_ticks_position = _ticks_from_vals(data_to_plot.columns)
    plt.xticks(x_ticks_position, x_ticks_text, fontsize=plt_desc.x_fontsize)
    y_ticks_text, y_ticks_position = _ticks_from_vals(data_to_plot.index)
    plt.yticks(y_ticks_position, y_ticks_text, fontsize=plt_desc.y_fontsize)

    if add_cross_at:
        cross_x, cross_y = add_cross_at
        x_vals = data_to_plot.columns
        y_vals = data_to_plot.index
        center_x = _compute_loc(cross_x, low_map=(0, x_vals.min()),
                                high_map=(len(x_vals), x_vals.max()))
        # For y, we have inverted the axis direction:
        center_y = _compute_loc(cross_y, low_map=(0, y_vals.max()),
                                high_map=(len(y_vals), y_vals.min()))
        plt.plot(center_x, center_y, "ko")

    plt.grid(plt_desc.include_grid)
    if filepath:
        plt.savefig(filepath)


# Utilities -------------------------------------------------------------------


def _compute_loc(x, low_map, high_map):
    """ Compute the location of a value in a space indexed by a different range
    """
    a = (high_map[0] - low_map[0])/(high_map[1] - low_map[1])
    b = low_map[0] - a * low_map[1]
    return a*x + b


def _ticks_from_vals(vals, num_ticks=5, precision=2):
    """ Extract ticks labels and positions from an array of values.
    """
    ticks_downsampling = len(vals) // num_ticks
    ticks = vals[::ticks_downsampling]
    ticks_text = [("{:." + str(precision) + "f}").format(val) for val in ticks]
    ticks_position = arange(len(vals))[::ticks_downsampling]
    return ticks_text, ticks_position
