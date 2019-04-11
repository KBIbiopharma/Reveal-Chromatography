from traits.api import Instance
from traitsui.api import Item, ModelView, OKCancelButtons, View

from app_common.traitsui.unit_scalar_editor import UnitScalarEditor  # noqa
from kromatography.model.component import Component


class ComponentView(ModelView):
    """ View for Component model.
    """
    model = Instance(Component)

    def default_traits_view(self):
        pka_tooltip = ("Negative logarithm of the acidity constant of the "
                       "component")
        view = View(
            Item("model.name"),
            Item("model.charge", label="Charge",
                 editor=UnitScalarEditor()),
            Item("model.pKa", label="pKa", tooltip=pka_tooltip,
                 editor=UnitScalarEditor()),

            # Relevant when used as standalone view:
            resizable=True, buttons=OKCancelButtons,
            title="Configure component"
        )

        return view
