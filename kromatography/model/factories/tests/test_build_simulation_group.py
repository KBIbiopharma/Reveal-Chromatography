
from unittest import TestCase
from numpy.testing import assert_array_almost_equal

from numpy import array, float64, linspace

from kromatography.model.simulation_group import SIM_COL_NAME, \
    SIM_GROUP_GRID_TYPE, SIM_GROUP_MC_TYPE, Simulation, SimulationGroup, \
    SingleParamSimulationDiff
from kromatography.model.parameter_scan_description import \
    ParameterScanDescription
from kromatography.model.random_parameter_scan_description import \
    RandomParameterScanDescription
from kromatography.model.lazy_simulation import LazyLoadingSimulation
from kromatography.model.tests.sample_data_factories import \
    make_sample_study2
from kromatography.model.factories.simulation_group import \
    build_random_simulation_group, build_simulation_grid, \
    param_scans_to_sim_group, sim_diffs_from_grid_parameter_scans, \
    sim_diffs_from_random_parameter_scans
from kromatography.model.tests.sample_data_factories import \
    make_sample_simulation
from kromatography.utils.assertion_utils import \
    assert_has_traits_almost_equal

NUM_VALUES = 10


class TestSimGridBuilder(TestCase):
    def setUp(self):
        study = make_sample_study2(add_transp_bind_models=True,
                                   add_sims='Run_1')
        self.std_sim = study.simulations[0]

    def test_sim_group_1_param(self):
        p1 = ParameterScanDescription(name="binding_model.sma_nu[1]", low=4,
                                      high=6, num_values=NUM_VALUES)
        group = param_scans_to_sim_group("test group", [p1], self.std_sim)
        self.assertValidSimGroup(group)

    def test_sim_group_2_param(self):
        p1 = ParameterScanDescription(name="binding_model.sma_nu[1]", low=4,
                                      high=6, num_values=NUM_VALUES)
        p2 = ParameterScanDescription(name="binding_model.sma_nu[2]", low=4,
                                      high=6, num_values=NUM_VALUES)
        group = param_scans_to_sim_group("test group", [p1, p2], self.std_sim)
        self.assertValidSimGroup(group, num_params=2)

    def test_sim_group_from_lazy_sim(self):
        sim = LazyLoadingSimulation.from_simulation(self.std_sim)

        p1 = ParameterScanDescription(name="binding_model.sma_nu[1]", low=4,
                                      high=6, num_values=NUM_VALUES)
        group = param_scans_to_sim_group("test group", [p1], sim)
        self.assertValidSimGroup(group)
        self.assertLazySimGroup(group)

    def test_lazy_sim_group_from_in_memory_sim(self):
        p1 = ParameterScanDescription(name="binding_model.sma_nu[1]", low=4,
                                      high=6, num_values=NUM_VALUES)
        group = param_scans_to_sim_group("test group", [p1], self.std_sim,
                                         lazy_loading=True)
        self.assertValidSimGroup(group)
        self.assertLazySimGroup(group)

    def test_group_data_column_order(self):
        p1 = ParameterScanDescription(name="binding_model.sma_nu[1]", low=4,
                                      high=6, num_values=NUM_VALUES)
        group = param_scans_to_sim_group("test group", [p1], self.std_sim)
        cols = group.group_data.columns.tolist()
        self.assertEqual(cols.index(p1.name), 1)

        # Make sure the order isn't alphabetical by selecting another parameter
        # with a name late in the alphabet:
        p2 = ParameterScanDescription(name="transport_model.bead_porosity",
                                      low=0.4, high=0.6, num_values=NUM_VALUES)
        group = param_scans_to_sim_group("test group", [p1, p2], self.std_sim)
        cols = group.group_data.columns.tolist()
        self.assertEqual(cols.index(p1.name), 1)
        self.assertEqual(cols.index(p2.name), 2)

    def test_change_nthreads_preferences(self):
        """ Make sure group conforms nthreads to preferences, not source sim.
        """
        from kromatography.utils.app_utils import get_preferences
        prefs = get_preferences()
        target_nthreads = prefs.solver_preferences.cadet_num_threads

        self.std_sim.solver.nthreads = target_nthreads+1
        p1 = ParameterScanDescription(name="binding_model.sma_nu[1]", low=4,
                                      high=6, num_values=NUM_VALUES)
        group = param_scans_to_sim_group("test group", [p1], self.std_sim)
        group.initialize_simulations()
        for sim in group.simulations:
            self.assertEqual(sim.solver.nthreads, target_nthreads)

    # Helper methods ----------------------------------------------------------

    def assertValidSimGroup(self, group, num_params=1):
        self.assertIsInstance(group, SimulationGroup)
        self.assertEqual(group.type, SIM_GROUP_GRID_TYPE)
        self.assertEqual(len(group.simulation_diffs), NUM_VALUES ** num_params)
        self.assertIsInstance(group.center_point_simulation, Simulation)
        self.assertFalse(group.has_run)
        for sim_diff in group.simulation_diffs:
            self.assertEqual(len(sim_diff), num_params)
            self.assertIsInstance(sim_diff[0], SingleParamSimulationDiff)

        self.assertEqual(group.group_data.dtypes.loc[SIM_COL_NAME], object)
        for i in range(len(group.group_data.dtypes)-1):
            self.assertEqual(group.group_data.dtypes.iloc[i+1], float64)

    def assertLazySimGroup(self, group):
        self.assertIsInstance(group.center_point_simulation,
                              LazyLoadingSimulation)
        self.assertTrue(group.is_lazy_loading)
        group.initialize_simulations()
        for sim in group.simulations:
            self.assertIsInstance(sim, LazyLoadingSimulation)


class TestBuildSimulationGridScriptApi(TestCase):
    def setUp(self):
        self.sim = make_sample_simulation()
        self.param1 = "binding_model.sma_ka[1]"
        self.param2 = "binding_model.sma_nu[1]"

    def test_build_sim_group_1d(self):
        val_ranges = 0.1
        grid = build_simulation_grid(self.sim, [self.param1],
                                     num_values=NUM_VALUES,
                                     val_ranges=val_ranges)
        cp = grid.center_point_simulation
        self.assertIsInstance(cp, LazyLoadingSimulation)
        assert_has_traits_almost_equal(cp, self.sim, check_type=False)
        self.assertEqual(len(grid.simulation_diffs), NUM_VALUES)

        for diff in grid.simulation_diffs:
            self.assertEqual(len(diff), 1)
            single_diff = diff[0]
            self.assertEqual(single_diff.extended_attr, self.param1)

        vals = array([diff[0].val for diff in grid.simulation_diffs])
        cp_val = eval("sim.{}".format(self.param1), {"sim": self.sim})
        min_val = cp_val * (1 - val_ranges)
        max_val = cp_val * (1 + val_ranges)
        assert_array_almost_equal(vals, linspace(min_val, max_val, NUM_VALUES))

        self.assertEqual(grid.simulations, [])
        grid.initialize_simulations()
        self.assertEqual(len(grid.simulations), NUM_VALUES)

    def test_build_sim_group_2d(self):
        val_ranges = 0.1
        params = [self.param1, self.param2]
        grid = build_simulation_grid(self.sim, params,
                                     num_values=NUM_VALUES,
                                     val_ranges=val_ranges)
        cp = grid.center_point_simulation
        self.assertIsInstance(cp, LazyLoadingSimulation)
        assert_has_traits_almost_equal(cp, self.sim, check_type=False)
        self.assertEqual(len(grid.simulation_diffs), NUM_VALUES**2)

        for diff in grid.simulation_diffs:
            self.assertEqual(len(diff), 2)
            single_diff = diff[0]
            self.assertIn(single_diff.extended_attr, params)

        diffs = grid.simulation_diffs
        vals = array([diff[0].val
                      for diff in diffs[:NUM_VALUES**2:NUM_VALUES]])
        cp_val = eval("sim.{}".format(self.param1), {"sim": self.sim})
        min_val = cp_val * (1 - val_ranges)
        max_val = cp_val * (1 + val_ranges)
        assert_array_almost_equal(vals, linspace(min_val, max_val, NUM_VALUES))

        vals = array([diff[1].val for diff in diffs[:NUM_VALUES]])
        cp_val = eval("sim.{}".format(self.param2), {"sim": self.sim})
        min_val = cp_val * (1 - val_ranges)
        max_val = cp_val * (1 + val_ranges)
        assert_array_almost_equal(vals, linspace(min_val, max_val, NUM_VALUES))

        self.assertEqual(grid.simulations, [])
        grid.initialize_simulations()
        self.assertEqual(len(grid.simulations), NUM_VALUES**2)


class TestBuildMCSimulationGroupScriptApi(TestCase):
    def setUp(self):
        self.sim = make_sample_simulation()
        self.param_names = ["method.method_steps[0].solutions[0].pH",
                            "method.method_steps[0].volume"]
        self.group_size = 50
        self.dist_desc_list = [(4., 6.), (3., 5.)]
        # pH and step volume are parameters that will be changed. That will
        # imply changes to the user_solution_times, section_times and
        # method_step_boundary_times:
        self.ignore = ["pH", "volume", "name", "user_solution_times",
                       "section_times", "method_step_boundary_times"]

    def test_fail_make_mc_group_no_desc(self):
        param_names = ["method.method_steps[0].solutions[0].pH",
                       "method.method_steps[0].volume"]
        dist_desc_list = []
        with self.assertRaises(AssertionError):
            build_random_simulation_group(
                self.sim, param_names, group_size=10,
                dist_types="uniform", dist_desc=dist_desc_list,
            )

    def test_make_mc_group_no_param(self):
        param_names = []
        group = build_random_simulation_group(
                self.sim, param_names, group_size=10,
                dist_types="uniform", dist_desc=[],
            )
        self.assertIsNone(group)

    def test_make_mc_group_no_size(self):
        param_names = ["method.method_steps[0].solutions[0].pH"]
        group = build_random_simulation_group(
                self.sim, param_names, group_size=0,
                dist_types="uniform", dist_desc=[(4., 6.)],
            )
        self.assertIsNone(group)

    def test_make_uniform_mc_group(self):
        group = build_random_simulation_group(
            self.sim, self.param_names, group_size=self.group_size,
            dist_types="uniform", dist_desc=self.dist_desc_list,
        )
        self.assertIsInstance(group, SimulationGroup)
        self.assertEqual(group.type, SIM_GROUP_MC_TYPE)
        self.assertEqual(group.size, self.group_size)
        group.initialize_simulations()
        group.initialize_group_data()
        for param, desc in zip(self.param_names, self.dist_desc_list):
            vec = group.group_data[param].astype(float)
            self.assertTrue(((desc[0] <= vec) & (vec < desc[1])).all())
            expected_mean = (desc[1] + desc[0])/2.
            self.assertAlmostEqual(vec.mean(), expected_mean, places=0)

        for sim in group.simulations:
            assert_has_traits_almost_equal(sim, self.sim,
                                           ignore=self.ignore)
            for param in self.param_names:
                cp_val = eval("sim.{}".format(param), {"sim": self.sim})
                val = eval("sim.{}".format(param), {"sim": sim})
                self.assertNotAlmostEqual(val, cp_val)

    def test_make_gaussian_mc_group(self):
        dist_desc_list = [(5., 1.), (4., 1.)]
        group = build_random_simulation_group(
            self.sim, self.param_names, group_size=self.group_size,
            dist_types="normal", dist_desc=dist_desc_list,
        )
        self.assertIsInstance(group, SimulationGroup)
        self.assertEqual(group.type, SIM_GROUP_MC_TYPE)
        self.assertEqual(group.size, self.group_size)
        group.initialize_simulations()
        group.initialize_group_data()
        for param, desc in zip(self.param_names, dist_desc_list):
            vec = group.group_data[param].astype(float)
            expected_mean = desc[0]
            expected_std = desc[1]
            self.assertAlmostEqual(vec.mean(), expected_mean, places=0)
            self.assertAlmostEqual(vec.std(), expected_std, places=0)

        for sim in group.simulations:
            assert_has_traits_almost_equal(sim, self.sim,
                                           ignore=self.ignore)
            for param in self.param_names:
                cp_val = eval("sim.{}".format(param), {"sim": self.sim})
                val = eval("sim.{}".format(param), {"sim": sim})
                self.assertNotAlmostEqual(val, cp_val)

    def test_lazy_sim_group(self):
        group = build_random_simulation_group(
            self.sim, self.param_names, group_size=self.group_size,
            dist_types="uniform", dist_desc=self.dist_desc_list,
            lazy_loading=True
        )
        self.assertIsInstance(group, SimulationGroup)
        self.assertEqual(group.type, SIM_GROUP_MC_TYPE)
        self.assertEqual(group.size, self.group_size)
        group.initialize_simulations()
        for sim in group.simulations:
            assert_has_traits_almost_equal(sim, self.sim,
                                           ignore=self.ignore,
                                           check_type=False)
            self.assertIsInstance(sim, LazyLoadingSimulation)

    def test_make_uniform_mc_group_coupled_params(self):
        load = "method.method_steps[0].solutions[0]"
        param_names = ["method.method_steps[0].volume",
                       load + ".product_component_assay_values[1]"]

        def compute_assay_conc(main_conc):
            return 100 - main_conc - 3.4

        dist_desc_list = [(3., 5.), (86, 90)]
        adtl_params = {
            param_names[1]:
                [(load + ".product_component_assay_values[0]",
                  compute_assay_conc)]
        }

        group_size = 20
        group = build_random_simulation_group(
            self.sim, param_names, group_size=group_size,
            dist_types="uniform", dist_desc=dist_desc_list,
            adtl_params=adtl_params
        )
        self.assertIsInstance(group, SimulationGroup)
        self.assertEqual(group.type, SIM_GROUP_MC_TYPE)
        self.assertEqual(group.size, group_size)
        # Make sure the group builds valid simulations
        group.initialize_simulations()
        group.initialize_group_data()
        # Make sure that the simulation diffs are as expected:
        for sim in group.simulations:
            vol = sim.method.method_steps[0].volume
            self.assertLess(vol, 5.)
            self.assertGreaterEqual(vol, 3.)

            load_sol = sim.method.method_steps[0].solutions[0]
            main_conc = load_sol.product_component_assay_values[1]
            self.assertLess(main_conc, 90)
            self.assertGreaterEqual(main_conc, 86)
            total = load_sol.product_component_assay_values.sum()
            self.assertAlmostEqual(float(total), 100.)


class TestBuildMCSimulationGroupAppApi(TestCase):
    def setUp(self):
        self.sim = make_sample_simulation()
        self.param_names = ["method.method_steps[0].solutions[0].pH",
                            "method.method_steps[0].volume"]
        self.group_size = 50
        self.group_name = "NEW GROUP"
        self.dist_desc_list = [(4., 6.), (3., 5.)]
        # pH and step volume are parameters that will be changed. That will
        # imply changes to the user_solution_times, section_times and
        # method_step_boundary_times:
        self.ignore = ["pH", "volume", "name", "user_solution_times",
                       "section_times", "method_step_boundary_times"]

    def test_make_uniform_mc_group_2_params(self):
        param_scans = []
        for name, desc in zip(self.param_names, self.dist_desc_list):
            p = RandomParameterScanDescription(
                name=name, distribution="Uniform", dist_param1=desc[0],
                dist_param2=desc[1], target_simulation=self.sim
            )
            param_scans.append(p)

        group = param_scans_to_sim_group(
            self.group_name, param_scans, self.sim,
            group_type=SIM_GROUP_MC_TYPE, group_size=self.group_size,
        )
        self.assertIsInstance(group, SimulationGroup)
        self.assertEqual(group.type, SIM_GROUP_MC_TYPE)
        self.assertEqual(group.size, self.group_size)
        self.assertEqual(group.name, self.group_name)
        group.initialize_simulations()
        group.initialize_group_data()
        for param, desc in zip(self.param_names, self.dist_desc_list):
            vec = group.group_data[param].astype(float)
            self.assertTrue(((desc[0] <= vec) & (vec < desc[1])).all())
            expected_mean = (desc[1] + desc[0])/2.
            self.assertAlmostEqual(vec.mean(), expected_mean, places=0)

        for sim in group.simulations:
            assert_has_traits_almost_equal(sim, self.sim,
                                           ignore=self.ignore)
            for param in self.param_names:
                cp_val = eval("sim.{}".format(param), {"sim": self.sim})
                val = eval("sim.{}".format(param), {"sim": sim})
                self.assertNotAlmostEqual(val, cp_val)

    def test_make_gaussian_mc_group_2_params(self):
        dist_desc_list = [(5., 1.), (4., 1.)]
        param_scans = []
        for name, desc in zip(self.param_names, dist_desc_list):
            p = RandomParameterScanDescription(
                name=name, distribution="Gaussian", dist_param1=desc[0],
                dist_param2=desc[1], target_simulation=self.sim
            )
            param_scans.append(p)

        group = param_scans_to_sim_group(
            self.group_name, param_scans, self.sim,
            group_type=SIM_GROUP_MC_TYPE, group_size=self.group_size,
        )
        self.assertIsInstance(group, SimulationGroup)
        self.assertEqual(group.type, SIM_GROUP_MC_TYPE)
        self.assertEqual(group.size, self.group_size)
        self.assertEqual(group.name, self.group_name)
        group.initialize_simulations()
        group.initialize_group_data()
        for param, desc in zip(self.param_names, dist_desc_list):
            vec = group.group_data[param].astype(float)
            expected_mean = desc[0]
            expected_std = desc[1]
            self.assertAlmostEqual(vec.mean(), expected_mean, places=0)
            self.assertAlmostEqual(vec.std(), expected_std, places=0)


class TestSimDiffsFromGridParamScans(TestCase):
    def setUp(self):
        self.num_values_per_param = 2

    def test_create_diffs_from_2_ortho_params(self):
        parameters = [
            ParameterScanDescription(
                name="method.method_steps[2].flow_rate",
                low=50, high=100, num_values=self.num_values_per_param
            ),
            ParameterScanDescription(
                name="method.collection_criteria.start_collection_target",
                low=30, high=60, num_values=self.num_values_per_param
            ),
        ]
        diffs = sim_diffs_from_grid_parameter_scans(parameters)
        self.assertEqual(len(diffs), self.num_values_per_param ** 2)
        for sim_diff in diffs:
            self.assertIsInstance(sim_diff, (tuple, list))
            for single_diff in sim_diff:
                self.assertIsInstance(single_diff, SingleParamSimulationDiff)

            params = {d.extended_attr for d in sim_diff}
            expected = {"method.method_steps[2].flow_rate",
                        "method.collection_criteria.start_collection_target"}
            self.assertEqual(params, expected)

        values = {tuple(float(d.val) for d in sim_diff) for sim_diff in diffs}
        expected = {(50., 30.), (50., 60.), (100., 30.), (100., 60.)}
        self.assertEqual(values, expected)

    def test_create_diffs_from_3_ortho_params(self):
        parameters = [
            ParameterScanDescription(
                name="method.method_steps[2].flow_rate",
                low=50, high=100, num_values=self.num_values_per_param
            ),
            ParameterScanDescription(
                name="method.collection_criteria.start_collection_target",
                low=30, high=60, num_values=self.num_values_per_param
            ),
            ParameterScanDescription(
                 name="method.collection_criteria.stop_collection_target",
                 low=20, high=40, num_values=self.num_values_per_param
            )
        ]
        diffs = sim_diffs_from_grid_parameter_scans(parameters)
        self.assertEqual(len(diffs), self.num_values_per_param ** 3)
        for sim_diff in diffs:
            self.assertIsInstance(sim_diff, (tuple, list))
            for single_diff in sim_diff:
                self.assertIsInstance(single_diff, SingleParamSimulationDiff)

            params = {d.extended_attr for d in sim_diff}
            expected = {"method.method_steps[2].flow_rate",
                        "method.collection_criteria.start_collection_target",
                        "method.collection_criteria.stop_collection_target"}
            self.assertEqual(params, expected)

        values = {tuple(float(d.val) for d in sim_diff) for sim_diff in diffs}
        expected = {(50.0, 60.0, 40.0), (100.0, 60.0, 40.0),
                    (100.0, 30.0, 20.0), (50.0, 30.0, 20.0),
                    (50.0, 60.0, 20.0), (100.0, 60.0, 20.0),
                    (100.0, 30.0, 40.0), (50.0, 30.0, 40.0)}
        self.assertEqual(values, expected)

    def test_create_diffs_from_2_ortho_params_1_parallel(self):
        parameters = [
            ParameterScanDescription(
                name="method.method_steps[2].flow_rate",
                low=50, high=100, num_values=self.num_values_per_param
            ),
            # Vary start and stop collect together, rather than orthogonally:
            (ParameterScanDescription(
                name="method.collection_criteria.start_collection_target",
                low=30, high=60, num_values=self.num_values_per_param
             ),
             ParameterScanDescription(
                 name="method.collection_criteria.stop_collection_target",
                 low=20, high=40, num_values=self.num_values_per_param
             ))
        ]
        diffs = sim_diffs_from_grid_parameter_scans(parameters)
        self.assertEqual(len(diffs), self.num_values_per_param ** 2)
        for sim_diff in diffs:
            self.assertIsInstance(sim_diff, (tuple, list))
            for single_diff in sim_diff:
                self.assertIsInstance(single_diff, SingleParamSimulationDiff)

            params = {d.extended_attr for d in sim_diff}
            expected = {"method.method_steps[2].flow_rate",
                        "method.collection_criteria.start_collection_target",
                        "method.collection_criteria.stop_collection_target"}
            self.assertEqual(params, expected)

        values = {tuple(float(d.val) for d in sim_diff) for sim_diff in diffs}
        expected = {(50.0, 60.0, 40.0), (100.0, 60.0, 40.0),
                    (100.0, 30.0, 20.0), (50.0, 30.0, 20.0)}
        self.assertEqual(values, expected)


class TestSimDiffsFromRandomParamScans(TestCase):
    def setUp(self):
        self.num_values_per_param = 20

    def test_create_diffs_no_params(self):
        scans = []
        diffs = sim_diffs_from_random_parameter_scans(scans, 5)
        self.assertEqual(diffs, [])

    def test_create_diffs_from_2_indep_params(self):
        scans = [
            RandomParameterScanDescription(
                name="method.method_steps[2].flow_rate",
                distribution="uniform",
                dist_param1=50, dist_param2=100
            ),
            RandomParameterScanDescription(
                name="method.collection_criteria.start_collection_target",
                distribution="uniform",
                dist_param1=30, dist_param2=50
            ),
        ]
        diffs = sim_diffs_from_random_parameter_scans(
            scans, self.num_values_per_param
        )
        self.assertEqual(len(diffs), self.num_values_per_param)
        for diff in diffs:
            self.assertEqual(len(diff), 2)
            expected = ["method.method_steps[2].flow_rate",
                        "method.collection_criteria.start_collection_target"]
            params = [sing_diff.extended_attr for sing_diff in diff]
            self.assertEqual(params, expected)

        flow_rates = [diff[0].val for diff in diffs]
        for fr in flow_rates:
            self.assertGreaterEqual(fr, 50)
            self.assertLess(fr, 100)

        start_colls = [diff[1].val for diff in diffs]
        for sc in start_colls:
            self.assertGreaterEqual(sc, 30)
            self.assertLess(sc, 50)

    def test_create_diffs_from_2_indep_params_1_dep_param(self):
        scans = [
            RandomParameterScanDescription(
                name="method.method_steps[2].flow_rate",
                distribution="uniform",
                dist_param1=50, dist_param2=100
            ),
            RandomParameterScanDescription(
                name="method.collection_criteria.start_collection_target",
                distribution="uniform",
                dist_param1=30, dist_param2=50
            ),
        ]
        col_crit = "method.collection_criteria."
        adtl_params = {
            col_crit + "start_collection_target":
                [(col_crit + "stop_collection_target", lambda x: 100-x)]
        }

        diffs = sim_diffs_from_random_parameter_scans(
            scans, self.num_values_per_param, adtl_params=adtl_params
        )
        self.assertEqual(len(diffs), self.num_values_per_param)
        for diff in diffs:
            self.assertEqual(len(diff), 3)
            expected = ["method.method_steps[2].flow_rate",
                        col_crit + "start_collection_target",
                        col_crit + "stop_collection_target"]
            params = [sing_diff.extended_attr for sing_diff in diff]
            self.assertEqual(params, expected)

        flow_rates = [diff[0].val for diff in diffs]
        for fr in flow_rates:
            self.assertGreaterEqual(fr, 50)
            self.assertLess(fr, 100)

        start_colls = [diff[1].val for diff in diffs]
        stop_colls = [diff[2].val for diff in diffs]
        for start, stop in zip(start_colls, stop_colls):
            self.assertGreaterEqual(start, 30)
            self.assertLess(start, 50)
            self.assertGreaterEqual(stop, 50)
            self.assertLess(stop, 70)
            self.assertAlmostEqual(start+stop, 100)
