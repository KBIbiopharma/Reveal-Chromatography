from numpy import ndarray
import pandas as pd

from traits.testing.unittest_tools import UnittestTools

from kromatography.compute.brute_force_optimizer_step import \
    ALL_COST_COL_NAME, SIM_COL_NAME
from kromatography.compute.cost_functions import CostFunction0
from kromatography.model.factories.job_manager import create_start_job_manager
from kromatography.compute.brute_force_optimizer_step import \
    BruteForceOptimizerStep
from kromatography.utils.string_definitions import MULTI_SIM_RUNNER_CREATED, \
    MULTI_SIM_RUNNER_FINISHED, MULTI_SIM_RUNNER_RUNNING
from kromatography.model.api import LazyLoadingSimulation

# Amount of time to wait to make sure that an async optimizer step has time to
# run
STEP_RUN_TIME = 15


class BaseTestOptimizer(UnittestTools):
    """ Base test class defining how to run a general grid search optimizer and
    test it has run.
    """
    @classmethod
    def setUpClass(cls):
        # Avoid over-allocating work processes to avoid crashing OS
        cls.job_manager = create_start_job_manager(max_workers=2)

    @classmethod
    def tearDownClass(cls):
        cls.job_manager.shutdown()

    # Helpers -----------------------------------------------------------------

    def run_and_assert_optimizer_and_steps(self, optim,
                                           step_run_time=STEP_RUN_TIME):
        """ Run the optimizer and assert that status and has_run attrs are set
        """
        step0 = optim.steps[0]
        # The async is needed because the job_manager.wait only waits for the
        # step 0 to be over, at which point, the job scheduler is temporarily
        # empty of jobs.
        with self.assertTraitChangesAsync(optim, "has_run", count=1,
                                          timeout=step_run_time):
            with self.assertTraitChangesAsync(step0, "has_run", count=1,
                                              timeout=step_run_time):
                # Status moves to running and then finished:
                with self.assertTraitChanges(optim, "status", count=2):
                    optim.run(self.job_manager, wait=True)

        for step in optim.steps:
            for group in step.simulation_groups:
                for sim in group.simulations:
                    self.assert_simulation_has_run(sim)
                self.assert_group_has_run(group)
                # Check that the step cleaned its groups to reduce memory
                # consumption:
                self.assertEqual(group.simulations, [])
                # But there is the ability to rebuild them:
                for i in range(group.size):
                    rebuilt_sim = group.get_simulation(i)
                    self.assertIsInstance(rebuilt_sim, LazyLoadingSimulation)
                    self.assertTrue(rebuilt_sim.has_run)
                    self.assertFalse(rebuilt_sim.editable)
                    # The editable flag is changed all the way down
                    self.assertFalse(rebuilt_sim.transport_model.editable)

            self.assert_step_has_run(step)

        self.assert_optim_has_run(optim)

    def assert_simulation_has_run(self, sim):
        self.assertTrue(sim.has_run)

    def assert_group_has_run(self, group):
        self.assertTrue(group.has_run)
        self.assertEqual(group.size_run, group.size)
        self.assertEqual(group.percent_run, "{:.2f} %".format(100.))

    def assert_step_has_run(self, step):
        self.assertTrue(step.has_run)
        self.assertEqual(step.status, MULTI_SIM_RUNNER_FINISHED)
        self.assertEqual(step.size_run, step.size)
        self.assertEqual(step.percent_run, "{:.2f} %".format(100.))

    def assert_optim_has_run(self, optim):
        self.assertTrue(optim.has_run)
        self.assertEqual(optim.status, MULTI_SIM_RUNNER_FINISHED)
        # Make sure cost data is the last column
        self.assertEqual(optim.cost_data.columns[-1], ALL_COST_COL_NAME)
        self.assertEqual(optim.size_run, optim.size)
        self.assertEqual(optim.percent_run, "{:.2f} %".format(100.))

    def assert_optimizer_initialized(self, optimizer, num_steps, size,
                                     target_exps='Run_1'):
        self.assertEqual(len(optimizer.steps), num_steps)
        for i in range(num_steps):
            self.assertIsInstance(optimizer.steps[i], BruteForceOptimizerStep)

        exp_list = target_exps.split(",")
        expected_map = {exp_name: [] for exp_name in exp_list}
        self.assertEqual(optimizer.optimal_simulation_map, expected_map)

        self.assertEqual(optimizer.status, MULTI_SIM_RUNNER_CREATED)
        self.assertEqual(optimizer.size, size)
        self.assertEqual(optimizer.target_experiment_names, exp_list)
        for step in optimizer.steps:
            self.assertEqual(step._group_cost_data, {})

        # Make sure cost data is the last column
        self.assertEqual(optimizer.cost_data.columns[-1], ALL_COST_COL_NAME)

    def assert_run_step_correct(self, optim, step_num=0, test_optim_run=True):
        """ Run step number step_num and assert status and has_run attrs.
        """
        step = optim.steps[step_num]
        with self.assertTraitChanges(step, "has_run", count=1):
            runner = optim.run_step(step_num)
            self.assertEqual(step.status, MULTI_SIM_RUNNER_RUNNING)
            self.assertEqual(optim.status, MULTI_SIM_RUNNER_RUNNING)
            runner.wait()
            self.assertEqual(step.status, MULTI_SIM_RUNNER_FINISHED)

        if test_optim_run:
            self.assertTrue(optim.has_run)
            self.assertEqual(optim.status, MULTI_SIM_RUNNER_FINISHED)

    def assert_all_step_sim_lazy(self, step):
        for group in step.simulation_groups:
            for sim in group.simulations:
                self.assertIsInstance(sim, LazyLoadingSimulation)

    def assert_valid_step(self, step, target_experiments, num_sim_per_exp,
                          params):
        """ Assert that provided run step is valid.
        """
        self.assertEqual(set(step.scanned_param_names), params)
        cp = step.simulation_groups[0].center_point_simulation
        components = set(cp.product.product_component_names)

        self.assertEqual(step._group_cost_data.keys(), target_experiments)

        # Step cost data:
        expected_cols = components | {ALL_COST_COL_NAME}
        cost_data = step.cost_data
        self.assertIsInstance(cost_data, pd.DataFrame)
        self.assertEqual(set(cost_data.columns), expected_cols)
        self.assertEqual(len(cost_data), num_sim_per_exp)
        self.assertEqual(set(cost_data.index.names), params)

        # Group cost data (1 group per target experiment):
        expected_cols = components | {ALL_COST_COL_NAME, SIM_COL_NAME}
        for target_exp in target_experiments:
            # Analyze the step cost_data
            cost_data = step._group_cost_data[target_exp]
            # Step cost data computes
            self.assertIsInstance(cost_data, pd.DataFrame)
            self.assertEqual(set(cost_data.columns), expected_cols)
            self.assertEqual(len(cost_data), num_sim_per_exp)
            self.assertEqual(set(cost_data.index.names), params)

        # Cost functions:
        self.assertEqual(step.cost_function_type, 'Position/height/Back-Slope')
        for group in step.simulation_groups:
            name = group.name
            self.assertIn(name, step.group_cost_functions.keys())
            self.assertIsInstance(step.group_cost_functions[name],
                                  CostFunction0)

        num_metrics = 3
        num_comp = len(components)
        # 1 is the number of target experiment for a given cost function.
        # That's almost always 1 since when we target multiple experiments, we
        # create multiple groups and therefore multiple cost functions, one for
        # each target exp.
        expected_exp = (num_metrics, 1, num_comp)
        expected_sim = (num_metrics, num_sim_per_exp, num_comp)
        for group_name, cost_func in step.group_cost_functions.items():
            self.assertIsInstance(cost_func, CostFunction0)
            # Computation data is cached:
            self.assertIsInstance(cost_func.cached_exp_data, ndarray)
            self.assertIsInstance(cost_func.cached_sim_data, ndarray)
            self.assertEqual(cost_func.cached_exp_data.shape, expected_exp)
            self.assertEqual(cost_func.cached_sim_data.shape, expected_sim)

    def assert_step_cost_functions_valid(self, step, comps):
        expected = {'target_components': comps, 'use_uv_for_cost': False}
        for group in step.simulation_groups:
            cost_func = step.group_cost_functions[group.name]
            all_weights = ["peak_time_weight", "peak_height_weight",
                           "peak_slope_weight"]
            expected.update({attr: getattr(cost_func, attr)
                             for attr in all_weights})
            self.assertEqual(step.cost_func_kw, expected)
