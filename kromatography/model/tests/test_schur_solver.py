""" Tests for the SchurSolver class. """

import unittest

from kromatography.model.schur_solver import SchurSolver


class TestSchurSolver(unittest.TestCase):

    def setUp(self):
        self.schur_solver = SchurSolver()

    # -------------------------------------------------------------------------
    # Tests
    # -------------------------------------------------------------------------
    def test_default_values(self):
        self.assertEqual(self.schur_solver.gs_type, 1,
                         msg="Default Value: schur_solver.gs_type")
        self.assertEqual(self.schur_solver.max_krylov, 0,
                         msg="Default Value: schur_solver.max_krylov")
        self.assertEqual(self.schur_solver.max_restarts, 0,
                         msg="Default Value: schur_solver.max_restarts")
        self.assertEqual(self.schur_solver.schur_safety, 1.0e-8,
                         msg="Default Value: schur_solver.schur_safety")

    def test_types(self):
        self.assertIsInstance(self.schur_solver.gs_type, int,
                              msg="Data Type: schur_solver.gs_type")
        self.assertIsInstance(self.schur_solver.gs_type, int,
                              msg="Data Type: schur_solver.gs_type")
        self.assertIsInstance(self.schur_solver.max_krylov, int,
                              msg="Data Type: schur_solver.max_krylov")
        self.assertIsInstance(self.schur_solver.max_restarts, int,
                              msg="Data Type: schur_solver.max_restarts")
        self.assertIsInstance(self.schur_solver.schur_safety, float,
                              msg="Data Type: schur_solver.schur_safety")


if __name__ == '__main__':
    unittest.main()
