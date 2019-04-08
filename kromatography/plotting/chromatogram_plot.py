import numpy as np

from chaco.api import ArrayPlotData, BaseTool, add_default_axes, DataRange1D, \
    Legend, Plot, PlotAxis

from chaco.tools.api import BetterSelectingZoom, LegendHighlighter, PanTool
from enable.layout.api import align, vbox
from traits.api import Bool, Dict, HasStrictTraits, Instance, Str

from app_common.chaco.constraints_plot_container import \
    ConstraintsPlotContainer

from kromatography.plotting.data_inspector_tool import add_data_inspector
from kromatography.utils.string_definitions import LOG_FAMILY_UV

LEGEND_TOOL_LOC = 0


class ChromatogramPlot(HasStrictTraits):
    """ The Chaco plot that provides an API to plot ChromeLog instances.
    """

    #: The collection of Plots in the container. Each Plot corresponds to a
    #: chrome-log family. The key corresponds to the name of the chrome-log
    #: family.
    plot_contexts = Dict(Str, Instance(Plot))

    #: Remove a Plot from the container if there are no curves being rendered.
    #: Set to `False` to avoid the resizing of the Plots in the container
    #: when the empty Plot is removed.
    remove_empty_plot = Bool(True)

    #: The instance of PlotContainer that contains all the Plots.
    container = Instance(ConstraintsPlotContainer)

    #: all_plots_index_range will store a common  index_range
    all_plots_index_range = Instance(DataRange1D)

    #: Legend attached to the UV plot
    _legend = Instance(Legend)

    #: Legend highlighting tool
    _legend_tool = Instance(BaseTool)

    def init(self):
        """ Initialize the plots.
        """
        self._create_container()

    # ChromatogramPlot public interface -----------------------------------

    def add_chrome_log(self, prefix, log):
        """ Add the given chrome-log to the appropriate plot container.

        Parameters
        ----------
        prefix : str
            Name of the ChromeLogCollection (typically the name of the exp/sim)
            the log is part of. Used to build the name of the plot renderer.

        log : ChromeLog
            Chromatography Log object, containing family information and the
            data to display.
        """
        plot_context = self._get_or_create_plot_context(log)
        self._add_log_to_plot_context(plot_context, log, prefix=prefix)

    def remove_chrome_log(self, prefix, log):
        """ Remove a single log (curve) from the appropriate plot container.

        Parameters
        ----------
        prefix : str
            Name of the ChromeLogCollection (typically the name of the exp/sim)
            the log is part of. Used to find the name of the plot renderer.

        log : ChromeLog
            Chromatography Log object, containing family information and the
            data to display.
        """
        family_name = log.family.name
        plot_context = self.plot_contexts.get(family_name)
        if plot_context is None:
            return

        self._remove_log_from_plot_context(plot_context, log, prefix=prefix)

        # Remove Plot objects that have no logs.
        if len(plot_context.plots) == 0:
            self.remove_log_family(family_name)

    def remove_log_family(self, family_name):
        """ Remove the family of logs grouped under `family_name`.
        """
        if not self.remove_empty_plot:
            plot_context = self.plot_contexts.get(family_name)
            if plot_context is None:
                return
            # clear all the renderers in the plot but leave the plot_context
            # in the container
            plot_context.delplot(*plot_context.plots.keys())
        else:
            plot_context = self.plot_contexts.pop(family_name, None)
            if plot_context is None:
                return
            # remove the plot_context from the container
            self.container.components.remove(plot_context)

    def refresh_container(self, force=False):
        if force:
            self.container.invalidate_and_redraw()
        else:
            self.container.request_redraw()

    # ChromatogramPlot private methods ------------------------------------

    def _remove_log_from_plot_context(self, plot_context, log, prefix):
        """ Request to remove a specific log from a plot context.
        """
        plot_name = self._get_unique_plot_name_for_log(prefix, log)
        if plot_name in plot_context.plots:
            plot_context.delplot(plot_name)

        # remove the data for the logs from the plot data object
        x_name = "{}_x".format(plot_name)
        y_name = "{}_y".format(plot_name)
        plot_data = plot_context.data
        plot_data_keys = plot_data.list_data()
        for key in [x_name, y_name]:
            if key in plot_data_keys:
                plot_data.del_data(key)

        if self._legend:
            self._legend.labels.remove(plot_name)

    def _add_log_to_plot_context(self, plot_context, log, prefix):
        """ Request to add a specific log to a plot context.
        """
        plot_name = self._get_unique_plot_name_for_log(prefix, log)
        x_name = "{}_x".format(plot_name)
        y_name = "{}_y".format(plot_name)
        plot_data = plot_context.data

        # check if the names are duplicate
        data_exists = (isinstance(plot_data.get_data(x_name), np.ndarray) or
                       isinstance(plot_data.get_data(y_name), np.ndarray))
        if data_exists:
            return

        plot_data.set_data(x_name, log.x_data)
        plot_data.set_data(y_name, log.y_data)

        # NOTE: depending on the type of data, we might have different
        # kinds of plots (e.g. log_book). This can be handled by passing
        # the appropriate renderer name in renderer_properties (key `type`).
        # Any new renderers, will need to be added to the list of known
        # renderers when creating the plot_context
        rend_props = log.renderer_properties
        plot_context.plot((x_name, y_name), name=plot_name, **rend_props)
        # Make sure the legend doesn't shuffle its entries
        if self._legend:
            self._legend.labels.append(plot_name)

    def _get_or_create_plot_context(self, log):
        """ Retrieve Plot for specific log type if exists, create  it otherwise
        """
        # get the family name for the log
        name = log.family.name

        # if a Plot exists for the requested `name` then just return it
        plot_context = self.plot_contexts.get(name)
        if plot_context is not None:
            return plot_context

        container_properties = log.family.plot_container_properties
        plot_context = build_new_plot_context(container_properties)

        if log.family.name == LOG_FAMILY_UV:
            self._configure_legend(plot_context, log)

        # Make all plots in the plot container have a common x-axis range
        if self.all_plots_index_range is None:
            self.all_plots_index_range = plot_context.index_range
        else:
            plot_context.index_range = self.all_plots_index_range

        # add to container and to the local cache and return
        self.plot_contexts[name] = plot_context
        self.container.add(plot_context)
        return plot_context

    def _configure_legend(self, plot, log):
        """ Initialize legend properties.
        """
        self._legend = plot.legend
        container_props = log.family.plot_container_properties
        legend_props = container_props['legend']
        self._legend.set(**legend_props)

        # add a highlighter tool, to allow turing on/off individual curves
        self._legend_tool = LegendHighlighter(component=self._legend)
        self._legend.tools.insert(LEGEND_TOOL_LOC, self._legend_tool)

    def show_legend(self):
        self._legend.tools.insert(LEGEND_TOOL_LOC, self._legend_tool)
        self._legend.visible = True
        self.plot_contexts[LOG_FAMILY_UV].request_redraw()

    def hide_legend(self):
        """ Hide the legend and disable its highighting tool to avoid mouse
        interactions.
        """
        self._legend.visible = False
        self._legend.tools.pop(LEGEND_TOOL_LOC)
        self.plot_contexts[LOG_FAMILY_UV].request_redraw()

    def _create_container(self):
        self.container = container = ConstraintsPlotContainer(
            bgcolor='transparent',
            padding_top=0,
            padding_bottom=5,
            padding_left=10,
            padding_right=5
        )
        container.layout_constraints = self._get_layout

    def _get_layout(self, container):
        """ Returns a list of constraits that is meant to be passed to
        a ConstraintsContainer.
        """
        constraints = []

        # NOTE: inequality expressions seem a lil shaky in that it requires
        # some tweaking to finding a set of constraints that works well !
        # But this is much better than manually tweaking padding etc.

        # Another option is to simply calculate the values of the height etc
        # and set it as simple inequalities (as opposed to using height as
        # another variable in the expressions)

        # FIXME: also, the layouts can prob. be specified as input similar to
        # the other plot properties.

        uv_comp = self.plot_contexts.get(LOG_FAMILY_UV)
        if uv_comp is not None:
            # uv_comp should exist in container.components
            assert(uv_comp in container.components)
            # NOTE:
            # 1. `>` doesent work but `>=` works !
            # 2. adding both >= and <= breaks if `contents_height` is specified
            # but works if integer values are specified
            constraints.append(
                uv_comp.layout_height >= 0.4 * container.contents_height
            )

        # split components into groups. For now, just UV and others
        other_components = [_comp for _comp in container.components
                            if _comp is not uv_comp]

        for plot in other_components:
            # FIXME: just setting `<=` constraint results in plot not showing
            # up *if* its the only plot in the container
            # need to figure out the appropriate layout helper function here
            # constraints.append(
            #     plot.layout_height <= 0.2 * container.contents_height
            # )
            # constraints.append(
            #     plot.layout_height >= 10
            # )
            pass

        # NOTE: looks like every comp in the container needs a constraint,
        # else they get messed up or ignored.

        # create an ordered (top to bottom) list of components
        sorted_components = [uv_comp] + other_components
        constraints.extend([
            # all components are in a vertical box
            vbox(*sorted_components, spacing=50, margins=50),
            # align widths of all components to be the same
            align('layout_width', *sorted_components),
            # align heights of *other* components to be the same
            align('layout_height', *other_components),
        ])
        return constraints

    def _get_unique_plot_name_for_log(self, prefix, log):
        return "{}: {}".format(prefix, log.name)


def build_new_plot_context(container_properties):
    """ Build an empty chaco Plot to display data, using provided props.

    Note that this builds an empty Plot or Container. See
    add_chrome_log and remove_chrome_log for adding/removing line plots in it.

    Parameters
    ----------
    container_properties : dict
        Properties to display the
    """
    # create a new empty Plot object and initialize defaults.
    context_props = container_properties['plot_context']
    plot_context = Plot(ArrayPlotData(), **context_props)

    # adding zoom and pan tools to the plot
    zoom = BetterSelectingZoom(component=plot_context, tool_mode="box",
                               always_on=False)
    plot_context.overlays.append(zoom)
    plot_context.tools.append(PanTool(component=plot_context))

    # configure axes
    axes_factory_props = container_properties['axes_factory']
    add_default_axes(plot_context, **axes_factory_props)

    # If necessary, add a secondary axis:
    context_props2 = container_properties.get('plot_context2', None)
    if context_props2:
        plot_context2 = Plot(ArrayPlotData(), **context_props2)

    second_axes_factory_props = container_properties.get('second_axes_factory',
                                                         None)
    if second_axes_factory_props:
        add_sharedx_axes(plot_context2, **second_axes_factory_props)

    # Add a tool to track mouse location
    short_x_axis_title = axes_factory_props['htitle'].split()[0]
    short_y_axis_title = axes_factory_props['vtitle'].split()[0]

    def message_for_data(coords):
        """ Convert a data coordinate into a message for the text overlay
        of the inspector tool.
        """
        msg = "{}: {:.3f}, {}: {:.3f}"
        msg = msg.format(short_x_axis_title, coords[0],
                         short_y_axis_title, coords[1])
        return msg

    add_data_inspector(plot_context, message_for_data=message_for_data,
                       include_overlay=True)
    return plot_context


def add_sharedx_axes(plot, orientation="normal", vtitle="", htitle="",
                     axis_class=PlotAxis):
    """
    Creates left and bottom axes for a plot.  Assumes that the index is
    horizontal and value is vertical by default; set *orientation* to
    something other than "normal" if they are flipped.
    """
    if orientation in ("normal", "h"):
        v_mapper = plot.value_mapper
        h_mapper = plot.index_mapper
    else:
        v_mapper = plot.index_mapper
        h_mapper = plot.value_mapper

    right = axis_class(orientation='right',
                       title=vtitle,
                       mapper=v_mapper,
                       component=plot)

    bottom = axis_class(orientation='bottom',
                        title=htitle,
                        mapper=h_mapper,
                        component=plot)

    plot.underlays.append(right)
    plot.underlays.append(bottom)
    return right, bottom
