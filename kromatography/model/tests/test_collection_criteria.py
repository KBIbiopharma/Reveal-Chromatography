""" Tests for the CollectionCriteria Class. """

import unittest

from kromatography.model.collection_criteria import CollectionCriteria
from kromatography.model.tests.example_model_data import (
    COLLECTION_CRITERIA_DATA
)


class TestCollectionCriteria(unittest.TestCase):

    def setUp(self):
        self.collection_criteria = CollectionCriteria(
            **COLLECTION_CRITERIA_DATA
        )

    # -------------------------------------------------------------------------
    # Tests
    # -------------------------------------------------------------------------
    def test_construction(self):
        criteria = self.collection_criteria
        for key, val in COLLECTION_CRITERIA_DATA.iteritems():
            self.assertEqual(getattr(criteria, key), val)
