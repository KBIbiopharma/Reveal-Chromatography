from unittest import TestCase

from chaco.tools.api import LegendHighlighter

from kromatography.plotting.chromatogram_plot import ChromatogramPlot, \
    LOG_FAMILY_UV
from kromatography.model.tests.sample_data_factories import \
    make_sample_chrom_model, make_sample_model_calibration_plot
from app_common.chaco.constraints_plot_container import \
    ConstraintsPlotContainer


class TestChromatogramPlot(TestCase):
    def setUp(self):
        self.exp_name = 'Run_1'
        self.chrom_model = make_sample_chrom_model(exp_name=self.exp_name)
        self.chromatogram_plot = make_sample_model_calibration_plot()

    def test_empty_chromatogram_plot_creation(self):
        model_calibration_plot = ChromatogramPlot()
        self.assertIsNone(model_calibration_plot.container)

        model_calibration_plot.init()
        self.assertEqual(model_calibration_plot.plot_contexts, {})
        self.assertIsInstance(model_calibration_plot.container,
                              ConstraintsPlotContainer)

    def test_remove_log_family_from_chromatogram_plot(self):
        chromatogram_plot = self.chromatogram_plot
        # By default, the UV log family is shown
        self.assertEqual(chromatogram_plot.plot_contexts.keys(),
                         [LOG_FAMILY_UV])
        chromatogram_plot.remove_log_family(LOG_FAMILY_UV)
        self.assertEqual(chromatogram_plot.plot_contexts, {})

    def test_add_log_to_chromatogram_plot(self):
        chromatogram_plot = self.chromatogram_plot
        self.assertEqual(chromatogram_plot.plot_contexts.keys(),
                         [LOG_FAMILY_UV])

        uv_plot = chromatogram_plot.plot_contexts[LOG_FAMILY_UV]
        # There should be 1 renderer for the 1 experiment:
        self.assertEqual(len(uv_plot.plots), 1)
        self.assertEqual(len(chromatogram_plot._legend.labels), 1)

        collection = self.chrom_model.log_collections[self.exp_name]
        for name, log in collection.logs.items():
            chromatogram_plot.add_chrome_log("NEW NAME", log)

        # There should now be 2 renderer since the 1 experiment was added twice
        self.assertEqual(len(uv_plot.plots), 2)
        self.assertEqual(len(chromatogram_plot._legend.labels), 2)

    def test_add_log_twice_to_chromatogram_plot(self):
        chromatogram_plot = self.chromatogram_plot
        self.assertEqual(chromatogram_plot.plot_contexts.keys(),
                         [LOG_FAMILY_UV])

        uv_plot = chromatogram_plot.plot_contexts[LOG_FAMILY_UV]
        # There should be 1 renderer for the 1 experiment:
        self.assertEqual(len(uv_plot.plots), 1)
        self.assertEqual(len(chromatogram_plot._legend.labels), 1)

        collection = self.chrom_model.log_collections[self.exp_name]
        for name, log in collection.logs.items():
            chromatogram_plot.add_chrome_log(self.exp_name, log)

        # Still only 1 renderer and 1 entry in the legend because the plot was
        # already present
        self.assertEqual(len(uv_plot.plots), 1)
        self.assertEqual(len(chromatogram_plot._legend.labels), 1)

    def test_remove_log_from_chromatogram_plot(self):
        chromatogram_plot = self.chromatogram_plot
        self.assertEqual(chromatogram_plot.plot_contexts.keys(),
                         [LOG_FAMILY_UV])

        uv_plot = chromatogram_plot.plot_contexts[LOG_FAMILY_UV]
        # There should be 1 renderer for the 1 experiment:
        self.assertEqual(len(uv_plot.plots), 1)
        self.assertEqual(len(chromatogram_plot._legend.labels), 1)

        collection = self.chrom_model.log_collections[self.exp_name]
        for name, log in collection.logs.items():
            chromatogram_plot.remove_chrome_log(self.exp_name, log)

        self.assertEqual(len(uv_plot.plots), 0)
        self.assertEqual(len(chromatogram_plot._legend.labels), 0)

    def test_show_hide_legend(self):
        chromatogram_plot = self.chromatogram_plot
        uv_plot = chromatogram_plot.plot_contexts[LOG_FAMILY_UV]
        self.assertIs(chromatogram_plot._legend, uv_plot.legend)
        self.assertTrue(uv_plot.legend.visible)
        self.assertIsInstance(uv_plot.legend.tools[0], LegendHighlighter)

        chromatogram_plot.hide_legend()
        self.assertIs(chromatogram_plot._legend, uv_plot.legend)
        self.assertFalse(uv_plot.legend.visible)
        # Tool removed to avoid messing up mouse interaction:
        self.assertEqual(uv_plot.legend.tools, [])

        chromatogram_plot.show_legend()
        self.assertIs(chromatogram_plot._legend, uv_plot.legend)
        self.assertTrue(uv_plot.legend.visible)
        self.assertIsInstance(uv_plot.legend.tools[0], LegendHighlighter)

    def test_plot_tools(self):
        chromatogram_plot = self.chromatogram_plot
        uv_plot = chromatogram_plot.plot_contexts[LOG_FAMILY_UV]

        plot_tools = [tool.__class__.__name__ for tool in uv_plot.tools]
        expected = ['PanTool', 'DataInspectorTool']
        self.assertEqual(plot_tools, expected)
