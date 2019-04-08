from unittest import TestCase

from app_common.traits.assertion_utils import assert_has_traits_almost_equal

from kromatography.model.data_source import DataSourceLookupError
from kromatography.model.tests.sample_data_factories import make_sample_study
from kromatography.ui.tests.base_model_view_test_case import \
    BaseModelViewTestCase


class TestStudyView(BaseModelViewTestCase, TestCase):
    """ Run all BaseModelViewTestCase tests for a study model.
    """

    def setUp(self):
        # Register all views
        BaseModelViewTestCase.setUp(self)

        # This could be the manual creation of an instance of the ChromData to
        # represent.
        self.model = make_sample_study()

    def test_get_set_product_name(self):
        view = self._get_model_view()
        self.assertEqual(view.product_name, 'NO PRODUCT SET')
        with self.assertRaises(DataSourceLookupError):
            view.product_name = 'Foo'

        desired_prod = 'Prod001'
        view.product_name = desired_prod
        self.assertEqual(view.product_name, desired_prod)
        prod = self.ds.get_object_of_type('products', desired_prod)
        assert_has_traits_almost_equal(self.model.product, prod)
