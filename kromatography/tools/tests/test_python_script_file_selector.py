from os.path import isdir
from os import listdir
from unittest import TestCase

from kromatography.tools.python_script_file_selector import \
    PythonScriptFileSelector


class TestPythonScriptFileSelector(TestCase):

    def setUp(self):
        self.selector = PythonScriptFileSelector()

    def test_sample_folder_contains_scripts(self):
        sample_loc = self.selector.sample_script_location
        self.assertTrue(isdir(sample_loc))
        content = [fname for fname in listdir(sample_loc)
                   if not fname.startswith("__") and fname.endswith(".py")]
        self.assertEqual(len(content), 9)
        self.assertIn("first_script.py", content)
        self.assertIn("second_script.py", content)
        self.assertIn("create_multiple_5point_grids.py", content)
