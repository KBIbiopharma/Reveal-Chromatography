""" Tests for the System and SystemType classes. """

import unittest

from kromatography.model.system import System, SystemType
from kromatography.model.tests.example_model_data import (
    SYSTEM_TYPE_DATA, SYSTEM_DATA
)


class TestSystemType(unittest.TestCase):

    def setUp(self):
        self.system_type = SystemType(**SYSTEM_TYPE_DATA)

    # -------------------------------------------------------------------------
    # Tests
    # -------------------------------------------------------------------------
    def test_construction(self):
        system_type = self.system_type
        for key, value in SYSTEM_TYPE_DATA.iteritems():
            self.assertEqual(getattr(system_type, key), value, msg=key)


class TestSystem(unittest.TestCase):

    def setUp(self):
        system_type = SystemType(**SYSTEM_TYPE_DATA)
        self.system = System(system_type=system_type, **SYSTEM_DATA)

    # -------------------------------------------------------------------------
    # Tests
    # -------------------------------------------------------------------------
    def test_construction(self):
        system = self.system
        for key, value in SYSTEM_DATA.iteritems():
            self.assertEqual(getattr(system, key), value, msg=key)
