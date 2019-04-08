""" Tests for the Discretization class. """

import unittest

from kromatography.model.discretization import Discretization
from kromatography.model.weno import Weno


class TestWeno(unittest.TestCase):

    def setUp(self):
        self.discretization = Discretization()

    # -------------------------------------------------------------------------
    # Tests
    # -------------------------------------------------------------------------
    def test_default_values(self):
        self.assertEqual(self.discretization.ncol, 50,
                         msg="Default Value: discretization.ncol")
        self.assertEqual(self.discretization.npar, 5,
                         msg="Default Value: discretization.npar")
        self.assertEqual(self.discretization.par_disc_type, 'EQUIDISTANT_PAR',
                         msg="Default Value: discretization.par_disc_type")
        self.assertEqual(self.discretization.reconstruction, 'WENO',
                         msg="Default Value: discretization.reconstruction")
        self.assertEqual(self.discretization.par_disc_vector.sum(), 0.0,
                         msg="Default Value: discretization." +
                             "par_disc_vector.sum()")
        self.assertEquals(len(self.discretization.par_disc_vector),
                          self.discretization.npar+1,
                          msg="Default Length: discretization." +
                              "par_disc_vector.sum()")

    def test_types(self):
        self.assertIsInstance(self.discretization.ncol, int,
                              msg="Data Type: discretization.ncol")
        self.assertIsInstance(self.discretization.npar, int,
                              msg="Data Type: discretization.npar")
        self.assertIsInstance(self.discretization.par_disc_type, str,
                              msg="Data Type: discretization.par_disc_type")
        self.assertIsInstance(self.discretization.reconstruction, str,
                              msg="Data Type: discretization.reconstruction")
        self.assertIsInstance(self.discretization.par_disc_vector[0], float,
                              msg="Data Type: discretization.par_disc_vector")
        self.assertIsInstance(self.discretization.weno, Weno,
                              msg="Data Type: discretization.weno")


if __name__ == '__main__':
    unittest.main()
