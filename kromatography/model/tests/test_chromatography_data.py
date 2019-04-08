""" Tests for the ChromatographyData class. """

import unittest

from kromatography.model.chromatography_data import ChromatographyData


class TestChromatographyData(unittest.TestCase):

    def setUp(self):
        self.data = ChromatographyData(
            name='dummy', type_id='Chromatography Data'
        )

    # -------------------------------------------------------------------------
    # Tests
    # -------------------------------------------------------------------------
    def test_invalid_construction(self):
        with self.assertRaises(ValueError):
            self.resin = ChromatographyData()

    def test_construction(self):
        data = self.data
        self.assertEqual(data.name, 'dummy')
        self.assertEqual(data.type_id, 'Chromatography Data')

        # by default, `_unique_keys` is `(type_id,)`. Check unique id returns
        # the correct value
        expected = {'name': 'dummy', 'type_id': 'Chromatography Data'}
        for key, val in expected.items():
            self.assertEqual(data.unique_id[key], val)

        self.assertEqual(set(data.unique_id.keys()),
                         {'name', "uuid", "type_id"})
