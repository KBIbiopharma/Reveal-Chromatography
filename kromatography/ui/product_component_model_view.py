from functools import partial

from traits.api import Bool, Instance, Property, Str
from traitsui.api import Item, ModelView, OKCancelButtons, TextEditor

from app_common.traitsui.unit_scalar_editor import UnitScalarEditor  # noqa
from kromatography.model.product import BAD_COMPONENT_NAMES
from kromatography.model.product_component import ProductComponent
from kromatography.utils.str_utils import is_string_valid_variable_name
from kromatography.utils.traitsui_utils import KromView

COMPONENT_NAME_TOOLTIP = "Case sensitive. Spaces, special characters and " \
                         "certain values not allowed."


VALID_COMP_NAME = partial(is_string_valid_variable_name, bad_char=" ,#",
                          bad_values=BAD_COMPONENT_NAMES.keys())


class ProductComponentView(ModelView):
    """ View for ProductComponent model.
    """
    model = Instance(ProductComponent)

    _invalid_name = Property(Bool, depends_on="model.name")

    name_editable = Bool(True)

    target_product_editable = Bool(True)

    title = Str("Configure Product Component")

    def default_traits_view(self):
        view = KromView(
            Item("model.name", tooltip=COMPONENT_NAME_TOOLTIP,
                 editor=TextEditor(invalid='_invalid_name'),
                 enabled_when='name_editable'),
            Item("model.target_product",
                 enabled_when="target_product_editable"),
            Item("model.extinction_coefficient", editor=UnitScalarEditor(),
                 width=200),
            Item("model.molecular_weight", editor=UnitScalarEditor(),
                 tooltip="Molecular weight of the component in kilo-Daltons "
                         "(1 kDa=1 kg/mol)"),

            # Relevant when used as standalone view:
            buttons=OKCancelButtons, title=self.title
        )

        return view

    def _get__invalid_name(self):
        """ Return whether the current user input for the model's name is valid
        """
        return not VALID_COMP_NAME(self.model.name)


if __name__ == '__main__':
    from kromatography.model.tests.example_model_data import \
        ACIDIC_1_PRODUCT_COMPONENT_DATA

    model = ProductComponent(**ACIDIC_1_PRODUCT_COMPONENT_DATA)

    model_view = ProductComponentView(model=model)
    model_view.configure_traits()
