from unittest import TestCase

from app_common.traits.assertion_utils import assert_has_traits_almost_equal

from kromatography.model.data_source import SimpleDataSource
from kromatography.ui.product_chooser_view import ProductChooser


class TestProductChooser(TestCase):

    def setUp(self):
        self.ds = SimpleDataSource()
        self.prod_chooser = ProductChooser(datasource=self.ds)

    def test_create_ui(self):
        ui = self.prod_chooser.edit_traits()
        ui.dispose()

    def test_selection(self):
        target_prod = self.ds.get_object_names_by_type("products")[0]
        self.prod_chooser.selected_product_name = target_prod

        expected = self.ds.get_object_of_type("products", target_prod)
        assert_has_traits_almost_equal(self.prod_chooser.selected_product,
                                       expected)
        assert(self.prod_chooser.selected_product is not expected)
