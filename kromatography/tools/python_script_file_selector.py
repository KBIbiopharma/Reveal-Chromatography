from os.path import dirname, join

from app_common.apptools.script_runner.python_script_file_selector import \
    PythonScriptFileSelector as BasePythonScriptFileSelector

import kromatography
from kromatography.utils.app_utils import get_python_script_folder


class PythonScriptFileSelector(BasePythonScriptFileSelector):
    def _sample_script_location_default(self):
        return join(dirname(kromatography.__file__), "data", "sample_scripts")

    def _default_location_default(self):
        return get_python_script_folder()
