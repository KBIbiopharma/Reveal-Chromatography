from traits.testing.unittest_tools import unittest
from traits.testing.unittest_tools import UnittestTools

from kromatography.plotting.animation_plot import (
    _build_animation_data_from_sim, AnimationPlot, EPS
)
from kromatography.utils.testing_utils import \
    load_default_experiment_simulation


class TestAnimationPlot(unittest.TestCase, UnittestTools):

    @classmethod
    def setUpClass(cls):
        _, cls.sim = load_default_experiment_simulation()

    def setUp(self):
        prod_comps = self.sim.product.product_component_names
        self.prod_comps = prod_comps
        all_data = {prod_comps[i]: _build_animation_data_from_sim(self.sim, i)
                    for i in range(len(prod_comps))}
        self.plot = AnimationPlot(all_data=all_data)

    def test_data_clipped(self):
        # Make sure all data below 0, and even below EPS has been clipped out
        # so that Chaco doesn't fail to plot
        for arr_name in self.plot.plot_data.arrays.keys():
            data = self.plot.plot_data.arrays[arr_name]
            self.assertFalse((data < EPS).any())

    def test_time_slice_changed_changes_data(self):
        # Changing the time slice should change the plot_data, but the colorbar
        # should have the same range.
        orig_array = self.plot.plot_data.arrays['z_column_liquid']
        self.plot.time_slice += 200
        new_array = self.plot.plot_data.arrays['z_column_liquid']
        self.assertFalse((orig_array == new_array).all())

    def test_time_slice_changed_doesnt_changes_colorbar_range(self):
        liq_colbar = self.plot.plot.components[1]
        init_liq_colbar_high = liq_colbar.value_mapper.range.high
        bound_colbar = self.plot.plot.components[3]
        init_bound_colbar_high = bound_colbar.value_mapper.range.high

        self.plot.time_slice += 200

        liq_colbar_high = liq_colbar.value_mapper.range.high
        self.assertEqual(init_liq_colbar_high, liq_colbar_high)
        bound_colbar_high = bound_colbar.value_mapper.range.high
        self.assertEqual(init_bound_colbar_high, bound_colbar_high)

    def test_prod_comp_changed_trigger_new_plot(self):
        with self.assertTraitChanges(self.plot, 'plot', count=1):
            self.plot.product_component = self.prod_comps[1]

    def test_prod_comp_changed_trigger_new_colorbars(self):
        init_liq_colorbar = self.plot.plot.components[1]
        init_bnd_colorbar = self.plot.plot.components[3]

        self.plot.product_component = self.prod_comps[1]

        liq_colorbar = self.plot.plot.components[1]
        bnd_colorbar = self.plot.plot.components[3]

        # Also colorbar are regenerated
        self.assertIsNot(liq_colorbar, init_liq_colorbar)
        self.assertIsNot(bnd_colorbar, init_bnd_colorbar)

    def test_column_plot_x_axis(self):
        col_plot = self.plot.plot.components[0]
        self.assertEqual(col_plot.x_axis.title, 'Column X Position (cm)')
        x_axis_high = col_plot.x_axis.mapper.range.high
        col_radius = float(self.sim.column.column_type.diameter/2.)
        self.assertAlmostEqual(x_axis_high, col_radius)
