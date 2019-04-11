
from unittest import TestCase
from numpy import arange
from os import listdir

from app_common.apptools.testing_utils import temp_fname

from kromatography.model.x_y_data import XYData


class TestXYData(TestCase):
    def test_create(self):
        XYData(name="test", x_data=arange(20), y_data=arange(20))

    def test_create_fail_when_missing_name(self):
        with self.assertRaises(ValueError):
            XYData(x_data=arange(20), y_data=arange(20))

    def test_plot_export(self):
        data = XYData(name="test", x_data=arange(20), y_data=arange(20),
                      x_metadata={"units": "min"}, y_metadata={"units": "AU"})
        filepath = "test.png"
        with temp_fname(filepath):
            data.mpl_show(filepath=filepath)
            self.assertIn(filepath, listdir("."))

    def test_plot_export_metadata_missing(self):
        data = XYData(name="test", x_data=arange(20), y_data=arange(20))
        filepath = "test.png"
        with temp_fname(filepath):
            data.mpl_show(filepath=filepath)
            self.assertIn(filepath, listdir("."))

    def test_plot_export_to_jpeg(self):
        data = XYData(name="test", x_data=arange(20), y_data=arange(20))
        filepath = "test.jpg"
        with temp_fname(filepath):
            data.mpl_show(filepath=filepath)
            self.assertIn(filepath, listdir("."))
