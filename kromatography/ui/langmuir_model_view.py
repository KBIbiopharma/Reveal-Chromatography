
from traits.api import Instance
from traitsui.api import BooleanEditor, HGroup, Item, OKButton, \
    OKCancelButtons, Spring, TextEditor, VGroup

from kromatography.utils.traitsui_utils import KromView
from kromatography.model.binding_model import Langmuir
from kromatography.ui.base_model_view_with_component_array import \
    BaseModelViewWithComponentArray


class LangmuirView(BaseModelViewWithComponentArray):
    """ View for the Langmuir Model.
    """

    # -------------------------------------------------------------------------
    # ModelView Interface
    # -------------------------------------------------------------------------

    #: Model to display
    model = Instance(Langmuir)

    def default_traits_view(self):
        view = KromView(
            VGroup(
                HGroup(
                    Item("model.name",
                         editor=TextEditor(auto_set=True, enter_set=True)),
                    Spring(),
                    Item("model.model_type", style='readonly', label="Type"),
                    Spring(),
                    Item("model.target_product", style='readonly')
                ),
                VGroup(
                    Item("model.is_kinetic", label="Is Kinetic",
                         editor=BooleanEditor()),
                    VGroup(
                        Item("component_array", label="Comp. Coeff.",
                             show_label=False, editor=self._tabular_editor),
                    ),
                    label="Parameters", show_border=True,
                ),
            ),
            # Relevant when used as standalone view:
            resizable=True, buttons=OKCancelButtons,
            default_button=OKButton,
            title="Configure {} model".format(self.model.model_type)
        )
        return view

    def _vector_attributes_default(self):
        return ['mcl_ka', 'mcl_kd', 'mcl_qmax']


if __name__ == '__main__':

    # Create Product for passing component names
    from kromatography.model.tests.example_model_data import PRODUCT_DATA, \
        Prod001_comp1, Prod001_comp2, Prod001_comp3
    from kromatography.model.product import Product

    product_components = [Prod001_comp1, Prod001_comp2, Prod001_comp3]
    prod = Product(product_components=product_components, **PRODUCT_DATA)

    # Build a model you want to visualize:
    model = Langmuir(len(prod.product_component_names),
                     component_names=prod.product_component_names)

    # Build model view, passing the model as a model and make a window for it:
    model_view = LangmuirView(model=model)
    model_view.configure_traits()
