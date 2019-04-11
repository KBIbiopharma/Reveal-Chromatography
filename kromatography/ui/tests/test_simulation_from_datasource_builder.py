from unittest import TestCase

from app_common.traits.assertion_utils import assert_has_traits_almost_equal

from kromatography.ui.simulation_from_datasource_builder import \
    SimulationFromDatasourceBuilder
from kromatography.model.data_source import SimpleDataSource
from kromatography.model.simulation import Simulation
from kromatography.model.buffer import Buffer
from kromatography.utils.cadet_simulation_builder import build_cadet_input, \
    CADETInput
from kromatography.model.tests.sample_data_factories import make_sample_study2
from kromatography.utils.string_definitions import DEFAULT_BINDING_MODEL_NAME,\
    DEFAULT_TRANSPORT_MODEL_NAME


class TestSimulationBuilderDialog(TestCase):

    def setUp(self):
        self.datasource = SimpleDataSource()
        self.study = make_sample_study2(add_transp_bind_models=True)
        self.study_ds = self.study.study_datasource
        self.sim_builder = SimulationFromDatasourceBuilder(
            datasource=self.datasource, study_datasource=self.study_ds
        )

    def test_bring_up(self):
        ui = self.sim_builder.edit_traits()
        ui.dispose()

    def test_product_selection(self):
        target_prod = self.datasource.get_object_names_by_type("products")[0]
        self.sim_builder.product_name = target_prod
        exp = self.datasource.get_object_of_type("products", target_prod)
        assert_has_traits_almost_equal(self.sim_builder.product, exp)

    def test_build_simulation(self):
        # Setup
        self.sim_builder.column_name = 'CP_001'
        self.sim_builder.method_name = 'Run_1'
        self.sim_builder.first_simulated_step_name = 'Load'
        self.sim_builder.last_simulated_step_name = 'Strip'
        self.sim_builder.transport_model_name = DEFAULT_TRANSPORT_MODEL_NAME
        self.sim_builder.binding_model_name = DEFAULT_BINDING_MODEL_NAME
        sim = self.sim_builder.to_simulation()
        self.assertIsInstance(sim, Simulation)

        # init buffer:
        self.assertEqual(self.sim_builder.initial_buffer_name, '')

        exp1 = self.study.search_experiment_by_name("Run_1")
        equil_buffer = exp1.method.method_steps[1].solutions[0].name
        self.assertEqual(sim.method.initial_buffer.name, equil_buffer)
        # the simulation has to be valid enough that it can be converted to a
        # CADET input...
        cadet_input = build_cadet_input(sim)
        self.assertIsInstance(cadet_input, CADETInput)

    def test_build_simulation_force_init_buffer(self):
        # Setup
        self.sim_builder.column_name = 'CP_001'
        self.sim_builder.method_name = 'Run_1'
        self.sim_builder.first_simulated_step_name = 'Load'
        self.sim_builder.last_simulated_step_name = 'Strip'
        self.sim_builder.initial_buffer_name = 'Elution_1'
        self.sim_builder.transport_model_name = DEFAULT_TRANSPORT_MODEL_NAME
        self.sim_builder.binding_model_name = DEFAULT_BINDING_MODEL_NAME
        sim = self.sim_builder.to_simulation()
        self.assertIsInstance(sim, Simulation)
        self.assertEqual(sim.method.initial_buffer.name, 'Elution_1')

    def test_change_method_name_changes_first_last_guesses(self):
        self.assertIsNone(self.sim_builder.first_simulated_step_name)
        self.assertIsNone(self.sim_builder.last_simulated_step_name)
        self.sim_builder.method_name = 'Run_1'
        self.assertEqual(self.sim_builder.first_simulated_step_name,
                         'Pre-Equilibration')
        self.assertEqual(self.sim_builder.last_simulated_step_name, 'Strip')

    def test_change_method_changes_solution_list(self):
        self.sim_builder.method_name = 'Run_1'
        all_solutions = []
        for step in self.sim_builder.method.method_steps:
            all_solutions += [sol.name for sol in step.solutions
                              if isinstance(sol, Buffer)]

        # Sim builder also allows the init_buffer to be blank so that it is
        # looked up in the source experiment:
        all_solutions += [""]
        self.assertEqual(set(all_solutions), set(self.sim_builder.all_buffers))
