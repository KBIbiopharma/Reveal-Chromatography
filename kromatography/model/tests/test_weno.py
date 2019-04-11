""" Tests for the Weno class. """

import unittest

from kromatography.model.weno import Weno


class TestWeno(unittest.TestCase):

    def setUp(self):
        self.weno = Weno()

    # -------------------------------------------------------------------------
    # Tests
    # -------------------------------------------------------------------------
    def test_default_values(self):
        self.assertEqual(self.weno.boundary_model, 0,
                         msg="Default Value: weno.boundary_model")
        self.assertEqual(self.weno.weno_eps, 1.0e-6,
                         msg="Default Value: weno.weno_eps")
        self.assertEqual(self.weno.weno_order, 3,
                         msg="Default Value: schur_solver.max_restarts")

    def test_types(self):
        self.assertIsInstance(self.weno.boundary_model, int,
                              msg="Data Type: weno.boundary_model")
        self.assertIsInstance(self.weno.weno_eps, float,
                              msg="Data Type: weno.weno_eps")
        self.assertIsInstance(self.weno.weno_order, int,
                              msg="Data Type: weno.weno_order")


if __name__ == '__main__':
    unittest.main()
