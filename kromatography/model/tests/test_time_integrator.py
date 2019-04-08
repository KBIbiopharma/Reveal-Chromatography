""" Tests for the TestTimeIntegrator class. """

import unittest

from kromatography.model.time_integrator import TimeIntegrator


class TestTimeIntegrator(unittest.TestCase):

    def setUp(self):
        self.time_integrator = TimeIntegrator()

    # -------------------------------------------------------------------------
    # Tests
    # -------------------------------------------------------------------------
    def test_default_values(self):
        self.assertEqual(self.time_integrator.abstol, 1e-8,
                         msg="Default Value: time_integrator.abstol")
        self.assertEqual(self.time_integrator.init_step_size, 1.0e-6,
                         msg="Default Value: time_integrator.init_step_size")
        self.assertEqual(self.time_integrator.max_steps, 10000,
                         msg="Default Value: time_integrator.max_steps")
        self.assertEqual(self.time_integrator.reltol, 0,
                         msg="Default Value: time_integrator.reltol")

    def test_types(self):
        self.assertIsInstance(self.time_integrator.abstol, float,
                              msg="Data Type: time_integrator.abstol")
        self.assertIsInstance(self.time_integrator.init_step_size, float,
                              msg="Data Type: time_integrator.init_step_size")
        self.assertIsInstance(self.time_integrator.max_steps, int,
                              msg="Data Type: time_integrator.max_steps")
        self.assertIsInstance(self.time_integrator.reltol, float,
                              msg="Data Type: time_integrator.reltol")


if __name__ == '__main__':
    unittest.main()
