import os
from unittest import TestCase
from nose.tools import assert_is
from time import sleep
from copy import copy

from pyface.ui.qt4.util.gui_test_assistant import GuiTestAssistant
from pyface.i_about_dialog import IAboutDialog
from pyface.tasks.action.api import SGroup
from pyface.image_resource import ImageResource
from pyface.ui.qt4.splash_screen import SplashScreen

from app_common.pyface.monitored_actions import MonitoredAction

from kromatography.ui.tasks.kromatography_task import APP_FAMILY, APP_TITLE, \
    KromatographyTask
from kromatography.utils.testing_utils import io_data_path
from kromatography.utils.app_utils import get_preference_file
from kromatography.model.tests.sample_data_factories import make_sample_app

GUI_DURATION = 1000


# -----------------------------------------------------------------------------


class TestKromatographyAppProperties(TestCase):
    def test_icon(self):
        app = make_sample_app()
        self.assertIsInstance(app.icon, ImageResource)
        self.assertIsInstance(app.splash_screen, SplashScreen)
        self.assertIsInstance(app.about_dialog, IAboutDialog)
        app.exit()

    def test_create_app_rewrite_preference_file(self):
        before_prefs_file_stats = os.stat(get_preference_file())
        # Make sure some time passes
        sleep(1)
        app = make_sample_app()
        # Make sure preference file was modified by the creation of the app
        after_prefs_file_stats = os.stat(get_preference_file())
        self.assertNotAlmostEqual(before_prefs_file_stats.st_mtime,
                                  after_prefs_file_stats.st_mtime)
        app.exit()


# -----------------------------------------------------------------------------


class TestKromatographyAppRun(GuiTestAssistant, TestCase):

    def test_run_gui(self):
        """ Test of high level app launcher (no arguments)
        """
        self._start_and_stop_gui_app()

    def test_run_gui_with_project_file(self):
        """ test of high level app launcher with project input argument.
        """
        filename = io_data_path('test.chrom')
        study_filename = 'Chrom Example Data.xlsx'
        self._start_and_stop_gui_app(init_files=[filename], num_windows=1)
        expected = '{} {}: {} ({})'.format(
            APP_FAMILY, APP_TITLE, os.path.abspath(filename), study_filename
        )
        # Window title added by _start_and_stop_gui_app:
        self.assertEqual(self.window_title, expected)

    def test_run_gui_with_2_project_files(self):
        filename1 = io_data_path('std_project_serialv0.chrom')
        filename2 = io_data_path('std_project_serialv3.chrom')
        self._start_and_stop_gui_app(init_files=[filename1, filename2],
                                     num_windows=2)

    # Helper method -----------------------------------------------------------

    def _start_and_stop_gui_app(self, init_files=None, num_windows=0):
        self.app = make_sample_app(init_files)
        self.gui.invoke_after(GUI_DURATION,
                              self.assert_and_stop_app(num_windows))
        self.app.run()

    def assert_and_stop_app(self, num_windows=0):
        def _assert_and_stop():
            self.window_title = self.app.windows_created[0].title
            try:
                if num_windows:
                    self.assertEqual(len(self.app.windows_created),
                                     num_windows)
            finally:
                self.app.exit()
                self.gui.stop_event_loop()
        return _assert_and_stop


# -----------------------------------------------------------------------------


class TestKromatographyAppHelpWindows(GuiTestAssistant, TestCase):

    def setUp(self):
        super(TestKromatographyAppHelpWindows, self).setUp()
        self.app = make_sample_app()

    def tearDown(self):
        self.app.exit()
        super(TestKromatographyAppHelpWindows, self).tearDown()

    def test_open_about_dialog(self):
        self.gui.invoke_after(100, self.gui.stop_event_loop)
        self.app.open_about_dialog()

    def test_bug_report_group_actions(self):
        all_action_factories = [x.factory for x in self.app.extra_actions]
        self.assertIn(self.app.create_bug_report_group, all_action_factories)
        bug_report_group = self.app.create_bug_report_group()
        self.assertIsInstance(bug_report_group, SGroup)
        self.assertEqual(bug_report_group.name, "HelpGroup")
        self.assertEqual(len(bug_report_group.items), 2)
        self.assertIn("issue", bug_report_group.items[0].name)
        self.assertIn("feedback", bug_report_group.items[0].name)
        about_action_name = 'Info about {} {}'.format(APP_FAMILY, APP_TITLE)
        self.assertEqual(bug_report_group.items[1].name, about_action_name)

    def test_docs_group_actions(self):
        all_action_factories = [x.factory for x in self.app.extra_actions]
        self.assertIn(self.app.create_documentation_group,
                      all_action_factories)
        help_group = self.app.create_documentation_group()

        sample_file_action_name = 'Show sample input files...'
        self.assertEqual(help_group.items[0].name, sample_file_action_name)
        doc_action_name = "Open documentation..."
        self.assertEqual(help_group.items[1].name, doc_action_name)

    def test_open_bug_report_dialog(self):
        self.gui.invoke_after(100, self.gui.stop_event_loop)
        self.app.open_bug_report()


# -----------------------------------------------------------------------------


class TestKromatographyAppTaskCreation(TestCase, GuiTestAssistant):

    def setUp(self):
        GuiTestAssistant.setUp(self)
        self.app = make_sample_app()

        # Make a copy of the current recent_files and reset at tearDown so
        # opening new one will not be impacted by running the test suite.
        self.recent_files = copy(self.app.recent_files)
        self.app.recent_files = []

    def tearDown(self):
        self.app.exit()
        GuiTestAssistant.tearDown(self)

    def test_task_creation(self):
        self.assertEqual(len(self.app.windows_created), 1)
        assert_app_valid(self.app)

    def test_task_creation_with_study(self):
        app = self.app
        filename = 'ChromExampleDataV2.xlsx'
        window = app.build_study_from_file(io_data_path(filename),
                                           allow_gui=False)
        task = window.active_task
        self.assertEqual(len(app.windows_created), 1)
        self.assertIsInstance(task, KromatographyTask)
        self.assertEqual(len(app.windows_created), 1)
        assert_app_valid(app)

    def test_task_creation_with_project(self):
        app = self.app
        filename = io_data_path('test.chrom')
        task = app.open_project_from_file(filename)
        self.assertEqual(len(app.windows_created), 1)
        self.assertIsInstance(task, KromatographyTask)
        assert_app_valid(app)
        self.assertEqual(len(app.recent_files), 1)
        self.assertEqual(app.recent_files[0], filename)

    def test_2_task_creations_with_project_files(self):
        app = self.app
        filename = io_data_path('std_project_serialv4.chrom')
        filename2 = io_data_path('std_project_serialv5.chrom')
        task1 = app.open_project_from_file(filename)
        task2 = app.open_project_from_file(filename2)
        self.assertIsInstance(task1, KromatographyTask)
        self.assertIsInstance(task2, KromatographyTask)

        self.assertEqual(len(app.windows_created), 2)
        assert_app_valid(app)
        self.assertEqual(len(app.recent_files), 2)
        # Reverse order:
        self.assertEqual(app.recent_files, [filename2, filename])

    def test_2_task_creations_with_same_project_file(self):
        app = self.app
        filename = io_data_path('std_project_serialv3.chrom')
        task1 = app.open_project_from_file(filename)
        task2 = app.open_project_from_file(filename)
        self.assertIsInstance(task1, KromatographyTask)
        # Second task is None since project already open:
        self.assertIsNone(task2, KromatographyTask)
        self.assertEqual(len(app.windows_created), 1)
        assert_app_valid(app)
        # Duplicates ignored:
        self.assertEqual(len(self.app.recent_files), 1)
        self.assertEqual(self.app.recent_files[0], filename)


# -----------------------------------------------------------------------------


class TestKromatographyAppMenuAction(TestCase):
    def setUp(self):
        self.app = make_sample_app()

    def tearDown(self):
        self.app.exit()

    def test_action_type(self):
        # Check that action group creation method returns monitored actions
        for schema_addition in self.app.extra_actions:
            method = schema_addition.factory
            action_group = method()
            for action in action_group.items:
                self.assertIsInstance(action, MonitoredAction)


# Helper functions ------------------------------------------------------------


def assert_app_valid(app):
    # FIXME: app.tasks_created doesn't contain a real list of Tasks but
    # their repr instead. We should investigate.
    for window in app.windows_created:
        task = window.active_task
        assert_is(app.datasource, task.project.datasource)
        assert_is(app.datasource, task.project.study.datasource)
