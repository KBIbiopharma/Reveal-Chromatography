""" Tests for the CADET Model class. """

import numpy as np
import unittest

from kromatography.model.cadet_model import CADETModel


class TestCADETModel(unittest.TestCase):

    #: Number of components
    num_components = 3

    #: Number of sections
    num_sections = 4

    def setUp(self):
        self.model = CADETModel(self.num_components, self.num_sections)

    # -------------------------------------------------------------------------
    # Tests
    # -------------------------------------------------------------------------
    def test_default_values(self):
        self.assertEqual(self.model.adsorption_type, 'STERIC_MASS_ACTION',
                         msg="Default Value: model.adsorption_type")
        self.assertEqual(self.model.col_dispersion, 6e-8,
                         msg="Default Value: model.col_dispersion")
        self.assertEqual(self.model.col_length, 0.2,
                         msg="Default Value: model.col_length")
        self.assertEqual(self.model.col_porosity, 0.35,
                         msg="Default Value: model.col_porosity")
        self.assertEqual(self.model.ncomp, self.num_components,
                         msg="Default Value: model.ncomp")
        self.assertEqual(self.model.film_diffusion.sum(), 0.0,
                         msg="Default Value: model.film_diffusion")
        self.assertEqual(len(self.model.film_diffusion), self.num_components,
                         msg="Default Length: model.film_diffusion")
        self.assertEqual(self.model.init_c.sum(), 0.0,
                         msg="Default Value: model.init_c")
        self.assertEqual(len(self.model.init_c), self.num_components,
                         msg="Default Length: model.init_c")
        self.assertEqual(self.model.init_cp.sum(), 0.0,
                         msg="Default Value: model.init_cp")
        self.assertEqual(len(self.model.init_cp), self.num_components,
                         msg="Default Length: model.init_cp")
        self.assertEqual(self.model.init_q.sum(), 0.0,
                         msg="Default Value: model.init_q")
        self.assertEqual(len(self.model.init_q), self.num_components,
                         msg="Default Length: model.init_q")
        self.assertEqual(self.model.par_diffusion.sum(), 0.0,
                         msg="Default Value: model.par_diffusion")
        self.assertEqual(len(self.model.par_diffusion), self.num_components,
                         msg="Default Length: model.par_diffusion")
        self.assertEqual(self.model.par_surfdiffusion.sum(), 0.0,
                         msg="Default Value: model.par_surfdiffusion")
        self.assertEqual(len(self.model.par_surfdiffusion),
                         self.num_components,
                         msg="Default Length: model.par_surfdiffusion")
        self.assertEqual(self.model.par_porosity, 0.5,
                         msg="Default Value: model.par_porosity")
        self.assertEqual(self.model.par_radius, 45e-6,
                         msg="Default Value: model.par_radius")
        self.assertEqual(len(self.model.velocity), self.num_sections,
                         msg="Default Value: model.velocity")

    def test_types(self):
        self.assertEqual(self.model.film_diffusion.dtype, np.float,
                         msg="Data Type: model.film_diffusion")
        self.assertEqual(self.model.init_c.dtype, np.float,
                         msg="Data Type: model.init_c")
        self.assertEqual(self.model.init_cp.dtype, np.float,
                         msg="Data Type: model.init_cp")
        self.assertEqual(self.model.init_q.dtype, np.float,
                         msg="Data Type: model.init_q")
        self.assertEqual(self.model.par_diffusion.dtype, np.float,
                         msg="Data Type: model.par_diffusion")
        self.assertEqual(self.model.par_surfdiffusion.dtype, np.float,
                         msg="Data Type: model.par_surfdiffusion")
        self.assertEqual(self.model.velocity.dtype, np.float,
                         msg="Data Type: model.velocity")

if __name__ == '__main__':
    unittest.main()
