""" Tests for the Resin class. """

import unittest

from kromatography.model.resin import Resin
from kromatography.model.tests.example_model_data import RESIN_DATA


class TestResin(unittest.TestCase):

    def setUp(self):
        self.resin = Resin(**RESIN_DATA)

    # -------------------------------------------------------------------------
    # Tests
    # -------------------------------------------------------------------------
    def test_invalid_construction(self):
        with self.assertRaises(ValueError):
            self.resin = Resin()

    def test_construction(self):
        resin = self.resin
        for key, value in RESIN_DATA.items():
            self.assertEqual(getattr(resin, key), value, msg=key)
        expected = {'type_id': resin.type_id, 'lot_id': resin.lot_id,
                    'resin_type': resin.resin_type, 'name': resin.name}
        self.assertEqual(resin.unique_id, expected)
