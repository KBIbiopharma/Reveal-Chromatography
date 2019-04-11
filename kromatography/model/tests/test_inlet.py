""" Tests for the Inlet class. """

import unittest

from kromatography.model.inlet import Inlet


class TestInlet(unittest.TestCase):

    def setUp(self):
        self.num_components = 4
        self.num_sections = 3
        self.inlet = Inlet(self.num_components, self.num_sections)

    # -------------------------------------------------------------------------
    # Tests
    # -------------------------------------------------------------------------
    def test_vector_lengths(self):
        num_sections = self.num_sections
        self.assertEqual(len(self.inlet.section_times), num_sections + 1,
                         msg="Vector Length: inlet.section_times")
        self.assertEqual(len(self.inlet.section_continuity), num_sections - 1,
                         msg="Vector Length: inlet.section_continuity")
        self.assertEqual(len(self.inlet.section), num_sections,
                         msg="Vector Length: inlet.section")

    def test_default_values(self):
        self.assertEqual(self.inlet.nsec, self.num_sections,
                         msg="Default Value: inlet.nsec")
        self.assertEqual(self.inlet.section_times.sum(), 0,
                         msg="Default Value: inlet.section_times")
        self.assertEqual(self.inlet.section_continuity.sum(), 0,
                         msg="Default Value: inlet.section_continuity")

    def test_types(self):
        self.assertIsInstance(self.inlet.nsec, int,
                              msg="Data Type: inlet.nsec")
        self.assertIsInstance(self.inlet.section_times[0], float,
                              msg="Data Type: inlet.section_times")
        self.assertIsInstance(self.inlet.section_continuity[0], int,
                              msg="Data Type: inlet.section_continuity")
