from unittest import TestCase
import os
import numpy as np
from shutil import copyfile
from uuid import uuid4

from scimath.units.api import UnitArray, UnitScalar

from kromatography.utils.assertion_utils import assert_roundtrip_identical
from kromatography.io.serializer import serialize
from kromatography.io.deserializer import deserialize
from kromatography.utils.testing_utils import io_data_path
from kromatography.model.tests.sample_data_factories import \
    make_sample_study2, make_sample_binding_model, \
    make_sample_langmuir_binding_model
from kromatography.io.simulation_updater import update_simulation_results
from kromatography.ui.tasks.kromatography_task import KromatographyTask
from kromatography.model.kromatography_project import KromatographyProject
from kromatography.model.simulation_group import SimulationGroup
from kromatography.model.api import LazyLoadingSimulation
from kromatography.model.parameter_scan_description import \
    ParameterScanDescription
from kromatography.utils.chromatography_units import absorption_unit, \
    extinction_coefficient_unit
from kromatography.model.tests.sample_data_factories import \
    make_sample_mc_simulation_group


class TestRoundTripBasicDataSerialization(TestCase):
    def test_str(self):
        val = "this is a random string to store"
        assert_roundtrip_identical(val)

    def test_int(self):
        val = 23746523
        assert_roundtrip_identical(val)

    def test_float(self):
        val = 2.
        assert_roundtrip_identical(val)

        val = 1.e-3
        assert_roundtrip_identical(val)

    def test_uuid(self):
        val = uuid4()
        assert_roundtrip_identical(val)

    def test_array(self):
        arr = np.array([1, 2, 3, 4])
        assert_roundtrip_identical(arr)

    def test_unitscalar(self):
        a = UnitScalar(1., units="m")
        assert_roundtrip_identical(a)

    def test_unitscalar_custom_units(self):
        a = UnitScalar(1., units=extinction_coefficient_unit)
        assert_roundtrip_identical(a)

        a = UnitScalar(1., units=absorption_unit)
        assert_roundtrip_identical(a)

    def test_unitarray(self):
        arr = np.array([1, 2, 3, 4])
        a = UnitArray(arr, units="m")
        assert_roundtrip_identical(a)


class TestRoundTripContainerDataSerialization(TestCase):

    def test_ParameterScanDescription(self):
        scan_data = {"name": "binding_model.sma_nu[2]", "low": 4, "high": 6,
                     "num_values": 5, "spacing": "Linear"}
        p = ParameterScanDescription(**scan_data)
        assert_roundtrip_identical(p)


class TestRoundTripChromDataSerialization(TestCase):
    def setUp(self):
        self.study = make_sample_study2(add_transp_bind_models=True,
                                        add_sims='Run_1')
        self.sim = self.study.simulations[0]

        # Save time by loading results from an already generated file:
        self.result_filepath = io_data_path("std_example_xlsx_run1_cadet.h5")
        update_simulation_results(self.sim, output_fname=self.result_filepath)
        self.sim.set_as_run()

        # Add a simulation grid
        grp = SimulationGroup(center_point_simulation=self.sim,
                              name="new group")
        self.study.analysis_tools.simulation_grids.append(grp)

        # Add a Monte Carlo simulation group
        mc_grp = make_sample_mc_simulation_group()
        self.study.analysis_tools.monte_carlo_explorations.append(mc_grp)
        # Skip attributes not stored in a study/task: (user) datasource,
        # study_datasource.dirty, sim group's cp,
        self.ignore = {'center_point_simulation', 'datasource', 'perf_params',
                       'dirty'}

    def test_task(self):
        project = KromatographyProject(study=self.study)
        object_to_save = KromatographyTask(project=project)
        # Ignore datasource since managed by the containing Application object
        # Ignore sim group cp because not serialized.
        assert_roundtrip_identical(object_to_save, ignore=self.ignore)

        serial_data, array_collection = serialize(object_to_save)
        new_object, _ = deserialize(serial_data, array_collection)
        # Until it is embedded into the KromApplication, the datasource is not
        # set:
        self.assertIsNone(new_object.project.datasource)
        self.assertIsNone(new_object.project.study.datasource)

    def test_study(self):
        object_to_save = self.study
        assert_roundtrip_identical(object_to_save, ignore=self.ignore)

    def test_product(self):
        object_to_save = self.study.product
        assert_roundtrip_identical(object_to_save)

    def test_simulation(self):
        assert_roundtrip_identical(self.sim)

    def test_lazy_loading_simulation(self):
        # Copy cadet file, so the lazy copy can find it and be run too:
        copyfile(self.result_filepath, self.sim.cadet_filepath)
        try:
            object_to_save = LazyLoadingSimulation.from_simulation(self.sim)
            self.assertIsNotNone(object_to_save.output)
            assert_roundtrip_identical(object_to_save)
        finally:
            os.remove(self.sim.cadet_filepath)

    def test_binding_model_sma(self):
        object_to_save = make_sample_binding_model()
        assert_roundtrip_identical(object_to_save)

    def test_binding_model_ph_sma(self):
        object_to_save = make_sample_binding_model(ph_dependence=True)
        assert_roundtrip_identical(object_to_save)

    def test_binding_model_langmuir(self):
        object_to_save = make_sample_langmuir_binding_model()
        assert_roundtrip_identical(object_to_save)

    def test_binding_model_langmuir_ph(self):
        object_to_save = make_sample_langmuir_binding_model(ph_dependence=True)
        assert_roundtrip_identical(object_to_save)

    def test_binding_parameters(self):
        object_to_save = self.sim.binding_model.sma_nu
        assert_roundtrip_identical(object_to_save)
