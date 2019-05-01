from __future__ import print_function
import getpass
import argparse
import logging
import os
from os.path import abspath, basename, dirname, isabs, isdir, isfile, join
import time
from subprocess import PIPE, Popen
from re import search

from app_common.std_lib.filepath_utils import attempt_empty_folder
from app_common.std_lib.sys_utils import IS_LINUX, IS_OSX, IS_WINDOWS  # noqa

from kromatography.ui.branding import APP_FAMILY, APP_TITLE, \
    BUG_REPORT_CONTENT_TEMPLATE, SUPPORT_EMAIL_ADDRESS
from kromatography import __build__, __version__
from .preferences import get_app_folder

# Spec to building the path to a serialized datasource
DS_PREFIX = "user_datasource"

# File extension for the user data source files
DS_EXT = ".chromds"

# Folder name for the updater tool
UPDATER_DIRNAME = "update"


def get_cadet_version(cadet_binary=None):
    """ Collect the version of git hash for the cadet-cs currently set in
    preferences.
    """
    if cadet_binary is None:
        preferences = get_preferences()
        cadet_binary = preferences.solver_preferences.solver_binary_path

    p = Popen([cadet_binary], stdout=PIPE, stderr=PIPE)
    out, err = p.communicate()
    patt = "version (\d\.\d\.\d).+commit (.+)"
    match = search(patt, out)
    if match:
        version, build = match.groups()
        return version.strip(), build.strip()
    else:
        return "", ""


def collect_user_name():
    """ Returns the username as provided by the OS. Returns a constant if it
    fails.
    """
    try:
        uname = getpass.getuser()
    except Exception as e:
        logger = logging.getLogger(__name__)
        msg = "Failed to collect the user name: error was {}.".format(e)
        logger.warning(msg)
        uname = "Unknown user"

    return uname


def initialize_unit_parser():
    """ Add custom units defined in this package to the unit parser.
    """
    import kromatography.utils.chromatography_units as chr_units
    from scimath.units.api import unit_parser

    # add all custom units
    unit_parser.parser.extend(chr_units)


def get_minimal_parser():
    """ Returns a minimal ArgumentParser instance for a generic script.
    """
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        conflict_handler='resolve'
    )
    parser.add_argument(
        '-o', '--output-dir', default='./',
        help='The name of directory to save the outputs of the script.',
    )
    parser.add_argument('-v', '--verbose', action='store_true',
                        help='Increase logging output.')
    parser.add_argument('--version', action='store_true',
                        help='Print the program version and exit.')
    parser.add_argument('-d', '--debug', action='store_true',
                        help='Shorten splash screen duration and increase '
                             'logging output.')
    log_group = parser.add_mutually_exclusive_group()
    log_group.add_argument('--log-dir', default='log',
                           help='Write the log files in DIR.')
    log_group.add_argument('--log',
                           help='Use FILENAME for log file.')
    return parser


def initialize_logging(prefix="krom_app", **kwargs):
    """ Set up logging for an analysis script, with a console handler and
    optionally a file handler.

    Set :arg:`verbose` to `True` to get DEBUG level logging calls. Pass a
    :arg:`prefix` string to create a log file in addition to the console
    logging. For more documentation on optional arguments, see
    :func:`app_common.logging.base_initialize_logging`
    """
    from app_common.std_lib.logging_utils import initialize_logging as \
        base_initialize_logging

    # Location of the log file:
    log_dir = get_log_folder()
    if not isabs(log_dir):
        app_folder = get_app_folder()
        log_dir = join(app_folder, log_dir)

    return base_initialize_logging(log_dir=log_dir, prefix=prefix, **kwargs)


def get_executor_folder():
    """ Scratch folder for solver executor temp files (like SLURM files).
    """
    return join(get_app_folder(), "executor_temp_files")


def get_preferences(filename=None, fileloc=None):
    """ Load from file and return the current Reveal preference object.
    """
    from .preferences import RevealChromatographyPreferences

    filepath = get_preference_file(filename=filename, fileloc=fileloc)
    if isfile(filepath):
        try:
            prefs = RevealChromatographyPreferences.from_preference_file(
                filepath)
        except Exception as e:
            from pyface.api import error
            logger = logging.getLogger(__name__)
            msg = "Failed to load preference file {}. Error was {}. Please " \
                  "report this issue, and please provide the log file."
            msg = msg.format(filepath, e)
            try:
                content = open(filepath).read()
                details = "Content of the preference file was:\n{}".format(
                    content)
            except Exception as e:
                details = "Unable to load the content of the preference file:"\
                          " error was {}".format(e)
            logger.error(msg+details)
            error(None, msg)
            prefs = RevealChromatographyPreferences()
    else:
        prefs = RevealChromatographyPreferences()

    prefs.dirty = False
    return prefs


def get_preference_file(filename=None, fileloc=None):
    """ Returns the path to the preference file, optionally overriding its name
    or location.
    """
    from .preferences import PREFERENCE_FILENAME
    if filename is None:
        filename = PREFERENCE_FILENAME

    if fileloc is None:
        fileloc = get_app_folder()

    filepath = join(fileloc, filename)
    return filepath


def reinitialize_preference_file():
    """ Make sure the default preference file is created/updated.
    """
    prefs = get_preferences()
    prefs.to_preference_file()


def get_log_folder():
    """ Returns the directory to create log files in.
    """
    preferences = get_preferences()
    return preferences.app_preferences.log_folder


def get_user_ds_folder():
    """ Returns the directory to create datasource files in.
    """
    preferences = get_preferences()
    return preferences.app_preferences.user_ds_folder


def get_python_script_folder():
    """ Returns the directory to create python script files in.
    """
    preferences = get_preferences()
    return preferences.app_preferences.python_script_folder


def get_cadet_input_folder():
    """ Returns the directory to create CADET input files in.
    """
    preferences = get_preferences()
    return preferences.solver_preferences.input_file_location


def get_updater_folder():
    """ Returns the directory to store the updater files.
    """
    return join(get_app_folder(), UPDATER_DIRNAME)


def initialize_updater_folder():
    """ Create the directory for updater files if it doesn't already exists.
    """
    folder = get_updater_folder()
    if not isdir(folder):
        os.makedirs(folder)


def initialize_cadet_input_folder():
    """ Create the cadet input folder if it doesn't already exists.

    Returns
    -------
    bool
        Returns True if the folder already exists or was successfully created.
    """
    from pyface.api import error
    from kromatography.tools.preferences_view import \
        RevealChromatographyPreferenceView

    input_file_folder = get_cadet_input_folder()
    if isdir(input_file_folder):
        return True
    else:
        try:
            os.makedirs(input_file_folder)
            return True
        except OSError as e:
            logger = logging.getLogger(__name__)
            msg = "Failed to create the CADET input folder {}. Drive missing?"\
                  " (Error was {}). Please review preference settings, save " \
                  "and relaunch."
            msg = msg.format(input_file_folder, e)
            logger.error(msg)
            error(None, msg)
            prefs = get_preferences()
            view = RevealChromatographyPreferenceView(model=prefs,
                                                      standalone=True)
            view.configure_traits()
            return False


def initialize_executor_temp_folder():
    executor_folder = get_executor_folder()
    if not isdir(executor_folder):
        os.makedirs(executor_folder)


def empty_cadet_input_folder():
    """ Delete all CADET input files.
    """
    path = get_cadet_input_folder()
    desc = "CADET input files"
    attempt_empty_folder(path, desc)


def empty_log_folder():
    """ Delete all Reveal Chromatography log files.
    """
    path = get_log_folder()
    desc = "log files"
    attempt_empty_folder(path, desc)


def launch_app_for_study(study, **kwargs):
    """ Create an application object around a study and run it.

    This can be useful for scripting or testing purposes: it allows anyone to
    create a custom study, and launch the application afterwards, to avoid
    having to click a lot.

    Parameters
    ----------
    study : Study
        Study to build the application around.

    kwargs : dict
        Additional attributes of the KromatographyApp object being created.
    """
    from kromatography.app.krom_app import KromatographyApp

    app = KromatographyApp(initial_studies=[study], **kwargs)
    app.run()
    return app


def build_user_datasource_filepath():
    """ Build a file path that the user can write to for storing the user
    datasource in a local, file based database.
    """
    db_file_template = DS_PREFIX + "_%Y-%m-%d-%H-%M-%S" + DS_EXT
    db_file = time.strftime(db_file_template)

    db_dir = get_user_ds_folder()

    if not isdir(db_dir):
        os.makedirs(db_dir)

    db_file = join(db_dir, db_file)
    return db_file


def get_newest_app_file(dir_to_search="", prefix=DS_PREFIX, extension=DS_EXT):
    """ Returns the absolute path to the most recent file of type specified.

    Files considered must:
        1. be in the standard folder for the type requested.
        2. start with the prefix of the type requested
        3. have the right file extension of the type requested

    Returns
    -------
    str or None : absolute path to the newest file from the directory specified
    or the default directory as specified by the utilities in this folder.
    Returns None if no file is found or if the directory to search doesn't
    exist.
    """
    # Logger defined here so that the logger can be defined after the
    # initialize_logging is called.
    logger = logging.getLogger(__name__)

    factories = {DS_EXT: build_user_datasource_filepath}

    if not dir_to_search:
        dir_to_search = dirname(factories[extension]())
    else:
        dir_to_search = abspath(dir_to_search)

    if not isdir(dir_to_search):
        msg = "Folder to search ({}) for {} type files doesn't exist."
        msg = msg.format(dir_to_search, extension)
        logger.warning(msg)
        return None

    candidates = []
    for filename in os.listdir(dir_to_search):
        if filename.startswith(prefix) and filename.endswith(extension):
            candidates.append(join(dir_to_search, filename))

    if not candidates:
        return None
    else:
        return sorted(candidates)[-1]


def load_default_user_datasource():
    """ Load or build the default user datasource.

    If a datasource was stored in the default, location, load the newest one.
    Otherwise, build a new SimpleDataSource.

    Returns
    -------
    tuple with a SimpleDatasource instance and the file if any that it was
    loaded from.
    """
    from kromatography.model.data_source import SimpleDataSource
    from kromatography.io.reader_writer import load_object

    # Logger defined here so that the logger can be defined after the
    # initialize_logging is called.
    logger = logging.getLogger(__name__)

    last_stored_ds_file = get_newest_app_file(extension=DS_EXT)
    if last_stored_ds_file is not None:
        try:
            ds, legacy_file = load_object(last_stored_ds_file)
            msg = "Loaded datasource from {}".format(last_stored_ds_file)
            logger.info(msg)
            if legacy_file:
                msg = "Datasource storage {} is a legacy file."
                logger.info(msg)

        except Exception as e:
            msg = ("Failed to load the last datasource file {}. The file "
                   "might be corrupted, and mights need to be removed. Error "
                   "was {}.").format(last_stored_ds_file, e)
            logger.error(msg)
            last_stored_ds_file = None

    # Not doing an else, so that this is executed when exception raised:
    if last_stored_ds_file is None:
        msg = "No valid datasource file found. Loading a default one."
        logger.debug(msg)
        ds = SimpleDataSource(name="User DataSource")
        last_stored_ds_file = ""

    return ds, last_stored_ds_file


def save_user_datasource_to(ds, filepath=None):
    """ Export the provided datasource to specified file path.

    If the filepath is left blank, the datasource is stored in the app's DS
    folder and the provided datasource becomes the application's default.
    """
    from kromatography.io.api import save_object

    logger = logging.getLogger(__name__)
    if filepath is None:
        filepath = build_user_datasource_filepath()

    logger.debug("Storing the user datasource to {}".format(filepath))
    save_object(filepath, ds)
    return filepath


def build_bug_report_content(app=None):
    """ Returns the content of the bug report dialog.
    """
    logger = logging.getLogger(__name__)
    user_name = collect_user_name()
    # The spaces must be replaced by %20 to be encoded correctly in the mailto
    # directive.
    support_email_subject = "Bug report from {}".replace(" ", "%20").format(
        user_name
    )

    if app:
        log_filepath = basename(app.log_filepath)
    else:
        logger.error("No log file was found!: app argument is {}".format(app))
        log_filepath = "NO LOG FILE FOUND"

    datasource_file_present = app and app.datasource_file
    if datasource_file_present:
        user_ds_filename = basename(app.datasource_file)
    else:
        user_ds_filename = "NO FILE FOUND"

    user_ds_dir = get_user_ds_folder()

    ds_item = '<li>'
    ds_item += 'The user datasource file used at the time of the issue, ' \
               'stored in <a href="file://{user_ds_dir}">{user_ds_dir}</a>.'

    if datasource_file_present:
        ds_item += '(The one currently in use is ' \
                   '<a href="file://{user_ds_dir}">{user_ds_file}</a>.)'
    else:
        ds_item += ("The current datasource isn't saved to file. Please close"
                    " this dialog, and select <i>File > Save User Data"
                    "</i> to create a file.")
    ds_item += '</li>'
    ds_item = ds_item.format(user_ds_file=user_ds_filename,
                             user_ds_dir=user_ds_dir)

    data = dict(email=SUPPORT_EMAIL_ADDRESS, subject=support_email_subject,
                app_family=APP_FAMILY, app_name=APP_TITLE,
                log_dir=get_log_folder(), log_file=log_filepath,
                ds_item=ds_item, version=__version__, build=__build__)
    bug_report_content = BUG_REPORT_CONTENT_TEMPLATE.format(**data)
    return bug_report_content


def initialize_reveal(verbose=True):
    """ Initialize all Reveal application tools: logging and unit parsers.
    """
    from logging import getLogger
    from kromatography.ui.branding import APP_TITLE

    logger = getLogger(__name__)

    initialize_logging(verbose=verbose)
    initialize_unit_parser()
    logger.info("{} tools initialized.".format(APP_TITLE))
