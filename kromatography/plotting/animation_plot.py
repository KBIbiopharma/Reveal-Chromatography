""" Build the chaco version of the animation plot, that is 3 contour plots
displaying the concentration of one of the product components in the column
liquid phase, in the bead liquid phase and in the bead-bound phase.
"""

from traits.api import Any, HasStrictTraits, Dict, Str, Int, Instance, Property
from chaco.api import ArrayPlotData, HPlotContainer, Plot, jet, ColorBar, \
    LinearMapper

from kromatography.plotting.animation_data import \
    _build_animation_data_from_sim, AnimationData
from kromatography.ui.simulation_selector import RanSimulationChooser


# Styling dictionary for the 3 Chaco contour plots and colorbar

COLUMN_CONC_PLOT_ARRAY_NAMES = ('columnliqX', 'columnliqY', 'z_column_liquid',
                                'levelsliq')

COLUMN_CONC_PLOT_STYLE_DICT = {
    '': {
        'type': 'poly',
        'poly_cmap': jet,
        'title': 'Column Liquid Phase',
    },
    'x_axis': {
        'title': 'Column X Position (cm)',
    },
    'y_axis': {
        'title': 'Column Depth Position (cm)'
    }
}

LIQ_CONC_PLOT_ARRAY_NAMES = ('beadX', 'beadY', 'z_bead_liquid', 'levelsliq')

LIQ_CONC_PLOT_STYLE_DICT = {
    '': {
        'type': 'poly',
        'poly_cmap': jet,
        'title': 'Bead Pores Liquid Phase',
    },
    'x_axis': {
        'title': 'Bead Position (um)',
    },
    'y_axis': {
        'tick_visible': False,
        'tick_label_formatter': lambda x: '',
    }
}
BOUND_CONC_PLOT_ARRAY_NAMES = ('beadX', 'beadY', 'z_bead_bound', 'levelsbound')

BOUND_CONC_PLOT_STYLE_DICT = {
    '': {
        'type': 'poly',
        'poly_cmap': jet,
        'title': 'Bead Pores Bound Phase',
    },
    'x_axis': {
        'title': 'Bead Position (um)',
    },
    'y_axis': {
        'tick_visible': False,
        'tick_label_formatter': lambda x: '',
    }
}

LIQ_CONC_COLOR_BAR_STYLE_DICT = {
    '': {
        'orientation': 'v',
        'resizable': 'v',
        'width': 30,
        'padding': 20,
        'padding_top': 50,
        'padding_bottom': 50,
        'padding_right': 0
    },
    '_axis': {
        'title': 'Liquid Concentration (g/L)',
        'orientation': 'left'
    }
}

BOUND_CONC_COLOR_BAR_STYLE_DICT = {
    '': {
        'orientation': 'v',
        'resizable': 'v',
        'width': 30,
        'padding': 20,
        'padding_top': 50,
        'padding_bottom': 50,
        'padding_right': 0
    },
    '_axis': {
        'title': 'Bound Concentration (g/L)',
        'orientation': 'left'
    }
}


# Smallest number a Chaco image plot can display
EPS = 1e-14


class AnimationPlot(HasStrictTraits):
    """ The plot model for the particle data for each product component in
    a given simulation
    """

    #: Container for the plots
    plot = Instance(HPlotContainer)

    #: the product component whose particle simulation data is currently viewed
    product_component = Str

    #: the index of the time dimension currently being plotted
    time_slice = Int(0)

    #: The particle simulation data for each product component
    all_data = Dict(Str, AnimationData)

    #: The current particle simulation data active
    active_anim_data = Property(Instance(AnimationData),
                                depends_on='product_component')

    #: the data currently being plotted in `plot`
    plot_data = Instance(ArrayPlotData)

    #: Name of the simulation from which the data is displayed
    simulation_name = Str

    #: Colorbar object for the liquid concentration plot
    _colorbar_liquid = Any

    #: Colorbar object for the liquid concentration plot
    _colorbar_bound = Any

    #: name of the plot
    name = Str('Column Animation')

    def __init__(self, **traits):
        super(AnimationPlot, self).__init__(**traits)

        # Negative concentrations are non-physical: clip at 0.
        for anim_data in self.all_data.values():
            anim_data.columnliqZ.clip(min=EPS, out=anim_data.columnliqZ)
            anim_data.beadliqZ.clip(min=EPS, out=anim_data.beadliqZ)
            anim_data.beadboundZ.clip(min=EPS, out=anim_data.beadboundZ)

    def _product_component_default(self):
        return self.all_data.keys()[0]

    def _plot_data_default(self):
        plot_data = ArrayPlotData(
            z_column_liquid=(
                self.active_anim_data.columnliqZ[:, :, self.time_slice]),
            z_bead_liquid=(
                self.active_anim_data.beadliqZ[:, :, self.time_slice]),
            z_bead_bound=(
                self.active_anim_data.beadboundZ[:, :, self.time_slice]))
        return plot_data

    def _get_active_anim_data(self):
        return self.all_data[self.product_component]

    def _reset_plot_data(self):
        self.plot_data.set_data(
            "z_column_liquid",
            self.active_anim_data.columnliqZ[:, :, self.time_slice])
        self.plot_data.set_data(
            "z_bead_liquid",
            self.active_anim_data.beadliqZ[:, :, self.time_slice])
        self.plot_data.set_data(
            "z_bead_bound",
            self.active_anim_data.beadboundZ[:, :, self.time_slice])

    def _product_component_changed(self):
        self._reset_plot_data()
        self.plot = self.regenerate_plots(including_colorbar=True)

    def _time_slice_changed(self):
        self._reset_plot_data()
        # Due to the colormapper's range being fixed now, this call must be
        # explicit:
        self.plot.request_redraw()

    def _plot_default(self):
        container = self.regenerate_plots(including_colorbar=True)
        return container

    def contour_plot_from_data(self, anim_data, array_names, style_dict=None):
        """ Returns the Container of contour plot corresponding to the
        array data in anim_data w.r.t. arraynames

        Parameters
        ----------
        anim_data: AnimationData
            Animation data to plot as a contour plot.

        array_names: 4-tuple of strings
            Attr names in anim_data which will be (x,y,z, levels) arrays for
            the contour plot.

        style_dict: dict
            Dictionary of extra stylings to set, currently allowing up to one
            level of nesting of attributes (with '' key meaning no nesting).
        """
        plot = Plot(self.plot_data)
        x_name, y_name, z_name, levels_name = array_names
        xs = getattr(anim_data, x_name)
        xbounds = (min(xs), max(xs))
        ys = getattr(anim_data, y_name)
        ybounds = (min(ys), max(ys))
        levels = getattr(anim_data, levels_name).tolist()
        kwargs = style_dict.get('') if '' in style_dict else {}

        # Override the colormap's range with the full range of the data
        if style_dict is BOUND_CONC_PLOT_STYLE_DICT:
            data_max = self.active_anim_data.beadboundZ.max()
        else:
            data_max = self.active_anim_data.columnliqZ.max()

        contour_plot = plot.contour_plot(
            z_name, xbounds=xbounds, ybounds=ybounds, levels=levels, **kwargs
        )[0]

        # Overwrite the colormapper range to be set by the full data, not just
        # the 1 time slice currently plotted:
        contour_plot.color_mapper.range.set_bounds(EPS, data_max)
        contour_plot.color_mapper.updated = True

        # Adjust plot style for any remaining attrs
        for attr_name, attr_styles in style_dict.items():
            if attr_name == '':
                continue
            attr = getattr(plot, attr_name)
            for attr_attr_name, attr_attr_val in attr_styles.items():
                setattr(attr, attr_attr_name, attr_attr_val)

        return plot

    def _color_bar_gen(self, plot, style_dict):
        """Returns a ColorBar with given style_dict settings

        Parameters
        ----------
        style_dict: dict
            dictionary of extra stylings to set, currently allowing up to one
            level of nesting of attributes (with '' key meaning no nesting)
        """
        renderer = plot.plots["plot0"][0]
        colormap = renderer.color_mapper
        style_dict['']['index_mapper'] = LinearMapper(range=colormap.range)
        style_dict['']['color_mapper'] = colormap
        style_dict['']['plot'] = renderer

        kwargs = style_dict.get('')
        color_bar = ColorBar(**kwargs)
        # adjust color bar for rest of the attrs
        for attr_name, attr_styles in style_dict.items():
            if attr_name == '':
                continue
            attr = getattr(color_bar, attr_name)
            for attr_attr_name, attr_attr_val in attr_styles.items():
                setattr(attr, attr_attr_name, attr_attr_val)
        return color_bar

    def regenerate_plots(self, including_colorbar=False):
        """Function to regenerate entire plot (because many parts of each
        renderer must be updated when product_component or time slice changes)
        """
        active_anim_data = self.active_anim_data

        # first plot
        column_conc_plot = self.contour_plot_from_data(
            active_anim_data,
            COLUMN_CONC_PLOT_ARRAY_NAMES,
            style_dict=COLUMN_CONC_PLOT_STYLE_DICT)

        # second plot
        liq_conc_plot = self.contour_plot_from_data(
            active_anim_data,
            LIQ_CONC_PLOT_ARRAY_NAMES,
            style_dict=LIQ_CONC_PLOT_STYLE_DICT)

        # Add colorbar to plot 2
        if including_colorbar:
            self._colorbar_liquid = self._color_bar_gen(
                liq_conc_plot, LIQ_CONC_COLOR_BAR_STYLE_DICT
            )

        # third plot
        bound_conc_plot = self.contour_plot_from_data(
            active_anim_data,
            BOUND_CONC_PLOT_ARRAY_NAMES,
            style_dict=BOUND_CONC_PLOT_STYLE_DICT)

        # Add colorbar to plot 3
        if including_colorbar:
            self._colorbar_bound = self._color_bar_gen(
                bound_conc_plot, BOUND_CONC_COLOR_BAR_STYLE_DICT
            )

        container = HPlotContainer(
            column_conc_plot, self._colorbar_liquid, liq_conc_plot,
            self._colorbar_bound, bound_conc_plot
        )

        container.bgcolor = "transparent"
        return container

    def get_current_step_time(self):
        """ Returns the step name and the time (in min) of the currently
        selected time slice.
        """
        data = self.active_anim_data
        tot_time = data.times[self.time_slice]
        step = ""
        for ii, step_time in enumerate(data.step_start_times):
            if tot_time >= step_time:
                step = data.step_names[ii]
        return step, tot_time

    def _simulation_name_default(self):
        return self.active_anim_data.simulation_name


def build_animation_plot_model(study):
    """ Returns instance of AnimationPlot and UUID of source simulation.
    """
    # select a ran simulation
    sim_chooser = RanSimulationChooser(study=study)

    ui = sim_chooser.edit_traits(kind="modal")

    if ui.result:
        sim_name = sim_chooser.simulation_selected
        sim = study.search_simulation_by_name(sim_name)
        prod_comps = sim.product.product_component_names

        # generate plot model and return
        all_data = {prod_comps[i]: _build_animation_data_from_sim(sim, i)
                    for i in range(len(prod_comps))}

        return AnimationPlot(all_data=all_data), sim.uuid
