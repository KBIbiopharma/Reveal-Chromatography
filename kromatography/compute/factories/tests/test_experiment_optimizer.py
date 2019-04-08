""" Test creating optimizers using ExperimentOptimizer factories.

See also kromatography/ui/tests/test_brute_force_optimizer_builder.py for more
tests and the UI aspects of it.
"""
from unittest import TestCase
import numpy as np

from app_common.traits.assertion_utils import assert_has_traits_almost_equal

from kromatography.model.tests.sample_data_factories import \
    make_sample_study2, make_sample_transport_model, \
    make_sample_optimizer_builder
from kromatography.model.parameter_scan_description import DEFAULT_NUM_VALUES,\
    ParameterScanDescription, SMAParameterScanDescription
from kromatography.compute.factories.experiment_optimizer import \
    optimizer_builder_to_optimizer
from kromatography.compute.constant_binding_model_optimizer_step import \
    ConstantBruteForceBindingModelOptimizerStep
from kromatography.compute.brute_force_binding_model_optimizer_step import \
    BruteForceBindingModelOptimizerStep
from kromatography.compute.brute_force_optimizer_step import \
    BruteForceOptimizerStep
from kromatography.compute.brute_force_binding_model_optimizer import \
    BRUTE_FORCE_2STEP_OPTIMIZER_TYPE
from kromatography.compute.brute_force_optimizer import \
    GRID_BASED_OPTIMIZER_TYPE, BruteForceOptimizer
from kromatography.compute.brute_force_binding_model_optimizer import \
    BruteForce2StepBindingModelOptimizer
from kromatography.model.lazy_simulation import LazyLoadingSimulation


class TestOptimizerBuilderToOptimizer(TestCase):
    def setUp(self):
        self.study = make_sample_study2()
        transport_model = make_sample_transport_model()
        self.study.study_datasource.transport_models.append(transport_model)
        self.exp_name = self.study.experiments[0].name

    def test_conversion_no_exp(self):
        builder = make_sample_optimizer_builder(self.study)
        with self.assertRaises(ValueError):
            optimizer_builder_to_optimizer(builder)

    def test_conversion_no_scan_param(self):
        builder = make_sample_optimizer_builder(
            self.study, self.exp_name,
            optimizer_type=BRUTE_FORCE_2STEP_OPTIMIZER_TYPE
        )
        with self.assertRaises(ValueError):
            optimizer_builder_to_optimizer(builder)

    def test_conversion_brute_force_with_scan_param(self):
        p1 = ParameterScanDescription(name="binding_model.sma_ka[1]", low=0.,
                                      high=10.)
        p2 = ParameterScanDescription(name="binding_model.sma_nu[1]", low=0.,
                                      high=10.)
        traits = {"parameter_scans": [p1, p2],
                  "optimizer_type": GRID_BASED_OPTIMIZER_TYPE}
        builder = make_sample_optimizer_builder(self.study, self.exp_name,
                                                **traits)
        optimizer = optimizer_builder_to_optimizer(builder)
        self.assertIsInstance(optimizer, BruteForceOptimizer)
        self.assertEqual(len(optimizer.steps), 1)

        optim_step = optimizer.steps[0]
        self.assertIsInstance(optim_step, BruteForceOptimizerStep)
        scanned = [p.name for p in optim_step.parameter_list]
        expected_scanned = ["binding_model.sma_ka[1]",
                            "binding_model.sma_nu[1]"]
        self.assertEqual(set(scanned), set(expected_scanned))
        self.assertLazyLoadingGroups(optim_step)
        group = optim_step.simulation_groups[0]
        self.assertEqual(group.size, DEFAULT_NUM_VALUES**2)

    def test_all_target_components_by_default(self):
        p1 = ParameterScanDescription(name="binding_model.sma_ka[1]", low=0.,
                                      high=10.)
        traits = {"parameter_scans": [p1],
                  "optimizer_type": GRID_BASED_OPTIMIZER_TYPE}
        builder = make_sample_optimizer_builder(self.study, self.exp_name,
                                                **traits)
        optimizer = optimizer_builder_to_optimizer(builder)
        all_comps = ['Acidic_2', 'Acidic_1', 'Native']
        self.assertEqual(optimizer.target_components, all_comps)
        optim_step = optimizer.steps[0]
        self.assertEqual(optim_step.target_components, all_comps)

    def test_control_target_components(self):
        p1 = ParameterScanDescription(name="binding_model.sma_ka[1]", low=0.,
                                      high=10.)
        traits = {"parameter_scans": [p1],
                  "optimizer_type": GRID_BASED_OPTIMIZER_TYPE,
                  "component_selected": ['Acidic_2', 'Acidic_1']}
        builder = make_sample_optimizer_builder(self.study, self.exp_name,
                                                **traits)
        optimizer = optimizer_builder_to_optimizer(builder)
        self.assertEqual(optimizer.target_components, ['Acidic_2', 'Acidic_1'])
        optim_step = optimizer.steps[0]
        self.assertEqual(optim_step.target_components,
                         ['Acidic_2', 'Acidic_1'])

    def test_conversion_binding_optim_with_scan_param(self):
        p1 = SMAParameterScanDescription(name="sma_ka")
        p2 = SMAParameterScanDescription(name="sma_nu")
        traits = {"parameter_scans": [p1, p2],
                  "optimizer_type": BRUTE_FORCE_2STEP_OPTIMIZER_TYPE}
        builder = make_sample_optimizer_builder(self.study, self.exp_name,
                                                **traits)
        optimizer = optimizer_builder_to_optimizer(builder)
        self.assertIsInstance(optimizer, BruteForce2StepBindingModelOptimizer)

        num_comp = len(optimizer.steps[0].component_names)
        self.assertEqual(len(optimizer.steps), 1 + num_comp)

        const_step = optimizer.steps[0]
        self.assertIsInstance(const_step,
                              ConstantBruteForceBindingModelOptimizerStep)
        scanned = {p.name for p in const_step.parameter_list}
        expected_scanned = {"binding_model.sma_ka[1:]",
                            "binding_model.sma_nu[1:]"}
        self.assertEqual(scanned, expected_scanned)
        self.assertLazyLoadingGroups(const_step)

        refine_step = optimizer.steps[1]
        self.assertIsInstance(refine_step, BruteForceBindingModelOptimizerStep)
        # Param list empty until the step0 is run:
        self.assertEqual(refine_step.parameter_list, [])

    def test_conversion_brute_force_with_parallel_parameters(self):
        p1name = "binding_model.sma_ka[1]"
        p2name = "binding_model.sma_nu[1]"
        p1 = ParameterScanDescription(name=p1name)
        p2 = ParameterScanDescription(name=p2name, parallel_parameters=[p1])
        traits = {"parameter_scans": [p2],
                  "optimizer_type": GRID_BASED_OPTIMIZER_TYPE}
        builder = make_sample_optimizer_builder(self.study, self.exp_name,
                                                **traits)
        optimizer = optimizer_builder_to_optimizer(builder)
        self.assertIsInstance(optimizer, BruteForceOptimizer)
        self.assertEqual(optimizer.size, DEFAULT_NUM_VALUES)
        self.assertEqual(len(optimizer.steps), 1)

        optim_step = optimizer.steps[0]
        self.assertIsInstance(optim_step, BruteForceOptimizerStep)
        self.assertEqual(optim_step.size, DEFAULT_NUM_VALUES)
        main_scanned = {p.name for p in optim_step.parameter_list}
        # The list only contains the 1 parameter passed as the main param
        self.assertEqual(main_scanned, {p2name})
        # But the scanned parameters are both parallel params:
        expected_scanned = {p1name, p2name}
        self.assertEqual(set(optim_step.scanned_param_names), expected_scanned)
        self.assertLazyLoadingGroups(optim_step)
        group = optim_step.simulation_groups[0]
        self.assertEqual(group.size, DEFAULT_NUM_VALUES)
        # Make sure that parameters were scanned in parallel:
        nus = [sim.binding_model.sma_nu[1] for sim in group.simulations]
        self.assertEqual(nus, list(np.linspace(0, 1., DEFAULT_NUM_VALUES)))
        kas = [sim.binding_model.sma_ka[1] for sim in group.simulations]
        self.assertEqual(kas, list(np.linspace(0, 1., DEFAULT_NUM_VALUES)))

    def test_conversion_brute_force_with_custom_discretization(self):
        p1name = "binding_model.sma_ka[1]"
        p1 = ParameterScanDescription(name=p1name)
        traits = {"parameter_scans": [p1],
                  "optimizer_type": GRID_BASED_OPTIMIZER_TYPE}
        builder = make_sample_optimizer_builder(self.study, self.exp_name,
                                                **traits)
        # Customize discretization
        sim0 = self.study.search_simulation_by_name(
            builder.starting_point_simulation_name)
        sim0.discretization.ncol = 30
        builder.update_starting_point_simulations()
        optimizer = optimizer_builder_to_optimizer(builder)
        self.assertIsInstance(optimizer, BruteForceOptimizer)
        self.assertEqual(optimizer.size, DEFAULT_NUM_VALUES)
        self.assertEqual(len(optimizer.steps), 1)
        # Make sure the custom discretization was reused:
        for step in optimizer.steps:
            for group in step.simulation_groups:
                cp = group.center_point_simulation
                assert_has_traits_almost_equal(cp.discretization,
                                               sim0.discretization)

    def test_conversion_brute_force_with_custom_solver(self):
        p1name = "binding_model.sma_ka[1]"
        p1 = ParameterScanDescription(name=p1name)
        traits = {"parameter_scans": [p1],
                  "optimizer_type": GRID_BASED_OPTIMIZER_TYPE}
        builder = make_sample_optimizer_builder(self.study, self.exp_name,
                                                **traits)
        sim0 = self.study.search_simulation_by_name(
            builder.starting_point_simulation_name)
        # Customize solver
        sim0.solver.number_user_solution_points = 500
        builder.update_starting_point_simulations()
        optimizer = optimizer_builder_to_optimizer(builder)
        self.assertIsInstance(optimizer, BruteForceOptimizer)
        self.assertEqual(optimizer.size, DEFAULT_NUM_VALUES)
        self.assertEqual(len(optimizer.steps), 1)
        # Make sure the custom solver was reused:
        for step in optimizer.steps:
            for group in step.simulation_groups:
                cp = group.center_point_simulation
                self.assertEqual(cp.solver.number_user_solution_points, 500)

    # Helper methods ----------------------------------------------------------

    def assertLazyLoadingGroups(self, step):
        self.assertEqual(len(step.simulation_groups), 1)
        group = step.simulation_groups[0]
        group.initialize_simulations()
        for sim in group.simulations:
            self.assertIsInstance(sim, LazyLoadingSimulation)

        # Make sure simulations have distinct uuids and therefore cadet file
        uuids = [sim.uuid for sim in group.simulations]
        self.assertEqual(len(uuids), len(set(uuids)))

        files = [sim.cadet_filepath for sim in group.simulations]
        self.assertEqual(len(files), len(set(files)))
