import os
from unittest import TestCase

from app_common.apptools.testing_utils import temp_fname

from kromatography.model.tests.sample_data_factories import \
    make_sample_binding_model_optimizer, make_sample_brute_force_optimizer
from kromatography.ui.tests.base_model_view_test_case import \
    BaseModelViewTestCase
from kromatography.compute.brute_force_optimizer_step import \
    ALL_COST_COL_NAME
from kromatography.ui.brute_force_optimizer_model_view import INVERTED_SUFFIX


class BaseBruteForceOptimizerViewTest(object):
    def test_export_data_event(self):
        fname_name = "testfile_TestBindingModelOptimizerView.csv"

        with temp_fname(fname_name) as fname_path:
            model_view = self._get_model_view()
            model_view.do_export_data(fname_name)
            found = os.listdir(os.path.dirname(fname_path))
            self.assertIn(fname_name, found)

    def test_export_data_event_bad_extension(self):
        fname_name = "testfile_TestBindingModelOptimizerView.blah"
        expected_fname = fname_name + ".csv"

        with temp_fname(fname_name) as fname_path:
            with temp_fname(expected_fname):
                model_view = self._get_model_view()
                model_view.do_export_data(fname_name)
                found = os.listdir(os.path.dirname(fname_path))
                self.assertNotIn(fname_name, found)
                self.assertIn(expected_fname, found)

    def test_sort_by_initial(self):
        view = self._get_model_view()
        # Even with empty cost_data, sort_by is already set correctly
        self.assertEqual(view.sort_by, ALL_COST_COL_NAME)
        expected = self.model.cost_data_cols
        expected += [val + INVERTED_SUFFIX for val in expected]
        self.assertEqual(set(view.sort_by_possible), set(expected))

        # Same default when data is present
        self.model.cost_data.loc[0, :] = [0, 0, 0]
        self.model.cost_data.loc[1, :] = [1, 1, 1]
        view = self._get_model_view()
        self.assertEqual(view.sort_by, ALL_COST_COL_NAME)

    def test_sort_cost_data(self):
        # Same default when data is present
        self.model.cost_data.loc[0, :] = [1, 1, 0]
        self.model.cost_data.loc[1, :] = [1, 1, 1]
        self.model.cost_data.loc[2, :] = [1, 1, 2]
        self.model.cost_data.loc[3, :] = [1, 1, 3]
        std_index = range(self.num_value**2)
        self.assertEqual(list(self.model.cost_data.index), std_index)
        self.assertEqual(list(self.model.cost_data[ALL_COST_COL_NAME]),
                         std_index)

        view = self._get_model_view()
        view.sort_by = ALL_COST_COL_NAME + INVERTED_SUFFIX
        self.assertEqual(list(self.model.cost_data.index), std_index[::-1])
        self.assertEqual(list(self.model.cost_data[ALL_COST_COL_NAME]),
                         std_index[::-1])


class TestBruteForceBindingModelOptimizerView(BaseModelViewTestCase, TestCase,
                                              BaseBruteForceOptimizerViewTest):
    """ Run all BaseModelViewTestCase tests for a binding model optimizer.
    """
    def setUp(self):
        # Register all views
        BaseModelViewTestCase.setUp(self)

        self.num_value = 2
        self.model = make_sample_binding_model_optimizer(
            num_values=self.num_value, with_data=True
        )


class TestBruteForceOptimizerView(BaseModelViewTestCase, TestCase,
                                  BaseBruteForceOptimizerViewTest):
    """ Run all BaseModelViewTestCase tests for general brute force optimizer.
    """
    def setUp(self):
        # Register all views
        BaseModelViewTestCase.setUp(self)

        self.num_value = 2
        self.model = make_sample_brute_force_optimizer(
            num_values=self.num_value, with_data=True
        )
