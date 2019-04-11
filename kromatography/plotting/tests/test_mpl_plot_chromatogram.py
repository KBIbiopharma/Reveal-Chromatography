from unittest import TestCase

from kromatography.plotting.mpl_plot_chromatogram import build_data, plot_data
from kromatography.utils.testing_utils import \
    load_default_experiment_simulation


class TestMPLChromatogram(TestCase):

    def test_mpl_chromatogram(self):
        """ Test loading an experiment and the corresponding simulation and
        plotting them in a MCP style, using MPL.
        """
        expt, sim = load_default_experiment_simulation()
        data = build_data(expt, sim)
        plot_data(data)
