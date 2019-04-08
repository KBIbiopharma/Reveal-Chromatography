from unittest import TestCase

from scimath.units.unit_scalar import UnitScalar

from app_common.apptools.testing_utils import temp_bringup_ui_for
from app_common.traits.assertion_utils import assert_values_almost_equal

from kromatography.model.method import Method
from kromatography.model.tests.example_model_data import METHOD_DATA
from kromatography.ui.tests.base_model_view_test_case import \
    BaseModelViewTestCase
from kromatography.ui.method_model_view import MethodModelView
from kromatography.model.method_step import MethodStep
from kromatography.model.data_source import InStudyDataSource
from kromatography.model.buffer import Buffer
from kromatography.utils.chromatography_units import column_volumes, cm_per_hr


class TestMethodModelView(BaseModelViewTestCase, TestCase):
    """ Run all MethodModelView tests for Method view.
    """

    def setUp(self):
        # Register all views
        BaseModelViewTestCase.setUp(self)

        # Build a model you want to visualize:
        testmethod = Method(**METHOD_DATA)
        self.model = testmethod

        empty_step_method_data = METHOD_DATA.copy()
        empty_step_method_data["method_steps"] = []
        self.empty_step_method = Method(**empty_step_method_data)
        self.initialize_datasource()

    def test_bringup_method_without_collection_criteria(self):
        method = self.model
        method.collection_criteria = None
        model_view = MethodModelView(model=method)
        with temp_bringup_ui_for(model_view):
            pass

    def initialize_datasource(self):
        self.solutions = []
        for step in self.model.method_steps:
            self.solutions += step.solutions
        self.datasource = InStudyDataSource()
        for sol in self.solutions:
            if isinstance(sol, Buffer):
                self.datasource.set_object_of_type("buffers", sol)
            else:
                self.datasource.set_object_of_type("loads", sol)

    def test_known_solutions(self):
        view = MethodModelView(model=self.empty_step_method,
                               datasource=self.datasource)
        expected = [sol.name for sol in self.solutions]
        self.assertEqual(set(view._known_solution_names), set(expected))

    def test_collection_start_num_proxy(self):
        # tests both setting and getting
        view = MethodModelView(model=self.empty_step_method,
                               datasource=self.datasource)
        # getting
        proxyvar = view._collection_step_num_off1
        realvar = view.model.collection_step_number
        self.assertEqual(proxyvar, 4)
        self.assertEqual(realvar, 3)
        # setting
        view._collection_step_num_off1 = 3
        proxyvar = view._collection_step_num_off1
        realvar = view.model.collection_step_number
        self.assertEqual(proxyvar, 3)
        self.assertEqual(realvar, 2)

    def test_solution_name_update(self):
        # The view is needed here to add listeners on the model's method_steps
        view = MethodModelView(model=self.empty_step_method,  # noqa
                               datasource=self.datasource)
        # Test add step
        sol = self.solutions[0]
        sol1 = self.solutions[2]
        step = MethodStep(name="new step0")
        self.empty_step_method.method_steps.append(step)

        # Fake setting the solution name in the view and make sure solutions
        # attribute updates
        step._solutions0_name = sol.name
        assert_values_almost_equal(step.solutions, [sol])

        step._solutions1_name = sol1.name
        assert_values_almost_equal(step.solutions, [sol, sol1])

    def test_view_model_with_no_solution_step_and_no_ds(self):
        # This situation can happen for now since the central pane views are
        # not being passed a datasource. Remove test once datasource passed to
        # central pane views.
        data = {
            'step_type': 'Gradient Elution',
            'name': 'Gradient Elution',
            'flow_rate': UnitScalar(100.0, units=cm_per_hr),
            'volume': UnitScalar(8.4, units=column_volumes)
        }
        no_sol_step = MethodStep(**data)
        self.model.method_steps.append(no_sol_step)
        view = MethodModelView(model=self.model)
        ui = view.edit_traits()
        ui.dispose()
