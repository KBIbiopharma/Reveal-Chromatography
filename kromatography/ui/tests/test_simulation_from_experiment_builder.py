from unittest import TestCase
from traits.testing.unittest_tools import UnittestTools

from app_common.traits.assertion_utils import assert_has_traits_almost_equal

from kromatography.ui.simulation_from_experiment_builder import \
    generate_sim_names, SimulationFromExperimentBuilder
from kromatography.model.factories.simulation import generate_sim_name
from kromatography.model.tests.sample_data_factories import \
    make_sample_study, make_sample_study2
from kromatography.ui.experiment_selector import ExperimentSelector
from kromatography.model.api import BindingModel, Buffer, Method, \
    Simulation, TransportModel

STUDY = make_sample_study(num_exp=5)


class TestGenerateSimNames(TestCase):
    def test_1_name(self):
        self.assertIsInstance(generate_sim_name("Run 1"), str)
        self.assertIsInstance(generate_sim_name("Run_1"), str)

    def test_n_names(self):
        names = generate_sim_names(["Run 1", "Run 2"], STUDY)
        self.assertIsInstance(names, list)
        for name in names:
            self.assertIsInstance(name, str)


class TestSimulationFromExperimentBuilder(TestCase, UnittestTools):

    @classmethod
    def setUpClass(cls):
        cls.study2 = make_sample_study2(add_transp_bind_models=True)

    def setUp(self):
        self.study = make_sample_study(num_exp=5)
        self.sim_builder = SimulationFromExperimentBuilder(
            experiment_selector=ExperimentSelector(study=self.study),
            target_study=self.study,
        )

    def test_bring_up(self):
        ui = self.sim_builder.edit_traits()
        ui.dispose()

    def test_create_builder_no_arg(self):
        with self.assertRaises(ValueError):
            SimulationFromExperimentBuilder()

    def test_create_builder_no_method_bounds(self):
        sim_builder = SimulationFromExperimentBuilder(target_study=self.study2)
        self.assertIsInstance(sim_builder, SimulationFromExperimentBuilder)

    def test_create_builder(self):
        sim_builder = SimulationFromExperimentBuilder(
            target_study=self.study2, first_simulated_step_name="Load",
            last_simulated_step_name="Strip"
        )
        self.assertIsInstance(sim_builder, SimulationFromExperimentBuilder)

    def test_build_sim_names(self):
        select = self.study.experiments[:2]
        self.sim_builder.experiment_selector.experiment_selected = \
            [expt.name for expt in select]
        expected = [generate_sim_name(expt.name) for expt in select]
        self.assertEqual(self.sim_builder.simulation_names, expected)

    def test_rotate_names(self):
        # Make some fake simulations to force new simulations to be appended a
        # suffix:
        first_exp_name = self.study.experiments[0].name
        sim = Simulation(name=generate_sim_name(first_exp_name))
        fake_rotated_sim_name = generate_sim_name(first_exp_name) + "_v2"
        sim2 = Simulation(name=fake_rotated_sim_name)
        self.study.simulations.extend([sim, sim2])

        select = self.study.experiments[:2]
        self.sim_builder.experiment_selector.experiment_selected = \
            [expt.name for expt in select]
        expected = [generate_sim_name(expt.name) for expt in select]
        expected[0] += "_v3"
        self.assertEqual(self.sim_builder.simulation_names, expected)

    def test_build_1sim(self):
        sim_builder = SimulationFromExperimentBuilder(
            target_study=self.study2, first_simulated_step_name="Load",
            last_simulated_step_name="Strip"
        )
        sim_builder.experiment_selector.experiment_selected = ['Run_1']
        sims = sim_builder.to_simulations()
        self.assertEqual(len(sims), 1)
        self.assertValidSimulations(sims, self.study2)

    def test_build_1sim_no_method_bounds(self):
        sim_builder = SimulationFromExperimentBuilder(target_study=self.study2)
        sim_builder.experiment_selector.experiment_selected = ['Run_1']
        sims = sim_builder.to_simulations()
        self.assertEqual(len(sims), 1)
        # first and last step names are the default value in the sim_builder
        # since nothing was passed.
        flstep = sim_builder.first_simulated_step_name
        # Don't check the product because there is no load in this sim...
        self.assertValidSimulations(sims, self.study2, fstep=flstep,
                                    lstep=flstep, check_product=False)

    def test_build_2sims(self):
        sim_builder = SimulationFromExperimentBuilder(
            target_study=self.study2, first_simulated_step_name="Load",
            last_simulated_step_name="Strip"
        )
        sim_builder.experiment_selector.experiment_selected = ['Run_1',
                                                               'Run_2']
        sims = sim_builder.to_simulations()
        self.assertEqual(len(sims), 2)
        self.assertValidSimulations(sims, self.study2)

    def test_build_1sim_from_method_start(self):
        sim_builder = SimulationFromExperimentBuilder(
            target_study=self.study2,
            first_simulated_step_name='Pre-Equilibration',
            last_simulated_step_name="Strip"
        )
        sim_builder.experiment_selector.experiment_selected = ['Run_1']
        # Fail because no initial_buffer specified, and no step before:
        with self.assertRaises(ValueError):
            sim_builder.to_simulations()

        sim_builder = SimulationFromExperimentBuilder(
            target_study=self.study2,
            first_simulated_step_name='Pre-Equilibration',
            last_simulated_step_name="Strip",
            initial_buffer_name="Equil_Wash_1"
        )
        sim_builder.experiment_selector.experiment_selected = ['Run_1']
        sims = sim_builder.to_simulations()
        self.assertEqual(len(sims), 1)
        # Init buffer read from experimental method:
        self.assertEqual(sims[0].method.initial_buffer.name, 'Equil_Wash_1')
        self.assertValidSimulations(sims, self.study2,
                                    fstep='Pre-Equilibration')

    def test_different_init_buffers_from_different_exp_method(self):
        # Set each exp to a different initial condition:
        initial_condition_step = 1
        exp_names = ['Run_1', 'Run_2']
        experiments = [self.study2.search_experiment_by_name(name)
                       for name in exp_names]
        for exp in experiments:
            buf = Buffer(name="New buf for {}".format(exp.name))
            exp.method.method_steps[initial_condition_step].solutions = [buf]

        sim_builder = SimulationFromExperimentBuilder(
            target_study=self.study2, first_simulated_step_name="Load",
            last_simulated_step_name="Strip"
        )
        sim_builder.experiment_selector.experiment_selected = exp_names
        sims = sim_builder.to_simulations()
        for sim, exp_name in zip(sims, exp_names):
            buf_name = "New buf for {}".format(exp_name)
            self.assertEqual(sim.method.initial_buffer.name, buf_name)

    def test_init_buffers_come_from_explicit_value(self):
        sim_builder = SimulationFromExperimentBuilder(
            target_study=self.study2, first_simulated_step_name="Load",
            last_simulated_step_name="Strip", initial_buffer_name="Strip_1"
        )
        exps = ['Run_1', 'Run_2']
        sim_builder.experiment_selector.experiment_selected = exps
        sims = sim_builder.to_simulations()
        for sim in sims:
            self.assertEqual(sim.method.initial_buffer.name, "Strip_1")

    def test_cannot_create(self):
        sim_builder = SimulationFromExperimentBuilder(
            target_study=self.study2, first_simulated_step_name="Load",
            last_simulated_step_name="Strip", initial_buffer_name="Strip_1"
        )
        self.assertFalse(sim_builder.can_create)
        with self.assertTraitChanges(sim_builder, "can_create"):
            sim_builder.experiment_selector.experiment_selected = ['Run_1']

        self.assertTrue(sim_builder.can_create)

    # Utilities ---------------------------------------------------------------

    def assertValidSimulations(self, sims, target_study, fstep='Load',
                               lstep="Strip", check_product=True):
        existing_sim_names = [sim.name for sim in target_study.simulations]
        for sim in sims:
            self.assertNotIn(sim.name, existing_sim_names)
            self.assertIsInstance(sim.method, Method)
            self.assertEqual(sim.method.method_steps[0].name, fstep)
            self.assertEqual(sim.method.method_steps[-1].name, lstep)
            self.assertIsInstance(sim.transport_model, TransportModel)
            self.assertIsInstance(sim.binding_model, BindingModel)
            source_exp = sim.source_experiment
            assert_has_traits_almost_equal(source_exp.column, sim.column)
            self.assertIsNot(source_exp.column, sim.column)
            if check_product:
                assert_has_traits_almost_equal(source_exp.product,
                                               sim.product)
