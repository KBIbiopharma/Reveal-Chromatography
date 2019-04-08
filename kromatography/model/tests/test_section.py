""" Tests for the SchurSolver class. """

import unittest

from kromatography.model.section import Section


class TestSection(unittest.TestCase):

    def setUp(self):
        self.section = Section(4)

    # -------------------------------------------------------------------------
    # Tests
    # -------------------------------------------------------------------------
    def test_vector_lengths(self):
        self.assertEqual(len(self.section.const_coeff), 4,
                         msg="Vector Length: section.const_coeff")
        self.assertEqual(len(self.section.lin_coeff), 4,
                         msg="Vector Length: section.lin_coeff")
        self.assertEqual(len(self.section.quad_coeff), 4,
                         msg="Vector Length: section.quad_coeff")
        self.assertEqual(len(self.section.cube_coeff), 4,
                         msg="Vector Length: section.cube_coeff")

    def test_default_values(self):
        self.assertEqual(self.section.const_coeff.sum(), 0.0,
                         msg="Default Value: section.const_coeff")
        self.assertEqual(self.section.lin_coeff.sum(), 0.0,
                         msg="Default Value: section.const_coeff")
        self.assertEqual(self.section.const_coeff.sum(), 0.0,
                         msg="Default Value: section.const_coeff")
        self.assertEqual(self.section.const_coeff.sum(), 0.0,
                         msg="Default Value: section.const_coeff")

    def test_types(self):
        self.assertIsInstance(self.section.const_coeff[0], float,
                              msg="Data Type: section.const_coeff")
        self.assertIsInstance(self.section.lin_coeff[0], float,
                              msg="Data Type: section.lin_coeff")
        self.assertIsInstance(self.section.quad_coeff[0], float,
                              msg="Data Type: section.quad_coeff")
        self.assertIsInstance(self.section.cube_coeff[0], float,
                              msg="Data Type: section.cube_coeff")


if __name__ == '__main__':
    unittest.main()
