from unittest import TestCase
from os.path import dirname, join
import numpy as np

import kromatography
from kromatography.io.study import load_study_from_excel
from kromatography.model.study import Experiment, Study
from kromatography.model.data_source import SimpleDataSource
from kromatography.data_release.data_source_content import DATA_CATALOG
from kromatography.utils.string_definitions import FRACTION_TOTAL_DATA_KEY

CONTINUOUS_KEYS = {'temperature', 'uv', 'flow', 'log_book', 'fraction',
                   'concentration', 'pH', 'conductivity'}
FRACTION_KEYS = {FRACTION_TOTAL_DATA_KEY, 'Acidic_2', 'Acidic_1', 'Native'}


def tutorial_data_path(fname):
    return join(dirname(kromatography.__file__), "data", "tutorial_data",
                fname)


class BaseTestLoadInputFiles(object):

    def test_read_input_files_with_internal_ds(self):
        ds = SimpleDataSource()
        # Make sure that's the internal datasource
        self.assertGreater(len(ds.products), 5)
        study = load_study_from_excel(self.tutorial_file, datasource=ds,
                                      allow_gui=False)
        self.assert_valid_tutorial_study(study)

    def test_read_input_files_with_release_ds(self):
        ds = SimpleDataSource.from_data_catalog(DATA_CATALOG)
        # Make sure that's the external datasource
        self.assertEqual(len(ds.products), 3)
        study = load_study_from_excel(self.tutorial_file, datasource=ds,
                                      allow_gui=False)
        self.assert_valid_tutorial_study(study)

    # Helper methods ----------------------------------------------------------

    def assert_valid_tutorial_study(self, study):
        self.assertIsInstance(study, Study)
        self.assertEqual(len(study.experiments), self.num_exp)
        exp = study.search_experiment_by_name(self.exp_name_to_analyze)
        self.assertIsInstance(exp, Experiment)
        self.assertIsNotNone(exp.output)
        self.assertEqual(set(exp.output.continuous_data.keys()),
                         self.cont_data)
        self.assertEqual(set(exp.output.fraction_data.keys()), self.frac_keys)


class TestExampleInputFilesProd000(BaseTestLoadInputFiles, TestCase):

    def setUp(self):
        self.tutorial_file = tutorial_data_path(
            "Example_Gradient_Elution_Study.xlsx"
        )
        self.num_exp = 3
        self.exp_name_to_analyze = "Run_1"
        self.cont_data = CONTINUOUS_KEYS
        self.comp_names = {'Native', 'Acidic_2', 'Acidic_1'}
        self.frac_keys = {FRACTION_TOTAL_DATA_KEY}.union(self.comp_names)

    # Helper methods ----------------------------------------------------------

    def assert_valid_tutorial_study(self, study):
        super(TestExampleInputFilesProd000, self).assert_valid_tutorial_study(
            study
        )
        exp = study.search_experiment_by_name(self.exp_name_to_analyze)
        average_uv = exp.output.continuous_data['uv'].y_data.mean()
        self.assertAlmostEqual(average_uv, 37.4494618, places=5)
        average_ph = np.nanmean(exp.output.continuous_data['pH'].y_data)
        self.assertAlmostEqual(average_ph, 5.959824, places=5)


class TestExampleInputFilesProd001(BaseTestLoadInputFiles, TestCase):

    def setUp(self):
        self.tutorial_file = tutorial_data_path(
            "PROD001_Example_Gradient_Elution_Study.xlsx"
        )
        self.num_exp = 2
        self.exp_name_to_analyze = '8.4CV'
        self.cont_data = CONTINUOUS_KEYS - {"temperature"}
        self.comp_names = {'Main_Peak_D', 'Pre_Peak_B', 'Post_Peak_E',
                           'Pre_Peak_C', 'Pre_Peak_A'}
        self.frac_keys = {FRACTION_TOTAL_DATA_KEY}.union(self.comp_names)


class TestExampleInputFilesProd001Pulse(BaseTestLoadInputFiles, TestCase):

    def setUp(self):
        self.tutorial_file = tutorial_data_path(
            "PROD001_Example_Pulse_Injection_Study.xlsx"
        )
        self.num_exp = 6
        self.exp_name_to_analyze = 'Run_1'
        self.cont_data = {'conductivity', 'PulseInjection_Inject', 'pH', 'uv',
                          'flow', 'log_book', 'PulseInjection_Pressure'}
        self.frac_keys = set([])
