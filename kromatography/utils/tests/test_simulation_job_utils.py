""" Tests for the utility functions in simulation_job_utils module. """

from unittest import TestCase

from traits.testing.unittest_tools import UnittestTools

from kromatography.model.tests.sample_data_factories import \
    make_sample_simulation
from kromatography.solve.simulation_job_utils import \
    walk_dataelement_editable


class TestSimWalker(UnittestTools, TestCase):

    def setUp(self):
        self.simulation = make_sample_simulation(name='Run_1')

    # -------------------------------------------------------------------------
    # Tests
    # -------------------------------------------------------------------------

    def test_sim_walker(self):
        # test a couple items in simulation object tree are flipped properly
        sim = self.simulation
        sim.editable = True
        sim.method.method_steps[1].editable = True

        walk_dataelement_editable(sim, False)

        self.assertEqual(sim.editable, False)
        assert(not sim.method.method_steps[1].editable)

    def test_skip_traits_walker(self):
        # test functionality to skip traits
        sim = self.simulation
        sim.method.method_steps[1].editable = True

        walk_dataelement_editable(sim, False, ['method_steps'])

        self.assertEqual(sim.method.method_steps[1].editable, True)
