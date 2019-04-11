""" Tests for the MethodStep Class. """

import unittest

from scimath.units.unit_scalar import UnitScalar

from kromatography.model.method_step import MethodStep
from kromatography.model.tests.example_model_data import (
    GRADIENT_ELUTION_STEP, PRE_EQUIL_STEP
)
from kromatography.utils.chromatography_units import cm_per_hr, column_volumes
from kromatography.model.tests.base_chrom_data_test_case import \
    BaseChromDataTestCase


class TestMethodStep(unittest.TestCase, BaseChromDataTestCase):

    # -------------------------------------------------------------------------
    # BaseChromDataTestCase
    # -------------------------------------------------------------------------

    def setUp(self):
        self.model = MethodStep(**PRE_EQUIL_STEP)

    # -------------------------------------------------------------------------
    # Custom tests
    # -------------------------------------------------------------------------

    def test_attrs_pre_eq_step(self):
        self.assertEqual(self.model.name, 'Pre-Equilibration')
        self.assertIsInstance(self.model.solutions, list)
        expected_flow_rate = UnitScalar(200, units=cm_per_hr)
        self.assertEqual(self.model.flow_rate, expected_flow_rate)
        expected_volume = UnitScalar(1.5, units=column_volumes)
        self.assertEqual(self.model.volume, expected_volume)

    def test_construction_gradient_elution_step(self):
        step = MethodStep(**GRADIENT_ELUTION_STEP)
        self.assertEqual(step.name, 'Gradient Elution')
        self.assertEqual(len(step.solutions), 2)
        self.assertEqual(step.flow_rate, UnitScalar(100, units=cm_per_hr))
        self.assertEqual(step.volume, UnitScalar(8.4, units=column_volumes))
