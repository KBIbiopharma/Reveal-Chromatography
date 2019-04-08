from unittest import TestCase

from scimath.units.api import UnitArray, UnitScalar

from kromatography.model.column import ColumnType
from kromatography.model.tests.example_model_data import COLUMN_TYPE_DATA
from kromatography.ui.tests.base_model_view_test_case import \
    BaseModelViewTestCase


class TestColumnTypeView(BaseModelViewTestCase, TestCase):
    """ Run all BaseModelViewTestCase + special tests for a Column view.
    """

    def setUp(self):
        # This registers all views defined in kromatography/ui/adapters/api.py
        BaseModelViewTestCase.setUp(self)
        self.model = ColumnType(**COLUMN_TYPE_DATA)

    def test_bed_height_proxy(self):
        # Make a view. Equivalent to view = ColumnView(model=self.model)
        model_view = self._get_model_view()
        range_units = self.model.bed_height_range.units

        # Check that the view got the initial values from the model:
        self.assertEqual(model_view.column_type_bed_height_min,
                         UnitScalar(10, units=range_units))
        self.assertEqual(model_view.column_type_bed_height_max,
                         UnitScalar(30, units=range_units))

        # Set model min/max values
        # FIXME: This min_val of 20.0 is required to avoid breaking tests in
        # test_simulation_from_experiment_builder. Somehow, this test is
        # setting CP_001's bed_height_actual to min_val, and other code then
        # try to add CP_001 with a bed_height_actual of 20 in the datasource,
        # provoking a DS collision. The connection is unclear at this point.
        min_val = 20.0
        max_val = 21.22
        min_val_unitted = UnitScalar(min_val, units=range_units)
        max_val_unitted = UnitScalar(max_val, units=range_units)

        # Set the view and make sure the model is updated
        model_view.column_type_bed_height_min = min_val_unitted
        model_view.column_type_bed_height_max = max_val_unitted

        # Check that model's range is updated
        self.assertEqual(self.model.bed_height_range,
                         UnitArray([min_val, max_val], units=range_units))
