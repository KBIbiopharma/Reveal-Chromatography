from unittest import TestCase
import os
from os.path import dirname, isfile, join
from shutil import copy2

from kromatography.utils.testing_utils import io_data_path
from kromatography.io.task import load_project, load_object, save_project
from kromatography.ui.tasks.kromatography_task import KromatographyTask, \
    KROM_EXTENSION
from kromatography.model.simulation import Simulation
from kromatography.io.api import save_object
from app_common.traits.assertion_utils import assert_has_traits_almost_equal

HERE = dirname(__file__)


class TestLoadProject(TestCase):
    """ Use the project/task loading/saving API and test its management of the
    project_filepath.
    """
    def setUp(self):
        self.filepath = io_data_path("std_project_serialv5.chrom")
        self.filepath_temp = join(HERE, "temp.chrom")
        self.filepath_wrong_ext = join(HERE, "temp.temp")

    def tearDown(self):
        if isfile(self.filepath_temp):
            os.remove(self.filepath_temp)

    def test_load_task(self):
        task, legacy = load_project(self.filepath)
        self.assertIsInstance(task, KromatographyTask)
        self.assertEqual(task.project_filepath, self.filepath)
        self.assertTrue(legacy)

    def test_copy_load_task(self):
        # Simulate a copy of a project between 2 users:
        copy2(self.filepath, self.filepath_temp)
        task, legacy = load_project(self.filepath_temp)
        self.assertIsInstance(task, KromatographyTask)
        self.assertTrue(legacy)

        # Make sure that loading the new file leads to a task that has updated
        # its project_filepath attribute
        self.assertEqual(task.project_filepath, self.filepath_temp)

    def test_save_task_to_new_file(self):
        task, legacy = load_project(self.filepath)
        self.assertTrue(legacy)

        save_project(self.filepath_temp, task)

        # Test that the resulting file contains the new file since load_object
        # doesn't modify the object it loads:
        task_again, legacy = load_object(self.filepath_temp)
        self.assertIsInstance(task_again, KromatographyTask)
        self.assertEqual(task_again.project_filepath, self.filepath_temp)
        self.assertFalse(legacy)

    def test_save_task_to_new_file_wrong_ext(self):
        """ If trying to save to wrong file extension, it's appended.
        """
        backup_filepath = self.filepath_wrong_ext + KROM_EXTENSION
        if isfile(backup_filepath):
            os.remove(backup_filepath)

        self.assertFalse(isfile(backup_filepath))

        task, _ = load_project(self.filepath)
        save_project(self.filepath_wrong_ext, task)
        self.assertFalse(isfile(self.filepath_wrong_ext))
        self.assertTrue(isfile(backup_filepath))

    def test_load_wrong_obj_type(self):
        obj = Simulation(name="dslkjf")
        save_object(self.filepath_temp, obj)
        task, legacy = load_project(self.filepath_temp)
        self.assertFalse(legacy)
        assert_has_traits_almost_equal(task, obj)
