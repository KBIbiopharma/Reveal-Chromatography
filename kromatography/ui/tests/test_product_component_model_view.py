from unittest import TestCase

from kromatography.model.tests.example_model_data import \
    ACIDIC_1_PRODUCT_COMPONENT_DATA
from kromatography.model.product_component import ProductComponent
from kromatography.ui.tests.base_model_view_test_case import \
    BaseModelViewTestCase


class TestProductComponentView(BaseModelViewTestCase, TestCase):
    """ Run all BaseModelViewTestCase for a ProductComponent model
    """

    def setUp(self):
        # Register the views
        BaseModelViewTestCase.setUp(self)
        self.model = ProductComponent(**ACIDIC_1_PRODUCT_COMPONENT_DATA)

    def test_component_name_valid(self):
        view = self._get_model_view()
        self.model.name = "BLAH"
        self.assertFalse(view._invalid_name)

        self.model.name = "BAR"
        self.assertFalse(view._invalid_name)

    def test_component_name_invalid_bad_char(self):
        view = self._get_model_view()
        self.model.name = "BLAH,"
        self.assertTrue(view._invalid_name)

        self.model.name = "BAR#"
        self.assertTrue(view._invalid_name)

        self.model.name = "BAR."
        self.assertTrue(view._invalid_name)

        self.model.name = "1BAR"
        self.assertTrue(view._invalid_name)

    def test_component_name_invalid_bad_value(self):
        view = self._get_model_view()
        self.model.name = "Product"
        self.assertTrue(view._invalid_name)
