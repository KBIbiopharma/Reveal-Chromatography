from unittest import TestCase
from os.path import isfile

from kromatography.model.api import LazyLoadingSimulation, Simulation
from kromatography.model.discretization import Discretization
from kromatography.model.solver import Solver
from kromatography.model.factories.simulation import \
    build_simulation_from_experiment
from kromatography.model.tests.sample_data_factories import \
    make_sample_experiment, make_sample_experiment2
from kromatography.utils.assertion_utils import \
    assert_has_traits_almost_equal


class TestBuildSimulationFromExperiment(TestCase):
    def setUp(self):
        self.exp = make_sample_experiment()
        self.exp2 = make_sample_experiment2()

    def test_build_sim_from_exp(self):
        sim = build_simulation_from_experiment(self.exp, fstep='Equilibration',
                                               lstep='Gradient Elution')
        self.assertValidSimFromExp(sim, self.exp,
                                   first_step_name='Equilibration',
                                   last_step_name='Gradient Elution')

    def test_build_sim_from_real_exp(self):
        sim = build_simulation_from_experiment(self.exp2)
        self.assertValidSimFromExp(sim, self.exp2)

    def test_build_sim_from_exp_no_collection_criteria(self):
        self.exp2.method.collection_criteria = None
        sim = build_simulation_from_experiment(self.exp2)
        self.assertValidSimFromExp(sim, self.exp2)

    def test_build_lazy_sim_from_exp(self):
        lazy_sim = build_simulation_from_experiment(self.exp2,
                                                    lazy_loading=True)
        self.assertIsInstance(lazy_sim, LazyLoadingSimulation)
        self.assertValidSimFromExp(lazy_sim, self.exp2)

        sim = build_simulation_from_experiment(self.exp2, lazy_loading=False)
        assert_has_traits_almost_equal(sim, lazy_sim, check_type=False)

    def test_build_with_custom_discretization(self):
        disc = Discretization(ncol=30)
        sim = build_simulation_from_experiment(self.exp2, discretization=disc)
        self.assertEqual(sim.discretization.ncol, 30)

    def test_build_with_custom_solver(self):
        solv = Solver(number_user_solution_points=500)
        sim = build_simulation_from_experiment(self.exp2, solver=solv)
        self.assertEqual(sim.solver.number_user_solution_points, 500)

    # Helper methods ----------------------------------------------------------

    def assertValidSimFromExp(self, sim, exp, first_step_name="Load",
                              last_step_name="Strip"):

        self.assertIsInstance(sim, Simulation)
        assert_has_traits_almost_equal(sim.product, exp.product)

        # Column
        self.assertIsNot(sim.column, exp.column)
        assert_has_traits_almost_equal(sim.column, exp.column)

        # Method
        self.assertIsNot(sim.method, exp.method)
        # Method - Collection criteria
        sim_cc = sim.method.collection_criteria
        exp_cc = exp.method.collection_criteria
        if exp_cc is None:
            self.assertIsNone(sim_cc)
        else:
            self.assertIsNot(sim_cc, exp_cc)
            assert_has_traits_almost_equal(sim_cc, exp_cc)

        # Method - steps
        for step in sim.method.method_steps:
            # sim step are only copies
            self.assertNotIn(step, exp.method.method_steps)

        first_sim_step = sim.method.method_steps[0]
        last_sim_step = sim.method.method_steps[-1]
        self.assertEqual(first_sim_step.name, first_step_name)
        self.assertEqual(last_sim_step.name, last_step_name)

        _, first_step_idx = exp.method.get_step_of_name(first_step_name,
                                                        collect_step_num=True)
        assert_has_traits_almost_equal(
            first_sim_step, exp.method.method_steps[first_step_idx]
        )
        assert_has_traits_almost_equal(last_sim_step,
                                       exp.method.method_steps[-1])

        # method's initial conditions
        equil_step = exp.method.method_steps[1]
        equil_buffer = equil_step.solutions[0]
        assert_has_traits_almost_equal(sim.method.initial_buffer,
                                       equil_buffer)

        # Solver
        self.assertEqual(sim.solver.write_at_user_times, 1)
        self.assertGreater(len(sim.solver.user_solution_times), 10)

        # Run attrs
        self.assertIsNone(sim.output)
        self.assertTrue(sim.editable)
        self.assertFalse(isfile(sim.cadet_filepath))
