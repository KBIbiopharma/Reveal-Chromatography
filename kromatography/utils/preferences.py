"""
Module to initialize and update application preferences.
"""
from __future__ import print_function
import logging
import sys
from os.path import join
import multiprocessing

from traits.api import Bool, Directory, File, Instance, Int, List, Property, \
    Range, Str

from app_common.apptools.preferences import BasePreferenceGroup, \
    BasePreferences
from app_common.traits.custom_trait_factories import PositiveInt
from app_common.std_lib.sys_utils import IS_LINUX, IS_OSX, IS_WINDOWS

from kromatography.utils.preference_utils import PREF_ALTERATION_FUNCS


# Name of the preference file
PREFERENCE_FILENAME = "preferences.yaml"
# Folder name to store application datasource files
DS_DIRNAME = "user_datasource"
# Folder name for application python scripts
PY_SCRIPT_DIRNAME = "python_scripts"
# Folder name for application solver input files
CADET_INPUT_DIRNAME = "cadet_input_files"
# Folder name for application log files
LOG_DIRNAME = "log"
# Latest version released:
CUR_VERSION = 4


def get_app_folder():
    """ Returns an absolute path on the current system where the current user
    should have write rights.

    Note: Tested on Windows 7, Windows 10 and OSX.
    """
    from kromatography.ui.branding import APP_FAMILY, APP_TITLE
    from app_common.apptools.app_config import base_get_app_folder

    return base_get_app_folder(APP_TITLE, app_family=APP_FAMILY)


class UIPreferenceGroup(BasePreferenceGroup):
    """ Storage for UI related preferences.
    """
    #: Default width of application's main window
    app_width = Int(1200)

    #: Default height of application's main window
    app_height = Int(1000)

    #: Should ask user confirmation everytime she/he closes a window?
    confirm_on_window_close = Bool(True)

    #: Automatically close empty windows when opening a new one?
    auto_close_empty_windows_on_open = Bool(True)

    #: Store the pane layout to file and remember at next launch
    # TODO: NOT IN USE!!
    remember_layout = Bool

    def _attrs_to_store_default(self):
        return ["remember_layout", "app_width", "app_height",
                "confirm_on_window_close", "auto_close_empty_windows_on_open"]


class AppPreferenceGroup(BasePreferenceGroup):
    """ Storage for Application related preferences.
    """
    #: Level of details in the console logging. DEBUG=10, INFO=20, WARNING=30
    console_logging_level = Int(30)

    #: Location for storing all log files
    log_folder = Directory

    #: Location for storing all user datasource files
    user_ds_folder = Directory

    #: Location for storing all python script files
    python_script_folder = Directory

    def _attrs_to_store_default(self):
        return ["console_logging_level", "log_folder", "user_ds_folder",
                "python_script_folder"]

    def _log_folder_default(self):
        return join(get_app_folder(), LOG_DIRNAME)

    def _python_script_folder_default(self):
        return join(get_app_folder(), PY_SCRIPT_DIRNAME)

    def _user_ds_folder_default(self):
        """ Returns the directory to create datasource files in. """
        return join(get_app_folder(), DS_DIRNAME)


class FilePreferenceGroup(BasePreferenceGroup):
    #: List of recent files loaded by the user
    recent_files = List(Str)

    #: Max number of recent files to remember
    max_recent_files = Int(20)

    #: Relative different in loaded mass beyond which warning is issued
    exp_importer_mass_threshold = Range(low=0., high=1., value=0.02)

    def _attrs_to_store_default(self):
        return ["recent_files", "max_recent_files",
                "exp_importer_mass_threshold"]


class OptimizerPreferenceGroup(BasePreferenceGroup):
    """ Storage for explorer and optimizer related preferences.
    """
    #: Max size of optimizer step groups
    # Increase to larger than number of CPUs for speed. Reduce to reduce memory
    # usage peaks during optimizations:
    optimizer_step_chunk_size = Int(100)

    def _attrs_to_store_default(self):
        return ["optimizer_step_chunk_size"]


class SolverPreferenceGroup(BasePreferenceGroup):
    """ Storage for solver related preferences.
    """
    #: Path (or name) to the solver executable to use
    solver_binary_path = File

    # Folder containing the solver input files
    input_file_location = Directory

    #: Number of max worker processes to run simulation grids on. 0=all CPUs.
    executor_num_worker = Int

    #: Clean up solver input files when exiting?
    auto_delete_solver_files_on_exit = Bool(True)

    #: CADET allows to run 1 simulation using multiple openMP threads
    cadet_num_threads = PositiveInt(1, exclude_low=True)

    #: Wrap solver execution with SLURM scheduling?
    use_slurm_scheduler = Bool

    #: Slurm scheduler batch run command
    slurm_binary = File("sbatch")

    #: SLURM Partition to run the solver on
    slurm_partition = Str

    #: Name of the SLURM jobs submitted when running the solver
    slurm_job_name = Str("slurm_chrom_solver")

    def _attrs_to_store_default(self):
        return ["input_file_location", "auto_delete_solver_files_on_exit",
                "executor_num_worker", "cadet_num_threads",
                "solver_binary_path", "use_slurm_scheduler", "slurm_partition",
                "slurm_job_name"]

    def _input_file_location_default(self):
        """ Returns the directory to create datasource files in.
        """
        return join(get_app_folder(), CADET_INPUT_DIRNAME)

    def _solver_binary_path_default(self):
        if IS_WINDOWS:
            return 'cadet-cs.exe'
        elif IS_OSX or IS_LINUX:
            return 'cadet-cs'
        else:
            msg = "Platform {} currently not supported.".format(sys.platform)
            raise NotImplementedError(msg)

    def _executor_num_worker_default(self):
        return multiprocessing.cpu_count()


PREFERENCE_CLASS_MAP = {
    "app_preferences": AppPreferenceGroup,
    "file_preferences": FilePreferenceGroup,
    "ui_preferences": UIPreferenceGroup,
    "solver_preferences": SolverPreferenceGroup,
    "optimizer_preferences": OptimizerPreferenceGroup
}


class RevealChromatographyPreferences(BasePreferences):
    """ Drive the loading and saving of preferences for Reveal app to/from file
    """
    app_preferences = Instance(AppPreferenceGroup, ())

    file_preferences = Instance(FilePreferenceGroup, ())

    ui_preferences = Instance(UIPreferenceGroup, ())

    solver_preferences = Instance(SolverPreferenceGroup, ())

    optimizer_preferences = Instance(OptimizerPreferenceGroup, ())

    dirty = Property(Bool, depends_on="app_preferences:dirty, "
                                      "file_preferences:dirty, "
                                      "ui_preferences:dirty, "
                                      "solver_preferences:dirty, "
                                      "optimizer_preferences:dirty")

    #: List of preference types to look for
    _preference_class_map = PREFERENCE_CLASS_MAP

    #: Dictionary of optional functions to apply to data before building the
    #: current version of the Preference object.
    _preference_alteration_funcs = PREF_ALTERATION_FUNCS

    def _version_default(self):
        return CUR_VERSION

    def _preference_filepath_default(self):
        return join(get_app_folder(), PREFERENCE_FILENAME)

    # Traits property getters/setters -----------------------------------------

    # FIXME: these 2 getter/setter methods are needed because the property is
    # overridden to specify what it depends on. Note sure why Traits requires
    # that...

    def _get_dirty(self):
        return super(RevealChromatographyPreferences, self)._get_dirty()

    def _set_dirty(self, value):
        super(RevealChromatographyPreferences, self)._set_dirty(value)


def reset_preferences(target_file=None):
    """ Reset preferences by overwriting preference file with current defaults.
    """
    msg = "Resetting all preferences to default values."
    print(msg)
    logger = logging.getLogger(__name__)
    logger.info(msg)
    prefs = RevealChromatographyPreferences()
    prefs.to_preference_file(target_file=target_file)


if __name__ == "__main__":
    reset_preferences()
