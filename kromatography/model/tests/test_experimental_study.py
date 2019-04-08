""" Tests for the Experimental Study class."""

import unittest

from kromatography.model.tests.base_study_test_case import BaseStudyTestCase
from kromatography.model.tests.example_model_data import EXPERIMENTAL_STUDY_DATA  # noqa
from kromatography.model.tests.sample_data_factories import \
    make_sample_experimental_study
from kromatography.model.experimental_study import ExperimentalStudy


class TestExperimentalStudy(unittest.TestCase, BaseStudyTestCase):

    def setUp(self):
        BaseStudyTestCase.setUp(self)
        self.study_class = ExperimentalStudy
        self.study = make_sample_experimental_study()
        self.constructor_data = EXPERIMENTAL_STUDY_DATA
