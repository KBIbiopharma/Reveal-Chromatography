from unittest import TestCase
from numpy import arange
from numpy.testing import assert_array_almost_equal
from pandas.util.testing import assert_frame_equal

from chaco.api import CMapImagePlot, ColorBar, HPlotContainer, Plot, \
    ScatterPlot
from traits.testing.unittest_tools import UnittestTools

from app_common.apptools.testing_utils import \
    reraise_traits_notification_exceptions, temp_bringup_ui_for

from kromatography.ui.optimizer_cost_function_explorer import \
    OptimizerCostFunctionExplorer
from kromatography.model.tests.sample_data_factories import \
    make_sample_binding_model_optimizer, make_sample_brute_force_optimizer
from kromatography.compute.experiment_optimizer_step import ALL_COST_COL_NAME

NUM_VALUES = 5


class BaseExplorerTest(UnittestTools):
    """ Common assertion around the chaco plot of the explorer.
    """

    def test_change_weight_change(self):
        """ Make sure changing weights changes the optimizer cost_data.

        Another test tests that changing the cost data triggers an update of
        the plot data.
        """
        explorer = self.explorer_small
        all_weights = ["peak_time_weight", "peak_height_weight",
                       "peak_slope_weight"]
        for weight in all_weights:
            with self.assertTraitChanges(self.optimizer_small, "cost_data", 1):
                value = getattr(explorer, weight)
                kw = {weight: value+1}
                explorer.trait_set(**kw)

    # Utilities ---------------------------------------------------------------

    def assertValidPlotData(self, explorer):
        self.assertFalse(explorer.no_cost_data)
        # Force the re-computation of the filtered data in case UI didn't
        # trigger it
        plot_data = explorer.cost_plot_data

        # Make sure the cost data was successfully filtered:
        x_param = explorer.x_axis_param
        filtered_data = explorer.filtered_cost_data
        axis_params = [x_param, explorer.y_axis_param]
        for param in set(explorer.param_list) - set(axis_params):
            values_found = filtered_data[param].unique()
            self.assertEqual(len(values_found), 1)
            trait = explorer._param_name_to_trait_name(param)
            self.assertAlmostEqual(values_found[0], getattr(explorer, trait))

        # For the axis params, there is a sampling of each possible value:
        for param in axis_params:
            values_found = filtered_data[param].unique()
            self.assertEqual(len(values_found), NUM_VALUES)

        # Filtered data is sorted:
        assert_frame_equal(filtered_data,
                           filtered_data.sort_values(by=axis_params))

        # Cost data is updated:
        for param, data in plot_data.arrays.items():
            if param == 'cost_data_2d':
                # Pivoted data contains all costs in a 2D matrix:
                self.assertEqual(data.shape, (NUM_VALUES, NUM_VALUES))
                assert_array_almost_equal(data.transpose().flatten(),
                                          plot_data.arrays[ALL_COST_COL_NAME])
            else:
                assert_array_almost_equal(data, filtered_data[param])

    def assertValid1DPlot(self, explorer):
        self.assertIsInstance(explorer.plot1_2d_container, HPlotContainer)
        components = explorer.plot1_2d_container.components
        self.assertEqual(len(components), 1)
        self.assertIsInstance(components[0], Plot)
        plot = components[0]
        # there are 2 renderers, a line and a scatter
        self.assertEqual(len(plot.plots), 1)
        # renderer_name = explorer.x_axis_param + "line"
        # self.assertIsInstance(plot.plots[renderer_name][0], LinePlot)
        renderer_name = explorer.x_axis_param + "scatter"
        self.assertIsInstance(plot.plots[renderer_name][0], ScatterPlot)

    def assertValid2DPlot(self, explorer):
        self.assertIsInstance(explorer.plot1_2d_container, HPlotContainer)
        components = explorer.plot1_2d_container.components
        self.assertEqual(len(components), 2)
        self.assertIsInstance(components[0], Plot)
        self.assertIsInstance(components[1], ColorBar)
        image_plot = components[0]
        self.assertEqual(len(image_plot.plots), 1)
        img_renderer = image_plot.plots['img_cost'][0]
        self.assertIsInstance(img_renderer, CMapImagePlot)

        colorbar = components[1]
        self.assertIs(colorbar, explorer.colorbar)
        self.assertIs(colorbar.index_mapper.range, explorer.colorbar_range)
        self.assertIs(colorbar.color_mapper.range, explorer.colorbar_range)
        self.assertIs(img_renderer.color_mapper.range, explorer.colorbar_range)


class TestOptimizerCostFunctionExplorerUI(TestCase):

    # Bring up tests ----------------------------------------------------------

    def test_bringup_for_optim_with_1_param(self):
        _, explorer = make_sample_brute_force_optimizer_explorer(num_param=1)
        self.assert_can_bringup_ui(explorer)

    def test_bringup_for_optim_with_2_params(self):
        _, explorer = make_sample_brute_force_optimizer_explorer(num_param=2)
        # Shouldn't be able to edit weights because no sims stored:
        self.assertFalse(explorer.can_change_weights)
        self.assert_can_bringup_ui(explorer)

    def test_bringup_for_optim_with_3_params(self):
        _, explorer = make_sample_brute_force_optimizer_explorer(num_param=3)
        self.assert_can_bringup_ui(explorer)

    def test_bringup_for_optim_with_2_params_in_2d(self):
        optimizer = make_sample_brute_force_optimizer(num_params=2,
                                                      with_data=True)
        explorer = OptimizerCostFunctionExplorer(
            optimizer=optimizer, show_cost_data_nd="2D",
            x_axis_param="binding_model.sma_lambda",
            y_axis_param="column.resin.ligand_density",
        )
        self.assert_can_bringup_ui(explorer)

    def test_bringup_when_empty_cost_data(self):
        _, explorer = make_sample_brute_force_optimizer_explorer(
            num_param=2, with_data=False
        )
        # Should be able to change weights before optimizer is run:
        self.assertTrue(explorer.can_change_weights)
        self.assert_can_bringup_ui(explorer)
        self.assertTrue(explorer.no_cost_data)

    def test_bringup_for_empty_sma_optim(self):
        optimizer = make_sample_binding_model_optimizer(num_params=2)
        explorer = OptimizerCostFunctionExplorer(optimizer=optimizer)
        self.assert_can_bringup_ui(explorer)
        self.assertTrue(explorer.no_cost_data)

    # Utilities ---------------------------------------------------------------

    def assert_can_bringup_ui(self, explorer):
        with temp_bringup_ui_for(explorer):
            pass


class TestOptimizerCostFunctionExplorer1DPlots(TestCase, BaseExplorerTest):
    def setUp(self):
        self.optimizer, self.explorer = \
            make_sample_brute_force_optimizer_explorer(num_param=2)

        kw = dict(show_cost_data_nd="1D",
                  x_axis_param="binding_model.sma_lambda")
        self.optimizer3d, self.explorer3d = \
            make_sample_brute_force_optimizer_explorer(num_param=3,
                                                       with_data=True, **kw)
        # Make a small one that will be run
        self.optimizer_small, self.explorer_small = \
            make_sample_brute_force_optimizer_explorer(num_param=2,
                                                       num_values=1, run=True)

    def test_plot_content_1d(self):
        _, explorer = make_sample_brute_force_optimizer_explorer(num_param=1)
        self.assertValidPlotData(explorer)
        self.assertValid1DPlot(explorer)

    def test_plot_content_1d_with_1extra_param(self):
        self.assertValidPlotData(self.explorer)
        self.assertValid1DPlot(self.explorer)

    def test_plot_content_1d_with_2extra_param(self):
        self.assertValidPlotData(self.explorer3d)
        self.assertValid1DPlot(self.explorer3d)

    def test_1D_plot_updates_from_second_param_changed(self):
        explorer = self.explorer
        optimizer = self.optimizer
        explorer.x_axis_param = "binding_model.sma_lambda"
        lig_dens_min = optimizer.cost_data["column.resin.ligand_density"].min()
        lig_dens_max = optimizer.cost_data["column.resin.ligand_density"].max()
        ligand_density_trait_name = "column_resin_ligand_density_control"
        lig_density = getattr(explorer, ligand_density_trait_name)
        self.assertAlmostEqual(lig_density, lig_dens_min)
        filt_data_x_series = explorer.filtered_cost_data[
            "binding_model.sma_lambda"
        ]
        filt_data_y_series = explorer.filtered_cost_data[ALL_COST_COL_NAME]
        assert_array_almost_equal(filt_data_x_series.values, arange(5))
        expected = 5 * arange(5)
        assert_array_almost_equal(filt_data_y_series.values, expected)

        # Change ligand density
        setattr(explorer, ligand_density_trait_name, lig_dens_max)
        filt_data_x_series = explorer.filtered_cost_data[
            "binding_model.sma_lambda"
        ]
        assert_array_almost_equal(filt_data_x_series.values, arange(5))
        filt_data_y_series = explorer.filtered_cost_data[ALL_COST_COL_NAME]
        expected = 5 * arange(5) + 4
        assert_array_almost_equal(filt_data_y_series.values, expected)

    def test_change_to_2d_plot(self):
        explorer = self.explorer
        self.assertValid1DPlot(explorer)
        explorer.show_cost_data_nd = "2D"
        self.assertEqual(explorer.y_axis_param, 'column.resin.ligand_density')
        self.assertValid2DPlot(explorer)

    def test_change_cost_data(self):
        """ Changing cost data should trigger update of plot data.

        Mimics what happens when the weights of the cost function have changed.
        """
        explorer = self.explorer
        explorer.x_axis_param = "binding_model.sma_lambda"

        initial_plot_data_dict = self.explorer.cost_plot_data.arrays.copy()
        new_cost_data = self.optimizer.cost_data.copy()
        cols_to_change = [ALL_COST_COL_NAME,
                          'binding_model.sma_lambda',
                          'column.resin.ligand_density']
        shift = 2.0
        new_cost_data[cols_to_change] += shift
        with reraise_traits_notification_exceptions():
            self.optimizer.cost_data = new_cost_data

        new_plot_data = self.explorer.cost_plot_data.arrays.copy()
        for key, new_arr in new_plot_data.items():
            assert_array_almost_equal(new_arr,
                                      initial_plot_data_dict[key] + shift)


class TestOptimizerCostFunctionExplorer2DPlots(TestCase, BaseExplorerTest):
    def setUp(self):
        kw = dict(show_cost_data_nd="2D",
                  x_axis_param="binding_model.sma_lambda",
                  y_axis_param="column.resin.ligand_density")

        self.optimizer, self.explorer = \
            make_sample_brute_force_optimizer_explorer(num_param=2,
                                                       with_data=True, **kw)

        self.optimizer3d, self.explorer3d = \
            make_sample_brute_force_optimizer_explorer(num_param=3,
                                                       with_data=True, **kw)
        # Make a small one that will be run
        self.optimizer_small, self.explorer_small = \
            make_sample_brute_force_optimizer_explorer(num_param=2,
                                                       num_values=1, run=True,
                                                       **kw)

    def test_plot_content_2d(self):
        self.assertValidPlotData(self.explorer)
        self.assertValid2DPlot(self.explorer)

    def test_plot_content_3_param(self):
        self.assertValidPlotData(self.explorer3d)
        self.assertValid2DPlot(self.explorer3d)

    def test_change_axis_params(self):
        self.assertEqual(self.explorer3d.x_axis_param,
                         'binding_model.sma_lambda')
        self.assertEqual(self.explorer3d.y_axis_param,
                         'column.resin.ligand_density')
        # No need to have this parameter update more than once, but currently
        # implementation triggers 2 updates.
        with self.assertTraitChanges(self.explorer3d, "filtered_cost_data", 2):
            self.explorer3d.y_axis_param = "binding_model.sma_nu[1]"

    def test_change_non_axis_param(self):
        """ Change off-axis params update filtered data, and array plot data
        """
        with self.assertTraitChanges(self.explorer3d, "filtered_cost_data", 1):
            self.explorer3d.binding_model_sma_nu_1_control = 20

        with self.assertTraitChanges(self.explorer3d.cost_plot_data,
                                     "data_changed", 1):
            self.explorer3d.binding_model_sma_nu_1_control = 0.1

    def test_change_color_bar_max_percentile(self):
        self.assert_colorbar_range_updates()

    def test_change_cost_data_and_color_bar_max_percentile(self):
        """ Test that updating the cost data doesn't prevent the colorbar
        range from being controlled.
        """
        new_cost_data = self.optimizer.cost_data.copy()
        self.optimizer.cost_data = new_cost_data
        self.assert_colorbar_range_updates()

    def test_change_cost_data(self):
        """ Changing cost data should trigger update of plot data and colorbar
        range. This mimics what happens when the weights of the cost function
        have changed.
        """
        initial_plot_data_dict = self.explorer.cost_plot_data.arrays.copy()
        colorbar_range = self.explorer.colorbar.index_mapper.range
        initial_low = colorbar_range.low
        initial_high = colorbar_range.high

        new_cost_data = self.optimizer.cost_data.copy()
        cols_to_change = [ALL_COST_COL_NAME, 'binding_model.sma_lambda',
                          'column.resin.ligand_density']
        shift = 2
        new_cost_data[cols_to_change] += shift
        # Don't silence exception raised when listening to changes to cost_data
        with reraise_traits_notification_exceptions():
            self.optimizer.cost_data = new_cost_data

        new_plot_data = self.explorer.cost_plot_data.arrays.copy()
        for key, new_arr in new_plot_data.items():
            assert_array_almost_equal(new_arr,
                                      initial_plot_data_dict[key] + shift)

        colorbar_range = self.explorer.colorbar.index_mapper.range
        new_low = colorbar_range.low
        new_high = colorbar_range.high
        self.assertAlmostEqual(new_low, initial_low + shift)
        self.assertAlmostEqual(new_high, initial_high + shift)

    def test_plot_content_2d_no_segfault(self):
        """ Reproduce a segfault crash when drawing the 2d image plot on OSX
        with gcc.
        """
        optimizer = make_sample_brute_force_optimizer(num_params=2,
                                                      with_data=True)
        explorer = OptimizerCostFunctionExplorer(
            optimizer=optimizer, show_cost_data_nd="2D",
            x_axis_param="binding_model.sma_lambda",
            y_axis_param="column.resin.ligand_density",
        )
        plot = explorer.plot1_2d_container.components[0]
        renderer = plot.plots['img_cost'][0]
        # This causes a segfault on OSX when enable is compiled with gcc or
        # even just when the active compiler is gcc instead of clang.
        for attr in ["h_center", "right", "top", "v_center"]:
            print(getattr(renderer, attr))

    def test_change_to_1d_plot(self):
        explorer = self.explorer
        self.assertValid2DPlot(explorer)
        explorer.show_cost_data_nd = "1D"
        self.assertValid1DPlot(explorer)

    # Utilities ---------------------------------------------------------------

    def assert_colorbar_range_updates(self):
        # Real range
        max_cost = self.optimizer.cost_data[ALL_COST_COL_NAME].max()
        min_cost = self.optimizer.cost_data[ALL_COST_COL_NAME].min()

        # This shows the full range
        self.explorer.color_bar_max_percentile = 100
        self.assertAlmostEqual(self.explorer.colorbar.index_mapper.range.high,
                               max_cost)
        self.assertAlmostEqual(self.explorer.colorbar.index_mapper.range.low,
                               min_cost)

        # This shows the least amount possible of the range
        self.explorer.color_bar_max_percentile = 1
        self.assertGreater(self.explorer.colorbar.index_mapper.range.high,
                           min_cost)
        self.assertAlmostEqual(self.explorer.colorbar.index_mapper.range.low,
                               min_cost)

        # This shows none of the range (the ui doesn't allow this)
        self.explorer.color_bar_max_percentile = 0
        self.assertAlmostEqual(self.explorer.colorbar.index_mapper.range.high,
                               min_cost)
        self.assertAlmostEqual(self.explorer.colorbar.index_mapper.range.low,
                               min_cost)


# Utilities -------------------------------------------------------------------


def make_sample_brute_force_optimizer_explorer(num_param,
                                               num_values=NUM_VALUES,
                                               with_data=True, run=False,
                                               **kwargs):
    optimizer = make_sample_brute_force_optimizer(
        num_params=num_param, num_values=num_values, with_data=with_data
    )
    if run:
        from kromatography.model.factories.job_manager import \
            create_start_job_manager

        job_manager = create_start_job_manager(max_workers=2)
        try:
            optimizer.run(job_manager, wait=True)
        finally:
            job_manager.shutdown()

    explorer = OptimizerCostFunctionExplorer(optimizer=optimizer, **kwargs)
    return optimizer, explorer
