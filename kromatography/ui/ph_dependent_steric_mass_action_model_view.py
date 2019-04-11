
from traits.api import Instance

from kromatography.ui.steric_mass_action_model_view import \
    StericMassActionModelView
from kromatography.model.binding_model import PhDependentStericMassAction
from kromatography.utils.traitsui_utils import build_array_adapter


class PhDependentStericMassActionModelView(StericMassActionModelView):
    """ View for the pH-dependent Steric Mass Action Model.
    """
    #: SMA model to display
    model = Instance(PhDependentStericMassAction)

    # -------------------------------------------------------------------------
    # Traits interface
    # -------------------------------------------------------------------------

    def _vector_attributes_default(self):
        """ Note that the quadratic terms for nu and sigma are for now not
        exposed though they are available in the model.
        """
        return ['sma_ka', 'sma_ka_ph', 'sma_ka_ph2', 'sma_kd', 'sma_kd_ph',
                'sma_kd_ph2', 'sma_nu', 'sma_nu_ph', 'sma_sigma',
                'sma_sigma_ph']

    def __comp_array_adapter_default(self):
        index_name = 'Property name'
        column_names = self.model.component_names
        row_names = ['sma_ka0', 'sma_ka1', 'sma_ka2', 'sma_kd0', 'sma_kd1',
                     'sma_kd2', 'sma_nu0', 'sma_nu1', 'sma_sigma0',
                     'sma_sigma1']
        adapter = build_array_adapter(index_name, column_names, row_names)
        return adapter

    def _param_formula_str_default(self):
        param_formula = """The following parameters get combined into an effective SMA model according to:
        ka = 10^(sma_ka_0 + sma_ka_1 * pH + sma_ka_2 * pH^2)
        kd = 10^(sma_kd_0 + sma_kd_1 * pH + sma_kd_2 * pH^2)
        nu = sma_nu_0 + sma_nu_1 * pH
        sigma = sma_sigma_0 + sma_sigma_1 * pH
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
    sma = PhDependentStericMassAction(
        len(prod.product_component_names), name="test ph-dep SMA",
        component_names=prod.product_component_names
    )

    # Build model view, passing the model as a model and make a window for it:
    sma_model_view = PhDependentStericMassActionModelView(model=sma)
    sma_model_view.configure_traits()
