from unittest import TestCase
import os
from os.path import isfile

from scimath.units.api import UnitScalar
from traits.api import HasTraits

from kromatography.io.reader_writer import load_object, save_object
from kromatography.utils.assertion_utils import \
    assert_has_traits_almost_equal, assert_values_almost_equal
from kromatography.model.tests.sample_data_factories import \
    make_sample_mc_simulation_group, make_sample_simulation_group, \
    make_sample_simulation_group2, make_sample_simulation2
from kromatography.model.tests.example_model_data import cm_per_hr
from kromatography.model.factories.job_manager import create_start_job_manager
from kromatography.utils.assertion_utils import assert_roundtrip_identical
from kromatography.model.simulation_group import SimulationGroup, \
    SingleParamSimulationDiff

SIM_GROUP_IGNORE = ["_simulation_output_cache", "center_point_simulation",
                    "sim_runner", "sims_run"]


class TestRoundTripSimulationGroupSerialization(TestCase):

    @classmethod
    def setUpClass(cls):
        cls.job_manager = create_start_job_manager(max_workers=2)

    @classmethod
    def tearDownClass(cls):
        cls.job_manager.shutdown()

    def setUp(self):
        self.filepath = "test.test"

    def tearDown(self):
        if isfile(self.filepath):
            os.remove(self.filepath)

    def test_create_save_load_sim_grid(self):
        obj = make_sample_simulation_group2()
        assert_roundtrip_identical(obj, ignore=SIM_GROUP_IGNORE)
        assert_round_trip_to_file_identical(self.filepath, obj,
                                            ignore=SIM_GROUP_IGNORE)

    def test_create_save_load_monte_carlo_sim_group(self):
        obj = make_sample_mc_simulation_group()
        assert_roundtrip_identical(obj, ignore=SIM_GROUP_IGNORE)
        assert_round_trip_to_file_identical(self.filepath, obj,
                                            ignore=SIM_GROUP_IGNORE)

    def test_create_run_save_load_sim_grid(self):
        object_to_save = make_sample_simulation_group()
        self.run_and_assert_serialization_succeeds(object_to_save)

    def test_create_save_load_sim_grid_unit_scalar(self):
        cp = make_sample_simulation2()

        diff = (SingleParamSimulationDiff("method.method_steps[0].flow_rate",
                                          UnitScalar(5, units=cm_per_hr)),)
        obj = SimulationGroup(center_point_simulation=cp, name="foo",
                              simulation_diffs=[diff])
        assert_roundtrip_identical(obj, ignore=SIM_GROUP_IGNORE)
        assert_round_trip_to_file_identical(self.filepath, obj,
                                            ignore=SIM_GROUP_IGNORE)

    def test_create_run_save_load_sim_grid_flow_rate(self):
        """ Save a grid that scanned a flow rate."""
        cp = make_sample_simulation2()

        diff = (SingleParamSimulationDiff("method.method_steps[0].flow_rate",
                                          UnitScalar(5, units=cm_per_hr)),)
        object_to_save = SimulationGroup(center_point_simulation=cp,
                                         name="foo", simulation_diffs=[diff])
        self.run_and_assert_serialization_succeeds(object_to_save)

    # Utilities ---------------------------------------------------------------

    def run_and_assert_serialization_succeeds(self, obj):
        obj.run(self.job_manager, wait=True)

        attrs_to_ignore = SIM_GROUP_IGNORE + ["simulations"]
        assert_roundtrip_identical(obj, ignore=attrs_to_ignore)
        assert_round_trip_to_file_identical(self.filepath, obj,
                                            ignore=attrs_to_ignore)


def assert_round_trip_to_file_identical(filepath, obj, ignore=()):
    save_object(filepath, obj)
    new_obj, _ = load_object(filepath)
    if isinstance(obj, HasTraits):
        assert_has_traits_almost_equal(new_obj, obj, ignore=ignore)
    else:
        assert_values_almost_equal(new_obj, obj, ignore=ignore)
