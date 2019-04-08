""" See also compute.factories.tests.test_experiement_optimizer for unit tests
around converting an optimizer builder to an optimizer.
"""
from unittest import TestCase
from contextlib import contextmanager

from pyface.ui.qt4.util.gui_test_assistant import GuiTestAssistant

from app_common.apptools.testing_utils import \
    reraise_traits_notification_exceptions
from app_common.traits.assertion_utils import assert_has_traits_almost_equal

from kromatography.ui.brute_force_optimizer_builder import \
    BRUTE_FORCE_2STEP_OPTIMIZER_TYPE, ExperimentSelector, \
    GRID_BASED_OPTIMIZER_TYPE
from kromatography.model.api import Buffer, LazyLoadingSimulation
from kromatography.model.tests.sample_data_factories import make_sample_study2
from kromatography.model.parameter_scan_description import \
    ParameterScanDescription, SMAParameterScanDescription
from kromatography.model.tests.sample_data_factories import \
    make_sample_binding_model_optimizer
from kromatography.model.factories.simulation import \
    build_simulation_from_experiment

NUM_PARAMETERS = 68


class BaseOptimizerBuilder(GuiTestAssistant):

    def make_optimizer_builder(self, *experims, **builder_kw):
        from kromatography.model.tests.sample_data_factories import \
            make_sample_optimizer_builder

        optim_builder = make_sample_optimizer_builder(
            self.study, select_exp_names=list(experims), **builder_kw
        )
        return optim_builder


class TestBringUpBruteForceOptimizerBuilder(BaseOptimizerBuilder, TestCase):

    def setUp(self):
        GuiTestAssistant.setUp(self)
        self.study = make_sample_study2()
        exp1 = self.study.search_experiment_by_name('Run_1')
        self.sim1 = build_simulation_from_experiment(exp1)
        self.study.simulations.append(self.sim1)

        exp2 = self.study.search_experiment_by_name('Run_2')
        self.sim2 = build_simulation_from_experiment(exp2)
        self.study.simulations.append(self.sim2)

    def test_bring_up(self):
        optim_builder = self.make_optimizer_builder()
        with self.build_temp_ui(optim_builder):
            pass

    def test_bringup_2step_with_empty_param_scans(self):
        traits = {"parameter_scans": []}
        exp = self.study.experiments[0].name
        optim_builder = self.make_optimizer_builder(exp, **traits)
        with self.build_temp_ui(optim_builder):
            pass

    def test_bringup_2step_with_binding_param_scans(self):
        p1 = SMAParameterScanDescription(name="sma_ka")
        p2 = SMAParameterScanDescription(name="sma_nu")
        traits = {"parameter_scans": [p1, p2]}
        exp = self.study.experiments[0].name
        optim_builder = self.make_optimizer_builder(exp, **traits)
        with self.build_temp_ui(optim_builder):
            pass

    def test_bringup_general_with_general_param_scans(self):
        p1name = 'binding_model.sma_lambda'
        p2name = 'column.resin.ligand_density'
        p1 = ParameterScanDescription(name=p1name)
        p2 = ParameterScanDescription(name=p2name)
        traits = {"parameter_scans": [p1, p2],
                  "optimizer_type": GRID_BASED_OPTIMIZER_TYPE}
        exp = self.study.experiments[0].name
        optim_builder = self.make_optimizer_builder(exp, **traits)
        with self.build_temp_ui(optim_builder):
            pass

    def test_bringup_with_parallel_parameters(self):
        p1name = 'binding_model.sma_lambda'
        p2name = 'column.resin.ligand_density'
        p1 = ParameterScanDescription(name=p1name)
        p2 = ParameterScanDescription(name=p2name, parallel_parameters=[p1])
        traits = {"parameter_scans": [p2],
                  "optimizer_type": GRID_BASED_OPTIMIZER_TYPE}
        exp = self.study.experiments[0].name
        optim_builder = self.make_optimizer_builder(exp, **traits)
        with self.build_temp_ui(optim_builder):
            pass

    # Helper methods ----------------------------------------------------------

    @contextmanager
    def build_temp_ui(self, optim_builder):
        ui = optim_builder.edit_traits()
        try:
            yield
        finally:
            ui.dispose()


class TestBruteForceOptimizerBuilder(BaseOptimizerBuilder, TestCase):

    def setUp(self):
        GuiTestAssistant.setUp(self)
        self.study = make_sample_study2()
        exp1 = self.study.search_experiment_by_name('Run_1')
        self.sim1 = build_simulation_from_experiment(exp1)
        self.study.simulations.append(self.sim1)

        exp2 = self.study.search_experiment_by_name('Run_2')
        self.sim2 = build_simulation_from_experiment(exp2)
        self.study.simulations.append(self.sim2)

    def test_initial_attributes(self):
        builder = self.make_optimizer_builder(
            optimizer_type=BRUTE_FORCE_2STEP_OPTIMIZER_TYPE
        )
        self.assertIsInstance(builder.starting_point_simulation_name, str)
        # No experiment was selected
        self.assertEqual(len(builder.experiment_selected), 0)
        self.assertEqual(len(builder.parameter_scans), 0)

        # No target experiment nor parameter scans defined: can't create
        self.assertFalse(builder.can_create)
        self.assertIsInstance(builder.starting_point_simulations, list)
        self.assertEqual(len(builder.starting_point_simulations), 0)

        self.assertEqual(builder.optimizer_name, "Optimizer0")
        self.assertEqual(builder.optimizer_type,
                         BRUTE_FORCE_2STEP_OPTIMIZER_TYPE)
        self.assertEqual(builder.parameter_scans, [])

    def test_initial_type_general_optimizer(self):
        builder = self.make_optimizer_builder(
            optimizer_type=GRID_BASED_OPTIMIZER_TYPE
        )
        self.assertEqual(builder.optimizer_type,
                         GRID_BASED_OPTIMIZER_TYPE)

    def test_can_create(self):
        builder = self.make_optimizer_builder(
            optimizer_type=GRID_BASED_OPTIMIZER_TYPE
        )
        self.assertEqual(len(builder.parameter_scans), 0)
        self.assertEqual(len(builder.experiment_selected), 0)
        # No target experiment nor parameter scans defined: can't create
        self.assertFalse(builder.can_create)

        # Update with missing elements
        p1name = 'binding_model.sma_lambda'
        p1 = ParameterScanDescription(name=p1name)
        builder.parameter_scans.append(p1)
        # Still no target experiment: can't create
        self.assertFalse(builder.can_create)

        first_exp = builder.target_study.experiments[0]
        builder.experiment_selected = [first_exp.name]
        self.assertTrue(builder.can_create)

    def test_update_starting_sim_from_name(self):
        """ Changing starting point sim should trigger a recomputation of cp
        """
        optim_builder = self.make_optimizer_builder()
        optim_builder.experiment_selected = ['Run_1']
        self.assertEqual(optim_builder.starting_point_simulation_name,
                         'Sim: Run_1')
        self.assertEqual(len(optim_builder.starting_point_simulations), 1)
        first_cp = optim_builder.starting_point_simulations[0]
        self.assertIsNot(first_cp, self.sim1)
        assert_has_traits_almost_equal(first_cp, self.sim1,
                                       check_type=False)

        with self.assertTraitChanges(optim_builder,
                                     "starting_point_simulations", 1):
            optim_builder.starting_point_simulation_name = 'Sim: Run_2'

        first_cp = optim_builder.starting_point_simulations[0]
        self.assertEqual(len(optim_builder.starting_point_simulations), 1)
        # The target experiment is still Run_1 so the resulting sim ~ sim1
        assert_has_traits_almost_equal(first_cp, self.sim1,
                                       check_type=False)
        self.assertIsInstance(first_cp, LazyLoadingSimulation)
        # But several quantities are pulled from the specified starting point
        self.assertEqual(first_cp.method.method_steps[0].name,
                         self.sim2.method.method_steps[0].name)
        self.assertEqual(first_cp.method.method_steps[-1].name,
                         self.sim2.method.method_steps[-1].name)

        # Choosing a different name
        with self.assertTraitDoesNotChange(optim_builder,
                                           "starting_point_simulations"):
            with self.assertRaises(KeyError):
                # Reraise the exception because it happens in listener
                with reraise_traits_notification_exceptions():
                    optim_builder.starting_point_simulation_name = \
                        "DOESN'T EXIST!"

    def test_multiple_target_exp_at_creation(self):
        """ Changing target experiments should trigger recomputing cp sims.
        """
        optim_builder = self.make_optimizer_builder('Run_1', 'Run_2')
        self.assertEqual(len(optim_builder.starting_point_simulations), 2)
        first_cp = optim_builder.starting_point_simulations[0]
        second_cp = optim_builder.starting_point_simulations[1]
        # The target experiment is still Run_1 so the resulting sim ~ sim1
        assert_has_traits_almost_equal(first_cp, self.sim1,
                                       check_type=False)
        assert_has_traits_almost_equal(second_cp, self.sim2,
                                       check_type=False)
        self.assertIsInstance(first_cp, LazyLoadingSimulation)
        self.assertIsInstance(second_cp, LazyLoadingSimulation)

    def test_update_experiment_selector(self):
        """ Changing target experiments should trigger recomputating starting
        center point simulations.
        """
        optim_builder = self.make_optimizer_builder()
        self.assertEqual(len(optim_builder.starting_point_simulations), 0)

        optim_builder.experiment_selector = ExperimentSelector(
                study=self.study, experiment_selected=['Run_1', 'Run_2']
            )
        self.assertEqual(len(optim_builder.starting_point_simulations), 2)
        first_cp = optim_builder.starting_point_simulations[0]
        second_cp = optim_builder.starting_point_simulations[1]
        # The target experiment is still Run_1 so the resulting sim ~= sim1
        assert_has_traits_almost_equal(first_cp, self.sim1,
                                       check_type=False)
        assert_has_traits_almost_equal(second_cp, self.sim2,
                                       check_type=False)
        self.assertIsInstance(first_cp, LazyLoadingSimulation)
        self.assertIsInstance(second_cp, LazyLoadingSimulation)

    def test_update_target_exp_after_creation(self):
        """ Changing target experiments should trigger recomputing starting
        center point simulations.
        """
        optim_builder = self.make_optimizer_builder()
        optim_builder.experiment_selected = ['Run_1']
        # Change by overwriting
        with self.assertTraitChanges(optim_builder,
                                     "starting_point_simulations", 1):
            optim_builder.experiment_selected = ['Run_2']

        first_cp = optim_builder.starting_point_simulations[0]
        self.assertEqual(len(optim_builder.starting_point_simulations), 1)
        # The target experiment is still Run_1 so the resulting sim ~ sim1
        assert_has_traits_almost_equal(first_cp, self.sim2,
                                       check_type=False)
        self.assertIsInstance(first_cp, LazyLoadingSimulation)

        # Change by append to the list of target experiences:
        with self.assertTraitChanges(optim_builder,
                                     "starting_point_simulations", 1):
            optim_builder.experiment_selected.append('Run_1')

        self.assertEqual(len(optim_builder.starting_point_simulations), 2)
        first_cp = optim_builder.starting_point_simulations[0]
        second_cp = optim_builder.starting_point_simulations[1]
        # The target experiment is still Run_1 so the resulting sim ~ sim1
        assert_has_traits_almost_equal(first_cp, self.sim2,
                                       check_type=False)
        assert_has_traits_almost_equal(second_cp, self.sim1,
                                       check_type=False)
        self.assertIsInstance(first_cp, LazyLoadingSimulation)
        self.assertIsInstance(second_cp, LazyLoadingSimulation)

    def test_optim_name_rotation(self):
        optim_builder = self.make_optimizer_builder()
        self.assertEqual(optim_builder.optimizer_name, "Optimizer0")
        # Making the second doesn't rotate the name because the study doesn't
        # own any optimizer:
        optim_builder = self.make_optimizer_builder()
        self.assertEqual(optim_builder.optimizer_name, "Optimizer0")

        # Store an optimizer
        optim = make_sample_binding_model_optimizer(5, name="Optimizer0")
        self.study.analysis_tools.optimizations.append(optim)
        optim_builder = self.make_optimizer_builder()
        self.assertEqual(optim_builder.optimizer_name, "Optimizer1")

    def test_target_exp_different_buffers(self):
        # Set each exp to a different initial condition:
        initial_condition_step = 1
        for exp in self.study.experiments:
            buf = Buffer(name="New buf for {}".format(exp.name))
            exp.method.method_steps[initial_condition_step].solutions = [buf]

        optim_builder = self.make_optimizer_builder('Run_1', 'Run_2', 'Run_3')
        initial_buffers = {sim.method.initial_buffer.name for sim in
                           optim_builder.starting_point_simulations}
        expected = {"New buf for {}".format(exp.name)
                    for exp in self.study.experiments}
        self.assertEqual(initial_buffers, expected)

        # Specific initial_buffer can be forced
        optim_builder = self.make_optimizer_builder(
            'Run_1', 'Run_2', 'Run_3', initial_buffer_name='Equil_Wash_1'
        )
        initial_buffers = {sim.method.initial_buffer.name for sim in
                           optim_builder.starting_point_simulations}
        expected = {'Equil_Wash_1' for _ in self.study.experiments}
        self.assertEqual(initial_buffers, expected)

    def test_filter_parameter_options_to_bind_mod(self):
        optim_builder = self.make_optimizer_builder('Run_1')
        optim_builder.new_parameter_button = True
        cp = optim_builder.starting_point_simulations[0]
        num_comp = len(cp.product.product_components)

        p1 = optim_builder.parameter_scans[0]
        self.assertEqual(len(p1.valid_parameter_names), NUM_PARAMETERS)

        # Make sure the parameters options are reduced when adding a filter
        with self.assertTraitChanges(p1, "valid_parameter_names"):
            with self.assertTraitChanges(optim_builder, "allowed_parameters"):
                optim_builder.param_name_filter = "binding_mod"

        # Complete set:
        expected = ['binding_model.sma_lambda']
        for bind_param in ["nu", "ka", "kd", "sigma"]:
            expected += ['binding_model.sma_{}[{}]'.format(bind_param, i)
                         for i in range(num_comp+1)]

        self.assertEqual(set(p1.valid_parameter_names), set(expected))

    def test_filter_parameter_options_to_nu(self):
        optim_builder = self.make_optimizer_builder('Run_1')
        cp = optim_builder.starting_point_simulations[0]
        num_comp = len(cp.product.product_components)

        # Make sure the parameters options are reduced when adding a filter
        with self.assertTraitChanges(optim_builder, "allowed_parameters"):
            optim_builder.param_name_filter = "nu"

        optim_builder.new_parameter_button = True
        expected = ['binding_model.sma_nu[{}]'.format(i)
                    for i in range(num_comp+1)]
        p1 = optim_builder.parameter_scans[0]
        self.assertEqual(set(p1.valid_parameter_names), set(expected))

    def test_filter_value_change(self):
        optim_builder = self.make_optimizer_builder('Run_1')
        cp = optim_builder.starting_point_simulations[0]
        num_comp = len(cp.product.product_components)

        #: Start with only nu parameters:
        optim_builder.param_name_filter = "nu"
        optim_builder.new_parameter_button = True
        p1 = optim_builder.parameter_scans[0]
        self.assertEqual(p1.name, "binding_model.sma_nu[0]")
        expected = ['binding_model.sma_nu[{}]'.format(i)
                    for i in range(num_comp+1)]
        p1 = optim_builder.parameter_scans[0]
        self.assertEqual(set(p1.valid_parameter_names), set(expected))

        # Change to ka, but make sure the name of existing param hasn't changed
        optim_builder.param_name_filter = "ka"
        expected = ['binding_model.sma_ka[{}]'.format(i)
                    for i in range(num_comp + 1)] + [p1.name]
        p1 = optim_builder.parameter_scans[0]
        self.assertEqual(set(p1.valid_parameter_names), set(expected))

    def test_modify_target_component_list(self):
        optim_builder = self.make_optimizer_builder()
        # By default, all components selected:
        self.assertEqual(optim_builder.component_selected,
                         ['Acidic_2', 'Acidic_1', 'Native'])

        # List can be changed:
        optim_builder.component_selected = ['Acidic_2', 'Acidic_1']
        self.assertEqual(optim_builder.component_selected,
                         ['Acidic_2', 'Acidic_1'])
