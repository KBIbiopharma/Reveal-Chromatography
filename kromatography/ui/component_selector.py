
from traits.api import Bool, HasStrictTraits, Instance, List, Str
from traitsui.api import Item, ListStrEditor, OKCancelButtons

from kromatography.model.product import Product
from kromatography.utils.traitsui_utils import KromView
from kromatography.utils.string_definitions import STRIP_COMP_NAME


class ComponentSelector(HasStrictTraits):
    """ Class to support select a set of experiments from a study
    """
    product = Instance(Product)

    ignore_strip_by_default = Bool(True)

    component_selected = List(Str)

    component_name_available = List(Str)

    view = KromView(
        Item("component_name_available",
             editor=ListStrEditor(
                title='Component List',
                selected="component_selected",
                multi_select=True,
                editable=False
             ),
             show_label=False),
        buttons=OKCancelButtons,
        title="Select components"
    )

    # Traits listener methods -------------------------------------------------

    def _product_changed(self):
        self.component_name_available = \
            self._component_name_available_default()
        self.component_selected = self._component_selected_default()

    # Traits initialization methods -------------------------------------------

    def _component_selected_default(self):
        ignore = []
        if self.ignore_strip_by_default:
            ignore.append(STRIP_COMP_NAME)

        return [name for name in self.component_name_available
                if name not in ignore]

    def _component_name_available_default(self):
        if self.product is None:
            return []

        return self.product.product_component_names


if __name__ == "__main__":
    from kromatography.model.tests.sample_data_factories import \
        make_sample_simulation

    prod = make_sample_simulation().product
    ComponentSelector(product=prod).configure_traits()
