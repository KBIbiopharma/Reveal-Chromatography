""" Tests for the Method Class. """

import unittest

from app_common.traits.assertion_utils import assert_has_traits_almost_equal

from kromatography.model.method import Method
from kromatography.model.method_step import MethodStep
from kromatography.model.tests.example_model_data import \
    GRADIENT_ELUTION_STEP, METHOD_DATA, PRE_EQUIL_STEP, LOAD_STEP


class TestMethod(unittest.TestCase):

    def setUp(self):
        self.method = Method(**METHOD_DATA)

    # -------------------------------------------------------------------------
    # Tests
    # -------------------------------------------------------------------------

    def test_construction(self):
        method = self.method
        # Default data contains a Pre-Equil, an Equil, a Load, and a Gradient
        # Elution
        self.assertEqual(method.num_steps, 4)
        for key, val in METHOD_DATA.iteritems():
            self.assertEqual(getattr(method, key), val)

    def test_construction_duplicate_step_name(self):
        # Make data with redundant step names:
        data = {
            'name': 'method-1',
            'run_type': 'Gradient Elution',
            'method_steps': [MethodStep(**PRE_EQUIL_STEP),
                             MethodStep(**PRE_EQUIL_STEP),
                             MethodStep(**LOAD_STEP),
                             MethodStep(**GRADIENT_ELUTION_STEP)],
        }
        with self.assertRaises(ValueError):
            Method(**data)

    def test_get_load(self):
        # Remove load from method
        load = self.method.method_steps.pop(2)
        with self.assertRaises(ValueError):
            self.method.load

        # Put load back and look it up
        self.method.method_steps.insert(2, load)
        self.assertIs(self.method.load, load)

    def test_get_step(self):
        with self.assertRaises(ValueError):
            self.method.get_step_of_type("")

        step = self.method.get_step_of_type('Pre-Equilibration')
        assert_has_traits_almost_equal(step, MethodStep(**PRE_EQUIL_STEP))
        step = self.method.get_step_of_type('Gradient Elution')
        assert_has_traits_almost_equal(step,
                                       MethodStep(**GRADIENT_ELUTION_STEP))

        # Collect step number
        step, num = self.method.get_step_of_type('Pre-Equilibration',
                                                 collect_step_num=True)
        assert_has_traits_almost_equal(step, MethodStep(**PRE_EQUIL_STEP))
        self.assertEqual(num, 0)

        # Don't raise on failures
        self.method.get_step_of_type("", handle_not_unique='warn')

    def test_get_step_by_name(self):
        with self.assertRaises(ValueError):
            self.method.get_step_of_name("")

        step = self.method.get_step_of_name('Pre-Equilibration')
        assert_has_traits_almost_equal(step, MethodStep(**PRE_EQUIL_STEP))
        step = self.method.get_step_of_name('whatever name')
        assert_has_traits_almost_equal(step, MethodStep(**LOAD_STEP))

        # Collect step number
        step, num = self.method.get_step_of_name('whatever name',
                                                 collect_step_num=True)
        assert_has_traits_almost_equal(step, MethodStep(**LOAD_STEP))
        self.assertEqual(num, 2)

        # Don't raise on failures
        self.method.get_step_of_name("", handle_not_unique='warn')

    def test_initial_buffer(self):
        from kromatography.model.tests.example_model_data import \
            buffer_equil_wash1

        self.assertEqual(self.method.initial_buffer_name, '')
        self.assertIsNone(self.method.initial_buffer)
        self.method.initial_buffer = buffer_equil_wash1
        self.assertEqual(self.method.initial_buffer_name, 'Equil_Wash_1')
        self.assertEqual(self.method.initial_buffer.name, 'Equil_Wash_1')
