from traits.api import Instance
from traitsui.api import InstanceEditor, Item, ModelView, OKCancelButtons, \
    VGroup, View

from app_common.traitsui.unit_scalar_editor import (
    UnitScalarEditor
)
from kromatography.model.column import Column
from kromatography.ui.column_type_model_view import ColumnTypeView
from kromatography.ui.resin_model_view import ResinView


class ColumnView(ModelView):
    """ View for a Column model.

    FIXME: The Resin Name should be chosen from the set of resins available
    in the system.  The resin lot should be from a list of resin lots of the
    resin type.
    FIXME: If you are not loading any experiments, use a simplified default
    view, if an experiment has been loaded, then use a detailed view similar
    to the one below
    """

    # -------------------------------------------------------------------------
    # ModelView interface
    # -------------------------------------------------------------------------

    model = Instance(Column)

    resin_view = Instance(ResinView)

    column_type_view = Instance(ColumnTypeView)

    def default_traits_view(self):
        bed_height_actual_tooltip = ("Must be within the range set by the "
                                     "Column Type")
        bed_height_actual_label = "Bed Height"
        col_type_bed_height_set = (
            self.model.column_type is not None and
            self.model.column_type.bed_height_range is not None
        )
        if col_type_bed_height_set:
            height_range = self.model.column_type.bed_height_range.tolist()
            bed_height_actual_tooltip += ": {}.".format(height_range)

            # bed_height_units = self.model.column_type.bed_height_range.units
            # bed_height_actual_label += " ({})".format(bed_height_units.label)

        hetp_tooltip = "Height Equivalent to a Theoretical Plate (HETP)"
        compress_factor_tooltip = "Compression Factor (settled vol/packed vol)"

        view = View(
            VGroup(
                Item("model.name", label="Column Name"),
                Item("model.column_lot_id", label="Column Lot ID"),
                Item("model.bed_height_actual", label=bed_height_actual_label,
                     editor=UnitScalarEditor(),
                     tooltip=bed_height_actual_tooltip),
                Item("model.volume", editor=UnitScalarEditor(),
                     style="readonly"),
                Item("model.compress_factor", label="Compression Factor",
                     editor=UnitScalarEditor(),
                     tooltip=compress_factor_tooltip),
                Item("model.hetp", label="HETP",
                     editor=UnitScalarEditor(), tooltip=hetp_tooltip),
                Item("model.hetp_asymmetry", label="HETP Asymmetry",
                     editor=UnitScalarEditor()),
                label="Packed Column", show_border=True,
            ),
            VGroup(
                Item("column_type_view", editor=InstanceEditor(),
                     style="custom", show_label=False),
                label="Column Type", show_border=True,
            ),
            VGroup(
                Item("resin_view", editor=InstanceEditor(), style="custom",
                     show_label=False),
                label="Resin", show_border=True
            ),
            # Relevant when used as standalone view:
            resizable=True, buttons=OKCancelButtons,
            title="Configure column"
        )

        return view

    def _column_type_view_default(self):
        return ColumnTypeView(model=self.model.column_type)

    def _resin_view_default(self):
        return ResinView(self.model.resin)


if __name__ == '__main__':
    from kromatography.model.tests.sample_data_factories import \
        make_sample_experiment

    # Build a model you want to visualize:
    experiment = make_sample_experiment()
    column = experiment.column

    # Build its model view, passing the model as a model
    # and make a window for it:
    column_model_view = ColumnView(model=column)
    column_model_view.configure_traits()
