from unittest import TestCase
from pandas import DataFrame
from numpy import array, random
from itertools import product
from os import remove
from os.path import isfile

from app_common.std_lib.filepath_utils import string2filename

from kromatography.model.simulation_group import SIM_COL_NAME
from kromatography.plotting.mpl_sim_grid import plot_sim_group_performances


class TestMplPlotSimGroup(TestCase):
    def setUp(self):

        self.param1 = u'column.bed_height_actual'
        self.param2 = u'method.method_steps[0].volume'
        self.outputs = [
            u'pool_concentration (g/L)', u'step_yield (%)',
            u'pool_volume (CV)', u'purity: comp1 (%)', u'purity: comp2 (%)',
        ]
        num_vals = 5
        num_sim = num_vals ** 2
        sim_names = ["Sim{}".format(i) for i in range(num_sim)]
        vals1, vals2 = zip(*list(product(range(num_vals), range(num_vals))))
        vals1 = array(vals1, dtype="float")
        vals2 = array(vals2, dtype="float")
        fake_data = {SIM_COL_NAME: sim_names, self.param1: vals1,
                     self.param2: vals2}
        more_data = {output: random.randn(num_sim) + 50
                     for output in self.outputs}
        fake_data.update(more_data)
        self.fake_data_df = DataFrame(fake_data)

    def test_build_plots(self):
        plot_sim_group_performances(self.fake_data_df, self.param1,
                                    self.param2, show_plots=False,
                                    save_plots=False)

    def test_save_plots(self):
        for file_format in [".png", ".pdf"]:
            self.assert_plot_saved(file_format)

    # Utilities ---------------------------------------------------------------

    def assert_plot_saved(self, file_format):
        expected_files = self.get_expected_filenames(
            file_format=file_format)
        self.cleanup_files(expected_files)

        try:
            plot_sim_group_performances(self.fake_data_df, self.param1,
                                        self.param2, show_plots=False,
                                        save_plots=True,
                                        file_format=file_format)

            for fname in expected_files:
                self.assertTrue(isfile(fname))

        finally:
            self.cleanup_files(expected_files)

    def get_expected_filenames(self, file_format=".png"):
        expected_files = []

        for output in self.outputs:
            fname = "reveal_generated_plot_{}_against_{}_and_{}{}"
            fname = fname.format(output, self.param1, self.param2, file_format)
            fname = string2filename(fname)
            expected_files.append(fname)

        return expected_files

    def cleanup_files(self, filenames):
        for fname in filenames:
            if isfile(fname):
                remove(fname)
