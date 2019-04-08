# -*- coding: utf-8 -*-
""" Tests for the utility functions in str_utils module. """

from nose.tools import assert_equal, assert_true, assert_false

from kromatography.utils.str_utils import get_dtype, sanitize_str_list, \
    is_string_valid_variable_name, strip_decode_strings


def test_validate_string():
    assert_true(is_string_valid_variable_name("CEX_Acidic1"))
    assert_false(is_string_valid_variable_name("CEX Acidic1"))
    assert_false(is_string_valid_variable_name("Acidic+"))
    assert_false(is_string_valid_variable_name("Aci+dic"))
    assert_false(is_string_valid_variable_name("1Acidic"))
    assert_false(is_string_valid_variable_name("Acidic="))
    assert_false(is_string_valid_variable_name("Acidic<"))
    assert_false(is_string_valid_variable_name(" "))

    # Test options
    assert_true(is_string_valid_variable_name("Acidic "))
    assert_false(is_string_valid_variable_name("Acidic ", bad_char=" "))
    assert_false(is_string_valid_variable_name("CEX_Acidic", bad_char="_"))
    assert_true(is_string_valid_variable_name("Product"))
    assert_false(is_string_valid_variable_name("Product",
                                               bad_values=["Product"]))


def test_get_dtype():
    assert_equal(get_dtype("foo"), "str")
    assert_equal(get_dtype("1"), "float")
    assert_equal(get_dtype("1."), "float")
    assert_equal(get_dtype("1.0"), "float")
    assert_equal(get_dtype(".01"), "float")


def test_strip_decode_strings():
    clean_list = ["foo", "bar"]
    assert_equal(strip_decode_strings(clean_list), ["foo", "bar"])

    # Clean spaces
    list_to_clean = ["foo ", " bar "]
    assert_equal(strip_decode_strings(list_to_clean), clean_list)

    # Clean non-ascii (degree symbol)
    list_to_clean = ["\xc2\xb0C"]
    assert_equal(strip_decode_strings(list_to_clean), ["C"])


def test_sanitize_str_list():
    clean_list = ["foo", "bar"]
    sanitize_str_list(clean_list)
    assert_equal(clean_list, ["foo", "bar"])

    list_to_clean = ["foo", "bar", ""]
    sanitize_str_list(list_to_clean)
    assert_equal(list_to_clean, clean_list)

    list_to_clean = ["foo", "bar", "", "", ""]
    sanitize_str_list(list_to_clean)
    assert_equal(list_to_clean, clean_list)
