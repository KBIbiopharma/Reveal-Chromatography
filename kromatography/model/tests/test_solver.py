""" Tests for the Solver class. """
import unittest

from kromatography.model.solver import DEFAULT_NUM_TIMES, Solver


class TestSolver(unittest.TestCase):

    def setUp(self):
        self.solver = Solver()

    # -------------------------------------------------------------------------
    # Tests
    # -------------------------------------------------------------------------

    def test_default_values(self):
        self.assertEqual(self.solver.nthreads, 1)
        self.assertEqual(self.solver.log_level, 'INFO')
        self.assertEqual(self.solver.print_config, 1)
        self.assertEqual(self.solver.print_paramlist, 0)
        self.assertEqual(self.solver.print_progress, 1)
        self.assertEqual(self.solver.print_statistics, 1)
        self.assertEqual(self.solver.print_timing, 1)
        self.assertEqual(self.solver.use_analytic_jacobian, 1)
        self.assertEqual(self.solver.number_user_solution_points,
                         DEFAULT_NUM_TIMES)
        self.assertEqual(self.solver.write_at_user_times, 0)
        self.assertEqual(self.solver.write_solution_times, 1)
        self.assertEqual(self.solver.write_solution_column_inlet, 1)
        self.assertEqual(self.solver.write_solution_column_outlet, 1)
        self.assertEqual(self.solver.write_solution_all, 1)
        self.assertEqual(self.solver.write_solution_last, 0)
        self.assertEqual(self.solver.write_sens_column_outlet, 0)
        self.assertEqual(self.solver.write_sens_all, 0)
        self.assertEqual(self.solver.write_sens_last, 0)

    def test_solution_times(self):
        self.solver.calculate_user_solution_times(end_time=1000)
        self.assertEqual(len(self.solver.user_solution_times),
                         DEFAULT_NUM_TIMES)
        self.assertEqual(self.solver.user_solution_times[0], 0.0)
        self.assertEqual(self.solver.user_solution_times[-1], 1000.0)
        self.assertEqual(self.solver.write_at_user_times, 1)
