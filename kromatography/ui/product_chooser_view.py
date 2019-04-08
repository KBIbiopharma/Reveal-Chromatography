from traits.api import HasStrictTraits, Instance, Property, Str
from traitsui.api import EnumEditor, Item, OKCancelButtons, View

from kromatography.model.data_source import DataSource


class ProductChooser(HasStrictTraits):
    """ Small modal UI to select a product from the ones contained in the
    provided Datasource.
    """

    datasource = Instance(DataSource)

    selected_product_name = Str

    selected_product = Property(depends_on="selected_product_name")

    def traits_view(self):
        if self.datasource is None:
            raise ValueError("A DataSource is needed since products must be "
                             "selected from there.")

        all_products = self.datasource.get_object_names_by_type("products")
        all_products = sorted(all_products)

        view = View(
            Item(
                "selected_product_name", label="Product Name",
                editor=EnumEditor(values=all_products)
            ),
            buttons=OKCancelButtons, title="Select a target product",
            width=300, resizable=True,
        )
        return view

    def _get_selected_product(self):
        prod = self.datasource.get_object_of_type("products",
                                                  self.selected_product_name)
        return prod.clone_traits(copy="deep")
