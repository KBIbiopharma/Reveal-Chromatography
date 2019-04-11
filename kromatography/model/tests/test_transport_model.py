""" Tests for the TransportModel class. """

import unittest
import numpy as np
from numpy.testing import assert_array_equal

from kromatography.model.transport_model import GeneralRateModel


class TestGeneralRateModel(unittest.TestCase):

    def setUp(self):
        self.ncomp = 4
        self.model = GeneralRateModel(self.ncomp, name="test")

        self.custom_names = list("abcd")
        self.model2 = GeneralRateModel(self.ncomp, name="test",
                                       component_names=self.custom_names)

    # -------------------------------------------------------------------------
    # Tests
    # -------------------------------------------------------------------------
    def test_default_values(self):
        model = self.model

        # check scalars attributes
        self.assertEqual(model.column_porosity, 0.3)
        self.assertEqual(model.axial_dispersion, 6.0e-8)
        self.assertEqual(model.bead_porosity, 0.5)

        # check array attributes
        zero_array = np.zeros(self.ncomp)
        ones_array = np.ones(self.ncomp)
        assert_array_equal(model.pore_diffusion, 1.0e-11 * ones_array)
        assert_array_equal(model.surface_diffusion, zero_array)
        assert_array_equal(model.film_mass_transfer, 5e-5 * ones_array)

    def test_component_names(self):
        default_names = ["Cation", "Component1", "Component2", "Component3"]
        self.assertEqual(self.model.component_names, default_names)
        self.assertEqual(self.model2.component_names, self.custom_names)
