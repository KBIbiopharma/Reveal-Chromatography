""" Tests for the Experiment class. """

from unittest import TestCase
import numpy as np

from scimath.units.api import UnitArray, UnitScalar
from traits.testing.unittest_tools import UnittestTools

from app_common.traits.assertion_utils import \
    assert_has_traits_not_almost_equal
from app_common.scimath.assertion_utils import assert_unit_array_almost_equal,\
    assert_unit_array_not_almost_equal, assert_unit_scalar_almost_equal

from kromatography.model.api import MethodStep, Product
from kromatography.model.tests.sample_data_factories import \
    make_sample_experiment, make_sample_experiment2, \
    make_sample_experiment2_with_strip
from kromatography.model.tests.example_model_data import COLUMN_DATA, \
    METHOD_DATA, RESIN_DATA, SYSTEM_TYPE_DATA, SYSTEM_DATA
from kromatography.utils.string_definitions import LOAD_STEP_TYPE, \
    STRIP_STEP_TYPE
from kromatography.model.factories.simulation import \
    build_simulation_from_experiment


class TestExperimentConstruction(TestCase):

    def setUp(self):
        self.experiment = make_sample_experiment(name='Run 1')

    # -------------------------------------------------------------------------
    # Tests
    # -------------------------------------------------------------------------
    def test_construction_no_product(self):
        # just some sanity tests
        experiment = self.experiment
        self.assertEqual(experiment.name, 'Run 1')
        self.assertEqual(experiment.column.name, COLUMN_DATA['name'])
        self.assertEqual(experiment.column.resin.name, RESIN_DATA['name'])
        self.assertEqual(experiment.system.name, SYSTEM_DATA['name'])
        self.assertEqual(experiment.system.system_type.name,
                         SYSTEM_TYPE_DATA['name'])
        self.assertEqual(experiment.method.name, METHOD_DATA['name'])
        self.assertEqual(experiment.output, None)

        # No product because the methods are a buffer and a no-solution step
        # (equil)
        self.assertIsInstance(experiment.product, Product)


class TestExperimentStripFraction(TestCase):
    def setUp(self):
        self.experim = make_sample_experiment2_with_strip()

    def test_change_strip_fraction(self):
        self.experim.strip_mass_fraction = UnitScalar(2, units="%")
        load = self.experim.method.load.solutions[0]
        self.assertAlmostEqual(load.product_component_assay_values[-1], 2.)

    def test_change_strip_fraction_if_no_strip_comp(self):
        experim2 = make_sample_experiment2()
        load = experim2.method.load.solutions[0]
        old_val = load.product_component_assay_values[-1]
        experim2.strip_mass_fraction = UnitScalar(2, units="%")
        self.assertAlmostEqual(load.product_component_assay_values[-1],
                               old_val)

    def test_change_strip_fraction_bad_value(self):
        self.experim.strip_mass_fraction = UnitScalar(2, units="%")
        load = self.experim.method.load.solutions[0]
        self.assertAlmostEqual(load.product_component_assay_values[-1], 2.)

        # This will fail by raising an exception, in the
        self.experim.strip_mass_fraction = UnitScalar(3, units="cm")
        self.assertAlmostEqual(load.product_component_assay_values[-1], 2.)
        assert_unit_scalar_almost_equal(
            self.experim.strip_mass_fraction, UnitScalar(2, units="%")
        )

    def test_strip_fraction_changes_simulation_from_exp(self):
        experim = self.experim
        sim_init = build_simulation_from_experiment(experim)
        experim.strip_mass_fraction = UnitScalar(10, units="%")
        sim_end = build_simulation_from_experiment(experim)
        # Sims are not almost equal
        assert_has_traits_not_almost_equal(sim_init, sim_end)

        # More precisely, the product_component_concentrations of the load must
        # be different:
        init_load = sim_init.method.method_steps[0].solutions[0]
        comp_conc_init = init_load.product_component_concentrations
        # by default, the strip fraction is 0:
        expected = UnitArray([75.33, 696.681, 37.989, 0.], units='m**-3*g')
        assert_unit_array_almost_equal(comp_conc_init, expected)

        end_load = sim_end.method.method_steps[0].solutions[0]
        comp_conc_end = end_load.product_component_concentrations
        assert_unit_array_not_almost_equal(comp_conc_init, comp_conc_end)
        self.assertNotAlmostEqual(np.array(comp_conc_end)[-1], 0.)
        # The presence of a strip component should reduce the concentration of
        # all other components by 10%:
        expected = expected * 9/10.
        assert_unit_array_almost_equal(comp_conc_end[:-1], expected[:-1])


class TestExperimentStepStartTimes(TestCase, UnittestTools):
    def setUp(self):
        self.experim = make_sample_experiment2()
        self.load_time = 58.0335760148217
        self.strip_time = 309.155309348155

    def test_get_step_start_time_no_offline_steps(self):
        self.experim.method.offline_steps = []
        load_start = self.experim.get_step_start_time(self.experim.method.load)
        expected = UnitScalar(self.load_time, units="min")
        assert_unit_scalar_almost_equal(load_start, expected)

        strip_step = self.experim.method.get_step_of_type(STRIP_STEP_TYPE)
        strip_start = self.experim.get_step_start_time(strip_step)
        expected = UnitScalar(self.strip_time, units="min")
        assert_unit_scalar_almost_equal(strip_start, expected)

    def test_get_step_start_time_default_offline_steps(self):
        self.assertEqual(self.experim.method.offline_steps,
                         ['Pre-Equilibration', 'Equilibration'])
        load_start = self.experim.get_step_start_time(self.experim.method.load)
        expected = UnitScalar(0., units="min")
        assert_unit_scalar_almost_equal(load_start, expected)

        strip_step = self.experim.method.get_step_of_type(STRIP_STEP_TYPE)
        strip_start = self.experim.get_step_start_time(strip_step)
        expected = UnitScalar(self.strip_time-self.load_time, units="min")
        assert_unit_scalar_almost_equal(strip_start, expected)

    def test_get_step_start_time_fail(self):
        load = MethodStep(step_type=LOAD_STEP_TYPE, name="test load")
        with self.assertRaises(KeyError):
            self.experim.get_step_start_time(load)

    def test_step_start_time_update_on_flow_rates(self):
        self.assertIsInstance(self.experim.method_step_boundary_times,
                              UnitArray)
        load = self.experim.method.load
        with self.assertTraitChanges(self.experim,
                                     "method_step_boundary_times", 1):
            load.flow_rate = load.flow_rate + UnitScalar(1, units="cm/hr")

    def test_step_start_time_update_on_volumes(self):
        self.assertIsInstance(self.experim.method_step_boundary_times,
                              UnitArray)
        load = self.experim.method.load
        with self.assertTraitChanges(self.experim,
                                     "method_step_boundary_times", 1):
            load.volume = load.volume + UnitScalar(1, units="CV")
