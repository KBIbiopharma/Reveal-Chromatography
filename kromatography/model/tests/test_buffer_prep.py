""" Tests for the Buffer Prep Class. """

import unittest

from kromatography.model.buffer_prep import BufferPrep
from kromatography.model.tests.example_model_data import BUFFER_PREP_ELUTION, \
    ELUTION_INTERNAL

from app_common.scimath.assertion_utils import assert_unit_array_almost_equal
from app_common.apptools.assertion_utils import flexible_assert_equal


class TestBufferPrep(unittest.TestCase):

    def setUp(self):
        self.elution = BufferPrep(**BUFFER_PREP_ELUTION)

    # -------------------------------------------------------------------------
    # Tests
    # -------------------------------------------------------------------------

    # FIXME test the Property calculations in buffer file
    # https://github.com/KBIbiopharma/Kromatography/issues/58
    def test_invalid_construction(self):
        with self.assertRaises(ValueError):
            self.elution = BufferPrep()

    def test_construction_elution(self):
        elution = self.elution
        for key, value in BUFFER_PREP_ELUTION.items():
            flexible_assert_equal(getattr(elution, key), value, msg=key)

        self.assertEqual(elution.unique_id, {'name': elution.name})

    def test_chemical_components(self):
        elution = self.elution
        self.assertEqual(
            [c.name for c in elution.chemical_components],
            [c.name for c in ELUTION_INTERNAL['components']]
        )

    def test_chemical_concentrations(self):
        elution = self.elution
        assert_unit_array_almost_equal(
            elution.chemical_concentrations,
            ELUTION_INTERNAL['chemical_concentrations'],
            atol=1e-1
        )
        self.assertEqual(elution.chemical_concentrations.units,
                         ELUTION_INTERNAL['chemical_concentrations'].units)

    def test_chemical_component_concentrations(self):
        elution = self.elution
        assert_unit_array_almost_equal(
            elution.chemical_component_concentrations,
            ELUTION_INTERNAL['chemical_component_concentrations'],
            atol=1e-1
        )
        self.assertEqual(
            elution.chemical_component_concentrations.units,
            ELUTION_INTERNAL['chemical_component_concentrations'].units
        )
