import os
from os.path import isfile
from shutil import copyfile
from unittest import TestCase

from app_common.traits.assertion_utils import assert_has_traits_almost_equal

from kromatography.model.tests.sample_data_factories import make_sample_study2
from kromatography.model.lazy_simulation import LazyLoadingSimulation
from kromatography.io.simulation_updater import update_simulation_results
from kromatography.utils.testing_utils import io_data_path
from kromatography.model.chromatography_results import SimulationResults

from .test_simulation import TestSimulationCopy, TestSimulation


class TestLazySimulationCreation(TestSimulation):

    def setUp(self):
        super(TestLazySimulationCreation, self).setUp()
        self.sim_from_scratch = LazyLoadingSimulation.from_simulation(
            self.sim_from_scratch
        )

    def test_update_results(self):
        # Since performance data pane shows sim's perf data, make sure the
        # change of name in sim is reflected in its performance data.
        sim = self.sim_from_scratch
        # Make it as if it is run:
        result_filepath = io_data_path("std_example_xlsx_run1_cadet.h5")
        update_simulation_results(sim, result_filepath)
        sim.set_as_run()
        self.assertTrue(sim.has_run)
        self.assertTrue(isfile(sim.cadet_filepath))
        self.assertIsInstance(sim.output, SimulationResults)

    def test_perf_data_name_update(self):
        # Since performance data pane shows sim's perf data, make sure the
        # change of name in sim is reflected in its performance data.
        sim = self.sim_from_scratch
        # Make it as if it is run:
        result_filepath = io_data_path("std_example_xlsx_run1_cadet.h5")
        update_simulation_results(sim, result_filepath)
        sim.set_as_run()
        sim.name = "foo"
        self.assertEqual(sim.output.performance_data.name, "foo")


class TestLazySimulationCopy(TestSimulationCopy):
    @classmethod
    def setUpClass(cls):
        super(TestLazySimulationCopy, cls).setUpClass()
        cls.real_sim = LazyLoadingSimulation.from_simulation(cls.real_sim)

    def setUp(self):
        super(TestLazySimulationCopy, self).setUp()
        self.sim_from_scratch = LazyLoadingSimulation.from_simulation(
            self.sim_from_scratch
        )
        self.sim_from_std_exp = LazyLoadingSimulation.from_simulation(
            self.sim_from_std_exp
        )


class TestConvertLazySimToFromSim(TestCase):
    """ Test conversions of Simulations to/from LazyLoadingSimulation.
    """
    def setUp(self):
        self.study = make_sample_study2(add_transp_bind_models=True,
                                        add_sims='Run_1')
        self.sim = self.study.simulations[0]

        self.sim_run = self.sim.copy()
        # Save time by loading results from an already generated file:
        self.result_filepath = io_data_path("std_example_xlsx_run1_cadet.h5")
        update_simulation_results(self.sim_run, self.result_filepath)
        self.sim_run.set_as_run()

    def tearDown(self):
        # To make the run sim realistic, some tests copy the cadet file to the
        # std location: this cleans things up:
        if isfile(self.sim_run.cadet_filepath):
            os.remove(self.sim_run.cadet_filepath)

    def test_std_sim_not_run_to_lazy_sim(self):
        lazy_sim = LazyLoadingSimulation.from_simulation(self.sim)
        assert_has_traits_almost_equal(lazy_sim, self.sim,
                                       check_type=False, ignore=('uuid',))

    def test_lazy_sim_not_run_to_std_sim(self):
        lazy_sim = LazyLoadingSimulation.from_simulation(self.sim)
        new_std_sim = lazy_sim.to_simulation()
        assert_has_traits_almost_equal(new_std_sim, self.sim,
                                       ignore=('uuid',))

    def test_lazy_sim_not_run_to_lazy_sim(self):
        # Make the run sim's filepath created
        copyfile(self.result_filepath, self.sim_run.cadet_filepath)
        lazy_sim = LazyLoadingSimulation.from_simulation(self.sim)
        lazy_sim2 = LazyLoadingSimulation.from_simulation(lazy_sim)
        assert_has_traits_almost_equal(lazy_sim, lazy_sim2,
                                       ignore=('uuid',))

    def test_std_sim_run_to_lazy_sim(self):
        """ Creating a Lazy sim from a run sim, with or without CADET file.
        """
        lazy_sim = LazyLoadingSimulation.from_simulation(self.sim_run)
        # With missing cadet file, the lazy copy isn't run:
        ignore = ('uuid', 'has_run', 'run_status', 'output', 'editable')
        assert_has_traits_almost_equal(lazy_sim, self.sim_run,
                                       check_type=False, ignore=ignore)
        self.assertFalse(lazy_sim.has_run)
        self.assertTrue(lazy_sim.editable)

        # With cadet file, the lazy sim is run:
        copyfile(self.result_filepath, self.sim_run.cadet_filepath)
        try:
            lazy_sim2 = LazyLoadingSimulation.from_simulation(self.sim_run)
            assert_has_traits_almost_equal(
                lazy_sim2, self.sim_run, check_type=False, ignore=('uuid',)
            )
        finally:
            os.remove(self.sim_run.cadet_filepath)

    def test_lazy_sim_run_to_std_sim(self):
        # Make the run sim's filepath created
        copyfile(self.result_filepath, self.sim_run.cadet_filepath)
        lazy_sim = LazyLoadingSimulation.from_simulation(self.sim_run)
        new_std_sim = lazy_sim.to_simulation()
        assert_has_traits_almost_equal(new_std_sim, self.sim_run,
                                       ignore=('uuid',))

    def test_lazy_sim_run_to_lazy_sim(self):
        # Make the run sim's filepath created
        copyfile(self.result_filepath, self.sim_run.cadet_filepath)
        lazy_sim = LazyLoadingSimulation.from_simulation(self.sim_run)
        lazy_sim2 = LazyLoadingSimulation.from_simulation(lazy_sim)
        assert_has_traits_almost_equal(lazy_sim, lazy_sim2,
                                       ignore=('uuid',))
