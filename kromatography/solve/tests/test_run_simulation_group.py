from unittest import TestCase
import pandas as pd
import numpy as np
from pandas.util.testing import assert_series_equal, assert_frame_equal
import os

from traits.testing.unittest_tools import UnittestTools

from app_common.apptools.testing_utils import \
    reraise_traits_notification_exceptions

from kromatography.model.factories.job_manager import create_start_job_manager
from kromatography.model.simulation_group import Simulation, SimulationGroup, \
    SingleParamSimulationDiff, SIM_COL_NAME
from kromatography.model.lazy_simulation import LazyLoadingSimulation
from kromatography.model.study import Study
from kromatography.model.tests.sample_data_factories import \
    make_sample_simulation, make_sample_simulation_group2
from kromatography.utils.string_definitions import MULTI_SIM_RUNNER_CREATED, \
    MULTI_SIM_RUNNER_FINISHED
from kromatography.utils.app_utils import get_cadet_input_folder

# This data was computed by running a group defined by:
# make_sample_simulation_group2(size=2)
SIM_GROUP_RAN = pd.DataFrame(
    {'pool_concentration (g/L)': {0: 2.510734,
                                  1: 2.321895},
     'pool_volume (CV)': {0: 1.756180,
                          1: 1.738878},
     SIM_COL_NAME: {0: 'Sim 0',
                    1: 'Sim 1'},
     'step_yield (%)': {0: 95.854382,
                        1: 87.771577},
     'binding_model.sma_ka[1]': {0: 0.001,
                                 1: 0.01}}
)


class BaseRunSimulationGroup(UnittestTools):
    """ Base class containing all tests that simulation groups should pass.
    """

    @classmethod
    def setUpClass(cls):
        # Limit the number of process to avoid saturating the machine
        cls.job_manager = create_start_job_manager(max_workers=2)

    @classmethod
    def tearDownClass(cls):
        cls.job_manager.shutdown()

    def setUp(self):
        orig_val = self.sim.binding_model.sma_ka[1]
        self.no_diff = (SingleParamSimulationDiff("binding_model.sma_ka[1]",
                                                  orig_val),)
        self.study = Study(name="test study", simulations=[self.sim])

        def frozen_sim_group_maker(**kw):
            return make_sample_simulation_group2(cp=self.sim, **kw)

        self.sim_group_maker = frozen_sim_group_maker

    def test_manual_creation(self):
        with reraise_traits_notification_exceptions():
            group = self.sim_group_maker(size=3)

        self.assertIsInstance(group, SimulationGroup)
        self.assertEqual(group.size, 3)
        self.assertIsInstance(group.center_point_simulation, self.sim_class)

        self.assertFalse(group.has_run)
        self.assertEqual(group.run_status, MULTI_SIM_RUNNER_CREATED)

        # test data dataframe
        df = group.group_data
        self.assertIsInstance(df, pd.DataFrame)
        expected_columns = {'binding_model.sma_ka[1]', 'pool_volume (CV)',
                            'pool_concentration (g/L)', 'step_yield (%)',
                            SIM_COL_NAME}
        components = self.sim.product.product_component_names
        expected_purities = {"purity: {} (%)".format(comp)
                             for comp in components}
        expected_columns = expected_columns.union(expected_purities)
        self.assertEqual(set(df.columns), expected_columns)
        expected_sims = {'Sim 2', 'Sim 1', 'Sim 0'}
        self.assertEqual(set(df[SIM_COL_NAME]), expected_sims)
        expected_index = range(len(expected_sims))
        self.assertEqual(list(df.index), expected_index)
        param_name = 'binding_model.sma_ka[1]'
        expected_bind_models = pd.Series([0.001, 0.01, 0.1], name=param_name)
        assert_series_equal(df[param_name], expected_bind_models)
        # No output set yet
        self.assertTrue(np.all(np.isnan(df.iloc[:, 2:])))

    def test_initialize_simulations(self):
        group = self.sim_group_maker(size=1)

        original_simulation_list = group.simulations
        # Until initialization, no simulations available
        self.assertEqual(len(group.simulations), 0)
        self.assertEqual(len(group.simulation_diffs), 1)
        self.assertEqual(len(group._simulation_output_cache), 0)

        group.initialize_simulations()

        # After initializing the list, simulations list is the same but filled
        self.assertIs(group.simulations, original_simulation_list)
        self.assertEqual(len(group.simulations), 1)
        self.assertEqual(len(group.simulation_diffs), 1)
        self.assertEqual(len(group._simulation_output_cache), 1)

        # Initializing a second time doesn't change the length of the lists:
        group.initialize_simulations()
        self.assertIs(group.simulations, original_simulation_list)
        self.assertEqual(len(group.simulations), 1)
        self.assertEqual(len(group.simulation_diffs), 1)
        self.assertEqual(len(group._simulation_output_cache), 1)

    def test_reinitialize_simulations(self):
        group = self.sim_group_maker(size=1)

        original_simulation_list = group.simulations
        # Until initialization, no simulations available
        self.assertEqual(len(group.simulations), 0)
        self.assertEqual(len(group.simulation_diffs), 1)
        self.assertEqual(len(group._simulation_output_cache), 0)

        #: Run sims (cadet output file is cached):
        group.run(self.job_manager, wait=True)
        # Empty sims to emulate an optimizer conserving memory
        group.clear_simulations()
        # Until initialization, no simulations available
        self.assertEqual(len(group.simulations), 0)
        self.assertEqual(len(group.simulation_diffs), 1)
        self.assertEqual(len(group._simulation_output_cache), 1)

        # Reinitialize using the cached results:
        group.initialize_simulations(use_output_cache=True)

        self.assertIs(group.simulations, original_simulation_list)
        self.assertEqual(len(group.simulations), 1)
        self.assertIsNotNone(group.simulations[0].output)
        self.assertTrue(group.simulations[0].has_run)

    def test_run_update_data(self):
        group = self.sim_group_maker(size=1)

        original_simulation_list = group.simulations
        # Until run, no simulations available
        self.assertEqual(len(group.simulations), 0)

        # Before running, the group_data has no output values
        df = group.group_data
        self.assertTrue(np.all(np.isnan(df.iloc[:, 2:])))
        with self.assertTraitChanges(group, "has_run"):
            # Change twice, from created to running and then to finished:
            with self.assertTraitChanges(group, "run_status", 2):
                group.run(self.job_manager, wait=True)

        self.assertTrue(group.has_run)
        self.assertEqual(group.run_status, MULTI_SIM_RUNNER_FINISHED)

        # After running, the group_data has output values filled
        self.assertFalse(np.any(np.isnan(df.iloc[:, 2:])))
        # After running, simulations contain is the same but filled
        self.assertIs(group.simulations, original_simulation_list)
        self.assertEqual(len(group.simulations), 1)
        self.assertIsInstance(group.simulations[0], self.sim_class)

        # Running a second time doesn't change size of simulations
        with self.assertTraitChanges(group, "has_run"):
            # Change twice, from created to running and then to finished:
            with self.assertTraitChanges(group, "run_status", 2):
                group.run(self.job_manager, wait=True)

        self.assertIs(group.simulations, original_simulation_list)
        self.assertEqual(len(group.simulations), 1)
        self.assertTrue(group.has_run)
        self.assertEqual(group.run_status, MULTI_SIM_RUNNER_FINISHED)

    def test_run_without_study_lookup(self):
        group = self.sim_group_maker(size=1)
        with self.assertTraitChanges(group, "has_run"):
            group.run(self.job_manager, wait=True)

    def test_sort_and_update_data(self):
        group = self.sim_group_maker(size=2)
        group.group_data = group.group_data.sort_values(by=SIM_COL_NAME,
                                                        ascending=False)
        group.run(self.job_manager, wait=True)
        # Sorting the group_data shouldn't affect the output values
        # (SIM_GROUP_RAN was computed without the sorting)
        group_data = group.group_data.sort_values(by=SIM_COL_NAME)
        for col in SIM_GROUP_RAN:
            assert_series_equal(group_data[col], SIM_GROUP_RAN[col])
        for col in group_data:
            if col.startswith("purity"):
                self.assertFalse(np.any(np.isnan(group_data[col])))

    def test_run_without_collection_criteria(self):
        sim = self.sim.copy()
        sim.method.collection_criteria = None
        group = make_sample_simulation_group2(cp=sim, size=1)

        self.assertFalse(group.has_run)
        self.assertEqual(group.run_status, MULTI_SIM_RUNNER_CREATED)
        self.assertEqual(len(group.simulations), 0)

        # Before running, the group_data has no output values
        df = group.group_data
        self.assertTrue(np.all(np.isnan(df.iloc[:, 2:])))
        with self.assertTraitChanges(group, "has_run"):
            # Change twice, from created to running and then to finished:
            with self.assertTraitChanges(group, "run_status", 2):
                group.run(self.job_manager, wait=True)

        # After running, the group has run, but the data is filled with nans
        # because there is no collection of pool
        self.assertTrue(group.has_run)
        self.assertEqual(group.run_status, MULTI_SIM_RUNNER_FINISHED)
        df = group.group_data
        self.assertTrue(np.all(np.isnan(df.iloc[:, 2:])))

    def test_run_creates_cadet_files(self):
        group = self.sim_group_maker(size=1)
        self.assertFalse(group.auto_delete_run_sims)
        with self.assertTraitChanges(group, "has_run"):
            group.run(self.job_manager, wait=True)

        self.assert_all_cadet_files_present(group)

    def test_run_and_autodelete_cadet_files(self):
        group = self.sim_group_maker(size=1)
        group.auto_delete_run_sims = True
        group.initialize_simulations()
        sim = group.simulations[0]
        filename = sim.cadet_filename
        with self.assertTraitChanges(group, "has_run"):
            group.run(self.job_manager, wait=True)

        self.assert_no_cadet_files_present(group, [filename])

    def test_run_and_add_to_itself(self):
        group = self.sim_group_maker(size=1)
        group.run(self.job_manager, wait=True)
        new = group + group
        self.assertIsInstance(new, SimulationGroup)
        self.assertEqual(new.simulation_diffs, group.simulation_diffs * 2)
        self.assertEqual(new.simulations, group.simulations * 2)
        group_data = group.group_data
        expected = pd.concat([group_data, group_data]).reset_index(drop=True)
        assert_frame_equal(new.group_data, expected)
        self.assertIs(new.center_point_simulation,
                      group.center_point_simulation)
        self.assertEqual(new.is_lazy_loading, group.is_lazy_loading)

    # Helper methods ----------------------------------------------------------

    def assert_all_cadet_files_present(self, group):
        cadet_folder = get_cadet_input_folder()
        for sim in group.simulations:
            filename = sim.cadet_filename
            self.assertIn(filename, os.listdir(cadet_folder))

    def assert_no_cadet_files_present(self, group, filenames):
        cadet_folder = get_cadet_input_folder()
        self.assertEqual(group.simulations, [])
        for filename in filenames:
            self.assertNotIn(filename, os.listdir(cadet_folder))

    def update_data_when_not_run(self):
        group = self.sim_group_maker(size=1)
        group.initialize_simulations()
        sim0 = group.simulations[0]
        # Fake the sim running and failing to update: this will trigger the
        # update of the group's data:
        with self.assertTraitChanges(group, "group_data_updated_event", 1):
            sim0.set_as_run()

        performance_arr = group.group_data.values[:, 2:].astype("float")
        self.assertTrue(np.all(np.isnan(performance_arr)))


class TestCreateRunSimulationGroup(BaseRunSimulationGroup, TestCase):
    """ Simulation groups containing standard in-memory simulations.
    """
    @classmethod
    def setUpClass(cls):
        super(TestCreateRunSimulationGroup, cls).setUpClass()
        cls.sim = make_sample_simulation()
        cls.sim_class = Simulation


class TestCreateRunLazySimulationGroup(TestCreateRunSimulationGroup):
    """ Simulation groups containing LazyLoading simulations.
    """
    @classmethod
    def setUpClass(cls):
        super(TestCreateRunLazySimulationGroup, cls).setUpClass()
        cls.sim = LazyLoadingSimulation.from_simulation(cls.sim)
        cls.sim_class = LazyLoadingSimulation
