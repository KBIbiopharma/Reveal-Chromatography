from unittest import TestCase

from kromatography.model.tests.sample_data_factories import (
    make_sample_experiment
)
from kromatography.ui.tests.base_model_view_test_case import \
    BaseModelViewTestCase


class TestColumnView(BaseModelViewTestCase, TestCase):
    """ Run all BaseModelViewTestCase + special tests for a Column view.
    """

    def setUp(self):
        # This registers all views defined in kromatography/ui/adapters/api.py
        BaseModelViewTestCase.setUp(self)

        experiment = make_sample_experiment()
        self.model = experiment.column
