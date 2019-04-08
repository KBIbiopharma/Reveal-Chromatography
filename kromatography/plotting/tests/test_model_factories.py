from unittest import TestCase
import numpy as np
from numpy.testing import assert_array_almost_equal

from kromatography.utils.testing_utils import \
    load_default_experiment_simulation, load_study_with_exps_and_ran_sims
from kromatography.plotting.model_factories import \
    build_chrome_log_collection_from_simulation, build_chromatogram_model

from kromatography.io.reader_writer import load_object
from kromatography.utils.testing_utils import io_data_path
from kromatography.model.simulation_group import SimulationGroup
from kromatography.plotting.data_models import ChromeLog


class TestModelFactoriesCollectionContent(TestCase):

    @classmethod
    def setUpClass(cls):
        cls.study = load_study_with_exps_and_ran_sims()

    def test_build_chrome_log_from_sim(self):
        _, simulation = load_default_experiment_simulation()
        sim_log = build_chrome_log_collection_from_simulation(simulation)
        chrom_logs = sim_log.logs.keys()
        expected = {'cation', 'Total_Sim', 'Acidic_1_Sim', 'Acidic_2_Sim',
                    'Native_Sim'}
        self.assertSetEqual(set(chrom_logs), expected)

    def test_build_chromatogram_model_exps(self):
        study = self.study
        exp = study.experiments[0]
        model_data = build_chromatogram_model(study, expts=[exp])
        # If building a plot with an experiment, sims built from them are added
        # too:
        expected = {'Run_1', 'Sim: Run_1'}
        self.assertSetEqual(set(model_data.log_collections.keys()), expected)

    def test_build_chromatogram_model_sims(self):
        study = self.study
        sim = study.simulations[0]
        model_data = build_chromatogram_model(study,
                                              sims=[sim])
        # If building a plot with a sim, its source experiments is added too:
        expected = {'Run_1', 'Sim: Run_1'}
        self.assertSetEqual(set(model_data.log_collections.keys()), expected)

    def test_build_chromatogram_model_default(self):
        study = self.study
        model_data = build_chromatogram_model(study)
        expected = {'Run_1', 'Sim: Run_1', 'Run_2 (no data)', 'Sim: Run_2'}
        self.assertSetEqual(set(model_data.log_collections.keys()), expected)
        run_1_logs = model_data.log_collections['Run_1'].logs
        expected = {
            'Run_1_Expt pH',
            'Sum comp. fractions',
            'Acidic_1',
            'Native',
            'Run_1_Expt UV',
            'Acidic_2',
            'Run_1_Expt Conductivity',
        }
        self.assertSetEqual(set(run_1_logs.keys()), expected)
        run_2_logs = model_data.log_collections['Run_2 (no data)'].logs
        self.assertEqual(run_2_logs, {})

    def test_build_chromatogram_model_sim_no_data(self):
        from kromatography.model.factories.simulation import \
            build_simulation_from_experiment

        study = self.study
        # Make a second simulation from Run_1:
        exp = study.search_experiment_by_name("Run_1")
        new_sim = build_simulation_from_experiment(exp, name="Sim2: Run_1")
        study.simulations.append(new_sim)
        model_data = build_chromatogram_model(study)

        # New sim not there because no data:
        self.assertIsNone(new_sim.output)
        self.assertNotIn("Sim2: Run_1", model_data.log_collections.keys())

    def test_chromatogram_colors_default(self):
        study = self.study
        # Make a second simulation from Run_1:
        sim = self.study.simulations[0]
        new_sim = sim.copy()
        new_sim.name = "Sim2: Run_1"
        new_sim.output = sim.output
        study.simulations.append(new_sim)
        model_data = build_chromatogram_model(study)

        # Colors are constant for all plots of a given experiment:
        run_1_logs = model_data.log_collections["Run_1"].logs.values()
        exp_colors = [log.renderer_properties["color"] for log in run_1_logs]
        for color in exp_colors:
            self.assertEqual(color, exp_colors[0])

        # Sim from experiment has same color as experiment:
        sim_1_logs = model_data.log_collections["Sim: Run_1"].logs.values()
        colors1 = [log.renderer_properties["color"] for log in sim_1_logs]
        for color in colors1:
            self.assertEqual(color, colors1[0])

        self.assertEqual(exp_colors[0], colors1[0])

        # Other sim from experiment has same color as experiment:
        sim_2_logs = model_data.log_collections["Sim2: Run_1"].logs.values()
        colors2 = [log.renderer_properties["color"] for log in sim_2_logs]
        for color in colors2:
            self.assertEqual(color, colors2[0])

        self.assertEqual(exp_colors[0], colors2[0])

        sim_3_logs = model_data.log_collections["Sim: Run_2"].logs.values()
        colors3 = [log.renderer_properties["color"] for log in sim_3_logs]
        for color in colors3:
            self.assertEqual(color, colors3[0])

        self.assertNotEqual(exp_colors[0], colors3[0])

    def test_fail_when_request_sim_and_exp(self):
        study = self.study
        exp = study.experiments[0]
        sim = study.simulations[0]
        with self.assertRaises(ValueError):
            build_chromatogram_model(study, expts=[exp], sims=[sim])

    def test_fail_when_request_sim_and_sim_group(self):
        # prepare the grid
        study = self.study
        sim = study.simulations[0]
        grid = SimulationGroup(name="SG", simulations=[sim])
        with self.assertRaises(ValueError):
            build_chromatogram_model(self.study, sims=[sim], sim_group=grid)


class TestModelFactoriesLogsContent(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.study = load_study_with_exps_and_ran_sims()
        cls.exp = cls.study.experiments[0]

    def test_expt_logs_content_nature(self):
        model_data = build_chromatogram_model(self.study, expts=[self.exp])
        collection = model_data.log_collections['Run_1']
        for key, log in collection.logs.items():
            self.assertIsInstance(log, ChromeLog)
            self.assertIsInstance(log.x_data, np.ndarray)
            self.assertIsInstance(log.y_data, np.ndarray)

        datasets = [("Run_1_Expt pH", "pH"),
                    ("Run_1_Expt Conductivity", 'conductivity')]
        for log_name, cont_data_name in datasets:
            log = collection.logs[log_name]
            source_data = self.exp.output.continuous_data[cont_data_name]
            assert_log_equal_source_data(log, source_data)

        for data_name in self.exp.output.fraction_data.keys():
            log = collection.logs[data_name]
            source_data = self.exp.output.fraction_data[data_name]
            assert_log_equal_source_data(log, source_data)

        # Custom handling for UV since it applies a factor:
        log = collection.logs["Run_1_Expt UV"]
        source_data = self.exp.output.continuous_data['uv']
        assert_array_almost_equal(log.x_data, source_data.x_data)
        # Plot applies a unit conversion factor:
        factor = 1000. * self.exp.system.abs_path_length[()]
        assert_array_almost_equal(log.y_data, source_data.y_data/factor)


class TestModelFactoriesSimFromScratch(TestCase):
    @classmethod
    def setUpClass(cls):
        stored_study = io_data_path(
            "std_study_with_run_sim_from_scratch.chrom"
        )
        cls.study, _ = load_object(stored_study)

    def test_build_chromatogram_model_sims_from_scratch(self):
        """ Sims from scratch have None as their source_experiment: make sure
        that doesn't break building a plot.
        """
        study = self.study
        sim = study.simulations[0]
        model_data = build_chromatogram_model(self.study,
                                              sims=[sim])
        self.assertEqual(model_data.log_collections.keys(), ["SimFromScratch"])

    def test_build_chromatogram_model_sim_group_from_scratch(self):
        """ Sims from scratch have None as their source_experiment: make sure
        that doesn't break building a plot.
        """
        # prepare the grid
        grid = self.study.analysis_tools.simulation_grids[0]
        sim = self.study.search_simulation_by_name('SimFromScratch')
        grid.simulations.append(sim)
        model_data = build_chromatogram_model(self.study, sim_group=grid)
        self.assertEqual(model_data.log_collections.keys(), ["SimFromScratch"])


# Assertion utilities ---------------------------------------------------------


def assert_log_equal_source_data(log, source_data):
    assert_array_almost_equal(log.x_data, source_data.x_data)
    assert_array_almost_equal(log.y_data, source_data.y_data)
