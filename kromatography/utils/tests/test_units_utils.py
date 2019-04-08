# -*- coding: utf-8 -*-
""" Tests for the utility functions in units_utils module. """

from unittest import TestCase
import numpy as np

from scimath.units.api import UnitArray, UnitScalar

from app_common.scimath.assertion_utils import assert_unit_scalar_almost_equal
from app_common.scimath.units_utils import unit_scalars_almost_equal

from kromatography.utils.units_utils import linear_flow_rate_to_volumetric, \
    time_to_volume, vol_to_time, volumetric_flow_rate_to_linear
from kromatography.model.tests.example_model_data import COLUMN_DATA, \
    COLUMN_TYPE_DATA
from kromatography.model.column import Column, ColumnType


class TestVolToTime(TestCase):
    def setUp(self):
        self.flow_rate_vol = UnitScalar(1., units="liter/minute")
        self.flow_rate_lin = UnitScalar(1., units="cm/minute")
        column_type = ColumnType(**COLUMN_TYPE_DATA)
        self.column = Column(column_type=column_type, **COLUMN_DATA)
        self.column.column_type.diameter = UnitScalar(10, units='cm')
        self.column.column_type.bed_height_range = UnitArray([10., 30.],
                                                             units="cm")
        self.column.volume = UnitScalar(1, units='liter')

    def test_vol_as_float(self):
        with self.assertRaises(ValueError):
            vol_to_time(3., self.flow_rate_vol)

    def test_vol_std_units_with_vol_flow(self):
        volume = UnitScalar(1., units="liter")
        time = vol_to_time(volume, self.flow_rate_vol)
        self.assertAlmostEqual(time, 1.)

        volume = UnitScalar(3., units="liter")
        time = vol_to_time(volume, self.flow_rate_vol)
        self.assertAlmostEqual(time, 3.)

    def test_vol_std_units_with_lin_flow(self):
        volume = UnitScalar(1., units="liter")
        time = vol_to_time(volume, flow_rate=self.flow_rate_lin,
                           column=self.column)
        self.assertAlmostEqual(time, 40./np.pi)

        volume = UnitScalar(3., units="liter")
        time = vol_to_time(volume, self.flow_rate_lin, column=self.column)
        self.assertAlmostEqual(time, 120./np.pi)

    def test_compute_with_volume_in_CV_units(self):
        flow_rate_vol = UnitScalar(1., units="liter/minute")
        volume = UnitScalar(1., units="CV")
        time = vol_to_time(volume, flow_rate_vol, column=self.column)
        self.assertAlmostEqual(time, 1.)


class TestTimeToVolume(TestCase):
    def setUp(self):
        self.flow_rate_vol = UnitScalar(1., units="liter/minute")
        self.flow_rate_lin = UnitScalar(1., units="cm/minute")
        column_type = ColumnType(**COLUMN_TYPE_DATA)
        self.column = Column(column_type=column_type, **COLUMN_DATA)
        self.column.column_type.diameter = UnitScalar(10, units='cm')
        self.column.column_type.bed_height_range = UnitArray([10., 30.],
                                                             units="cm")
        self.column.volume = UnitScalar(1, units='liter')

    def test_time_as_float(self):
        with self.assertRaises(ValueError):
            time_to_volume(3., self.flow_rate_vol)

    def test_time_std_units_with_vol_flow(self):
        time = UnitScalar(1., units="minute")
        volume = time_to_volume(time, self.flow_rate_vol, self.column)
        assert_unit_scalar_almost_equal(volume, UnitScalar(1., units="CV"))

        time = UnitScalar(3., units="minute")
        volume = time_to_volume(time, self.flow_rate_vol, self.column)
        assert_unit_scalar_almost_equal(volume, UnitScalar(3., units="CV"))

    def test_time_std_units_with_lin_flow(self):
        time = UnitScalar(10., units="minute")
        volume = time_to_volume(time, flow_rate=self.flow_rate_lin,
                                column=self.column)
        self.assertAlmostEqual(volume, UnitScalar(np.pi/4., units="CV"))

        time = UnitScalar(30., units="minute")
        volume = time_to_volume(time, self.flow_rate_lin, column=self.column)
        assert_unit_scalar_almost_equal(volume, UnitScalar(3 * np.pi / 4.,
                                                           units="CV"))

    def test_compute_with_volume_in_CV_units(self):
        time = UnitScalar(1., units="minute")
        volume = time_to_volume(time, self.flow_rate_vol, to_unit="liter")
        assert_unit_scalar_almost_equal(volume, UnitScalar(1., units="liter"))

        time = UnitScalar(3., units="minute")
        volume = time_to_volume(time, self.flow_rate_vol, to_unit="liter")
        assert_unit_scalar_almost_equal(volume, UnitScalar(3., units="liter"))


class TestLinearFlowRateToVolumetric(TestCase):
    def test_convert(self):
        flow_rate_lin = UnitScalar(1., units="cm/minute")
        diam = UnitScalar(2/np.sqrt(0.1 * np.pi), units="0.1*m")
        expected_vol_flow = UnitScalar(1., units="liter/minute")
        vol_flow = linear_flow_rate_to_volumetric(flow_rate_lin, diam)
        self.assertTrue(unit_scalars_almost_equal(vol_flow, expected_vol_flow))

    def test_convert_with_unit_change(self):
        flow_rate_lin = UnitScalar(1., units="cm/minute")
        diam = UnitScalar(2/np.sqrt(0.1 * np.pi), units="0.1*m")
        expected_vol_flow = UnitScalar(1., units="liter/minute")
        vol_flow = linear_flow_rate_to_volumetric(flow_rate_lin, diam,
                                                  to_unit="liter/minute")
        self.assertTrue(unit_scalars_almost_equal(vol_flow, expected_vol_flow))


class TestVolumetricFlowRateToLinear(TestCase):
    def test_convert(self):
        expected_lin_flow = UnitScalar(1., units="cm/minute")
        diam = UnitScalar(2/np.sqrt(0.1 * np.pi), units="0.1*m")
        vol_flow_rate = UnitScalar(1., units="liter/minute")
        lin_flow = volumetric_flow_rate_to_linear(vol_flow_rate, diam)
        self.assertTrue(unit_scalars_almost_equal(lin_flow, expected_lin_flow))

    def test_convert_with_unit_change(self):
        expected_lin_flow = UnitScalar(1., units="cm/minute")
        diam = UnitScalar(2/np.sqrt(0.1 * np.pi), units="0.1*m")
        vol_flow_rate = UnitScalar(1., units="liter/minute")
        lin_flow = volumetric_flow_rate_to_linear(vol_flow_rate, diam,
                                                  to_unit="cm/minute")
        self.assertTrue(unit_scalars_almost_equal(lin_flow, expected_lin_flow))
