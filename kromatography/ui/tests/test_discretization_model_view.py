from unittest import TestCase

from kromatography.ui.tests.base_model_view_test_case import \
    BaseModelViewTestCase
from kromatography.model.discretization import Discretization


class TestDiscretizationView(BaseModelViewTestCase, TestCase):
    """ Run all BaseModelViewTestCase tests for a Discretization model.
    """

    def setUp(self):
        # Register all views
        BaseModelViewTestCase.setUp(self)

        # Create instance of Discretization
        testmodel = Discretization()
        self.model = testmodel
