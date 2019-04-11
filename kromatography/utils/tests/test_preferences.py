from unittest import TestCase
from os.path import curdir, dirname, isfile, join
import os
import sys
from shutil import copy
import multiprocessing
from textwrap import dedent

from traits.testing.unittest_tools import UnittestTools

from app_common.traits.assertion_utils import assert_has_traits_almost_equal

from kromatography.utils.preferences import CUR_VERSION, reset_preferences, \
    RevealChromatographyPreferences
from kromatography.utils.app_utils import get_app_folder, get_preference_file,\
    get_preferences
from kromatography.solve.api import run_cadet_simulator
from kromatography.solve.cadet_executor import InvalidExecutorError
from kromatography.utils.testing_utils import io_data_path

NUM_CPU = multiprocessing.cpu_count()

HERE = dirname(curdir)

if sys.platform == "win32":
    CADET_EXT = ".exe"
else:
    CADET_EXT = ""


class TestPreferencesIO(TestCase):

    def setUp(self):
        self.default_prefs = RevealChromatographyPreferences()
        self.filepath = get_preference_file(fileloc=HERE)
        if isfile(self.filepath):
            os.remove(self.filepath)

    def tearDown(self):
        if isfile(self.filepath):
            os.remove(self.filepath)

    def test_write_read_current_format(self):
        self.default_prefs.to_preference_file(target_file=self.filepath)
        self.assertTrue(isfile(self.filepath))
        loaded = RevealChromatographyPreferences.from_preference_file(
            self.filepath
        )
        assert_has_traits_almost_equal(loaded, self.default_prefs)

    def test_read_format_1_default_vals(self):
        app_folder_prefix = get_app_folder() + os.path.sep
        version1_content = dedent("""
        app_preferences:
            app_height: 1000
            app_width: 1200
            console_logging_level: 30
            log_folder: {0}log
            python_script_folder: {0}python_scripts
            user_ds_folder: {0}user_datasource
        solver_preferences:
            auto_delete_solver_files_on_exit: true
            cadet_num_threads: 1
            executor: ProcessPoolExecutor
            executor_num_worker: {1}
            input_file_location: {0}cadet_input_files
        ui_preferences:
            remember_layout: false
        version: 1
        """.format(app_folder_prefix, NUM_CPU))
        with open(self.filepath, "w") as f:
            f.write(version1_content)

        loaded = RevealChromatographyPreferences.from_preference_file(
            self.filepath
        )
        assert_has_traits_almost_equal(loaded, self.default_prefs)

    def test_read_format_1_non_default_vals(self):
        app_folder_prefix = get_app_folder() + os.path.sep
        version1_content = dedent("""
        app_preferences:
            app_height: 800
            app_width: 1000
            console_logging_level: 30
            log_folder: {0}log
            python_script_folder: {0}python_scripts
            user_ds_folder: {0}user_datasource
        solver_preferences:
            auto_delete_solver_files_on_exit: true
            cadet_num_threads: 2
            executor: ProcessPoolExecutor
            executor_num_worker: {1}
            input_file_location: {0}cadet_input_files
        ui_preferences:
            remember_layout: false
        version: 1
        """.format(app_folder_prefix, NUM_CPU))
        with open(self.filepath, "w") as f:
            f.write(version1_content)

        loaded = RevealChromatographyPreferences.from_preference_file(
            self.filepath
        )
        modified_prefs = self.default_prefs
        # Modify the default prefs to match the choices made in text above:
        modified_prefs.ui_preferences.app_width = 1000
        modified_prefs.ui_preferences.app_height = 800
        modified_prefs.solver_preferences.cadet_num_threads = 2
        modified_prefs.dirty = False
        assert_has_traits_almost_equal(loaded, modified_prefs)

    def test_read_format_2_non_default_vals(self):
        app_folder_prefix = get_app_folder() + os.path.sep
        version2_content = """
        app_preferences:
            console_logging_level: 30
            log_folder: {0}log
            python_script_folder: {0}python_scripts
            user_ds_folder: {0}user_datasource
        optimizer_preferences:
            optimizer_step_chunk_size: 100
            max_in_memory_group_size: 50
        solver_preferences:
            auto_delete_solver_files_on_exit: true
            cadet_num_threads: 2
            executor_num_worker: {1}
            input_file_location: {0}cadet_input_files
            solver_binary_path: cadet-cs{2}
        ui_preferences:
            app_height: 800
            app_width: 1000
            auto_close_empty_windows_on_open: true
            confirm_on_window_close: true
            remember_layout: false
        version: 2
        """.format(app_folder_prefix, NUM_CPU, CADET_EXT)
        with open(self.filepath, "w") as f:
            f.write(version2_content)

        loaded = RevealChromatographyPreferences.from_preference_file(
            self.filepath
        )
        modified_prefs = self.default_prefs
        # Modify the default prefs to match the choices made in text above:
        modified_prefs.ui_preferences.app_width = 1000
        modified_prefs.ui_preferences.app_height = 800
        modified_prefs.solver_preferences.cadet_num_threads = 2
        modified_prefs.dirty = False
        assert_has_traits_almost_equal(loaded, modified_prefs)

    def test_change_cadet_executable(self):
        cadet_file = io_data_path("Chrom_Example_Run_1_cadet_simulation.h5")
        copy(cadet_file, "backup.h5")
        try:
            run_cadet_simulator(cadet_file)

            modified_prefs = self.default_prefs

            # Make sure changing the executable breaks the ability to run cadet
            current_executable = \
                modified_prefs.solver_preferences.solver_binary_path
            modified_prefs.solver_preferences.solver_binary_path = "BLAH"
            modified_prefs.to_preference_file()
            try:
                with self.assertRaises(InvalidExecutorError):
                    run_cadet_simulator(cadet_file)
            finally:
                modified_prefs.solver_preferences.solver_binary_path = \
                    current_executable
                modified_prefs.to_preference_file()
        finally:
            copy("backup.h5", cadet_file)

    def test_reset_preferences(self):
        reset_preferences(target_file=self.filepath)
        prefs = RevealChromatographyPreferences.from_preference_file(
            self.filepath
        )
        assert_has_traits_almost_equal(prefs, self.default_prefs)


class TestPreferencesAppUtils(TestCase):

    def test_get_default_preference_file(self):
        default_pref_file = get_preference_file()
        self.assertEqual(dirname(default_pref_file), get_app_folder())

    def test_get_default_preferences(self):
        prefs = get_preferences()
        self.assertIsInstance(prefs, RevealChromatographyPreferences)
        self.assertEqual(prefs.version, CUR_VERSION)

    def test_get_local_preferences(self):
        reset_preferences(target_file=join(HERE, "preferences.yaml"))
        prefs = get_preferences(fileloc=HERE)
        assert_has_traits_almost_equal(prefs,
                                       RevealChromatographyPreferences())


class TestPreferencesDirtyFlag(TestCase, UnittestTools):

    def setUp(self):
        self.default_prefs = RevealChromatographyPreferences()

    def test_make_group_dirty(self):
        self.assertFalse(self.default_prefs.app_preferences.dirty)
        with self.assertTraitChanges(self.default_prefs.app_preferences,
                                     "dirty"):
                self.default_prefs.app_preferences.console_logging_level = 20

        self.assertTrue(self.default_prefs.app_preferences.dirty)

    def test_make_prefs_dirty(self):
        self.assertFalse(self.default_prefs.dirty)
        with self.assertTraitChanges(self.default_prefs, "dirty"):
            self.default_prefs.app_preferences.dirty = True

        self.assertTrue(self.default_prefs.dirty)

    def test_prefs_group_clean(self):
        self.assertFalse(self.default_prefs.dirty)
        with self.assertTraitChanges(self.default_prefs, "dirty"):
                self.default_prefs.app_preferences.console_logging_level = 20

        self.assertTrue(self.default_prefs.dirty)
        self.default_prefs.dirty = False
        self.assertFalse(self.default_prefs.dirty)
        self.assertFalse(self.default_prefs.app_preferences.dirty)
