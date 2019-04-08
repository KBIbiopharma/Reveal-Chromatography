
from traits.api import Instance
from traitsui.api import HGroup, Item, OKButton, OKCancelButtons, Spring, \
    VGroup

from kromatography.utils.traitsui_utils import KromView
from app_common.traitsui.positive_float_editor import \
    PositiveFloatEditor
from kromatography.ui.base_model_view_with_component_array import \
    BaseModelViewWithComponentArray
from kromatography.model.transport_model import GeneralRateModel


class GeneralRateModelView(BaseModelViewWithComponentArray):
    """ View for the General Rate Model.
    """
    model = Instance(GeneralRateModel)

    def default_traits_view(self):
        view = KromView(
            VGroup(
                HGroup(
                    Item("model.name"),
                    Spring(),
                    Item("model.target_product", style='readonly'),
                ),
                VGroup(
                    HGroup(
                        Item("model.column_porosity", label="Column Porosity",
                             editor=PositiveFloatEditor()),
                        Item("model.bead_porosity", label="Bead Porosity",
                             editor=PositiveFloatEditor(),
                             tooltip="Protein bead porosity"),
                        label="Porosity", show_border=True
                    ),
                ),
                VGroup(
                    VGroup(
                        Item("model.axial_dispersion",
                             label="Axial Dispersion",
                             editor=PositiveFloatEditor()),
                    ),
                    VGroup(
                        Item("component_array", label="Comp. Coeff.",
                             show_label=False,
                             editor=self._tabular_editor),
                    ),
                    label="Transport Parameters", show_border=True,
                ),
            ),
            # Relevant when used as standalone view:
            resizable=True, buttons=OKCancelButtons,
            default_button=OKButton,
            title="Configure General Rate model"
        )
        return view

    def _vector_attributes_default(self):
        return ['film_mass_transfer', 'pore_diffusion', 'surface_diffusion']


if __name__ == '__main__':
    # Create Product for passing component names
    from kromatography.model.tests.example_model_data import PRODUCT_DATA
    from kromatography.model.product import Product
    prod = Product(**PRODUCT_DATA)

    # Build a model you want to visualize:
    grm = GeneralRateModel(len(prod.product_component_names),
                           component_names=prod.product_component_names)

    # Build model view, passing the model as a model and make a window for it:
    grm_model_view = GeneralRateModelView(model=grm)
    grm_model_view.configure_traits()
