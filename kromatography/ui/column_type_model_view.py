from traits.api import Instance, Property
from scimath.units.api import UnitScalar
from traitsui.api import Item, ModelView, OKCancelButtons, VGroup, View

from app_common.traitsui.unit_scalar_editor import (
    UnitScalarEditor
)
from kromatography.model.column import ColumnType


class ColumnTypeView(ModelView):
    """ View for a ColumnType model.
    """

    # -------------------------------------------------------------------------
    # ColumModel traits
    # -------------------------------------------------------------------------

    column_type_bed_height_min = Property(depends_on="model")
    column_type_bed_height_max = Property(depends_on="model")

    # -------------------------------------------------------------------------
    # ModelView interface
    # -------------------------------------------------------------------------

    model = Instance(ColumnType)

    def default_traits_view(self):
        view = View(
            VGroup(
                Item("model.name", label="Column Model"),
                Item("model.manufacturer",
                     label="Column Manufacturer"),
                Item("model.manufacturer_name",
                     label="Manufacturer Model Number"),
                Item("model.diameter", label="Column Diameter",
                     editor=UnitScalarEditor()),
                Item("column_type_bed_height_min", editor=UnitScalarEditor(),
                     label="Min Bed Height"),
                Item("column_type_bed_height_max", editor=UnitScalarEditor(),
                     label="Max Bed Height"),
                Item("model.bed_height_adjust_method",
                     label="Bed Height Adjustment Method"),
            ),
            # Relevant when used as standalone view:
            resizable=True, buttons=OKCancelButtons,
            title="Configure Column Type"
        )
        return view

    # -------------------------------------------------------------------------
    # Traits interface
    # -------------------------------------------------------------------------

    def _get_column_type_bed_height_min(self):
        range_units = self.model.bed_height_range.units
        bed_height_min = self.model.bed_height_range[0]
        return UnitScalar(bed_height_min, units=range_units)

    def _get_column_type_bed_height_max(self):
        range_units = self.model.bed_height_range.units
        bed_height_max = self.model.bed_height_range[1]
        return UnitScalar(bed_height_max, units=range_units)

    def _set_column_type_bed_height_min(self, value):
        self.model.bed_height_range[0] = value

    def _set_column_type_bed_height_max(self, value):
        self.model.bed_height_range[1] = value


if __name__ == '__main__':
    from kromatography.model.tests.sample_data_factories import \
        make_sample_experiment

    # Build a model you want to visualize:
    experiment = make_sample_experiment()
    model = experiment.column.column_type

    # Build its model view, passing the model as a model
    # and make a window for it:
    column_model_view = ColumnTypeView(model=model)
    column_model_view.configure_traits()
