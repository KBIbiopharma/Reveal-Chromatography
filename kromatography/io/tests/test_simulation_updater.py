from unittest import TestCase

from traits.testing.unittest_tools import UnittestTools
from scimath.units.api import UnitScalar

from kromatography.utils.assertion_utils import assert_unit_scalar_almost_equal
from kromatography.utils.testing_utils import io_data_path
from kromatography.model.tests.sample_data_factories import \
    make_sample_simulation
from kromatography.io.simulation_updater import update_simulation_results
from kromatography.model.chromatography_results import PerformanceData, \
    SimulationResults
from kromatography.model.solution_with_product import SolutionWithProduct


class TestUpdateSimulation(TestCase, UnittestTools):
    def test_update_std_run_sim(self):
        sim = make_sample_simulation(name='Run_1')
        self.assertIsNone(sim.output)
        # Contains data from the CADET run:
        h5file = io_data_path("Sample_Sim_from_Run_1_cadet_simulation_run.h5")
        with self.assertTraitChanges(sim, "perf_param_data_event", 1):
            update_simulation_results(sim, h5file)

        self.assertIsInstance(sim.output, SimulationResults)
        perf_params = sim.output.performance_data
        self.assertIsInstance(perf_params, PerformanceData)
        self.assertIsInstance(perf_params.pool, SolutionWithProduct)
        num_comp = len(sim.product.product_components)
        self.assertEqual(len(perf_params.pool.product_component_concentrations),  # noqa
                         num_comp)
        assert_unit_scalar_almost_equal(perf_params.pool_volume,
                                        UnitScalar(1.727090, units="CV"),
                                        eps=1.e-6)
        assert_unit_scalar_almost_equal(perf_params.step_yield,
                                        UnitScalar(95.814, units='%'),
                                        eps=1.e-3)
        assert_unit_scalar_almost_equal(perf_params.start_collect_time,
                                        UnitScalar(200.946, units='minute'),
                                        eps=1.e-3)
        assert_unit_scalar_almost_equal(perf_params.stop_collect_time,
                                        UnitScalar(227.9, units='minute'),
                                        eps=1.e-3)
