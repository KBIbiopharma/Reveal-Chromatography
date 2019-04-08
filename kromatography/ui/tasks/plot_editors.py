from abc import abstractmethod

from traits.api import Any, Instance, Property, Str
from traitsui.api import UI
from pyface.tasks.api import Editor

from kromatography.plotting.data_models import ChromatogramModel
from kromatography.ui.chromatogram_model_view import ChromatogramModelView
from kromatography.plotting.animation_plot import AnimationPlot
from kromatography.ui.animation_plot_view import AnimationPlotView


class PlotEditor(Editor):
    """ Interface for a plot editor.

    Subclasses should specify the plot_model in `obj`, and implement
    the `_create_control` method
    """

    traits_ui = Instance(UI)

    # -------------------------------------------------------------------------
    # 'Editor' interface
    # -------------------------------------------------------------------------

    # The editor's user-visible name.
    name = Property(Str, depends_on="obj")

    # The tooltip to show for the editor's tab, if any.
    tooltip = Property(Str, depends_on="obj")

    # The toolkit-specific control that represents the editor.
    control = Any

    # -------------------------------------------------------------------------
    # 'Editor' interface methods
    # -------------------------------------------------------------------------

    def create(self, parent):
        """ Create and set the toolkit-specific control that represents the
        editor.
        """
        self.control = self._create_control(parent)

    # -------------------------------------------------------------------------
    # Traits property methods
    # -------------------------------------------------------------------------

    def _get_name(self):
        return "Plot: {0:5s}".format(self.obj.name)

    def _get_tooltip(self):
        return "Plot: {0}".format(self.obj.name)

    # -------------------------------------------------------------------------
    # Private interface.
    # -------------------------------------------------------------------------

    @abstractmethod
    def _create_control(self, parent):
        """ Creates the view and then toolkit-specific control for the widget.
        """


class ChromatogramPlotEditor(PlotEditor):
    """ Editor for viewing and modifying a ChromatogramModel object using the
    TraitsUI view it provides. It invokes the view factories it knows to create
    the control it needs to display.

    This could have been done using pyface.tasks.traits_editor.TraitsEditor.
    Using this custom one because the create method in our case will invoke
    edit_traits on the obj being edited.
    """

    # The object that the editor is editing.
    obj = Instance(ChromatogramModel)

    #: The obj adapter to build a ModelView
    obj_view = Any

    # -------------------------------------------------------------------------
    # Private interface.
    # -------------------------------------------------------------------------

    def _create_control(self, parent):
        """ Creates the view and then toolkit-specific control for the widget.
        """
        self.obj_view = ChromatogramModelView(chromatogram_model=self.obj)

        # Setting the kind and the parent allows for the ui to be embedded
        # within the parent UI
        self.traits_ui = self.obj_view.edit_traits(kind="subpanel",
                                                   parent=parent)

        # Grab the Qt widget to return to the editor area
        control = self.traits_ui.control
        return control


class AnimationPlotEditor(PlotEditor):
    """ Editor for viewing and modifying a AnimationPlotModel object using the
    TraitsUI view it provides. It invokes the view factories it knows to create
    the control it needs to display.

    This could have been done using pyface.tasks.traits_editor.TraitsEditor.
    Using this custom one because the create method in our case will invoke
    edit_traits on the obj being edited.
    """

    # The object that the editor is editing.
    obj = Instance(AnimationPlot)

    # -------------------------------------------------------------------------
    # Private interface.
    # -------------------------------------------------------------------------

    def _create_control(self, parent):
        """ Creates the view and then toolkit-specific control for the widget.
        """
        # build view for the object
        view = AnimationPlotView(model=self.obj)

        # Setting the kind and the parent allows for the ui to be embedded
        # within the parent UI
        self.traits_ui = view.edit_traits(kind="subpanel", parent=parent)

        # Grab the Qt widget to return to the editor area
        control = self.traits_ui.control
        return control
