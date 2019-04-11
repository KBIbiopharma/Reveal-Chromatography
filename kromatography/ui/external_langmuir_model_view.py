
from traits.api import Instance, Str
from traitsui.api import BooleanEditor, HGroup, Item, OKButton, \
    OKCancelButtons, Spring, TextEditor, VGroup

from kromatography.utils.traitsui_utils import KromView
from kromatography.model.binding_model import ExternalLangmuir
from kromatography.ui.base_model_view_with_component_array import \
    BaseModelViewWithComponentArray
from kromatography.utils.traitsui_utils import build_array_adapter


class ExternalLangmuirView(BaseModelViewWithComponentArray):
    """ View for the External Langmuir Model.
    """
    # -------------------------------------------------------------------------
    # ModelView interface
    # -------------------------------------------------------------------------

    model = Instance(ExternalLangmuir)

    #: Explanations for the component parameter table (if any)
    param_formula_str = Str

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
                        Item('param_formula_str', style="readonly",
                             show_label=False),
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
        return ['mcl_ka', 'extl_ka_t', 'extl_ka_tt', 'extl_ka_ttt', 'mcl_kd',
                'extl_kd_t', 'extl_kd_tt', 'extl_kd_ttt', 'mcl_qmax',
                'extl_qmax_t', 'extl_qmax_tt', 'extl_qmax_ttt']

    def __comp_array_adapter_default(self):
        index_name = 'Property name'
        column_names = self.model.component_names
        row_names = ['ka0', 'ka1', 'ka2', 'ka3',
                     'kd0', 'kd1', 'kd2', 'kd3',
                     'qmax0', 'qmax1', 'qmax2', 'qmax3']
        adapter = build_array_adapter(index_name, column_names, row_names)
        return adapter

    def _param_formula_str_default(self):
        param_formula = """The following parameters get combined into an effective Langmuir model according to:
        ka(pH) = ka0 + ka1 * pH + ka2 * pH^2 + ka3 * pH^3
        kd(pH) = kd0 + kd1 * pH + kd2 * pH^2 + kd3 * pH^3
        qmax(pH) = qmax0 + qmax1 * pH + qmax2 * pH^2 + qmax3 * pH^3
"""  # noqa
        return param_formula


if __name__ == '__main__':

    # Create Product for passing component names
    from kromatography.model.tests.example_model_data import PRODUCT_DATA, \
        Prod001_comp1, Prod001_comp2, Prod001_comp3
    from kromatography.model.product import Product

    product_components = [Prod001_comp1, Prod001_comp2, Prod001_comp3]
    prod = Product(product_components=product_components, **PRODUCT_DATA)

    # Build a model you want to visualize:
    extl = ExternalLangmuir(len(prod.product_component_names),
                            component_names=prod.product_component_names)

    # Build model view, passing the model as a model and make a window for it:
    extl_model_view = ExternalLangmuirView(model=extl)
    extl_model_view.configure_traits()
