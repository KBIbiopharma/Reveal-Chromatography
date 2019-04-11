""" Base TestCase for the TestStudy classes."""

from kromatography.model.product import Product
from kromatography.model.tests.sample_data_factories import (
    make_sample_experiment
)
from kromatography.utils.app_utils import initialize_unit_parser

initialize_unit_parser()


class BaseStudyTestCase(object):

    def setUp(self):
        # Attributes that need to be overwritten in subclasses:
        self.study_class = None
        self.study = None
        self.constructor_data = {}

        experim1 = make_sample_experiment(name="Experim1")
        experim2 = make_sample_experiment(name="Experim2")
        experim3 = make_sample_experiment(name="Experim3")
        self.experims = [experim1, experim2, experim3]

    # -------------------------------------------------------------------------
    # Tests
    # -------------------------------------------------------------------------

    def test_failed_construction_empty_study(self):
        # A name is required
        with self.assertRaises(ValueError):
            self.study_class()

    def test_construction_no_experim(self):
        study = self.study
        for key, value in self.constructor_data.items():
            self.assertEqual(getattr(study, key), value, msg=key)

        self.assertEqual(set(study.unique_id.keys()),
                         {'name', 'uuid', 'type_id'})
        self.assertEqual(study.unique_id['name'], study.name)
        self.assertIn(study.unique_id['type_id'],
                      ['EXPERIMENTAL_STUDY', 'STUDY'])

    def test_add_1_experim(self):
        study = self.study
        experim1 = make_sample_experiment(name="Experim1")
        study.add_experiments(experim1)
        self.assertEqual(study.experiments[0], experim1)

    def test_add_experims(self):
        study = self.study
        study.add_experiments(self.experims)
        for i, exp in enumerate(self.experims):
            self.assertEqual(study.experiments[i], exp)

    def test_product(self):
        study = self.study
        self.assertIs(study.product, None)

        experim1 = make_sample_experiment(name="Experim1")
        study.add_experiments(experim1)
        self.assertIsInstance(study.product, Product)
