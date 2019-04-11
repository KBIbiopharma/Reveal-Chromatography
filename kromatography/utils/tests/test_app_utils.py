""" Tests for the utility functions in app_utils module.
"""
import os
from os.path import split
from unittest import TestCase

from scimath.units.api import unit_parser
from pyface.ui.qt4.util.gui_test_assistant import GuiTestAssistant
from pyface.api import information

from app_common.traits.assertion_utils import assert_has_traits_almost_equal
from app_common.std_lib.sys_utils import get_bin_folder

from kromatography.utils.app_utils import build_bug_report_content, \
    build_user_datasource_filepath, get_cadet_version, \
    get_user_ds_folder, initialize_unit_parser, launch_app_for_study, \
    load_default_user_datasource, save_user_datasource_to
from kromatography.model.data_source import SimpleDataSource
from kromatography.io.api import load_object
from kromatography.model.tests.sample_data_factories import make_sample_study

CURRENT_CADET_VERSION = "2.3.2"

CURRENT_CADET_HASH = '2288c67bf3b4a8efcd5d36542ec7543dad21fa28'

STARTUP_TIME_MS = 3000


class TestAppUtils(GuiTestAssistant, TestCase):
    def test_parse_absorption_units(self):
        # add custom units to the parser.
        initialize_unit_parser()

        # check we can parse based on the unit name
        u1 = unit_parser.parse_unit('absorption_unit', suppress_unknown=False)
        self.assertEqual(u1.label, 'absorption_unit')

        # check we can parse based on the unit label
        u2 = unit_parser.parse_unit('AU', suppress_unknown=False)
        self.assertEqual(u2.label, 'AU')

        # check the two units mean the same thing (except labels)
        self.assertEqual(u1.derivation, u2.derivation)
        self.assertEqual(u1.offset, u2.offset)
        self.assertEqual(u1.value, u2.value)

    def test_launch_app_for_study(self):
        # Make a study, and launch the app around it
        study = make_sample_study()
        self.gui.invoke_after(STARTUP_TIME_MS, self.gui.stop_event_loop)
        app = launch_app_for_study(study, splash_screen_duration=0.,
                                   confirm_on_window_close=False,
                                   auto_close_empty_windows_on_open=True)
        self.assertIn(study, app.initial_studies)
        app.stop()

    def test_build_dir(self):
        bin_dir = get_bin_folder()
        self.assertTrue(os.path.isdir(bin_dir))

    def test_get_cadet_version(self):
        version, build = get_cadet_version()
        self.assertEqual(version, CURRENT_CADET_VERSION)
        self.assertEqual(build, CURRENT_CADET_HASH)


class TestDatasourceStorage(TestCase):
    def test_build_user_datasource_filepath(self):
        """ Make sure the default datasource file location is writable.
        """
        filepath = build_user_datasource_filepath()
        try:
            open(filepath, "w").write("TEST")
        finally:
            os.remove(filepath)

    def test_load_default_user_datasource(self):
        ds, filename = load_default_user_datasource()
        self.assertIsInstance(ds, SimpleDataSource)
        self.assertIn("Prod000", ds.get_object_names_by_type("products"))
        self.assertIsInstance(filename, basestring)

    def test_save_ds_to_file_default_loc(self):
        ds = load_default_user_datasource()[0]
        filename = save_user_datasource_to(ds)
        try:
            self.assertEqual(split(filename)[0], get_user_ds_folder())
            ds2, filename2 = load_default_user_datasource()
            self.assertEqual(filename, filename2)
            assert_has_traits_almost_equal(ds, ds2)
        finally:
            os.remove(filename)

    def test_save_ds_to_custom_file(self):
        ds = load_default_user_datasource()[0]
        filename = save_user_datasource_to(ds, "test.chromds")
        self.assertEqual(filename, "test.chromds")
        reloaded_ds, _ = load_object("test.chromds")
        assert_has_traits_almost_equal(ds, reloaded_ds)


class TestBugReportDialog(GuiTestAssistant, TestCase):
    def test_open_dialog(self):
        self.gui.invoke_after(100, self.gui.stop_event_loop)
        information(None, build_bug_report_content())
