from unittest import TestCase

from app_common.apptools.testing_utils import temp_bringup_ui_for
from kromatography.ui.project_file_selector import ProjectFileSelector


class TestProjectFileSelector(TestCase):
    def test_bring_up(self):
        sel = ProjectFileSelector(path_list=["foo.chrom", "bar.chrom"])
        with temp_bringup_ui_for(sel):
            pass
