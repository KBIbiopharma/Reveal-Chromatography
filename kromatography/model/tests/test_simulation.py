""" Tests for the Simulation class. See kromatography/solve/tests for run
tests.
"""

from unittest import TestCase
from os.path import isfile
import os
from uuid import uuid4

from traits.api import HasTraits
from traits.testing.unittest_tools import UnittestTools
from scimath.units.api import UnitScalar
from scimath.units.time import second
from numpy.testing import assert_array_almost_equal
from numpy import array
from copy import deepcopy

from app_common.traits.has_traits_utils import is_trait_event
from app_common.traits.assertion_utils import assert_has_traits_almost_equal, \
    assert_values_almost_equal

from kromatography.model.buffer import Buffer
from kromatography.model.column import Column, ColumnType
from kromatography.model.discretization import Discretization
from kromatography.model.factories.job_manager import create_start_job_manager
from kromatography.model.method import Method
from kromatography.model.resin import Resin
from kromatography.model.sensitivity import Sensitivity
from kromatography.model.simulation import FILENAME_SUFFIX, Simulation
from kromatography.model.solver import Solver
from kromatography.model.tests.example_model_data import (
    COLUMN_TYPE_DATA, COLUMN_DATA, METHOD_DATA, RESIN_DATA
)
from kromatography.model.tests.sample_data_factories import \
    make_sample_simulation, make_sample_study2
from kromatography.model.factories.simulation import \
    build_simulation_from_experiment
from kromatography.model.chromatography_results import SimulationResults
from kromatography.utils.chromatography_units import column_volumes as cv
from kromatography.model.performance_data import PerformanceData


class TestSimulation(TestCase, UnittestTools):
    """ Test simulation creation and attribute updates.

    For test on sims built from exp, see
    model/factories/tests/test_build_simulation_from_experiment.py.
    """
    def setUp(self):
        # Manual construction
        column_type = ColumnType(**COLUMN_TYPE_DATA.copy())
        resin = Resin(**RESIN_DATA.copy())
        column = Column(column_type=column_type, resin=resin,
                        **COLUMN_DATA.copy())
        method = Method(**deepcopy(METHOD_DATA))

        self.sim_from_scratch = Simulation(
            name='Sim1', column=column, method=method, output=None
        )
        self.expected_sec_times = array([0., 540., 1080., 1620., 7668.])

    # -------------------------------------------------------------------------
    # Tests
    # -------------------------------------------------------------------------
    def test_manual_construction(self):
        sim = self.sim_from_scratch
        self.assertEqual(sim.name, 'Sim1')

        # These need to be explicitly provided.
        self.assertIsNone(sim.binding_model)
        self.assertIsNone(sim.transport_model)

        # These should have defaults.
        self.assertIsInstance(sim.solver, Solver)
        self.assertIsInstance(sim.discretization, Discretization)
        self.assertIsInstance(sim.sensitivity, Sensitivity)
        self.assertIsNone(sim.source_experiment)
        self.assertIsInstance(sim.cadet_filename, str)
        self.assertFalse(isfile(sim.cadet_filepath))

        assert_array_almost_equal(sim.section_times, self.expected_sec_times)
        self.assertEqual(sim.section_times.units, second)

    def test_cadet_filepath_update_on_cadet_filename_change(self):
        sim = self.sim_from_scratch

        with self.assertTraitChanges(sim, "cadet_filepath"):
            # This should trigger an update of the filename and therefore the
            # filepath.
            sim.uuid = uuid4()

        self.assertIn(sim.cadet_filename, sim.cadet_filepath)

    def test_section_time_update_on_method_change(self):
        sim = self.sim_from_scratch

        with self.assertTraitChanges(sim.solver, "user_solution_times"):
            sim.method.method_steps.pop(-1)

        assert_array_almost_equal(sim.section_times,
                                  self.expected_sec_times[:-1])

    def test_section_time_update_on_step_volume_change(self):
        sim = self.sim_from_scratch
        with self.assertTraitChanges(sim.solver, "user_solution_times"):
            sim.method.method_steps[1].volume = \
                sim.method.method_steps[1].volume + UnitScalar(1, units=cv)

        expected = self.expected_sec_times
        # 1 CV corresponds to 6 minutes at 200cm/hour:
        expected[2:] += 6 * 60
        assert_array_almost_equal(sim.section_times, expected)

    def test_section_time_update_on_step_flowrate_change(self):
        sim = self.sim_from_scratch

        with self.assertTraitChanges(sim.solver, "user_solution_times"):
            factor = 2
            sim.method.method_steps[1].flow_rate = \
                sim.method.method_steps[1].flow_rate * factor

        expected = self.expected_sec_times
        # Second step is now half as short:
        expected[2:] -= (expected[2]-expected[1]) / factor
        assert_array_almost_equal(sim.section_times, expected)

    def test_section_time_update_on_bed_height_change(self):
        sim = self.sim_from_scratch

        with self.assertTraitChanges(sim.solver, "user_solution_times"):
            sim.column.bed_height_actual = \
                sim.column.bed_height_actual + UnitScalar(10, units="cm")

        # Each step is 1.5x longer
        expected = array([0., 810., 1620., 2430., 11502.])
        # Second step is now half as short:
        assert_array_almost_equal(sim.section_times, expected)

    def test_section_time_update_on_column_diam_change(self):
        sim = self.sim_from_scratch

        with self.assertTraitChanges(sim.solver, "user_solution_times"):
            sim.column.column_type.diameter = \
                sim.column.column_type.diameter + UnitScalar(1, units="cm")

        expected = self.expected_sec_times
        # Nothing changes here because the volumes are in CVs:
        assert_array_almost_equal(sim.section_times, expected)

    def test_section_time_update_on_num_solution_times_change(self):
        sim = self.sim_from_scratch

        with self.assertTraitChanges(sim.solver, "user_solution_times"):
            sim.solver.number_user_solution_points += 1

        self.assertEqual(len(sim.solver.user_solution_times),
                         sim.solver.number_user_solution_points)

    def test_perf_data_name_update(self):
        # Since performance data pane shows sim's perf data, make sure the
        # change of name in sim is reflected in its performance data.
        sim = self.sim_from_scratch
        perf = PerformanceData(name=sim.name)
        sim.output = SimulationResults(name="dummy", performance_data=perf)

        with self.assertTraitChanges(sim.output.performance_data, "name"):
            sim.name = "foo"

        self.assertEqual(sim.output.performance_data.name, "foo")

    def test_create_cadet_file(self):
        from kromatography.model.tests.sample_data_factories import \
            make_sample_simulation

        sim = make_sample_simulation()

        self.assertFalse(isfile(sim.cadet_filepath))
        res = sim.create_cadet_input_file()
        try:
            self.assertTrue(isfile(sim.cadet_filepath))
            self.assertEqual(res, sim.cadet_filepath)
            # Asking for it again just returns the filename
            res2 = sim.create_cadet_input_file()
            self.assertEqual(res, res2)
        finally:
            if isfile(sim.cadet_filepath):
                os.remove(sim.cadet_filepath)

    def test_create_cadet_file_fail_no_transport_model(self):
        sim = self.sim_from_scratch

        # Must fail because the simulation has no transport model
        with self.assertRaises(AttributeError):
            sim.create_cadet_input_file()

        if isfile(sim.cadet_filepath):
            os.remove(sim.cadet_filepath)

    def test_change_uuid(self):
        sim = make_sample_simulation()
        self.assert_cadet_filename_consistent(sim)

        new_uuid = uuid4()
        with self.assertTraitChanges(sim, "cadet_filename", 1):
            with self.assertTraitChanges(sim, "cadet_filepath", 1):
                sim.uuid = new_uuid

        self.assert_cadet_filename_consistent(sim)

    def test_change_filename(self):
        sim = make_sample_simulation()
        new_fname = str(uuid4()) + FILENAME_SUFFIX
        with self.assertTraitChanges(sim, "uuid", 1):
            with self.assertTraitChanges(sim, "cadet_filepath", 1):
                sim.cadet_filename = new_fname

        self.assert_cadet_filename_consistent(sim)

    # Assertion utilities -----------------------------------------------------

    def assert_cadet_filename_consistent(self, sim):
        self.assertIn(str(sim.uuid), sim.cadet_filename)
        self.assertIn(str(sim.uuid), sim.cadet_filepath)
        self.assertTrue(sim.cadet_filename.endswith(sim.cadet_filename))


class TestSimulationCopy(TestCase, UnittestTools):

    @classmethod
    def setUpClass(cls):
        cls.real_study = make_sample_study2(add_transp_bind_models=True)
        cls.real_exp = cls.real_study.search_experiment_by_name('Run_1')
        cls.real_sim = build_simulation_from_experiment(cls.real_exp)
        cls.job_manager = create_start_job_manager(max_workers=1)

    @classmethod
    def tearDownClass(cls):
        cls.job_manager.shutdown()

    def setUp(self):
        # Manual construction
        column_type = ColumnType(**COLUMN_TYPE_DATA)
        resin = Resin(**RESIN_DATA)
        column = Column(column_type=column_type, resin=resin, **COLUMN_DATA)
        method = Method(**METHOD_DATA)

        self.sim_from_scratch = Simulation(
            name='Sim1', column=column, method=method,
            output=None
        )
        self.sim_from_std_exp = make_sample_simulation()

    def test_copy_sim_from_scratch_not_run(self):
        new_sim1 = self.sim_from_scratch.copy()
        self.assertValidCopy(new_sim1, self.sim_from_scratch)

    def test_copy_sim_with_bind_transp_not_run(self):
        # Using utility will contain a binding and transport model
        new_sim2 = self.sim_from_std_exp.copy()
        self.assertValidCopy(new_sim2, self.sim_from_std_exp)

    def test_copy_complete_sim_not_run(self):
        # Build a simulation from an experiment and add a fake output
        sim3 = self.real_sim
        sim3.output = SimulationResults(name='fake output')
        sim3.editable = False

        new_sim3 = sim3.copy()
        self.assertValidCopy(new_sim3, sim3)

    def test_copy_sim_run(self):
        self.real_sim.run(self.job_manager, wait=True)

        self.assertIsNotNone(self.real_sim.output)
        self.assertTrue(self.real_sim.has_run)
        sim = self.real_sim.copy()
        self.assertIsNone(sim.output)
        self.assertFalse(sim.has_run)
        self.assertTrue(sim.editable)
        self.assertFalse(isfile(sim.cadet_filepath))

    # Utilities ---------------------------------------------------------------

    def assertValidCopy(self, new_sim, orig_sim):
        """ Test that a copy leads to identical attributes except run related.
        """
        self.assertIsInstance(new_sim, orig_sim.__class__)

        # copies have no output
        self.assertIsNone(new_sim.output)
        # Copies use the same buffer in every step
        self.assertTrue(new_sim.editable)

        # All uses of buffers are the same object
        buffers = {}
        for step in new_sim.method.method_steps:
            for solution in step.solutions:
                if isinstance(solution, Buffer):
                    if solution.name in buffers:
                        self.assertIs(solution, buffers[solution.name])
                    else:
                        buffers[solution.name] = solution

        # All subobjects are equal except the outputs, the editable flag
        # and the events attributes.
        skip_attr = {"output", "editable", "has_run", "uuid", "cadet_filename",
                     "cadet_filepath"}
        relevant_attrs = set(new_sim.trait_names()) - skip_attr

        for attr in relevant_attrs:
            if is_trait_event(orig_sim, attr):
                continue
            val1, val2 = getattr(new_sim, attr), getattr(orig_sim, attr)
            if isinstance(val1, HasTraits):
                assert_has_traits_almost_equal(val1, val2)
            else:
                assert_values_almost_equal(val1, val2)

        # The uuid and cadet input files on the other hand is guaranteed to be
        # different
        self.assertNotEqual(orig_sim.uuid, new_sim.uuid)
        self.assertNotEqual(orig_sim.cadet_filename, new_sim.cadet_filename)
        self.assertNotEqual(orig_sim.cadet_filepath, new_sim.cadet_filepath)
