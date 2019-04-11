""" Tests for the Component class. """

import unittest

from kromatography.model.component import Component
from kromatography.model.tests.example_model_data import COMPONENT_DATA


class TestComponent(unittest.TestCase):

    def setUp(self):
        self.component = Component(**COMPONENT_DATA)

    # -------------------------------------------------------------------------
    # Tests
    # -------------------------------------------------------------------------

    def test_invalid_construction(self):
        with self.assertRaises(ValueError):
            self.component = Component()

    def test_construction(self):
        component = self.component
        for key, value in COMPONENT_DATA.iteritems():
            self.assertEqual(getattr(component, key), value, msg=key)
