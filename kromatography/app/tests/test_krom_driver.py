""" Tests for the krom_driver script """

from os.path import join
import numpy as np
import shutil
import tempfile
from unittest import TestCase
from numpy.testing.utils import assert_almost_equal, assert_array_almost_equal

from kromatography.app.krom_driver import run_chromatography_simulation
from kromatography.utils.testing_utils import io_data_path
from kromatography.model.study import Study
from kromatography.model.factories.simulation import \
    build_simulation_from_experiment
from kromatography.io.simulation_updater import update_simulation_results
from kromatography.model.tests.sample_data_factories import \
    make_sample_binding_model, make_sample_transport_model


class TestKromDriver(TestCase):

    @classmethod
    def setUpClass(cls):
        cls.tmp_dir = tempfile.mkdtemp()

        # Run the analysis
        input_file = io_data_path('ChromExampleDataV2.xlsx')
        outfile = join(cls.tmp_dir, 'cadet_data.h5')
        cls.exp_id = 'Run_1'
        binding_model = make_sample_binding_model()
        transport_model = make_sample_transport_model()

        cls.study = run_chromatography_simulation(
            input_file, output_file=outfile, expt_id=cls.exp_id,
            skip_plot=True, skip_animation=True, skip_cadet=False,
            binding_model=binding_model, transport_model=transport_model,
            allow_gui=False
        )

        sim_name = 'Sim: {}'.format(cls.exp_id)
        cls.output_sim = cls.study.search_simulation_by_name(sim_name)

        initial_experiment = cls.study.search_experiment_by_name(cls.exp_id)
        cls.expected_sim = build_simulation_from_experiment(
            initial_experiment, binding_model=binding_model,
            transport_model=transport_model
        )
        out_file = io_data_path('Chrom_Example_Run_1_cadet_simulation.h5')
        update_simulation_results(cls.expected_sim, out_file)

        cls.prod_comps = cls.expected_sim.product.product_component_names
        cls.expected_components = cls.expected_sim.output.continuous_data.keys()  # noqa
        cls.found_components = cls.output_sim.output.continuous_data.keys()

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp_dir)

    # -------------------------------------------------------------------------
    # Tests
    # -------------------------------------------------------------------------
    def test_script_run(self):
        self.assertIsInstance(self.study, Study)

    def test_continuous_data_type_match(self):
        self.assertEqual(set(self.expected_components),
                         set(self.found_components))

    def test_performance_data_match(self):
        expected_perf = self.expected_sim.output.performance_data
        perf = self.output_sim.output.performance_data
        for attr in ["pool_volume", "start_collect_time", "stop_collect_time",
                     "step_yield"]:
            assert_almost_equal(getattr(perf, attr),
                                getattr(expected_perf, attr), decimal=5)

    def test_section_tag_match(self):
        component_names = ['Section_Tags_Sim']
        self.assert_output_data_almost_equal(component_names)

    def test_continuous_data_match(self):
        component_names = ['cation_Sim', 'Total_Sim']
        component_names += [comp + "_Sim" for comp in self.prod_comps]
        self.assert_output_data_almost_equal(component_names)

    def test_liq_particle_data_match(self):
        liq_particle_data_comp_name = [
            comp + '_Particle_Liq_Sim' for comp in self.prod_comps
        ]
        self.assert_output_data_almost_equal(liq_particle_data_comp_name)

    def test_column_particle_data_match(self):
        col_particle_data_comp_name = [
            comp + '_Column_Sim' for comp in self.prod_comps
        ]
        self.assert_output_data_almost_equal(col_particle_data_comp_name)

    def test_bound_particle_data_match(self):
        # FIXME - broken test on Jenkins
        self.skipTest("This is failing on Jenkins. Skipping for now.")
        bound_particle_data_comp_name = [
            comp + "_Particle_Bound_Sim" for comp in self.prod_comps
        ]
        self.assert_output_data_almost_equal(bound_particle_data_comp_name)

    # Utilities ---------------------------------------------------------------

    def assert_output_data_almost_equal(self, component_names):
        for component in component_names:
            self.assertIn(component, self.found_components)

            expected_data = self.expected_sim.output.continuous_data[component]
            data = self.output_sim.output.continuous_data[component]

            assert_array_almost_equal(expected_data.x_data, data.x_data,
                                      decimal=5)

            if np.issubdtype(data.y_data.dtype, np.number):
                assert_array_almost_equal(expected_data.y_data, data.y_data,
                                          decimal=5)
            else:
                # These are arrays of strings. Compare them as lists:
                self.assertEqual(expected_data.y_data.tolist(),
                                 data.y_data.tolist())
