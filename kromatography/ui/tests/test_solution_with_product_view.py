from unittest import TestCase

from app_common.apptools.testing_utils import \
    reraise_traits_notification_exceptions

from kromatography.model.tests.example_model_data import \
    SOLUTIONWITHPRODUCT_LOAD, SOLUTIONWITHPRODUCT_LOAD_WITH_STRIP
from kromatography.model.solution_with_product import SolutionWithProduct
from kromatography.ui.tests.base_model_view_test_case import \
    BaseModelViewTestCase
from kromatography.ui.solution_with_product_view import SolutionWithProductView


class TestSolutionWithProductView(BaseModelViewTestCase, TestCase):
    """ Tests for a SolutionWithProduct model.
    """

    def setUp(self):
        BaseModelViewTestCase.setUp(self)

        self.model = SolutionWithProduct(**SOLUTIONWITHPRODUCT_LOAD)

    def test_change_chemical_component_list(self):
        view = self._get_model_view()
        original = self.model.chemical_components
        try:
            self.assertEqual(len(view.chemical_components), 3)
            self.assertEqual(len(self.model.chemical_components), 3)
            with reraise_traits_notification_exceptions():
                view.chemical_components = view.chemical_components[1:]

            self.assertEqual(len(self.model.chemical_components), 2)

            with reraise_traits_notification_exceptions():
                view.chemical_components = []

            self.assertEqual(len(self.model.chemical_components), 0)

        finally:
            # Reset to initial value
            self.model.chemical_components = original

    def test_change_model_chem_components(self):
        view = self._get_model_view()
        self.assertEqual(len(self.model.chemical_components), 3)
        with reraise_traits_notification_exceptions():
            self.model.chemical_components = self.model.chemical_components[1:]

        # The view doesn't change from model changes until the
        # update_chemical_components is explicitely called:
        self.assertEqual(len(view.chemical_components), 3)
        view.update_chemical_components()
        self.assertEqual(len(view.chemical_components), 2)

    def test_change_product_assays_list(self):
        view = self._get_model_view()
        original = view.product_assays
        try:
            self.assertEqual(len(view.product_assays), 3)
            self.assertEqual(len(self.model.product_component_assay_values), 3)
            with reraise_traits_notification_exceptions():
                view.product_assays = view.product_assays[1:]

            self.assertEqual(len(self.model.product_component_assay_values), 2)

            with reraise_traits_notification_exceptions():
                view.product_assays = []

            self.assertEqual(len(self.model.product_component_assay_values), 0)

        finally:
            # Reset to make ready for next steps
            view.product_assays = original

    def test_change_model_assays(self):
        view = self._get_model_view()
        original = view.product_assays
        try:
            self.assertEqual(len(self.model.product_component_assay_values), 3)
            self.assertEqual(len(view.product_assays), 3)
            with reraise_traits_notification_exceptions():
                self.model.product_component_assay_values = \
                    self.model.product_component_assay_values[1:]

            # The view doesn't change from model changes until the
            # update_chemical_components is explicitely called:
            self.assertEqual(len(view.product_assays), 3)
            view.update_product_assays()
            self.assertEqual(len(view.product_assays), 2)
        finally:
            view.product_assays = original

    def test_has_strip(self):
        # Default model doesn't contain strip assay
        view = self._get_model_view()
        self.assertFalse(view._has_strip)

        model = SolutionWithProduct(**SOLUTIONWITHPRODUCT_LOAD_WITH_STRIP)
        view = SolutionWithProductView(model=model, datasource=self.ds)
        self.assertTrue(view._has_strip)

    # Utilities ---------------------------------------------------------------

    def _get_model_view(self):
        return SolutionWithProductView(model=self.model, datasource=self.ds)
