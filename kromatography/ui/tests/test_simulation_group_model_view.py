from unittest import TestCase
import os

from traits.testing.unittest_tools import UnittestTools

from pybleau.app.api import DataFrameAnalyzer, DataFrameAnalyzerView
from app_common.apptools.testing_utils import temp_bringup_ui_for, temp_fname

from kromatography.model.tests.sample_data_factories import \
    make_sample_simulation_group
from kromatography.ui.tests.base_model_view_test_case import \
    BaseModelViewTestCase
from kromatography.model.simulation_group import PERF_PARAMS, \
    PURITY_PERF_PREFIX, SIM_COL_NAME
from kromatography.ui.simulation_group_model_view import INVERTED_SUFFIX


class TestSimulationGroupView(BaseModelViewTestCase, TestCase, UnittestTools):
    """ Run all BaseModelViewTestCase tests for a Simulation group model.
    """

    def setUp(self):
        # Register all views
        BaseModelViewTestCase.setUp(self)

        # This could be the manual creation of an instance of the ChromData to
        # represent.
        self.model = make_sample_simulation_group()

    def test_sort_data(self):
        view = self._get_model_view()
        scanned_param = 'binding_model.sma_ka[1]'
        expected = [SIM_COL_NAME, scanned_param] + PERF_PARAMS.keys()
        cp = self.model.center_point_simulation
        comps = cp.product.product_component_names
        expected += ["{} {} (%)".format(PURITY_PERF_PREFIX, comp)
                     for comp in comps]
        expected += [param + INVERTED_SUFFIX for param in expected]
        self.assertEqual(set(view.sort_by_possible), set(expected))

        # Sorting should change the model
        with self.assertTraitChanges(self.model, 'group_data', 1):
            view.sort_by = SIM_COL_NAME + INVERTED_SUFFIX

        # Sorting should trigger the update event that the uI listen to:
        with self.assertTraitChanges(self.model, 'group_data_updated_event', 1):  # noqa
            view.sort_by = SIM_COL_NAME

        # Sorting on the same variable shouldn't trigger updates:
        with self.assertTraitChanges(self.model, 'group_data_updated_event', 0):  # noqa
            view.sort_by = SIM_COL_NAME

    def test_export_data_event(self):
        fname_name = "testfile_TestSimGroupView.csv"

        with temp_fname(fname_name) as fname_path:
            model_view = self._get_model_view()
            model_view.do_export_data(fname_name)
            found = os.listdir(os.path.dirname(fname_path))
            self.assertIn(fname_name, found)

    def test_export_data_event_bad_extension(self):
        fname_name = "testfile_TestSimGroupView.blah"
        expected_fname = fname_name + ".csv"

        with temp_fname(fname_name) as fname_path:
            with temp_fname(expected_fname):
                model_view = self._get_model_view()
                model_view.do_export_data(fname_name)
                found = os.listdir(os.path.dirname(fname_path))
                self.assertNotIn(fname_name, found)
                self.assertIn(expected_fname, found)


class TestGroupDataDFAnalyzer(TestCase):
    def setUp(self):
        self.model = make_sample_simulation_group()

    def test_bringup_df_analyzer_view(self):
        model = DataFrameAnalyzer(source_df=self.model.group_data)
        view = DataFrameAnalyzerView(model=model, include_plotter=True)
        with temp_bringup_ui_for(view):
            pass

    def test_data_columns_df_analyzer(self):
        model = DataFrameAnalyzer(source_df=self.model.group_data)
        # Make sure a copy is made
        self.assertIsNot(model.source_df, self.model.group_data)
        # Make sure that the columns were modified to be valid variable names:
        expected_cols = ["Simulation_name", "binding_model_sma_ka_1",
                         "pool_concentration_g_L", "pool_volume_CV",
                         "purity_Acidic_1", "purity_Acidic_2", "purity_Native",
                         "step_yield"]
        self.assertEqual(expected_cols, model.source_df.columns.tolist())
