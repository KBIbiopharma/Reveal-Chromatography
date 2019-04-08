""" Utilities providing new custom assertions to support unit tests.
"""
# Import even if not used, to retain backward compatibility:
from app_common.traits.assertion_utils import assert_has_traits_almost_equal, assert_values_almost_equal  # noqa
from app_common.scimath.assertion_utils import *  # noqa
from app_common.traits.assertion_utils import assert_has_traits_not_almost_equal, assert_values_not_almost_equal  # noqa

from kromatography.io.serializer import serialize
from kromatography.io.deserializer import deserialize
from kromatography.io.reader_writer import load_object, save_object


def assert_roundtrip_identical(obj, ignore=(), eps=1e-9):
    """ Serialize and deserialize an object and assert that the resulting
    object is identical to the input object.

    Returns
    -------
    Any
        Object serialized and recreated is returned if user needs to run
        additional tests.
    """
    from app_common.apptools.io.assertion_utils import \
        assert_roundtrip_identical

    return assert_roundtrip_identical(obj, serial_func=serialize,
                                      deserial_func=deserialize, ignore=ignore,
                                      eps=eps)


def assert_file_roundtrip_identical(obj, ignore=(), eps=1e-9, target_dir=None):
    """ Serialize and deserialize an object to file and assert that the
    resulting object is identical to the input object.

    Returns
    -------
    Any
        Object serialized and recreated is returned if user needs to run
        additional tests.
    """
    from app_common.apptools.io.assertion_utils import \
        assert_file_roundtrip_identical

    return assert_file_roundtrip_identical(
        obj, save_func=save_object, load_func=load_object, ignore=ignore,
        eps=eps, target_dir=target_dir)
