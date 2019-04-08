""" Tests for the Sensitivity class. """

import unittest

from kromatography.model.sensitivity import Sensitivity


class TestSensitivity(unittest.TestCase):

    def setUp(self):
        self.sensitivity = Sensitivity()

    # -------------------------------------------------------------------------
    # Tests
    # -------------------------------------------------------------------------
    def test_default_values(self):
        self.assertEqual(self.sensitivity.nsens, 0,
                         msg="Default Value: sensitivity.nsens")
        self.assertEqual(self.sensitivity.sens_method, "ad1",
                         msg="Default Value: sensitivity.sens_method")

    def test_types(self):
        self.assertIsInstance(self.sensitivity.nsens, int,
                              msg="Data Type: sensitivity.nsens")
        self.assertIsInstance(self.sensitivity.sens_method, str,
                              msg="Data Type: sensitivity.sens_method")


if __name__ == '__main__':
    unittest.main()
