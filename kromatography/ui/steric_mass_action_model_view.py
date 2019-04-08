
from traits.api import Instance, Str
from traitsui.api import BooleanEditor, HGroup, Item, OKButton, \
    OKCancelButtons, Spring, TextEditor, VGroup

from app_common.traitsui.positive_float_editor import \
    PositiveFloatEditor
from kromatography.ui.base_model_view_with_component_array import \
    BaseModelViewWithComponentArray
from kromatography.model.binding_model import PH_STERIC_BINDING_MODEL, \
    StericMassAction
from kromatography.utils.traitsui_utils import KromView


class StericMassActionModelView(BaseModelViewWithComponentArray):
    """ View for the Steric Mass Action Model.
    """
    #: SMA model to display
    model = Instance(StericMassAction)

    #: Explanations for the component parameter table (if any)
    param_formula_str = Str

    def default_traits_view(self):
        visible_when_ph = "model.model_type == '{}'".format(
            PH_STERIC_BINDING_MODEL
        )

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
                    VGroup(
                        Item("model.is_kinetic", label="Is Kinetic",
                             editor=BooleanEditor()),
                        Item("model.sma_lambda", label="SMA Lambda",
                             editor=PositiveFloatEditor()),
                    ),
                    VGroup(
                        Item('param_formula_str', visible_when=visible_when_ph,
                             style="readonly", show_label=False),
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
        return ['sma_ka', 'sma_kd', 'sma_nu', 'sma_sigma']


if __name__ == '__main__':

    # Create Product for passing component names
    from kromatography.model.tests.example_model_data import PRODUCT_DATA, \
        Prod001_comp1, Prod001_comp2, Prod001_comp3
    from kromatography.model.product import Product

    product_components = [Prod001_comp1, Prod001_comp2, Prod001_comp3]
    prod = Product(product_components=product_components, **PRODUCT_DATA)

    # Build a model you want to visualize:
    sma = StericMassAction(len(prod.product_component_names), name="test SMA",
                           component_names=prod.product_component_names)

    # Build model view, passing the model as a model and make a window for it:
    sma_model_view = StericMassActionModelView(model=sma)
    sma_model_view.configure_traits()
