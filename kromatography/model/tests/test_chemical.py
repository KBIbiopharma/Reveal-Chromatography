""" Tests for the Chemical class. """

import unittest

from kromatography.model.chemical import Chemical
from kromatography.model.tests.example_model_data import CHEMICAL_DATA


class TestChemical(unittest.TestCase):

    # -------------------------------------------------------------------------
    # Tests
    # -------------------------------------------------------------------------

    def test_invalid_construction(self):
        with self.assertRaises(ValueError):
            self.chemical = Chemical()

    def test_construction(self):
        chemical = Chemical(**CHEMICAL_DATA)

        # Derived attributes
        self.assertEqual(chemical.formula, "1Sodium+1Chloride")
        self.assertEqual(chemical.component_atom_counts, [1, 1])

        # Derived ChromatographyData attributes
        expected_unique_id = {'formula': '1Sodium+1Chloride', 'state': 'Solid',
                              'type_id': 'CHEMICAL'}
        self.assertEqual(chemical.unique_id, expected_unique_id)
