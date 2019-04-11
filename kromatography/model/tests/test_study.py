""" Tests for the Study class."""

from unittest import TestCase
import numpy as np
import pandas as pd

from traits.testing.unittest_tools import UnittestTools
from app_common.traits.assertion_utils import assert_has_traits_almost_equal

from kromatography.model.chromatography_results import ChromatographyResults
from kromatography.model.data_source import InStudyDataSource
from kromatography.model.product import BLANK_PRODUCT_NAME
from kromatography.model.simulation_group import SimulationGroup, \
    SingleParamSimulationDiff
from kromatography.model.study import add_sims_from_exp_to_study, \
    make_blank_study, SimulationNameCollisionError, Study
from kromatography.model.tests.base_study_test_case import BaseStudyTestCase
from kromatography.model.tests.example_model_data import STUDY_DATA
from kromatography.model.tests.sample_data_factories import \
    make_sample_experiment
from kromatography.model.tests.sample_data_factories import make_sample_study
from kromatography.model.tests.sample_data_factories import \
    make_sample_study2
from kromatography.utils.testing_utils import \
    load_default_experiment_simulation
from kromatography.model.factories.job_manager import create_start_job_manager


class TestStudy(TestCase, BaseStudyTestCase, UnittestTools):

    @classmethod
    def setUpClass(cls):
        cls.study2 = make_sample_study2(add_transp_bind_models=True)
        add_sims_from_exp_to_study(cls.study2, ['Run_1'],
                                   first_simulated_step_name="Load",
                                   last_simulated_step_name="Strip")
        cls.job_manager = create_start_job_manager(max_workers=2)

    @classmethod
    def tearDownClass(cls):
        cls.job_manager.shutdown()

    def setUp(self):
        BaseStudyTestCase.setUp(self)

        self.study_class = Study
        self.study = make_sample_study()
        self.constructor_data = STUDY_DATA

    def test_product(self):
        study = self.study
        self.assertEqual(study.product.name, BLANK_PRODUCT_NAME)

        # If we add an experiment with a product, the product changes
        experim1 = make_sample_experiment(name="Experim1")
        study.add_experiments(experim1)
        self.assertEqual(study.product, experim1.product)

        # If we add an experiment with no product, the product doesn't change
        experim2 = make_sample_experiment(name="Experim2")
        study.add_experiments(experim2)
        self.assertEqual(study.product, experim2.product)

    def test_study_datasource_from_adding_experiment(self):
        study = self.study
        ds = study.study_datasource

        # Initially the datasource is blank
        assert_has_traits_almost_equal(ds, InStudyDataSource(),
                                       ignore=["name"])
        experim1, _ = load_default_experiment_simulation(expt_id='Run_1')
        study.add_experiments(experim1)

        # Check that the method was collected
        self.assertEqual([experim1.method], ds.object_catalog["methods"])

        # Check that the solutions were collected
        solutions = []
        for step in experim1.method.method_steps:
            solutions += step.solutions
        for sol in solutions:
            found = (sol in ds.object_catalog["loads"] or
                     sol in ds.object_catalog["buffers"])
            assert found

        # Adding another times the same experiment doesn't change the :
        # object_catalog
        study.add_experiments(experim1)
        self.assertEqual([experim1.method], ds.object_catalog["methods"])

    def test_run_sim_group(self):
        study = self.study2
        cp = study.simulations[0]
        diff = (SingleParamSimulationDiff("binding_model.sma_ka[1]", 0.01),)
        group = SimulationGroup(center_point_simulation=cp,
                                name="foo", simulation_diffs=[diff])

        # Before running the group, the simulations have no results.
        assert not group.has_run
        for sim in group.simulations:
            self.assertIsNone(sim.output)
            assert not sim.has_run

        with self.assertTraitChanges(group, 'has_run', 1):
            study.run_simulation_group(self.job_manager, sim_group=group,
                                       wait=True)

        # Has run
        assert group.has_run
        for sim in group.simulations:
            self.assertIsInstance(sim.output, ChromatographyResults)
            assert sim.has_run

        df = group.group_data
        self.assertIsInstance(df, pd.DataFrame)
        self.assertEqual(df.shape, (1, 8))
        self.assertEqual(df.loc[0, "binding_model.sma_ka[1]"], 0.01)
        output_cols = ['pool_volume (CV)', 'pool_concentration (g/L)',
                       'step_yield (%)']
        self.assertFalse(np.any(np.isnan(df.loc[:, output_cols])))

    def test_search_simulation_by_name(self):
        study = self.study2
        cp = study.simulations[0]
        with self.assertRaises(KeyError):
            study.search_simulation_by_name("wrong name")

        searched = study.search_simulation_by_name(cp.name, how="deep")
        self.assertIs(searched, cp)
        searched = study.search_simulation_by_name(cp.name, how="shallow")
        self.assertIs(searched, cp)

    def test_search_simulation_in_group_by_name(self):
        study = self.study2
        cp = study.simulations.pop(0)
        group = SimulationGroup(name="BLAH", simulations=[cp])
        study.analysis_tools.simulation_grids.append(group)
        with self.assertRaises(KeyError):
            study.search_simulation_by_name(cp.name, how="shallow")

        searched = study.search_simulation_by_name(cp.name, how="deep")
        self.assertIs(searched, cp)

    def test_add_1_simulation(self):
        study = self.study2
        cp = study.simulations[0]
        cp2 = cp.copy()
        cp2.name = cp.name + "2"
        study.add_simulations(cp2)
        self.assertIn(cp2, study.simulations)

    def test_add_2_simulations(self):
        study = self.study2
        cp = study.simulations[0]
        cp3 = cp.copy()
        cp3.name = cp.name + "3"
        cp4 = cp.copy()
        cp4.name = cp.name + "4"
        study.add_simulations([cp4, cp3])
        self.assertIn(cp4, study.simulations)
        self.assertIn(cp3, study.simulations)

    def test_add_simulation_collision(self):
        study = self.study2
        cp = study.simulations[0]

        with self.assertRaises(SimulationNameCollisionError):
            study.add_simulations(cp)


class TestBlankStudy(TestCase):

    def setUp(self):
        self.study = make_blank_study()

    def test_is_blank(self):
        self.assertTrue(self.study.is_blank)

    def test_modify_study_metadata(self):
        self.study.study_purpose = "x"
        self.assertFalse(self.study.is_blank)

    def test_add_exp(self):
        from kromatography.model.experiment import Experiment
        exp = Experiment(name="foo")
        self.study.experiments.append(exp)
        self.assertFalse(self.study.is_blank)

    def test_add_sim(self):
        from kromatography.model.simulation import Simulation
        sim = Simulation(name="foo")
        self.study.simulations.append(sim)
        self.assertFalse(self.study.is_blank)

    def test_set_product(self):
        ds = self.study.datasource
        prod0 = ds.products[0]
        self.study.product = prod0
        self.assertFalse(self.study.is_blank)

    def test_add_ds(self):
        from kromatography.model.binding_model import StericMassAction
        ds = self.study.study_datasource
        ds.binding_models.append(StericMassAction(1, name="foo"))
        self.assertFalse(self.study.is_blank)
