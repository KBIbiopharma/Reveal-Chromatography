""" Tool to explore and ultimately optimize the cost function used by an
optimizer.
"""
import logging
import pandas as pd
import numpy as np

from traits.api import Array, Bool, Button, cached_property, Dict, Enum, \
    Float, HasTraits, Instance, Int, List, on_trait_change, Property, Str
from traitsui.api import EnumEditor, HGroup, Item, Label, OKButton, \
    RangeEditor, Spring, VGroup
from chaco.api import ArrayPlotData, ColorBar, cool, DataRange1D, \
    HPlotContainer, LinearMapper, Plot
from enable.api import ComponentEditor

from kromatography.utils.traitsui_utils import KromView
from kromatography.compute.brute_force_optimizer import BruteForceOptimizer
from kromatography.compute.experiment_optimizer_step import ALL_COST_COL_NAME
from kromatography.compute.cost_functions import SIM_COL_NAME
from kromatography.model.simulation import Simulation

logger = logging.getLogger(__name__)

# The percentile of the max value of the colorbar in the 2D plot case
DEFAULT_PERCENT_LOW_COST_VALUES = 50

# Max possible weight to be given to a cost function component
MAX_WEIGHT = 30.

# Name of the 2D array of pivoted data to display in the 2D plot case
TWO_D_DATA_NAME = "cost_data_2d"


class OptimizerCostFunctionExplorer(HasTraits):
    """ Viewer and editor for the default brute force optimizer cost function.

    FIXME: Refactor the plot part into an nD dataframe viewer
    FIXME: Make it more general by not assume what component the cost function
    is made of.
    """
    #: Optimizer whose cost function is being being edited/viewed
    optimizer = Instance(BruteForceOptimizer)

    # Cost function weight attributes -----------------------------------------

    #: Proxy weight (relative importance) of the peak time location
    peak_time_weight = Float

    #: Proxy weight (relative importance) of the height of the peak
    peak_height_weight = Float

    #: Proxy weight (relative importance) of the peak's back slope
    peak_slope_weight = Float

    #: Array of proxy weights
    cost_func_weights = Property(Array, depends_on="peak_time_weight, "
                                                   "peak_height_weight, "
                                                   "peak_slope_weight")

    #: Toggle the weight edit mode
    edit_weights_button = Button("Edit weights/View weights")

    #: Is there enough data to recompute costs
    can_change_weights = Property(Bool)

    #: Allow to edit the weights of the cost function?
    weight_edit_mode = Bool

    # Cost data attributes ----------------------------------------------------

    #: Complete cost data computed by the cost function
    cost_data = Instance(pd.DataFrame)

    #: Cost data, filtered on all the parameters that are not plotted
    filtered_cost_data = Instance(pd.DataFrame)

    #: List of simulation objects the cost data is computed for.
    simulations = List(Simulation)

    #: Selector to see the cost data in a 2D plot.
    # TODO: add "3D" for a mayavi plot
    show_cost_data_nd = Enum(["1D", "2D"])

    #: 1d or 2d view of cost data
    plot1_2d_container = Instance(HPlotContainer)

    #: Data for 2d plot
    cost_plot_data = Instance(ArrayPlotData)

    #: What parameter to see along x
    x_axis_param = Str

    #: What parameter to see along y
    y_axis_param = Str(ALL_COST_COL_NAME)

    #: What parameter to see along color
    color_axis_param = Str(ALL_COST_COL_NAME)

    #: 2D visualization colorbar
    colorbar = Instance(ColorBar)

    #: Range of the color bar for the 2D visualization.
    colorbar_range = Property(Instance(DataRange1D), depends_on="cost_data")

    #: Percentile of max value on colorbar (for 2D vis only)
    color_bar_max_percentile = Int(DEFAULT_PERCENT_LOW_COST_VALUES)

    #: List of parameters being scanned
    param_list = Property(List(Str))

    #: Mapping trait controlling value of a param -> param name
    trait_name_param_name_map = Dict

    #: Whether there is cost data to display
    no_cost_data = Property(Bool)

    def __init__(self, **traits):
        if "optimizer" not in traits or traits["optimizer"] is None:
            msg = "To create an OptimizerCostFunction explorer, an optimizer" \
                  " must be provided."
            logger.exception(msg)
            raise ValueError(msg)

        # Make sure the optimizer is set first to avoid listeners to fail due
        # to lack of data access:
        optim_dict = {"optimizer": traits.pop("optimizer")}
        super(OptimizerCostFunctionExplorer, self).__init__(**optim_dict)
        self.trait_set(trait_change_notify=False, **traits)

        if self.no_cost_data:
            return

        for param in self.param_list:
            trait_name = self._param_name_to_trait_name(param)
            self.trait_name_param_name_map[trait_name] = param
            self.add_trait(trait_name, Float)
            self.on_trait_change(self.update_on_param_change, trait_name)

        self.rebuild_all()

    def traits_view(self):
        additional_param_controls = self._build_additional_param_editors()
        param_list_with_cost = [ALL_COST_COL_NAME] + self.param_list
        two_d_plot_shown = "show_cost_data_nd == '2D' and y_axis_param != " \
                           "'{}'".format(ALL_COST_COL_NAME)
        weight_range_editor = RangeEditor(low=0., high=MAX_WEIGHT)
        weight_doc = Label("The following control the relative importance or "
                           "the various components that go into computing the"
                           " cost of a model,\nthat is the difference between "
                           "a simulation with that model and the corresponding"
                           " experiment."),
        view = KromView(
            VGroup(
                VGroup(
                    weight_doc,
                    HGroup(
                        Item("peak_time_weight", label="Peak time"),
                        Item("peak_height_weight", label="Peak height"),
                        Item("peak_slope_weight", label="Peak slope"),
                    ),
                    show_border=True, label="Weights", enabled_when="False",
                    visible_when="not weight_edit_mode"
                ),
                VGroup(
                    weight_doc,
                    Item("peak_time_weight", label="Peak time",
                         editor=weight_range_editor),
                    Item("peak_height_weight", label="Peak height",
                         editor=weight_range_editor),
                    Item("peak_slope_weight", label="Peak slope",
                         editor=weight_range_editor),
                    show_border=True, label="Weights",
                    visible_when="weight_edit_mode"
                ),
                HGroup(
                    Spring(),
                    Item("edit_weights_button", show_label=False,
                         enabled_when="can_change_weights")
                ),
                VGroup(
                    HGroup(
                        Item("show_cost_data_nd", label="Plot type",
                             style="custom",
                             enabled_when="len(param_list) > 1"),
                        Item("x_axis_param",
                             editor=EnumEditor(values=self.param_list)),
                        Item("y_axis_param",
                             editor=EnumEditor(values=param_list_with_cost),
                             enabled_when="show_cost_data_nd != '1D'"),
                    ),
                    Item("plot1_2d_container", editor=ComponentEditor(),
                         show_label=False),
                    HGroup(
                        Spring(),
                        Item('color_bar_max_percentile',
                             editor=RangeEditor(low=1, high=100,
                                                mode='spinner'),
                             label='Colorbar high percentile (%)',
                             visible_when=two_d_plot_shown)
                    ),
                    VGroup(
                        *additional_param_controls
                    ),
                    label="Cost function plot", show_border=True,
                    visible_when="not no_cost_data"
                ),
            ),
            buttons=[OKButton],
            title="View/Edit optimizer cost function"
        )
        return view

    def rebuild_all(self):
        self.reset_filtered_cost_data()
        self.update_plot_data()
        self.rebuild_renderer()

    def rebuild_renderer(self, container=None):
        """ Remove and rebuild all renderers of the cost data plot container.
        """
        if container is None:
            container = self.plot1_2d_container

        self.remove_existing_renderers(container)

        renderer_factories = {"1D": self.rebuild_1d_renderer,
                              "2D": self.rebuild_2d_renderer}
        renderer_factories[self.show_cost_data_nd](container)

        plot = container.plot_components[0]
        self._reset_plot_axis_titles(plot)

    def rebuild_1d_renderer(self, container):
        """ Remove all renderers & view costs with a scatter plot.
        """
        plot = container.plot_components[0]
        # Create scatter renderer for the new x_axis choice
        plot.plot((self.x_axis_param, self.y_axis_param), type="scatter",
                  color="blue", name=self.x_axis_param + "scatter")

    def rebuild_2d_renderer(self, container):
        """ Remove all renderers & view costs with a image plot.
        """
        plot = container.plot_components[0]
        #: Compute approximate boundaries between cells
        x = self.cost_data[self.x_axis_param]
        xbounds = (x.min(), x.max())
        y = self.cost_data[self.y_axis_param]
        ybounds = (y.min(), y.max())
        renderer = plot.img_plot(TWO_D_DATA_NAME, xbounds=xbounds,
                                 ybounds=ybounds, colormap=cool,
                                 name="img_cost")[0]
        renderer.color_mapper.range = self.colorbar_range
        self.recompute_colorbar(plot)
        container.add(self.colorbar)

    def remove_existing_renderers(self, container):
        """ Remove all existing renderers.
        """
        # Remove renderers from main plot
        if container.plot_components:
            plot = container.plot_components[0]
            plot.delplot(*plot.plots.keys())
        if len(container.plot_components) > 1:
            # remove the colorbar
            container.remove(container.plot_components[1])

    def recompute_colorbar(self, plot):
        """ Create a colorbar for the image plot provided, and add to
        plot1_2d_container
        """
        img_renderer = plot.plots["img_cost"][0]
        colormap = img_renderer.color_mapper
        # Constant mapper for the color bar so that the colors stay the same
        # even when different slices are selected-=
        index_mapper = LinearMapper(range=self.colorbar_range)
        self.colorbar = ColorBar(index_mapper=index_mapper,
                                 color_mapper=colormap,
                                 padding_top=plot.padding_top,
                                 padding_bottom=plot.padding_bottom,
                                 padding_right=20,
                                 resizable='v',
                                 orientation='v',
                                 width=30)

    def pivot_filtered_data(self):
        """ Pivot the cost values into a 2d matrix with x_axis_name along x
        (columns) and y_axis_name changing along y (index)
        """
        data = self.filtered_cost_data.pivot_table(
            index=self.y_axis_param, columns=self.x_axis_param,
            values=ALL_COST_COL_NAME
        )
        return data

    def reset_filtered_cost_data(self):
        """ Recompute the filtered cost data from the cost_data and the list of
        plotted parameters as opposed to not.
        """
        # Set all other params to their lowest value:
        axis_params = {self.x_axis_param, self.y_axis_param}
        for param_name in set(self.param_list) - axis_params:
            low = self.cost_data[param_name].min()
            trait_name = self._param_name_to_trait_name(param_name)
            setattr(self, trait_name, low)

        self.update_filtered_cost_data()

    def update_filtered_cost_data(self):
        """ A parameter that isn't plotted has changed: modify the section of
        filtered_cost_data that will be plotted
        """
        if self.no_cost_data:
            return

        axis_params = [self.x_axis_param, self.y_axis_param]

        # Reset the data
        filtered_cost_data = self.cost_data.copy()

        # Initialize the mask
        global_mask = np.ones(len(filtered_cost_data), dtype=np.bool)
        for param in set(self.param_list) - set(axis_params):
            trait_name = self._param_name_to_trait_name(param)
            cur_val = getattr(self, trait_name)
            scanned_values = self.cost_data[param].unique()
            requested_value_idx = np.abs(scanned_values - cur_val).argmin()
            requested_value = scanned_values[requested_value_idx]
            mask = filtered_cost_data[param] == requested_value
            global_mask *= mask

        filtered_cost_data = filtered_cost_data.loc[global_mask, :]

        # Sort the data following the x axis and then the y axis
        self.filtered_cost_data = filtered_cost_data.sort_values(
            by=axis_params
        )

    def update_plot_data(self):
        if self.no_cost_data:
            return

        update_plot_data_methods = {"1D": self.update_1D_cost_plot_data,
                                    "2D": self.update_2D_cost_plot_data}
        update_plot_data_methods[self.show_cost_data_nd]()

    def update_1D_cost_plot_data(self):
        """ Reset the arrays of the 1D ArrayPlotData based on new x and y axis
        choices.
        """
        new_values = self.filtered_cost_data[self.x_axis_param].values
        self.cost_plot_data.set_data(self.x_axis_param, new_values)
        new_values = self.filtered_cost_data[self.y_axis_param].values
        self.cost_plot_data.set_data(self.y_axis_param, new_values)

    def update_2D_cost_plot_data(self):
        cost_data_2d = self.pivot_filtered_data()
        self.cost_plot_data.set_data(TWO_D_DATA_NAME, cost_data_2d.values)

    # Private interface -------------------------------------------------------

    def _build_additional_param_editors(self):
        """ Build a list of view elements for user to control parameters not
        plotted.
        """
        if self.no_cost_data:
            return []

        def build_visible_when(param_name):
            x_axis_criteria = "x_axis_param != '{}'".format(param_name)
            y_axis_criteria = "y_axis_param != '{}'".format(param_name)
            return x_axis_criteria + " and " + y_axis_criteria

        items = []
        for param_name in self.param_list:
            low, high = self._get_param_range(param_name)
            trait_name = self._param_name_to_trait_name(param_name)
            editor = RangeEditor(low=low, high=high, mode='slider')
            item = Item(trait_name, editor=editor, label=param_name,
                        visible_when=build_visible_when(param_name))
            items.append(item)
        return items

    def _param_name_to_trait_name(self, param_name):
        trait_name = param_name + "_control"
        for char in [".", "[", "]", ":"]:
            trait_name = trait_name.replace(char, "_")

        while "_"*2 in trait_name:
            trait_name = trait_name.replace("_"*2, "_")
        return trait_name

    def _get_param_range(self, param_name):
        """ Collect the low and high bounds explored in the cost_data DF for a
        given parameter.
        """
        values = self.cost_data[param_name]
        low = values.min()
        high = values.max()
        return low, high

    def _compute_cost_value_range(self):
        """ Compute the range of cost values to display in the colorbar.
        """
        all_costs = self.cost_data[ALL_COST_COL_NAME]
        low = all_costs.min()
        high = np.percentile(all_costs, self.color_bar_max_percentile)
        return low, high

    def _reset_plot_axis_titles(self, plot):
        plot.x_axis.title = self.x_axis_param
        plot.y_axis.title = self.y_axis_param

    # Trait listeners ---------------------------------------------------------

    def update_on_param_change(self):
        self.update_filtered_cost_data()
        self.update_plot_data()

    def _x_axis_param_changed(self):
        self.rebuild_all()

    def _y_axis_param_changed(self, new):
        self.reset_filtered_cost_data()
        if new == ALL_COST_COL_NAME:
            self.show_cost_data_nd = "1D"
        elif new == self.x_axis_param:
            # Incompatible choice for a 2D plot, do nothing
            return

        self.update_plot_data()
        self.rebuild_renderer()

    def _show_cost_data_nd_changed(self, new):
        if new == "1D":
            self.y_axis_param = ALL_COST_COL_NAME
        else:
            possible_ys = list(set(self.param_list) - {self.x_axis_param})
            self.y_axis_param = possible_ys[0]

    def _color_bar_max_percentile_changed(self, new):
        """ Update the high value of the colorbar's mappers based on new choice
        """
        high = np.percentile(self.cost_data[ALL_COST_COL_NAME], new)
        colorbar_range = self.colorbar.index_mapper.range
        colorbar_range.high = high

    def _edit_weights_button_fired(self):
        self.weight_edit_mode = not self.weight_edit_mode

    @on_trait_change('optimizer:cost_data', post_init=True)
    def cost_data_changed(self):
        """ Optimizer cost data changed: update all ArrayPlotData entries.
        """
        self.cost_data = self.optimizer.cost_data.copy()
        self.reset_filtered_cost_data()
        # Reset the 1D arrays
        for col_name in self.filtered_cost_data.columns:
            if col_name != SIM_COL_NAME:
                data = self.filtered_cost_data[col_name].values
                self.cost_plot_data.set_data(col_name, data)

        if self.show_cost_data_nd == "2D":
            if self.y_axis_param in self.param_list:
                self.update_2D_cost_plot_data()

            self.update_colorbar_range()

    def update_colorbar_range(self):
        low, high = self._compute_cost_value_range()
        colorbar_range = self.colorbar.index_mapper.range
        colorbar_range.low, colorbar_range.high = low, high

    @on_trait_change("peak_height_weight, peak_slope_weight, peak_time_weight")
    def recompute_cost_data(self):
        self.optimizer.recompute_costs_for_weights(self.cost_func_weights)

    # Traits initialization methods -------------------------------------------

    def _filtered_cost_data_default(self):
        return self.optimizer.cost_data.copy()

    def _cost_plot_data_default(self):
        if self.cost_data is None or len(self.cost_data) == 0:
            return

        self.reset_filtered_cost_data()

        cols = {}
        # Collect 1D arrays
        for col_name in self.filtered_cost_data.columns:
            if col_name != SIM_COL_NAME:
                cols[col_name] = self.filtered_cost_data[col_name].values

        # Collect 2D arrays if y_axis_param not set as output:
        if self.y_axis_param in self.param_list:
            cost_data_2d = self.pivot_filtered_data()
            cols[TWO_D_DATA_NAME] = cost_data_2d.values

        data = ArrayPlotData(**cols)
        return data

    def _plot1_2d_container_default(self):
        if self.cost_data is None or len(self.cost_data) == 0:
            return

        plot = Plot(self.cost_plot_data)
        plot.title = "Cost function"
        plot.padding_left = 80
        container = HPlotContainer()
        container.add(plot)
        self.rebuild_renderer(container)
        return container

    def _x_axis_param_default(self):
        if self.param_list:
            return self.param_list[0]
        else:
            return ""

    def _cost_data_default(self):
        if self.optimizer.cost_data is not None:
            return self.optimizer.cost_data.copy()

    def _peak_time_weight_default(self):
        """ Return the weight from the first group of the first step.

        This assumes the steps were all created with the same weights.
        """
        return self.optimizer.steps[0].cost_func_kw['peak_time_weight']

    def _peak_height_weight_default(self):
        """ Return the weight from the first group of the first step.

        This assumes the steps were all created with the same weights.
        """
        return self.optimizer.steps[0].cost_func_kw['peak_height_weight']

    def _peak_slope_weight_default(self):
        """ Return the weight from the first group of the first step.

        This assumes the steps were all created with the same weights.
        """
        return self.optimizer.steps[0].cost_func_kw['peak_slope_weight']

    # Traits property getters/setters -----------------------------------------

    def _get_param_list(self):
        if self.no_cost_data:
            return []

        exclude = {ALL_COST_COL_NAME, SIM_COL_NAME}
        param_list = sorted(list(set(self.cost_data.columns) - exclude))
        return param_list

    @cached_property
    def _get_colorbar_range(self):
        """ Build and return a data range spanning the first values of the full
        spectrum.
        """
        if self.no_cost_data:
            return

        low, high = self._compute_cost_value_range()
        data_range = DataRange1D(low=low, high=high)
        return data_range

    def _get_can_change_weights(self):
        """ Can recompute the costs when changing the weights?

        Cannot recompute the costs data if we don't have access to the
        simulations run.
        """
        first_step = self.optimizer.steps[0]
        cost_functions_available = first_step.group_cost_functions != {}
        return self.no_cost_data or cost_functions_available

    @cached_property
    def _get_cost_func_weights(self):
        return np.array([self.peak_time_weight, self.peak_height_weight,
                         self.peak_slope_weight], dtype=np.float64)

    def _get_no_cost_data(self):
        return self.cost_data is None or len(self.cost_data) == 0


if __name__ == "__main__":
    from kromatography.io.reader_writer import load_object
    task = load_object("demo_with_2_types_optim.chrom")
    optimizer = task.project.study.analysis_tools.optimizations[2]
    explorer = OptimizerCostFunctionExplorer(
        optimizer=optimizer,
        show_cost_data_nd="2D", x_axis_param="binding_model.sma_ka[3]",
        y_axis_param="binding_model.sma_nu[3]"
    )
    explorer.configure_traits()
