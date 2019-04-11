from unittest import TestCase

from kromatography.ui.tests.base_model_view_test_case import \
    BaseModelViewTestCase


class TestProductView(BaseModelViewTestCase, TestCase):
    """ Run all BaseModelViewTestCase + special tests for a Column view.
    """

    def setUp(self):
        # This registers all views defined in kromatography/ui/adapters/api.py
        BaseModelViewTestCase.setUp(self)

        self.model = self.ds.get_object_of_type('products', 'Prod001')
