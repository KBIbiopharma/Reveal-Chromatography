import os
import pandas as pd
from unittest import TestCase

from traitsui.api import ModelView

from app_common.apptools.testing_utils import temp_fname

from kromatography.model.tests.sample_data_factories import \
    make_sample_binding_model_optimizer, make_sample_brute_force_optimizer
from kromatography.ui.tests.base_model_view_test_case import \
    BaseModelViewTestCase
from kromatography.compute.brute_force_binding_model_optimizer_step import \
    BruteForceBindingModelOptimizerStep


class TestConstantBindingModelOptimizerStepView(BaseModelViewTestCase,
                                                TestCase):
    """ Tests for a constant brute force binding model optimizer step model.
    """

    def setUp(self):
        # Register all views
        BaseModelViewTestCase.setUp(self)

        # This could be the manual creation of an instance of the ChromData to
        # represent.
        self.model = make_sample_binding_model_optimizer(5).steps[0]
        # Add fake data to test displaying the DF:
        self.model.cost_data = pd.DataFrame({"Product1": [0., 0.1]},
                                            index=["Sim1", "Sim2"])

    def test_view_non_constant_step(self):
        self.model = make_sample_binding_model_optimizer(5).steps[1]
        self.assertIsInstance(self.model, BruteForceBindingModelOptimizerStep)
        model_view = self._get_model_view()
        self.assertIsInstance(model_view, ModelView)

    def test_export_data_event(self):
        fname_seed = "testfile_TestBindingModelOptimizerView.csv"
        with temp_fname(fname_seed) as fname:
            model_view = self._get_model_view()
            model_view.do_export_data(fname)
            self.assertIn(fname_seed, os.listdir(os.path.dirname(fname)))


class TestBindingModelOptimizerStepView(BaseModelViewTestCase, TestCase):
    """ Tests for a general brute force binding model optimizer step model.
    """

    def setUp(self):
        # Register all views
        BaseModelViewTestCase.setUp(self)

        # This could be the manual creation of an instance of the ChromData to
        # represent.
        self.model = make_sample_binding_model_optimizer(5).steps[1]
        # Add fake data to test displaying the DF:
        self.model.cost_data = pd.DataFrame({"Product1": [0., 0.1]},
                                            index=["Sim1", "Sim2"])


class TestBruteForceOptimizerStepView(BaseModelViewTestCase, TestCase):
    """ Tests for a brute force optimizer step model.
    """

    def setUp(self):
        # Register all views
        BaseModelViewTestCase.setUp(self)

        self.model = make_sample_brute_force_optimizer(num_values=3).steps[0]
        # Add fake data to test displaying the DF:
        self.model.cost_data = pd.DataFrame({"Product1": [0., 0.1]},
                                            index=["Sim1", "Sim2"])
