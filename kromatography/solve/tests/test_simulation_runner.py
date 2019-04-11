""" Tests for the simulation runner module.
"""

from unittest import TestCase

from traits.testing.unittest_tools import UnittestTools

from kromatography.model.tests.sample_data_factories import \
    make_sample_simulation
from kromatography.solve.simulation_runner import run_simulations
from kromatography.model.simulation import SIM_FINISHED_SUCCESS
from kromatography.model.factories.job_manager import \
    create_start_job_manager


class TestSimRunner(UnittestTools, TestCase):

    @classmethod
    def setUpClass(cls):
        cls.job_manager = create_start_job_manager(max_workers=2)

    @classmethod
    def tearDownClass(cls):
        cls.job_manager.shutdown()

    def setUp(self):
        self.simulation = make_sample_simulation(name='Run_1')

    # -------------------------------------------------------------------------
    # Tests
    # -------------------------------------------------------------------------

    def test_sim_runner_sim_list(self):
        sim = self.simulation
        sim2 = sim.clone()
        sim_list = [sim, sim2]
        with self.assertTraitChangesAsync(sim, 'has_run', count=1):
            with self.assertTraitChangesAsync(sim2, 'has_run', count=1):
                run_simulations(sim_list, job_manager=self.job_manager,
                                wait=True)

        for sim in sim_list:
            self.assertIsNotNone(sim.output)
            self.assertEqual(sim.run_status, SIM_FINISHED_SUCCESS)
            self.assertTrue(sim.has_run)
            self.assertFalse(sim.editable)

    def test_sim_runner_editable(self):
        sim = self.simulation
        self.assertTrue(sim.editable)
        with self.assertTraitChangesAsync(sim, 'editable', count=1):
            run_simulations([sim], job_manager=self.job_manager, wait=True)

        self.assertFalse(sim.editable)
