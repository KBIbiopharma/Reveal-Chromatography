import unittest
import numpy as np
from nose.tools import assert_equal, assert_raises, assert_true
from numpy.testing.utils import assert_array_almost_equal

from scimath.units.api import UnitArray, UnitScalar
from traits.api import Enum, HasTraits, Str, TraitError

from app_common.traits.custom_trait_factories import (
    Key, Parameter, ParameterArray, ParameterFloat, ParameterInt,
    ParameterUnitArray, PositiveFloat, PositiveFloatParameter, PositiveInt,
    PositiveIntParameter
)


def test_key_str():

    class TestObject(HasTraits):
        str_attr = Key()
        str_attr_with_default = Key(Str("test_default_str"))

    a = TestObject()

    assert_equal(a.str_attr, "")
    assert_equal(a.str_attr_with_default, "test_default_str")

    for attr in ["str_attr", "str_attr_with_default"]:
        assert_true(a.trait(attr).is_key)


def test_key_enum():

    class TestObject(HasTraits):
        enum_attr = Key(Enum(["val1", "val2"]))

    a = TestObject()
    assert_equal(a.enum_attr, "val1")
    assert_true(a.trait("enum_attr").is_key)

    # Test enum behaves normally
    a.enum_attr = "val2"  # no error
    with assert_raises(TraitError):
        a.enum_attr = "val3"


class GeneralPositiveInt(object):
    def test_initial_value(self):
        self.assertEqual(self.a.int_attr, 0)
        self.assertEqual(self.a.int_attr_with_default, 5)
        self.assertEqual(self.a.int_attr_exclude_low, 5)

    def test_negative_value(self):
        # check negative values are not accepted
        with assert_raises(TraitError):
            self.a.int_attr = -1

    def test_float_value(self):
        # check floats are not accepted
        with assert_raises(TraitError):
            self.a.int_attr = 1.5

    def test_exclude_zero_value(self):
        # check zero is not accepted when exclude_true=True
        with assert_raises(TraitError):
            self.a.int_attr_exclude_low = 0


class TestPositiveInt(unittest.TestCase, GeneralPositiveInt):

    def setUp(self):
        class TestObject(HasTraits):
            int_attr = PositiveInt()
            int_attr_with_default = PositiveInt(value=5)
            int_attr_with_float_default = PositiveInt(value=5)
            int_attr_exclude_low = PositiveInt(value=5, exclude_low=True)

        self.a = TestObject()


class TestPositiveIntParameter(unittest.TestCase, GeneralPositiveInt):

    def setUp(self):
        class TestObject(HasTraits):
            int_attr = PositiveIntParameter()
            int_attr_with_default = PositiveIntParameter(value=5)
            int_attr_with_float_default = PositiveIntParameter(value=5)
            int_attr_exclude_low = PositiveIntParameter(value=5,
                                                        exclude_low=True)

        self.a = TestObject()

    def test_is_parameter(self):
        attr_list = ["int_attr", "int_attr_with_default",
                     "int_attr_with_float_default", "int_attr_exclude_low"]
        for attr_name in attr_list:
            trait = self.a.trait(attr_name)
            assert trait.is_parameter


class GeneralPositiveFloat(object):

    def test_initial_value(self):

        self.assertEqual(self.a.float_attr, 0.0)
        self.assertEqual(self.a.float_attr_with_default, 5.50)
        self.assertEqual(self.a.float_attr_with_int_default, 5.0)
        assert isinstance(self.a.float_attr_with_int_default, float)

    def test_negative_value(self):
        # check negative values are not accepted
        with assert_raises(TraitError):
            self.a.float_attr = -1.0

    def test_exclude_zero_value(self):
        # check zero is not accepted when exclude_true=True
        with assert_raises(TraitError):
            self.a.float_attr_exclude_low = 0.0


class TestPositiveFloat(unittest.TestCase, GeneralPositiveFloat):

    def setUp(self):
        class TestObject(HasTraits):
            float_attr = PositiveFloat()
            float_attr_with_default = PositiveFloat(value=5.5)
            float_attr_with_int_default = PositiveFloat(value=5)
            float_attr_exclude_low = PositiveFloat(value=5.0, exclude_low=True)

        self.a = TestObject()


class TestPositiveFloatParameter(unittest.TestCase, GeneralPositiveFloat):

    def setUp(self):
        class TestObject(HasTraits):
            float_attr = PositiveFloatParameter()
            float_attr_with_default = PositiveFloatParameter(value=5.5)
            float_attr_with_int_default = PositiveFloatParameter(value=5)
            float_attr_exclude_low = PositiveFloatParameter(value=5.0,
                                                            exclude_low=True)

        self.a = TestObject()

    def test_is_parameter(self):
        attr_list = ["float_attr", "float_attr_with_default",
                     "float_attr_with_int_default", "float_attr_exclude_low"]
        for attr_name in attr_list:
            trait = self.a.trait(attr_name)
            assert trait.is_parameter


class GeneralParameter(object):

    def setUp(self):
        class TestObject(HasTraits):
            empty_attr = self.klass
            attr_with_default = self.klass(self.default)

        self.a = TestObject()

    def test_initial_value(self):
        self.assertIsNone(self.a.empty_attr)
        if isinstance(self.default, np.ndarray):
            assert_array_almost_equal(self.a.attr_with_default, self.default)
        else:
            self.assertEqual(self.a.attr_with_default, self.default)

    def test_is_parameter(self):
        attr_list = ["empty_attr", "attr_with_default"]
        for attr_name in attr_list:
            trait = self.a.trait(attr_name)
            assert trait.is_parameter


class TestParameterInt(unittest.TestCase, GeneralParameter):
    def setUp(self):
        self.default = 2
        self.klass = ParameterInt
        GeneralParameter.setUp(self)

    def test_float_value(self):
        with assert_raises(TraitError):
            self.a.empty_attr = 1.5

    def test_array_value(self):
        with assert_raises(TraitError):
            self.a.empty_attr = np.array([1, 2, 3])


class TestParameterFloat(unittest.TestCase, GeneralParameter):
    def setUp(self):
        self.default = 2.0
        self.klass = ParameterFloat
        GeneralParameter.setUp(self)

    def test_int_value(self):
        with assert_raises(TraitError):
            self.a.empty_attr = "1"

    def test_array_value(self):
        with assert_raises(TraitError):
            self.a.empty_attr = np.array([1, 2, 3])


class TestParameter(unittest.TestCase, GeneralParameter):
    def setUp(self):
        self.default = UnitScalar(1, units="cm")
        self.klass = Parameter
        GeneralParameter.setUp(self)

    def test_float_value(self):
        with assert_raises(TraitError):
            self.a.empty_attr = 1.5

    def test_unit_array_value(self):
        with assert_raises(TraitError):
            self.a.empty_attr = UnitArray([1, 2], units="cm")


class TestParameterArray(unittest.TestCase, GeneralParameter):
    def setUp(self):
        self.default = np.array([1, 2])
        self.klass = ParameterArray
        GeneralParameter.setUp(self)

    def test_float_value(self):
        with assert_raises(TraitError):
            self.a.empty_attr = 1.5

    def test_unit_array_value(self):
        # A unitArray is just an array with a units attribute, so this is legal
        self.a.empty_attr = UnitArray([1, 2], units="cm")


class TestParameterUnitArray(unittest.TestCase, GeneralParameter):
    def setUp(self):
        self.default = UnitArray([1, 2], units="cm")
        self.klass = ParameterUnitArray
        GeneralParameter.setUp(self)

    def test_float_value(self):
        with assert_raises(TraitError):
            self.a.empty_attr = 1.5

    def test_unit_scalar_value(self):
        # UnitScalar subclasses UnitArray, so this is legal
        self.a.empty_attr = UnitScalar(1, units="cm")
