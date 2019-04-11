import logging

from traits.api import Bool, Instance, HasStrictTraits, List, Property, Str
from traitsui.api import EnumEditor, InstanceEditor, Item, ModelView, \
    OKCancelButtons, Tabbed, VGroup, View

from kromatography.model.data_source import DataSource
from app_common.traitsui.unit_scalar_editor import UnitScalarEditor  # noqa
from kromatography.model.system import System, SystemType
from kromatography.ui.system_type_model_view import SystemTypeView

logger = logging.getLogger(__name__)


class SystemView(ModelView):
    """ View for a System model.
    """

    # -------------------------------------------------------------------------
    # ModelView interface
    # -------------------------------------------------------------------------

    #: Model being edited
    model = Instance(System)

    #: Multi-study datasource
    datasource = Instance(DataSource)

    # Since we have a custom view for this part of the model, we need to build
    # it to display as part of the system view to support creating new systems
    # from scratch.
    _system_type_view = Instance(SystemTypeView)

    #: Allow editing of the system type?
    _allow_type_editing = Bool(True)

    def default_traits_view(self):
        view = View(
            Tabbed(
                VGroup(
                    Item("model.name", label="System Name"),
                    Item("model.system_number", label="System ID"),
                    Item("model.abs_path_length", editor=UnitScalarEditor(),
                         label="Absorbance Detector Path Length"),
                    Item("model.holdup_volume", editor=UnitScalarEditor()),
                    label="System in use"
                ),
                VGroup(
                    Item("_system_type_view", editor=InstanceEditor(),
                         style="custom", show_label=False,
                         enabled_when="_allow_type_editing"),
                    label="System type"
                ),
            ),
            buttons=OKCancelButtons
        )

        return view

    def __system_type_view_default(self):
        return SystemTypeView(model=self.model.system_type)


class SystemTypeSelector(HasStrictTraits):
    """ Utility view to select a SystemType among the existing ones.
    """

    #: Multi-study datasource to find all available system types
    datasource = Instance(DataSource)

    #: Selected system type name
    system_type_name = Str

    #: Selected system type
    selected_system_type = Property(Instance(SystemType),
                                    depends_on='system_type_name')

    #: List of available system type names
    _system_type_names = Property(List(Str), depends_on="datasource")

    def default_traits_view(self):
        view = View(Item("system_type_name",
                         editor=EnumEditor(values=self._system_type_names)),
                    buttons=OKCancelButtons,
                    title="Select the system type")
        return view

    def _get__system_type_names(self):
        return self.datasource.get_object_names_by_type("system_types")

    def _get_selected_system_type(self):
        return self.datasource.get_object_of_type("system_types",
                                                  self.system_type_name)


if __name__ == '__main__':
    from kromatography.model.tests.sample_data_factories import (
        make_sample_experiment
    )
    from kromatography.ui.api import register_all_data_views

    register_all_data_views()

    experiment = make_sample_experiment()
    model = experiment.system
    model_view = SystemView(model=model)
    model_view.configure_traits()
