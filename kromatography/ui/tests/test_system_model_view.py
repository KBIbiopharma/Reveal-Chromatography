from unittest import TestCase

from kromatography.model.tests.sample_data_factories import (
    make_sample_experiment
)
from kromatography.ui.tests.base_model_view_test_case import \
    BaseModelViewTestCase


class TestSystemView(BaseModelViewTestCase, TestCase):
    """ Run all BaseModelViewTestCase tests and SystemView tests.
    """

    def setUp(self):
        # This registers all views defined in kromatography/ui/adapters/api.py
        BaseModelViewTestCase.setUp(self)

        experiment = make_sample_experiment()
        self.model = experiment.system
