from traits.api import Instance
from traitsui.api import Item, ModelView, OKCancelButtons, View

from app_common.traitsui.unit_scalar_editor import \
    UnitScalarEditor
from kromatography.model.resin import Resin


class ResinView(ModelView):
    """ View for a Resin model.
    """
    model = Instance(Resin)

    def default_traits_view(self):
        view = View(
            Item("model.name", label="Resin Name"),
            Item("model.resin_type", label="Resin Type"),
            Item("model.lot_id", label="Resin Lot ID"),
            Item("model.average_bead_diameter", label="Avg. Bead Diameter",
                 editor=UnitScalarEditor()),
            Item("model.ligand_density", label="Ligand Density",
                 editor=UnitScalarEditor()),
            Item("model.settled_porosity", label="Settled Porosity",
                 editor=UnitScalarEditor()),

            # Relevant when used as standalone view:
            resizable=True, buttons=OKCancelButtons,
            title="Configure component"
        )
        return view


if __name__ == '__main__':
    from kromatography.model.tests.sample_data_factories import \
        make_sample_experiment

    # Build a model you want to visualize:
    experiment = make_sample_experiment()
    resin = experiment.column.resin

    # Build its model view, passing the model as a model
    # and make a window for it:
    resin_view = ResinView(model=resin)
    resin_view.configure_traits()
