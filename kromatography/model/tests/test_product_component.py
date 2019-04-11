""" Tests for the Product Component Class. """
from unittest import TestCase

from kromatography.model.product_component import ProductComponent
from kromatography.model.tests.example_model_data import \
    ACIDIC_1_PRODUCT_COMPONENT_DATA


class TestProductComponent(TestCase):

    def setUp(self):
        self.product_component = ProductComponent(
            **ACIDIC_1_PRODUCT_COMPONENT_DATA
        )
        self.target_product = ACIDIC_1_PRODUCT_COMPONENT_DATA['target_product']

    # -------------------------------------------------------------------------
    # Tests
    # -------------------------------------------------------------------------
    def test_invalid_construction(self):
        with self.assertRaises(ValueError):
            self.product_component = ProductComponent()

    def test_construction(self):
        product_component = self.product_component
        for key, value in ACIDIC_1_PRODUCT_COMPONENT_DATA.iteritems():
            self.assertEqual(getattr(product_component, key), value, msg=key)

        expected_id = {'target_product': self.target_product,
                       'name': product_component.name}
        self.assertEqual(product_component.unique_id, expected_id)
