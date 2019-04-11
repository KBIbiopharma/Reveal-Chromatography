from unittest import TestCase

from kromatography.model.data_source import SimpleDataSource
from kromatography.data_release.data_source_content import DATA_CATALOG

ALL_RELEASED_PRODUCTS = {"Prod000", "Prod001", "Prod001_Pulse"}


class TestSimpleDataSourceRelease(TestCase):

    def setUp(self):
        self.ds = SimpleDataSource.from_data_catalog(data_catalog=DATA_CATALOG)

    def test_product_content(self):
        all_products = self.ds.get_object_names_by_type("products")
        self.assertEqual(set(all_products), ALL_RELEASED_PRODUCTS)

    def test_product_component_content(self):
        all_comps = self.ds.get_object_names_by_type("product_components")
        expected_comp_names = {"Acidic_1", "Acidic_2", "Native",
                               "Protein",
                               'Main_Peak_D', 'Post_Peak_E', 'Pre_Peak_A',
                               'Pre_Peak_B', 'Pre_Peak_C'}
        self.assertEqual(set(all_comps), expected_comp_names)

        target_prods = self.ds.get_object_names_by_type("product_components",
                                                        "target_product")
        self.assertEqual(set(target_prods), ALL_RELEASED_PRODUCTS)
