from unittest import TestCase
from os.path import isfile
import numpy as np

from traits.testing.unittest_tools import UnittestTools
from app_common.traits.assertion_utils import \
    assert_has_traits_almost_equal, assert_has_traits_not_almost_equal, \
    assert_values_almost_equal, assert_values_not_almost_equal

from kromatography.model.binding_model import LANGMUIR_BINDING_MODEL, \
    PH_LANGMUIR_BINDING_MODEL, PH_STERIC_BINDING_MODEL, STERIC_BINDING_MODEL
from kromatography.model.factories.job_manager import create_start_job_manager
from kromatography.model.tests.sample_data_factories import \
    make_sample_study2, make_sample_langmuir_binding_model, \
    make_sample_binding_model2
from kromatography.utils.string_definitions import \
    DEFAULT_BINDING_MODEL_NAME, DEFAULT_TRANSPORT_MODEL_NAME
from kromatography.ui.simulation_from_datasource_builder import \
    SimulationFromDatasourceBuilder
from kromatography.utils.string_definitions import SIM_FINISHED_FAIL, \
    SIM_FINISHED_SUCCESS, SIM_NOT_RUN
from kromatography.model.lazy_simulation import LazyLoadingSimulation
from kromatography.utils.io_utils import read_from_h5
from kromatography.model.cadet_model import ALL_CADET_TYPES


class TestSimulationRun(TestCase, UnittestTools):
    """ Tests around running simulations.
    """
    @classmethod
    def setUpClass(cls):
        cls.real_study = make_sample_study2(add_transp_bind_models=True,
                                            add_sims='Run_1')
        cls.real_sim = cls.real_study.simulations[0]

        # Limit the number of process to avoid saturating the machine
        cls.job_manager = create_start_job_manager(max_workers=2)
        # Run the sim
        cls.real_sim.run(cls.job_manager, wait=True)

    @classmethod
    def tearDownClass(cls):
        cls.job_manager.shutdown()

    def test_run(self):
        """ Test that a simulation built from experiment can run & have outputs
        """
        # .copy() resets all run related attrs: output, cadet_file, ... (see
        # above)
        sim = self.real_sim.copy()
        self.assert_sim_run_successfully(sim)

    def test_run_sim_from_scratch(self):
        """ Test that a simulation built from scratch leads to identical
        outputs as a sim built from an experiment.
        """
        sim = self.build_sim_from_scratch()
        self.assert_sim_run_successfully(sim)
        self.assert_output_close_to_reference(sim)

    def test_run_sim_from_scratch_langmuir(self):
        bind_model = make_sample_langmuir_binding_model()
        sim = self.build_sim_from_scratch()
        sim.binding_model = bind_model
        self.assert_sim_run_successfully(sim, bind_type=LANGMUIR_BINDING_MODEL)

    def test_run_sim_from_scratch_pH_langmuir(self):
        bind_model = make_sample_langmuir_binding_model(ph_dependence=True)
        sim = self.build_sim_from_scratch()
        sim.binding_model = bind_model
        self.assert_sim_run_successfully(sim, PH_LANGMUIR_BINDING_MODEL)

    def test_run_simulation_with_pH_binding_model_like_no_ph(self):
        """ Test that a simulation built with pH-dependent binding model, with
        all pH params set to 0 leads to identical outputs as a sim built from
        an experiment.
        """
        ncomp = len(self.real_sim.product.product_components)
        binding_model = make_sample_binding_model2(ncomp+1, ph_dependence=True)
        self.real_study.study_datasource.set_object_of_type("binding_models",
                                                            binding_model)
        sim = self.build_sim_from_scratch(bind_model=binding_model.name)
        self.assert_sim_run_successfully(sim, PH_STERIC_BINDING_MODEL)
        self.assert_output_close_to_reference(sim)

    def test_run_simulation_with_pH_binding_model(self):
        """ Test that a simulation built with pH-dependent binding model, with
        pH dependence.
        """
        from kromatography.model.tests.sample_data_factories import \
            make_sample_binding_model2

        ncomp = len(self.real_sim.product.product_components)
        binding_model = make_sample_binding_model2(ncomp+1, ph_dependence=True,
                                                   like_no_ph=False)
        binding_model.name += "_v2"
        self.real_study.study_datasource.set_object_of_type("binding_models",
                                                            binding_model)
        sim = self.build_sim_from_scratch(bind_model=binding_model.name)
        self.assert_sim_run_successfully(sim, PH_STERIC_BINDING_MODEL)
        self.assert_output_not_close_to_reference(sim)

    def test_run_bad_sim(self):
        """ Test that a valid simulation but with bad parameters is recognized
        as a CADET failure.
        """
        sim = self.real_sim.copy()
        # Break the binding model enough to trigger an exception in CADET...
        sim.binding_model.sma_ka[1:] = -1
        runner = sim.run(self.job_manager, wait=True)
        self.assertIn(runner.job_id, self.job_manager._job_results.keys())
        self.assertEqual(self.job_manager._pending_jobs, set())
        # ... and make sure that the sim reports back that CADET failed:
        self.assertIsNone(sim.output)
        self.assertTrue(sim.has_run)
        self.assertEqual(sim.run_status, SIM_FINISHED_FAIL)

    def test_run_sim_no_collection_criteria(self):
        sim = self.real_sim.copy()
        sim.method.collection_criteria = None
        self.assert_sim_run_successfully(sim)
        nan_attrs = ['start_collect_time', 'stop_collect_time', 'pool_volume',
                     'step_yield', 'pool_concentration']
        for attr in nan_attrs:
            val = getattr(sim.output.performance_data, attr)
            self.assertTrue(np.isnan(val))
            self.assertEqual(val.units.label, "none")

    # Utilities ---------------------------------------------------------------

    def assert_sim_run_successfully(self, sim, bind_type=STERIC_BINDING_MODEL):
        self.assertFalse(sim.has_run)
        self.assertEqual(sim.run_status, SIM_NOT_RUN)

        # Status changing 2 times, from not run to submitted and then finished
        # successfully:
        with self.assertTraitChanges(sim, "run_status", 2):
            with self.assertTraitChanges(sim, "has_run", 1):
                runner = sim.run(self.job_manager, wait=True)

        self.assertTrue(runner.job_id.startswith("Job "))
        self.assertEqual(len(runner.work_item_ids), 1)
        self.assertIsNotNone(sim.output)
        self.assertTrue(sim.has_run)
        self.assertEqual(sim.run_status, SIM_FINISHED_SUCCESS)
        self.assertFalse(sim.editable)
        # The editable flag is changed all the way down
        self.assertFalse(sim.transport_model.editable)
        self.assertFalse(sim.column.editable)
        self.assertFalse(sim.output.performance_data.editable)
        # Make sure that the cadet file now exists. We don't erase it because
        # we want to test that these files are unique and don't collide from
        # one test run to the next.
        output_fname = sim.cadet_filepath
        self.assertTrue(isfile(output_fname))
        output_data = read_from_h5(output_fname, root='/output/solution')

        input_data = read_from_h5(output_fname, root='/input')
        cadet_bind_type = input_data["adsorption_type"]
        # Make sure HDF5 file binding model type is as requested
        self.assertEqual(cadet_bind_type, ALL_CADET_TYPES[bind_type])

        # Make sure HDF5 file is consistent on the size of the output
        key = 'solution_column_outlet_comp_000'
        self.assertIsInstance(output_data[key], np.ndarray)
        size = input_data['number_user_solution_points']
        self.assertEqual(output_data[key].shape, (size,))

    def assert_output_close_to_reference(self, sim):
        """ Make sure the output data is close to identical. """
        ref_perf_data = self.real_sim.output.performance_data
        ref_cont_data = self.real_sim.output.continuous_data
        assert_has_traits_almost_equal(sim.output.performance_data,
                                       ref_perf_data, eps=1e-5,
                                       ignore=('name',))
        assert_values_almost_equal(sim.output.continuous_data, ref_cont_data,
                                   eps=8.e-5)

    def assert_output_not_close_to_reference(self, sim):
        """ Make sure the output data is close to identical.
        """
        ref_perf_data = self.real_sim.output.performance_data
        ref_cont_data = self.real_sim.output.continuous_data
        assert_has_traits_not_almost_equal(sim.output.performance_data,
                                           ref_perf_data, eps=1e-5,
                                           ignore=('name',))
        assert_values_not_almost_equal(sim.output.continuous_data,
                                       ref_cont_data, eps=8.e-5)

    def build_sim_from_scratch(self, tr_model="", bind_model="", name="Sim"):
        """ Create a simulation from scratch that is similar to real_sim.
        """
        if not tr_model:
            tr_model = DEFAULT_TRANSPORT_MODEL_NAME

        if not bind_model:
            bind_model = DEFAULT_BINDING_MODEL_NAME

        study_ds = self.real_study.study_datasource
        sim_builder = SimulationFromDatasourceBuilder(
            datasource=self.real_study.datasource, study_datasource=study_ds
        )
        # Setup
        sim_builder.simulation_name = name
        sim_builder.product_name = self.real_sim.product.name
        sim_builder.column_name = 'CP_001'
        sim_builder.method_name = 'Run_1'
        sim_builder.first_simulated_step_name = 'Load'
        sim_builder.last_simulated_step_name = 'Strip'
        sim_builder.transport_model_name = tr_model
        sim_builder.binding_model_name = bind_model
        sim = sim_builder.to_simulation()
        return sim


class TestLazySimulationRun(TestSimulationRun):
    @classmethod
    def setUpClass(cls):
        super(TestLazySimulationRun, cls).setUpClass()
        # Convert the simulation to a LazyLoading one
        cls.real_sim = LazyLoadingSimulation.from_simulation(cls.real_sim)
