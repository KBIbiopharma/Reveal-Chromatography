from unittest import TestCase

from kromatography.model.tests.sample_data_factories import \
    make_sample_experiment
from kromatography.ui.tests.base_model_view_test_case import \
    BaseModelViewTestCase


class TestResinView(BaseModelViewTestCase, TestCase):
    """ Run all BaseModelViewTestCase tests for a Resin model.
    """

    def setUp(self):
        # Register all views
        BaseModelViewTestCase.setUp(self)

        # This could be the manual creation of an instance of the Resin togit
        # represent.
        experiment = make_sample_experiment()
        self.model = experiment.column.resin
