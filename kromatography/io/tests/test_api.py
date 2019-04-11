from unittest import TestCase
from os.path import isfile
import os

from kromatography.io.api import load_object, load_study_from_project_file, \
    save_study_to_project_file
from kromatography.model.study import Study
from kromatography.model.data_source import SimpleDataSource
from kromatography.utils.testing_utils import io_data_path
from kromatography.ui.tasks.kromatography_task import KromatographyTask
from kromatography.utils.assertion_utils import \
    assert_has_traits_almost_equal


class TestIoApiLoad(TestCase):

    def setUp(self):
        self.fname = io_data_path("std_project_serialv5.chrom")

    def test_load_project_no_ds(self):
        study = load_study_from_project_file(self.fname, with_user_data=False)
        self.assertIsInstance(study, Study)
        self.assertIsNone(study.datasource)

    def test_load_project_with_ds(self):
        study = load_study_from_project_file(self.fname)
        self.assertIsInstance(study, Study)
        self.assertIsInstance(study.datasource, SimpleDataSource)


class TestIoApiSave(TestCase):

    def setUp(self):
        self.fname = io_data_path("std_project_serialv5.chrom")
        self.save_target_file = "test.chrom"

        if isfile(self.save_target_file):
            os.remove(self.save_target_file)

    def tearDown(self):
        if isfile(self.save_target_file):
            os.remove(self.save_target_file)

    def test_save_project_no_ds(self):
        study = load_study_from_project_file(self.fname, with_user_data=False)
        save_study_to_project_file(self.save_target_file, study)
        self.assertTrue(isfile(self.save_target_file))
        task, _ = load_object(self.save_target_file)
        self.assertIsInstance(task, KromatographyTask)
        study2 = task.project.study
        assert_has_traits_almost_equal(study2, study)
