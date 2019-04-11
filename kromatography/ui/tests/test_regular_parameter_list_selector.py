from unittest import TestCase

from kromatography.ui.regular_parameter_list_selector import \
    RegularParameterListSelector, ParameterScanDescription
from kromatography.model.tests.sample_data_factories import \
    make_sample_simulation
from app_common.apptools.testing_utils import temp_bringup_ui_for


NUM_PARAMS = 68


class TestRegularParameterListSelector(TestCase):
    def setUp(self):
        self.source_param = ParameterScanDescription(
            name="binding_model.sma_nu[2]",
            low=4, high=6, num_values=10
        )
        self.sim = make_sample_simulation()

    def test_bring_up_with_parallel_params(self):
        selector = RegularParameterListSelector(center_sim=self.sim,
                                                allow_parallel_params=True)
        with temp_bringup_ui_for(selector):
            pass

    def test_bring_up_without_parallel_params(self):
        selector = RegularParameterListSelector(center_sim=self.sim,
                                                allow_parallel_params=False)
        with temp_bringup_ui_for(selector):
            pass

    def test_add_params(self):
        selector = RegularParameterListSelector(center_sim=self.sim,
                                                allow_parallel_params=True)
        selector.new_parameter_button = True
        self.assertEqual(len(selector.parameter_scans), 1)
        p = selector.parameter_scans[0]
        p.name = "binding_model.sma_nu[1]"
        self.assertAlmostEqual(p.center_value, 5.0)

        selector.new_parameter_button = True
        self.assertEqual(len(selector.parameter_scans), 2)
        selector.new_parameter_button = True
        selector.new_parameter_button = True
        self.assertEqual(len(selector.parameter_scans), 4)

    def test_add_param_fixed_num_values(self):
        selector = RegularParameterListSelector(center_sim=self.sim,
                                                allow_parallel_params=False,
                                                num_values_fixed=22)
        selector.new_parameter_button = True
        param = selector.parameter_scans[0]
        self.assertEqual(param.num_values, 22)

    def test_create(self):
        selector = RegularParameterListSelector(center_sim=self.sim,
                                                allow_parallel_params=True)
        self.assertEqual(len(selector.allowed_parameters), NUM_PARAMS)
