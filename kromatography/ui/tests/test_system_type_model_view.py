from unittest import TestCase

from scimath.units.api import UnitArray, UnitScalar

from kromatography.model.tests.sample_data_factories import (
    make_sample_experiment
)
from kromatography.ui.tests.base_model_view_test_case import \
    BaseModelViewTestCase
from kromatography.utils.chromatography_units import ml_per_min


class TestSystemView(BaseModelViewTestCase, TestCase):
    """ Run all BaseModelViewTestCase tests and SystemView tests.
    """

    def setUp(self):
        # This registers all views defined in kromatography/ui/adapters/api.py
        BaseModelViewTestCase.setUp(self)

        experiment = make_sample_experiment()
        self.model = experiment.system.system_type

    def test_flow_range_view(self):
        model_view = self._get_model_view()

        flow_range = self.model.flow_range
        view_flow_range = UnitArray([
            model_view.system_type_flow_range_min.tolist(),
            model_view.system_type_flow_range_max.tolist()],
            units=model_view.system_type_flow_range_max.units
        )
        self.assertEqual(flow_range, view_flow_range)

    def test_set_flow_range(self):
        model_view = self._get_model_view()

        new_flow_range_min = UnitScalar(1, units=ml_per_min)
        new_flow_range_max = UnitScalar(2, units=ml_per_min)
        model_view.system_type_flow_range_max = new_flow_range_max
        model_view.system_type_flow_range_min = new_flow_range_min
        new_flow_range = UnitArray([1, 2], units=ml_per_min)
        self.assertEqual(self.model.flow_range, new_flow_range)
