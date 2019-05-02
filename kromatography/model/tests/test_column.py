""" Tests for the Column and ColumnType classes. """

import unittest
from numpy import linspace

from scimath.units.api import UnitScalar
from traits.testing.unittest_tools import UnittestTools

from app_common.scimath.assertion_utils import assert_unit_scalar_almost_equal
from app_common.apptools.assertion_utils import flexible_assert_equal

from kromatography.model.resin import Resin
from kromatography.model.column import Column, ColumnType
from kromatography.model.tests.example_model_data import COLUMN_DATA, \
    COLUMN_TYPE_DATA, RESIN_DATA
from kromatography.utils.chromatography_units import milliliter


class TestColumnType(unittest.TestCase):

    def setUp(self):
        self.column_type = ColumnType(**COLUMN_TYPE_DATA)

    # -------------------------------------------------------------------------
    # Tests
    # -------------------------------------------------------------------------
    def test_invalid_construction(self):
        with self.assertRaises(ValueError):
            self.column_type = ColumnType()

    def test_construction(self):
        column_type = self.column_type
        for key, value in COLUMN_TYPE_DATA.items():
            flexible_assert_equal(getattr(column_type, key), value, msg=key)


class TestColumn(unittest.TestCase, UnittestTools):

    def setUp(self):
        self.column_type = ColumnType(**COLUMN_TYPE_DATA)
        self.resin = Resin(**RESIN_DATA)
        self.column = Column(column_type=self.column_type, resin=self.resin,
                             **COLUMN_DATA)

    # -------------------------------------------------------------------------
    # Tests
    # -------------------------------------------------------------------------
    def test_invalid_construction(self):
        with self.assertRaises(ValueError):
            self.column = Column()

    def test_construction(self):
        column = self.column
        for key, value in COLUMN_DATA.items():
            flexible_assert_equal(getattr(column, key), value, msg=key)

        for key, value in COLUMN_TYPE_DATA.items():
            flexible_assert_equal(getattr(column.column_type, key), value,
                                  msg=key)

        for key, value in RESIN_DATA.items():
            flexible_assert_equal(getattr(column.resin, key), value, msg=key)

    def test_wrong_bed_height(self):
        # set to a range of allowed values
        height_range = self.column.column_type.bed_height_range
        # FIXME: would be nice for scimath to make these UnitScalar
        # automatically
        h_min, h_max = height_range

        for height in linspace(h_min, h_max):
            height = UnitScalar(height, units=height_range.units)
            self.column.bed_height_actual = height

        # setting outside the range of allowed values fails
        with self.assertRaises(ValueError):
            too_large = UnitScalar(h_max + 1, units=height_range.units)
            self.column.bed_height_actual = too_large

        with self.assertRaises(ValueError):
            too_small = UnitScalar(h_min - 1, units=height_range.units)
            self.column.bed_height_actual = too_small

    def test_volume_calculation(self):
        actual_col_vol = UnitScalar(157079.63, units=milliliter)
        assert_unit_scalar_almost_equal(self.column.volume, actual_col_vol,
                                        eps=1e-2)

    def test_set_volume_bad_values(self):
        with self.assertRaises(ValueError):
            self.column.volume = 1.

        with self.assertRaises(ValueError):
            self.column.volume = UnitScalar(1., units="cm")

    def test_set_volume(self):
        x = UnitScalar(1e-1, units="m**3")
        with self.assertTraitChanges(self.column, "bed_height_actual", 1):
            self.column.volume = x
        assert_unit_scalar_almost_equal(self.column.volume, x)

        # Do nothing if value is already set
        with self.assertTraitDoesNotChange(self.column, "bed_height_actual"):
            self.column.volume = x

        # Different unit
        x2 = UnitScalar(150, units="liter")
        with self.assertTraitChanges(self.column, "bed_height_actual", 1):
            self.column.volume = x2
        assert_unit_scalar_almost_equal(self.column.volume, x2)
