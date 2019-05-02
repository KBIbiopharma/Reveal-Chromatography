""" Tests for the Buffer Class. """

import unittest

from kromatography.model.buffer import Buffer
from kromatography.model.tests.example_model_data import BUFFER_ELUTION

from app_common.apptools.assertion_utils import flexible_assert_equal


class TestBuffer(unittest.TestCase):

    def setUp(self):
        self.elution = Buffer(**BUFFER_ELUTION)

    # -------------------------------------------------------------------------
    # Tests
    # -------------------------------------------------------------------------

    # FIXME test the Property calculations in buffer file
    # https://github.com/KBIbiopharma/Kromatography/issues/58
    def test_invalid_construction(self):
        with self.assertRaises(ValueError):
            self.elution = Buffer()

    def test_construction_elution(self):
        elution = self.elution
        for key, value in BUFFER_ELUTION.items():
            flexible_assert_equal(getattr(elution, key), value, msg=key)

        self.assertEqual(elution.unique_id, {'name': elution.name})
