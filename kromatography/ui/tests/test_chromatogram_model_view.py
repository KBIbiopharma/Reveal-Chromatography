from unittest import TestCase
from traits.api import TraitError

from app_common.apptools.testing_utils import temp_bringup_ui_for

from kromatography.ui.chromatogram_model_view import ChromatogramModelView, \
    PlotColorEditor
from kromatography.model.tests.sample_data_factories import \
    make_sample_chrom_model, make_sample_model_calibration_plot
from kromatography.utils.string_definitions import LOG_FAMILY_UV


class TestChromatogramPlotView(TestCase):
    def setUp(self):
        self.exp_name = 'Run_1'
        self.chrom_model = make_sample_chrom_model(exp_name=self.exp_name)

    def test_open_close(self):
        view = ChromatogramModelView(chromatogram_model=self.chrom_model)
        with temp_bringup_ui_for(view):
            pass

    def test_all_uv_on_open(self):
        view = ChromatogramModelView(chromatogram_model=self.chrom_model,
                                     open_uv_on_open=True)
        with temp_bringup_ui_for(view):
            self.assertEqual(view.displayed_log_family_names, [LOG_FAMILY_UV])
            self.assertEqual(view.displayed_log_collection_names,
                             [self.exp_name])

    def test_no_uv_on_open(self):
        view = ChromatogramModelView(chromatogram_model=self.chrom_model,
                                     open_uv_on_open=False)
        with temp_bringup_ui_for(view):
            self.assertEqual(view.displayed_log_family_names, [])
            self.assertEqual(view.displayed_log_collection_names, [])

    def test_2_collections(self):
        # Model with 1 exp and 1 sim from it
        chrom_model = make_sample_chrom_model(exp_name=self.exp_name,
                                              include_sim=True)
        view = ChromatogramModelView(chromatogram_model=chrom_model,
                                     open_uv_on_open=True)
        with temp_bringup_ui_for(view):
            self.assertEqual(view.displayed_log_family_names, [LOG_FAMILY_UV])
            self.assertEqual(view.displayed_log_collection_names,
                             [self.exp_name, "Sim: "+self.exp_name])

    def test_connected_collections_have_same_color(self):
        # Model with 1 exp and 1 sim from it
        chrom_model = make_sample_chrom_model(exp_name=self.exp_name,
                                              include_sim=True)
        view = ChromatogramModelView(chromatogram_model=chrom_model,
                                     open_uv_on_open=True)
        with temp_bringup_ui_for(view):
            self.assertEqual(view.displayed_log_family_names, [LOG_FAMILY_UV])
            self.assertEqual(view.displayed_log_collection_names,
                             [self.exp_name, "Sim: "+self.exp_name])


class TestChromatogramPlot(TestCase):

    def test_range_index(self):
        family_names = ('P1', 'P2')
        chromatogram_plot = make_sample_model_calibration_plot(
            family_names=family_names
        )
        pc1 = chromatogram_plot.plot_contexts[family_names[0]]
        pc2 = chromatogram_plot.plot_contexts[family_names[1]]
        self.assertNotEqual(pc1, pc2)
        self.assertIs(pc1.index_range, pc2.index_range)


class TestChromatogramPlotViewChangeColor(TestCase):
    def setUp(self):
        self.exp_name = 'Run_1'
        self.chrom_model = make_sample_chrom_model(exp_name=self.exp_name)
        self.view = ChromatogramModelView(chromatogram_model=self.chrom_model)

    def test_change_plot_color_exp_plot(self):
        collection = self.chrom_model.log_collections['Run_1']

        # in initial state, color is blue:
        for log in collection.logs.values():
            props = log.renderer_properties
            self.assertEqual(props["color"], "blue")

        new_color = "red"
        self.view.apply_new_colors({'Run_1': new_color})
        # Setting the color changes the chrom model...
        for log in collection.logs.values():
            props = log.renderer_properties
            self.assertEqual(props["color"], new_color)

        # ... as well as all renderers for the experiment
        plot = self.view._chromatogram_plot
        for plot in plot.plot_contexts.values():
            for fam, renderer_list in plot.plots.items():
                for renderer in renderer_list:
                    self.assertEqual(renderer.color, new_color)

    def test_change_plot_colors_wrong_plot(self):
        with self.assertRaises(KeyError):
            self.view.apply_new_colors({"FOO": "red"})

    def test_change_plot_colors_wrong_color(self):
        with self.assertRaises(TraitError):
            self.view.apply_new_colors({"Run_1": "goobar"})


class TestChromatogramPlotColorEditor(TestCase):
    def setUp(self):
        self.exp_name = 'Run_1'
        self.chrom_model = make_sample_chrom_model(exp_name=self.exp_name)

    def test_open_close_empty_editor(self):
        editor = PlotColorEditor()
        with temp_bringup_ui_for(editor):
            pass

    def test_open_close_non_empty_editor(self):
        editor = PlotColorEditor(
            collection_list=self.chrom_model.log_collections
        )
        with temp_bringup_ui_for(editor):
            pass

    def test_connected_visibility(self):
        # Model with 1 exp and 1 sim from it
        chrom_model = make_sample_chrom_model(exp_name=self.exp_name,
                                              include_sim=True)
        editor = PlotColorEditor(collection_list=chrom_model.log_collections)
        # exp only should be visible:
        color_trait = editor.collection_map[self.exp_name]
        exp_idx = color_trait.split("_")[-1]
        visibility_trait = "plot_always_visible_{}".format(exp_idx)
        self.assertTrue(getattr(editor, visibility_trait))

        sim_idx = 1 if exp_idx == "0" else 0
        visibility_trait = "plot_always_visible_{}".format(sim_idx)
        self.assertFalse(getattr(editor, visibility_trait))

    def test_connected_change_color(self):
        # Model with 1 exp and 1 sim from it
        chrom_model = make_sample_chrom_model(exp_name=self.exp_name,
                                              include_sim=True)
        sim_name = "Sim: " + self.exp_name
        editor = PlotColorEditor(collection_list=chrom_model.log_collections)
        self.assertFalse(editor.disconnected_plots)
        color_trait = editor.collection_map[self.exp_name]
        editor.trait_set(**{color_trait: "red"})
        self.assertIn(self.exp_name, editor.modified_colors)
        self.assertEqual(editor.modified_colors[self.exp_name], "red")
        self.assertIn(sim_name, editor.modified_colors)
        self.assertEqual(editor.modified_colors[sim_name], "red")

    def test_disconnected_change_exp_color(self):
        # Model with 1 exp and 1 sim from it
        chrom_model = make_sample_chrom_model(exp_name=self.exp_name,
                                              include_sim=True)
        sim_name = "Sim: " + self.exp_name
        editor = PlotColorEditor(collection_list=chrom_model.log_collections,
                                 disconnected_plots=True)
        color_trait = editor.collection_map[self.exp_name]
        editor.trait_set(**{color_trait: "red"})
        self.assertIn(self.exp_name, editor.modified_colors)
        self.assertEqual(editor.modified_colors[self.exp_name], "red")
        self.assertNotIn(sim_name, editor.modified_colors)

    def test_disconnect_change_sim_color_reconnect(self):
        # Model with 1 exp and 1 sim from it
        chrom_model = make_sample_chrom_model(exp_name=self.exp_name,
                                              include_sim=True)
        sim_name = "Sim: " + self.exp_name
        editor = PlotColorEditor(
            collection_list=chrom_model.log_collections,
            disconnected_plots=True)
        sim_color_trait = editor.collection_map[sim_name]
        editor.trait_set(**{sim_color_trait: "red"})
        self.assertIn(sim_name, editor.modified_colors)
        self.assertEqual(editor.modified_colors[sim_name], "red")
        self.assertNotIn(self.exp_name, editor.modified_colors)
        exp_color_trait = editor.collection_map[self.exp_name]
        self.assertEqual(getattr(editor, exp_color_trait), "blue")

        # Reconnecting makes the simulation's color to be set back to the color
        # of its source experiment:
        editor.disconnected_plots = False
        self.assertEqual(editor.modified_colors[sim_name], "blue")
