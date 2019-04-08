from unittest import TestCase

from kromatography.ui.tests.base_model_view_test_case import \
    BaseModelViewTestCase
from kromatography.model.solver import Solver


class TestSolverView(BaseModelViewTestCase, TestCase):
    """ Run all BaseModelViewTestCase tests for a Solver model.
    """

    def setUp(self):
        # Register all views
        BaseModelViewTestCase.setUp(self)

        # This could be the manual creation of an instance of the Solver
        testmodel = Solver()
        self.model = testmodel
