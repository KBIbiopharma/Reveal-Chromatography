""" Test the storage and retrieval of various types of objects in a .chrom
project file.
"""

from unittest import TestCase
import os
import sys
from nose.tools import assert_equal, assert_true

from scimath.units.api import UnitScalar

from app_common.apptools.testing_utils import \
    reraise_traits_notification_exceptions
from app_common.traits.assertion_utils import assert_has_traits_almost_equal

from kromatography.utils.assertion_utils import assert_file_roundtrip_identical
from kromatography.io.reader_writer import load_object, save_object
from kromatography.io.api import load_study_from_excel, \
    load_study_from_project_file
from kromatography.io.serializer import Serializer
from kromatography.io.deserializer import deSerializer
from kromatography.model.kromatography_project import KromatographyProject
from kromatography.model.data_source import SimpleDataSource
from kromatography.model.simulation_group import SimulationGroup
from kromatography.model.study import Study
from kromatography.model.component import Component
from kromatography.model.tests.sample_data_factories import \
    make_sample_simulation_group
from kromatography.model.factories.simulation import \
    build_simulation_from_experiment
from kromatography.ui.tasks.kromatography_task import KromatographyTask
from kromatography.utils.testing_utils import io_data_path
from kromatography.compute.brute_force_binding_model_optimizer import \
    BruteForce2StepBindingModelOptimizer as BindModelOptim

sys.setrecursionlimit(2000)

HERE = os.path.dirname(__file__)


class TestCaseWithTempFile(TestCase):
    """ Base class for defining TestCases with a temporary local file.
    """
    def setUp(self):
        Serializer.array_collection = {}
        deSerializer.array_collection = {}

        self.test_file = os.path.join(HERE, 'test_file.chrom')
        if os.path.exists(self.test_file):
            os.remove(self.test_file)

    def tearDown(self):
        if os.path.exists(self.test_file):
            os.remove(self.test_file)


class TestHighLevelStorageFromAnywhere(TestCaseWithTempFile):
    """ Test of high level functions save_object and load_object.
    """
    def setUp(self):
        super(TestHighLevelStorageFromAnywhere, self).setUp()
        # Change dir so that we fake running from installed software location:
        self.curdir = os.path.abspath(os.curdir)
        if sys.platform == "win32":
            non_writable_location = r"C:\Users"
        else:
            non_writable_location = "/usr"

        os.chdir(non_writable_location)

    def tearDown(self):
        os.chdir(self.curdir)
        super(TestHighLevelStorageFromAnywhere, self).tearDown()

    def test_write_empty_task_fails(self):
        task = KromatographyTask()
        with self.assertRaises(IOError):
            # Fail if writing in current dir:
            assert_file_roundtrip_identical(task)

        # But not when providing a regular folder as target:
        assert_file_roundtrip_identical(task, target_dir=HERE)


class TestHighLevelFileStorage(TestCaseWithTempFile):
    """ Test of high level functions save_object and load_object.
    """
    def setUp(self):
        super(TestHighLevelFileStorage, self).setUp()
        input_file = io_data_path('ChromExampleDataV2.xlsx')
        self.study = load_study_from_excel(input_file, allow_gui=False)

        # Building and running simulation for only 1 experiment
        expt = self.study.experiments[0]
        sim = build_simulation_from_experiment(expt)
        self.study.simulations.append(sim)

    def test_write_empty_task(self):
        task = KromatographyTask()
        assert_file_roundtrip_identical(task)

    def test_write_non_empty_task(self):
        project = KromatographyProject(study=self.study)
        obj = KromatographyTask(project=project)
        # Ignore dirty flag on study datasource since currently not in use
        # Also ignore the datasource since it isn;t stored when storing a task
        assert_file_roundtrip_identical(obj, ignore=['datasource', 'dirty'])

    def test_write_complete_study(self):
        # Ignore dirty flag on study datasource since currently not in use
        # Also ignore the datasource since it isn;t stored when storing a study
        assert_file_roundtrip_identical(self.study,
                                        ignore=['datasource', 'dirty'])

    def test_write_complete_study_with_sim_group(self):
        sim = self.study.simulations[0]
        sim_group = make_sample_simulation_group(cp=sim)
        self.study.analysis_tools.simulation_grids.append(sim_group)
        try:
            # FIXME: SimulationGroup not fully serialized, so it can't be
            # identical => test parts of it:
            save_object(self.test_file, self.study)
            new_obj, _ = load_object(self.test_file)
            self.assertIsInstance(new_obj, Study)
            self.assertEqual(len(new_obj.analysis_tools.simulation_grids), 1)
            self.assertIsInstance(new_obj.analysis_tools.simulation_grids[0],
                                  SimulationGroup)
        finally:
            # Clean up for other tests since cls.study is created in setUpClass
            self.study.analysis_tools.simulation_grids.pop(-1)

    def test_store_akta_settings(self):
        # This file was created after akta settings were added to the models
        fname = 'std_input_with_akta_shift.chrom'
        file_with_stored_settings = io_data_path(fname)
        task, _ = load_object(file_with_stored_settings)
        exp0 = task.project.study.search_experiment_by_name('Run_1')
        self.assertIsInstance(exp0.output.import_settings, dict)

        custom_patterns = {
            'uv': r'(UV.*280nm)',
            'conductivity': r'(COND$)',
            'concentration': r'(CONC$)',
            'pH': r'(pH$)',
            'flow': r'(FLOW$)',
            'fraction': r'(FRACTIONS?$)',
            'log_book': r'(Log(book)?$)',
            'temperature': r'(TEMP$)',
        }
        expected = {"time_of_origin": UnitScalar(102.050, units="minute"),
                    "col_name_patterns": custom_patterns,
                    'holdup_volume': UnitScalar(0.0, units='minute')}
        self.assertEqual(exp0.output.import_settings, expected)

    def test_load_same_file_twice(self):
        filename = "demo_with_optimizerv8.chrom"
        obj1, _ = load_object(io_data_path(filename))
        obj2, _ = load_object(io_data_path(filename))
        # Make sure they are identical without being the same object:
        assert_has_traits_almost_equal(obj1, obj2, eps=1e-15)
        self.assertIsNot(obj1, obj2)
        self.assertIsNot(obj1.project.study, obj2.project.study)


class TestHighLevelFileStorageWithRunSims(TestCaseWithTempFile):
    """ Test of high level functions save_object and load_object when run
    simulations are involved.
    """
    def setUp(self):
        super(TestHighLevelFileStorageWithRunSims, self).setUp()
        input_file = io_data_path('test_roudoff_error.chrom')
        self.study = load_study_from_project_file(input_file)

        # Building and running simulation for only 1 experiment
        expt = self.study.experiments[0]
        self.sim = build_simulation_from_experiment(expt)
        self.study.simulations.append(self.sim)

    def test_run_save_bring_back(self):
        # Ensure/fake a round-off error on disk
        self.sim.section_times[-1] -= 1e-12
        save_object(self.test_file, self.sim)
        new_sim, _ = load_object(self.test_file)
        # Precision must be reduced because for the new simulation, the
        # section_times will be recomputed.
        assert_has_traits_almost_equal(new_sim, self.sim, eps=1e-11)
        # This is NOT assertAlmostEqual, because these 2 numbers must be
        # completely identical for CADET2 not to CRASH!
        assert_equal(new_sim.section_times[-1],
                     new_sim.solver.user_solution_times[-1])


class TestHighLevelFileStorageDataSource(TestCaseWithTempFile):
    """ Test of high level functions save_object and load_object on
    SimpleDatasource instances.
    """

    def setUp(self):
        super(TestHighLevelFileStorageDataSource, self).setUp()
        self.ds = SimpleDataSource()

    def test_default_simple_datasource(self):
        assert_file_roundtrip_identical(self.ds)

    def test_modified_simple_datasource_via_list(self):
        # FIXME: adding to the datasource currently means adding to the
        # object_catalog, to the data catalog and the corresponding list
        new_comp = Component(name="New Component",
                             charge=UnitScalar(0.0, units='1'),
                             pKa=UnitScalar(0.0, units='1'))
        self.ds.set_object_of_type("components", new_comp)
        self.ds.make_clean()
        assert_file_roundtrip_identical(self.ds)


class TestOldFilesUpdated(TestCase):

    def test_binding_transport_model_target_prod_set(self):
        """ Make sure old files' binding and transport models are updated once
            loaded, such that they have target products.
        """
        task, _ = load_object(io_data_path("demo_with_optimizerv8.chrom"))
        study = task.project.study
        prod_name = study.product.name
        # Find all binding and transport models to test for their
        # target_product:
        optimizers = [optim for optim in study.analysis_tools.optimizations
                      if isinstance(optim, BindModelOptim)]
        optim_models = []
        for optim in optimizers:
            optim_models += [model for model in optim.optimal_models]

        all_models = (study.study_datasource.binding_models +
                      study.study_datasource.transport_models + optim_models)
        for model in all_models:
            self.assertEqual(model.target_product, prod_name)

    def test_experiment_import_settings(self):
        """ Test that experiments import settings get updated.
        """
        filenames = ["std_project_serialv5.chrom", "demo_final_statev5.chrom",
                     "demo_final_statev6.chrom", "demo_with_optimizerv8.chrom",
                     "demo_with_general_optimizerv9.chrom"]
        for filename in filenames:
            task, _ = load_object(io_data_path(filename))
            study = task.project.study
            for exp in study.experiments:
                expected = {"time_of_origin", "col_name_patterns",
                            'holdup_volume'}
                settings = exp.output.import_settings
                self.assertEqual(set(settings.keys()), expected)
                self.assertIsInstance(settings["time_of_origin"], UnitScalar)
                self.assertIsInstance(settings["holdup_volume"], UnitScalar)


class TestReaderAllVersions(TestCase):
    """ Make sure that all serialized version of a project can be loaded by the
    current software.

    Note: the v0 version of the project was created before June 29th 2016.
    The other files loaded here correspond to versions of the same project,
    saved later. Every time the (de)serializers were modified and one ore more
    instance had their protocol number bumped, a new version of a file was
    (re)saved.
    """
    @classmethod
    def setUpClass(cls):
        # Ignore the names of objects and method's collection_step_number since
        # defaults have changed.
        cls.ignore = ['name', 'collection_step_number', 'job_manager']
        cls.reference_filename = "std_project_serialv5.chrom"
        cls.ref_task, _ = load_object(io_data_path(cls.reference_filename))

    def test_read_file_serializer_v0(self):
        assert_old_file_read("std_project_serialv0.chrom",
                             self.ref_task, ignore=self.ignore)

    def test_read_file_serializer_v3(self):
        assert_old_file_read("std_project_serialv3.chrom",
                             self.ref_task, ignore=self.ignore)

    def test_read_file_serializer_v4(self):
        assert_old_file_read("std_project_serialv4.chrom",
                             self.ref_task)

    def test_read_file_serializer_v5(self):
        assert_old_file_read("std_project_serialv0.7.2.chrom",
                             self.ref_task)


class TestReaderAllVersionsWithParamExplorer(TestCase):
    """ Make sure that all serialized version of a project can be loaded by the
    current software.
    """
    @classmethod
    def setUpClass(cls):
        # Ignore the names of objects and method's collection_step_number since
        # defaults have changed.
        cls.ignore = ['simulation_diffs', 'center_point_simulation',
                      'perf_params']
        cls.reference_filename = "demo_final_statev0.7.2.chrom"
        cls.ref_task, _ = load_object(io_data_path(cls.reference_filename))

    def test_read_file_serializer_v5_with_parameter_explorer(self):
        # Ignoring things that change between the 2 versions:
        assert_old_file_read("demo_final_statev5.chrom", self.ref_task,
                             ignore=self.ignore)

    def test_read_file_serializer_v6_with_parameter_explorer(self):
        assert_old_file_read("demo_final_statev6.chrom", self.ref_task,
                             ignore=[])


class TestReaderAllVersionsWithOptimizer(TestCase):
    """ Make sure that all serialized version of a project can be loaded by the
    current software.
    """
    @classmethod
    def setUpClass(cls):
        cls.ref_task, _ = load_object(
            io_data_path("demo_with_optimizerv7.chrom"))
        cls.ref_task2, _ = load_object(io_data_path(
            "demo_with_general_optimizerv9.chrom"))
        cls.ref_task3, _ = load_object(io_data_path(
            "demo_with_general_optimizerv10.chrom"))

    def test_read_file_serializer_v7_with_optimizer(self):
        assert_old_file_read("demo_with_optimizerv8.chrom", self.ref_task)

    def test_read_file_serializer_v8_with_general_optimizer(self):
        assert_old_file_read("demo_with_general_optimizerv8.chrom",
                             self.ref_task2)

    def test_read_file_serializer_v9_with_general_optimizer(self):
        assert_old_file_read("demo_with_general_optimizerv0.7.2.chrom",
                             self.ref_task2)

    def test_read_file_serializer_v10_with_both_optimizers(self):
        assert_old_file_read("demo_with_general_optimizerv10.chrom",
                             self.ref_task3)


# Utility functions -----------------------------------------------------------


def assert_old_file_read(filename, reference_task, ignore=(), eps=1e-9):
    with reraise_traits_notification_exceptions():
        obj, legacy = load_object(io_data_path(filename))

    assert_has_traits_almost_equal(obj.project, reference_task.project,
                                   ignore=ignore, eps=eps)
    assert_true(legacy)
