from unittest import TestCase
import logging
from os.path import abspath, dirname, join

from pyface.action.action_event import ActionEvent

from app_common.pyface.monitored_actions import MonitoredAction, \
    MonitoredTaskAction
from app_common.pyface.logging_utils import action_monitoring, get_log_file
from app_common.std_lib.filepath_utils import attempt_remove_file

from kromatography.utils.app_utils import get_log_folder, initialize_logging

HERE = dirname(__file__)


class TestMonitorAction(TestCase):
    def setUp(self):
        self.log_file = abspath(join(HERE, "temp.log"))
        initialize_logging(log_file=self.log_file)

    def tearDown(self):
        root_logger = logging.getLogger()
        del root_logger
        attempt_remove_file(self.log_file)

    def test_monitor_func_pass(self):
        def action1():
            pass

        action_name = "Do nothing action"
        with action_monitoring(action_name):
            action1()

        self.assert_do_nothing_action_monitored(action_name)

    def test_monitor_func_fail(self):
        msg = "EXPECTED FAILURE: PLEASE IGNORE."

        def action2():
            raise ValueError(msg)

        action_name = "Raise error action"
        with action_monitoring(action_name, allow_gui=False):
            action2()

        self.assert_raise_action_monitored(action_name, msg)

    def test_monitor_success_pyface_action(self):
        def do_nothing():
            pass

        action_name = "Do nothing action"
        action = MonitoredAction(name=action_name, on_perform=do_nothing)
        action.perform(ActionEvent())
        self.assert_do_nothing_action_monitored(action_name)

    def test_monitor_raise_pyface_action(self):
        msg = "EXPECTED FAILURE: PLEASE IGNORE."

        def raise_error():
            raise ValueError(msg)

        action_name = "Raise error action"
        action = MonitoredAction(name=action_name, on_perform=raise_error,
                                 allow_gui=False)
        action.perform(ActionEvent())
        self.assert_raise_action_monitored(action_name, msg)

    def test_monitor_success_pyface_task_action(self):
        def do_nothing():
            pass

        action_name = "Do nothing action"
        action = MonitoredTaskAction(name=action_name, on_perform=do_nothing)
        action.perform(ActionEvent())
        self.assert_do_nothing_action_monitored(action_name)

    def test_monitor_raise_pyface_task_action(self):
        msg = "EXPECTED FAILURE: PLEASE IGNORE."

        def raise_error():
            raise ValueError(msg)

        action_name = "Raise error action"
        action = MonitoredTaskAction(name=action_name, on_perform=raise_error,
                                     allow_gui=False)
        action.perform(ActionEvent())
        self.assert_raise_action_monitored(action_name, msg)

    # Utilities ---------------------------------------------------------------

    def assert_do_nothing_action_monitored(self, action_name):
        log_content = open(self.log_file).read()
        self.assertIn("DEBUG", log_content)
        self.assertIn(action_name, log_content)
        self.assertIn('requested', log_content)
        self.assertIn('performed successfully', log_content)

    def assert_raise_action_monitored(self, action_name, msg):
        log_content = open(self.log_file).read()
        self.assertIn(action_name, log_content)
        self.assertIn('requested', log_content)
        self.assertIn(msg, log_content)
        self.assertIn("ERROR", log_content)
        self.assertIn('failed!', log_content)
        self.assertIn("traceback", log_content)


class TestGetLogFile(TestCase):

    def test_get_log_file_when_no_file(self):
        root_logger = logging.getLogger()
        while root_logger.handlers:
            root_logger.handlers.pop(0)

        self.assert_log_file_not_found()

    def test_get_log_file(self):
        root_logger = logging.getLogger()
        while root_logger.handlers:
            root_logger.handlers.pop(0)

        log_file = abspath(join(HERE, "temp.log"))
        try:
            root_logger.addHandler(logging.FileHandler(log_file))
            found_log_file = get_log_file()
            self.assertEqual(found_log_file, log_file)
        finally:
            del root_logger
            attempt_remove_file(log_file)

    def test_setuplogging_default_has_file(self):
        initialize_logging()
        self.assert_log_file_found()

    def test_setuplogging_with_prefix(self):
        initialize_logging(prefix="TEMP")
        try:
            self.assert_log_file_found()
        finally:
            log_file = get_log_file()
            attempt_remove_file(log_file)

    def test_setuplogging_with_file(self):
        log_file = abspath(join(HERE, "temp.log"))
        initialize_logging(log_file=log_file)
        try:
            self.assert_log_file_found(expected_file=log_file)
        finally:
            attempt_remove_file(log_file)

    # Utilities ---------------------------------------------------------------

    def assert_log_file_not_found(self):
        found_log_file = get_log_file()
        folder = get_log_folder()
        self.assertFalse(found_log_file.startswith(folder))

    def assert_log_file_found(self, expected_file=None):
        found_log_file = get_log_file()
        if expected_file is None:
            folder = get_log_folder()
            self.assertTrue(found_log_file.startswith(folder))
        else:
            self.assertEqual(found_log_file, expected_file)
