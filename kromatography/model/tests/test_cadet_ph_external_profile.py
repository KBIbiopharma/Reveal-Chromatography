from unittest import TestCase

from scimath.units.api import convert, convert_str
from scimath.units.length import meter
from scimath.units.time import second

from kromatography.model.cadet_ph_external_profile import \
    CADETPhExternalProfile, get_step_velocity
from kromatography.model.tests.sample_data_factories import \
    make_sample_simulation2
from kromatography.utils.assertion_utils import \
    assert_unit_scalar_almost_equal, assert_unit_scalar_not_almost_equal


class TestCADETPhExternalProfile(TestCase):

    def setUp(self):
        self.sim = make_sample_simulation2()
        self.method = self.sim.method
        self.method.method_steps[0].name = "Load"
        self.column = self.sim.column

    def test_create_from_1_step_method(self):
        self.sim.method.method_steps = self.sim.method.method_steps[:1]
        cadet_ext = self.create_cadet_external_and_validate()
        # Only 1 step with 1 solution, so 3 values in profile (for the initial
        # buffer pH and then the step solution) and solution values identical
        self.assertEqual(len(cadet_ext.ext_profile), 3)
        self.assertEqual(cadet_ext.ext_profile[1], cadet_ext.ext_profile[2])

    def test_create_from_2step_no_gap_and_gradient_method(self):
        self.sim.method.method_steps = self.sim.method.method_steps[:2]
        # Guaranty no pH gap:
        step1_solution = self.sim.method.method_steps[1].solutions[0]
        step0_solution = self.sim.method.method_steps[0].solutions[0]
        step1_solution.pH = step0_solution.pH
        step_start_phs = [s.solutions[0].pH for s in
                          self.sim.method.method_steps]
        assert_unit_scalar_almost_equal(step_start_phs[0], step_start_phs[1])
        cadet_ext = self.create_cadet_external_and_validate()

        # 2 steps without a gap: initial_buffer contributes 1 value, first step
        # always contributes 2 values, second step also
        self.assertEqual(len(cadet_ext.ext_profile), 4)
        # First step has constant ph:
        self.assertEqual(cadet_ext.ext_profile[1], cadet_ext.ext_profile[2])
        # Step 2 is a gradient elution so pH changes:
        self.assertNotAlmostEqual(cadet_ext.ext_profile[2],
                                  cadet_ext.ext_profile[3])

    def test_create_from_2step_with_gap_and_gradient_method(self):
        self.sim.method.method_steps = self.sim.method.method_steps[:2]
        step_start_phs = [s.solutions[0].pH for s in
                          self.sim.method.method_steps]
        assert_unit_scalar_not_almost_equal(step_start_phs[0],
                                            step_start_phs[1])
        cadet_ext = self.create_cadet_external_and_validate()

        # 2 steps with a gap: initial_buffer contributes 1 value, first step
        # always contributes 2 values, second step also since elution:
        self.assertEqual(len(cadet_ext.ext_profile), 5)
        # First step has constant ph:
        self.assertEqual(cadet_ext.ext_profile[1], cadet_ext.ext_profile[2])
        # pH gap between both steps:
        self.assertNotAlmostEqual(cadet_ext.ext_profile[2],
                                  cadet_ext.ext_profile[3])
        # Step 2 is a gradient elution so pH changes:
        self.assertNotAlmostEqual(cadet_ext.ext_profile[3],
                                  cadet_ext.ext_profile[4])

    def test_create_from_constant_speed_sim(self):
        # Set all speeds to be identical
        for step in self.sim.method.method_steps:
            step.flow_rate = self.sim.method.method_steps[0].flow_rate

        self.create_cadet_external_and_validate()

    # Utilities ---------------------------------------------------------------

    def get_step_duration(self, step):
        step_duration = self.column.bed_height_actual / step.flow_rate
        step_duration = convert(float(step_duration),
                                from_unit=step_duration.units, to_unit=second)
        return step_duration

    def create_cadet_external_and_validate(self, sim=None):
        if sim is None:
            sim = self.sim

        cadet_ext = CADETPhExternalProfile.from_simulation(sim)
        # lengths of arrays:
        self.assertEqual(len(cadet_ext.ext_prof_delta),
                         len(cadet_ext.ext_profile))

        one_col_length = float(convert_str(self.column.bed_height_actual, "cm",
                                           "m"))
        # Initial values: depths start at 0, and includes 1 column of initial
        # buffer:
        self.assertEqual(cadet_ext.ext_prof_delta[0], 0.0)
        self.assertEqual(cadet_ext.ext_prof_delta[1], one_col_length)

        init_solution = self.sim.method.initial_buffer
        first_step = self.sim.method.method_steps[0]
        self.assertEqual(cadet_ext.ext_profile[0], float(init_solution.pH))
        self.assertEqual(cadet_ext.ext_profile[1], first_step.solutions[0].pH)

        flow_rate0 = first_step.flow_rate
        first_velocity = convert(float(flow_rate0), from_unit=flow_rate0.units,
                                 to_unit=meter/second)
        self.assertEqual(cadet_ext.ext_velocity, first_velocity)

        # Step lengths, in column, all add up to the profile_deltas:
        col_lengths = [one_col_length]

        step_velocity0 = get_step_velocity(first_step)
        for step in self.method.method_steps:
            step_velocity = float(get_step_velocity(step))
            step_volume = float(step.volume)
            # Normalize the duration based on the velocity of the step
            col_length = step_volume * step_velocity0 / step_velocity
            col_length *= one_col_length
            col_lengths.append(float(col_length))

        self.assertAlmostEqual(cadet_ext.ext_prof_delta.sum(),
                               sum(col_lengths))
        return cadet_ext
