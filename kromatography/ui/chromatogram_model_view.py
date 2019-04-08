from enable.api import ColorTrait, ComponentEditor
from traits.api import Bool, Button, Dict, HasTraits, Instance, Int, List, \
    Property, on_trait_change, Str
from traitsui.api import CheckListEditor, Group, HGroup, Item, Label, \
    OKCancelButtons, Spring, UItem, VGroup

from kromatography.utils.traitsui_utils import KromView
from kromatography.plotting.api import ChromatogramPlot, ChromatogramModel
from kromatography.utils.string_definitions import LOG_FAMILY_UV, \
    LOG_FAMILY_CATION, LOG_FAMILY_PH

LOG_FAMILY_DISPLAY_ORDER = [LOG_FAMILY_UV, LOG_FAMILY_CATION, LOG_FAMILY_PH]


class ChromatogramModelView(HasTraits):
    """ The view class for a ChromatogramModel model.
    """

    # -------------------------------------------------------------------------
    # ChromatogramModelView interface
    # -------------------------------------------------------------------------

    #: Model containing chromatography data in appropriate units.
    chromatogram_model = Instance(ChromatogramModel)

    #: Names for log collections (experiments/simulations) used in the plot.
    displayed_log_collection_names = List()

    #: Launcher for editor tool to control collection colors
    color_editor = Button("Edit plot styles")

    #: Simulations originating from the same experiment colored like the exp?
    disconnected_plots = Bool(False)

    #: The names for the log families ('UV' / 'Cond' etc.) to be plotted.
    displayed_log_family_names = List()

    #: Open all UV curves on plot creation?
    open_uv_on_open = Bool(True)

    #: Control to select/unselect all experiments/simulations to be displayed
    select_all_collections = Bool(True)

    # -------------------------------------------------------------------------
    # Private interface
    # -------------------------------------------------------------------------

    #: Control to display/hide the chaco plot legend
    _show_legend = Bool(True)

    #: Control to display hide the plot controls
    _show_control = Bool(True)

    #: Min width of the Chaco plot part of the view
    _plot_width = Int

    #: The list of all available log collections.
    _all_log_collection_names = Property(List, depends_on='chromatogram_model')

    #: The list of all available log families.
    _all_log_family_names = Property(List, depends_on='chromatogram_model')

    #: The container (ConstraintsPlotContainer) displaying the plots.
    _container = Property(depends_on='_chromatogram_plot')

    #: Instance of ChromatogramPlot used by editor to display the plots.
    _chromatogram_plot = Instance(ChromatogramPlot)

    def __init__(self, **traits):
        super(ChromatogramModelView, self).__init__(**traits)

        # Initialize the plot with all UV curves if requested
        if self.open_uv_on_open:
            self.displayed_log_family_names = [LOG_FAMILY_UV]
            self.add_all_uv_curves()

    def default_traits_view(self):
        view = KromView(
            HGroup(
                VGroup(
                    Group(
                        Item("select_all_collections", label="All"),
                        UItem('displayed_log_collection_names',
                              editor=CheckListEditor(
                                values=self._all_log_collection_names),
                              style='custom'),
                        HGroup(
                            UItem("color_editor"),
                        ),
                        label='Experiments/Simulations',
                        show_border=True,
                    ),
                    Group(
                        UItem('displayed_log_family_names',
                              editor=CheckListEditor(
                                  values=self._all_log_family_names,
                                  format_func=lambda a: a),
                              style='custom'),
                        label='Plot Grouping', show_border=True,
                    ),
                    visible_when='_show_control'
                ),
                VGroup(
                    UItem('_container', editor=ComponentEditor(),
                          show_label=False),
                    show_border=True,
                ),
            ),
            title="Chromatogram Plot",
        )
        return view

    def add_all_uv_curves(self):
        """ Add to the ChromatogramPlot provided all logs that contain UV
        data by initializing the displayed_log_collection_names list.
        """
        displayed_log_collection_names = set()
        model = self.chromatogram_model
        for coll_name in model.log_collections:
            if coll_name.find("no data") == -1:
                displayed_log_collection_names.add(coll_name)

        self.displayed_log_collection_names = list(
            displayed_log_collection_names
        )

    # Trait property getters/setters ------------------------------------------

    def _get__all_log_collection_names(self):
        """ Initialize the list of possible collection names from their name.
        """
        return sorted(self.chromatogram_model.log_collections.keys())

    def _get__all_log_family_names(self):
        model = self.chromatogram_model
        available_log_families = {
            _log.family.name
            for _coll in model.log_collections.values()
            for _log in _coll.logs.values()
        }
        # Build the list of families showing the known (ordered ones) first
        ordered_families = []

        for family in LOG_FAMILY_DISPLAY_ORDER:
            if family in available_log_families:
                ordered_families.append(family)

        remaining_fam = available_log_families - set(LOG_FAMILY_DISPLAY_ORDER)
        ordered_families += list(remaining_fam)
        return ordered_families

    def _get__container(self):
        return self._chromatogram_plot.container

    # Trait listener methods --------------------------------------------------

    def _color_editor_fired(self):
        model = self.chromatogram_model
        editor = PlotColorEditor(collection_list=model.log_collections,
                                 disconnected_plots=self.disconnected_plots)
        ui = editor.edit_traits(kind="livemodal")
        if ui.result:
            self.apply_new_colors(editor.modified_colors)
            self.disconnected_plots = editor.disconnected_plots

    def apply_new_colors(self, modified_colors):
        """ Apply the colors selected by the editor.

        Parameters
        ----------
        modified_colors : dict
            Dictionary mapping collection names to the color to change to.
        """
        model = self.chromatogram_model
        # Modify the model...
        for name, new_color in modified_colors.items():
            collection = model.log_collections[name]
            for log in collection.logs.values():
                log.renderer_properties["color"] = new_color

        # and modify the renderer properties of the existing plots:
        chromatogram_plot = self._chromatogram_plot
        for family, plot in chromatogram_plot.plot_contexts.items():
            for renderer_name, renderer_list in plot.plots.items():
                collection_name = ":".join(renderer_name.split(":")[:-1])
                color = modified_colors.get(collection_name, None)
                if color is None:
                    # That collection wasn't modified
                    continue

                for renderer in renderer_list:
                    renderer.color = color

    @on_trait_change('displayed_log_collection_names[]', post_init=True)
    def _handle_update_to_log_collection_names(self, obj, name, old, new):
        """ Simulation/experiment selected have changed. Update the plot
        container.
        """
        # get the set of of new collections and the removed collections.
        old, new = set(old), set(new)
        added = new - old
        deleted = old - new

        model = self.chromatogram_model
        chromatogram_plot = self._chromatogram_plot

        # if a experiment/simulation is disabled/removed, remove all corr. logs
        for coll_name in deleted:
            logs = model.log_collections[coll_name].logs
            for log in logs.values():
                chromatogram_plot.remove_chrome_log(coll_name, log)

        # if a experiment/simulation is enabled/added, then add *selected* logs
        for coll_name in added:
            logs = model.log_collections[coll_name].logs
            for log in logs.values():
                if log.family.name not in self.displayed_log_family_names:
                    continue
                chromatogram_plot.add_chrome_log(coll_name, log)

        chromatogram_plot.refresh_container()

    @on_trait_change('displayed_log_family_names[]', post_init=True)
    def _handle_update_to_log_family_names(self, obj, name, old, new):
        """ Requested log family names changed. Redraw the plot.
        """
        old, new = set(old), set(new)
        added = new - old
        deleted = old - new

        model = self.chromatogram_model
        chromatogram_plot = self._chromatogram_plot

        for family_name in deleted:
            chromatogram_plot.remove_log_family(family_name)

        for family_name in added:
            # FIXME: move this into a chromatogram_plot.add_log_family method
            for coll_name in self.displayed_log_collection_names:
                logs = model.log_collections[coll_name].logs
                for log in logs.values():
                    if log.family.name != family_name:
                        continue
                    # NOTE: no need to check if this family should be displayed
                    # as we are iterating over the list of new/added family
                    # names and so they must be displayed.
                    chromatogram_plot.add_chrome_log(coll_name, log)

        chromatogram_plot.refresh_container()

    def _select_all_collections_changed(self, new):
        if new:
            self.add_all_uv_curves()
        else:
            self.displayed_log_collection_names = []

    def __show_legend_changed(self, new):
        if new:
            self._chromatogram_plot.show_legend()
        else:
            self._chromatogram_plot.hide_legend()

    # Trait initialization methods --------------------------------------------

    def __chromatogram_plot_default(self):
        plot = ChromatogramPlot()
        plot.init()
        return plot


class PlotColorEditor(HasTraits):
    """ Tool to edit the colors of the log collections.
    """
    #: Map of LogCollections that may be editable
    collection_list = Dict

    #: Maps the collection name to the trait storing its color
    collection_map = Dict

    #: Map the name of the collection to the user modified color attribute
    modified_colors = Dict

    #: Simulations originating from the same experiment colored like the exp?
    disconnected_plots = Bool(False)

    def default_traits_view(self):
        from app_common.traitsui.common_traitsui_groups import \
            make_window_title_group

        title = make_window_title_group("Select Plot Colors")
        msg = "By default, a simulation and the experiment it was built from "\
              "share the same color. Check the box to control the color of " \
              "all plots and\nun-check to keep simulation colors the same as" \
              " their source experiments."
        connected_colors = VGroup(
            Label(msg),
            HGroup(
                Spring(),
                Item("disconnected_plots", label="Control simulation colors")
            ),
            show_border=False
        )
        items = []
        for i, name in enumerate(self.collection_list):
            if name not in self.collection_map:
                continue

            always_visible = "plot_always_visible_{}".format(i)
            name_attr = "plot_name_{}".format(i)
            label = getattr(self, name_attr)
            items.append(
                Item("plot_color_{}".format(i), label=label,
                     visible_when="disconnected_plots or " + always_visible),
            )

        view = KromView(
            VGroup(
                title,
                connected_colors,
                VGroup(
                    *items,
                    show_border=True,
                    label="Experiments/Simulations"
                ),
            ),
            buttons=OKCancelButtons,
            title="Chromatogram Plot Styles",
            width=400
        )
        return view

    def __init__(self, **traits):
        super(PlotColorEditor, self).__init__(**traits)

        for i, (name, collection) in enumerate(self.collection_list.items()):
            # In case an experiment/simulation is loaded without data:
            if not collection.logs:
                continue

            # The color control will be always visible only if the collection
            # stems from an experiment
            visibility_trait = "plot_always_visible_{}".format(i)
            self.add_trait(visibility_trait, Bool)
            always_visible = collection.source_type == "experiment"
            self.trait_set(**{visibility_trait: always_visible})

            # Grab the current color
            props = collection.logs.values()[0].renderer_properties
            color = props["color"]

            # Create traits for the collection name and color
            color_trait = "plot_color_{}".format(i)
            self.add_trait(color_trait, ColorTrait(color))
            self.on_trait_change(self.color_modified, color_trait)
            self.add_trait("plot_name_{}".format(i), Str(name))

            # Connect the name to color trait for lookup
            self.collection_map[name] = color_trait

    def color_modified(self, name, new):
        """ Store the new colors for the modified collections.

        Also apply changes to connected collections.
        """
        i = name.split("_")[-1]
        name_trait = "plot_name_{}".format(i)
        collection_name = getattr(self, name_trait)
        self.modified_colors[collection_name] = new

        # Also apply changes to connected collections
        if not self.disconnected_plots:
            for collection in self.collection_list.values():
                if collection.source == collection_name:
                    self.modified_colors[collection.name] = new

    def _disconnected_plots_changed(self, new):
        """ If resetting to connected, change the name
        """
        if not new:
            for collection in self.collection_list.values():
                if not collection.logs or collection.source is None:
                    continue

                color_trait = self.collection_map[collection.source]
                color = getattr(self, color_trait)
                self.modified_colors[collection.name] = color
