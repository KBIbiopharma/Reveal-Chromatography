from unittest import TestCase

from traits.api import adapt
from traits.testing.unittest_tools import UnittestTools
from traitsui.api import ModelView

from kromatography.model.tests.sample_data_factories import \
    make_sample_simulation, make_sample_simulation2, make_sample_binding_model
from kromatography.ui.tests.base_model_view_test_case import \
    BaseModelViewTestCase


class TestSimulationView(BaseModelViewTestCase, TestCase, UnittestTools):
    """ Run all BaseModelViewTestCase tests for a Simulation group model.
    """

    def setUp(self):
        # Register all views
        BaseModelViewTestCase.setUp(self)

        # This could be the manual creation of an instance of the ChromData to
        # represent.
        self.model = make_sample_simulation()

    def test_simulation2(self):
        model = make_sample_simulation2()
        view = adapt(model, ModelView)
        ui = view.edit_traits()
        ui.dispose()

    def test_details_view(self):
        view = self._get_model_view()
        details = view._get_simulation_details()
        ui = details.edit_traits()
        ui.dispose()

    def test_view_sim_with_ph_binding_model(self):
        self.model.binding_model = make_sample_binding_model(
            ph_dependence=True
        )
        view = self._get_model_view()
        ui = view.edit_traits()
        ui.dispose()
