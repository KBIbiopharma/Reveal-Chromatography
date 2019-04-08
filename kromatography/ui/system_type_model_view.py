""" View for a SystemType.
"""
from traits.api import Instance, Property
from traitsui.api import HGroup, Item, ModelView, OKCancelButtons, VGroup, View
from scimath.units.api import UnitScalar

from app_common.traitsui.unit_scalar_editor import UnitScalarEditor  # noqa
from kromatography.model.system import SystemType


class SystemTypeView(ModelView):
    """ View for a SystemTypeView
    """
    # -------------------------------------------------------------------------
    # ModelView interface
    # -------------------------------------------------------------------------

    model = Instance(SystemType)

    # -------------------------------------------------------------------------
    # SystemTypeView traits
    # -------------------------------------------------------------------------

    system_type_flow_range_min = Property(depends_on="model")
    system_type_flow_range_max = Property(depends_on="model")

    def default_traits_view(self):
        view = View(
            VGroup(
                Item("model.name"),
                Item("model.manufacturer",
                     label="Manufacturer"),
                Item("model.manufacturer_name",
                     label="Manufacturer Model"),
                Item("model.num_inlets",
                     label="Number of Inlets"),
                Item("model.num_channels",
                     label="Number of Channels"),
                HGroup(
                    Item("system_type_flow_range_min",
                         editor=UnitScalarEditor(),
                         label="Min Flow"),
                    Item("system_type_flow_range_max",
                         editor=UnitScalarEditor(),
                         label="Max Flow"),
                ),
                label="System Type", show_border=True,
            ),
            buttons=OKCancelButtons
        )
        return view

    # -------------------------------------------------------------------------
    # Traits interface
    # -------------------------------------------------------------------------

    def _get_system_type_flow_range_min(self):
        if self.model.flow_range is not None:
            range_units = self.model.flow_range.units
            flow_range_min = self.model.flow_range[0]
            return UnitScalar(flow_range_min, units=range_units)

    def _get_system_type_flow_range_max(self):
        if self.model.flow_range is not None:
            range_units = self.model.flow_range.units
            flow_range_max = self.model.flow_range[1]
            return UnitScalar(flow_range_max, units=range_units)

    def _set_system_type_flow_range_min(self, value):
        self.model.flow_range[0] = value

    def _set_system_type_flow_range_max(self, value):
        self.model.flow_range[1] = value


if __name__ == '__main__':
    from kromatography.model.tests.sample_data_factories import (
        make_sample_experiment
    )
    from kromatography.ui.api import register_all_data_views

    register_all_data_views()

    experiment = make_sample_experiment()
    model = experiment.system.system_type
    model_view = SystemTypeView(model=model)
    model_view.configure_traits()
