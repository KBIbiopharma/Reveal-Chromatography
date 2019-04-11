""" TaskApplication object and executable script to run the Reveal
Chromatography application.
"""

from __future__ import absolute_import, division, print_function, \
    unicode_literals
import logging
import os
from os.path import abspath, dirname, join
from contextlib import contextmanager
from copy import copy

from traits.api import Bool, Either, Instance, Int, List, Str
from pyface.tasks.action.api import SchemaAddition, SGroup
from pyface.api import confirm, error, ImageResource, information, NO, \
    SplashScreen, YES

from app_common.encore.job_manager import JobManager
from app_common.pyface.monitored_actions import MonitoredAction as Action, \
    MonitoredUndoAction as UndoAction, MonitoredRedoAction as RedoAction
from app_common.pyface.ui.tasks.task_gui_application import TaskGuiApplication  # noqa
from app_common.std_lib.filepath_utils import open_file
from app_common.std_lib.sys_utils import IS_WINDOWS

import kromatography
from kromatography.ui.tasks.kromatography_task import KromatographyTask
from kromatography.ui.branding import ABOUT_HTML, ABOUT_MSG, APP_FAMILY, \
    APP_TITLE, DEBUG_SPLASH_DURATION, DEFAULT_SPLASH_DURATION
from kromatography.ui.api import register_all_data_views

from kromatography.model.kromatography_project import KromatographyProject
from kromatography.model.data_source import DataSource
from kromatography.model.study import Study

logger = logging.getLogger(__name__)


class KromatographyApp(TaskGuiApplication):
    """ An application to run CADET simulations and confront to experiments.
    """

    # -------------------------------------------------------------------------
    # TaskGuiApplication interface
    # -------------------------------------------------------------------------

    #: Application name in CamelCase. Used to set ETSConfig.application_data
    app_name = Str()

    # -------------------------------------------------------------------------
    # KromatographyApp interface
    # -------------------------------------------------------------------------

    #: Files to load at start-up.
    initial_files = Either(None, List(Str))

    #: Files to load at start-up.
    recent_files = List

    #: Max number of project file paths to remember
    max_recent_files = Int

    #: Initial list of studies to launch on start
    initial_studies = List(Instance(Study))

    #: Source of default data objects for creating new studies.
    datasource = Instance(DataSource)

    #: Manager for running CADET jobs
    job_manager = Instance(JobManager)

    #: File path to the user datasource that the app is using if applicable.
    datasource_file = Str

    #: File path to the log file in use.
    log_filepath = Str

    #: Global schema additions.
    extra_actions = List(Instance(
        'pyface.tasks.action.schema_addition.SchemaAddition'
    ))

    #: Force show all logger calls in console? Read preferences otherwise.
    verbose = Bool(False)

    #: Ask confirmation every time one closes a window?
    confirm_on_window_close = Bool

    #: Issue warning dialog
    warn_if_old_file = Bool(True)

    #: Automatically close empty windows when opening a new one?
    auto_close_empty_windows_on_open = Bool

    # -------------------------------------------------------------------------
    # TaskGuiApplication interface methods
    # -------------------------------------------------------------------------

    def start(self):
        """ The application could be started with no argument, with files that
        should be open on start or with custom studies that should be opened on
        start. The application will build a task for any files or study passed
        at launch.
        """
        from kromatography.ui.tasks.kromatography_task import KROM_EXTENSION
        from kromatography.ui.branding import APP_TITLE

        starting = super(KromatographyApp, self).start()
        if not starting:
            return False

        self._log_application_start()

        register_all_data_views()

        if self.initial_files:
            for filepath in self.initial_files:
                ext = os.path.splitext(filepath)[1]
                if ext == KROM_EXTENSION:
                    self.open_project_from_file(filepath)
                elif ext == ".xlsx":
                    self.build_study_from_file(filepath)
                else:
                    msg = "{} was requested but {} is unable to load {} files."
                    msg = msg.format(filepath, APP_TITLE, ext)
                    logger.exception(msg)
                    error(None, msg)

        elif self.initial_studies:
            for study in self.initial_studies:
                self.create_new_task_window(study=study)
        else:
            # Nothing was requested: open a new empty window
            self.create_new_task_window()

        self.job_manager.start()
        return True

    # -------------------------------------------------------------------------
    # Task creation methods
    # -------------------------------------------------------------------------

    def create_new_task_window(self, study=None):
        """ Create a new KromatographyProject, task and open a window with it.

        Parameters
        ----------
        study : Study or None
            Create the task and window for the study passed.

        Returns
        -------
        window : TaskWindow
            Window that was created, containing the newly created task.
        """
        traits = {}
        if study is not None:
            traits["study"] = study

        model = KromatographyProject(**traits)
        task = KromatographyTask(project=model)
        return self._finalize_task_and_open_task_window(task)

    def new_study_from_experimental_study_file(self):
        """ Create new study from experimental study file from disk, prompting
        user for the path.
        """
        from kromatography.utils.extra_file_dialogs import study_file_requester
        path = study_file_requester()
        if path is not None:
            self.build_study_from_file(path)

    def new_blank_project(self):
        """ Set the current study to non-blank so that the view updates to the
        editing mode.
        """
        self.active_task.project.study.is_blank = False

    def build_study_from_file(self, filepath, allow_gui=True):
        """ Build a new task and window from loading an ExperimentalStudy file.

        Returns
        -------
        TaskWindow
            Returns the newly created TaskWindow around the provided study.
        """
        from kromatography.io.study import load_study_from_excel

        study = load_study_from_excel(filepath, datasource=self.datasource,
                                      allow_gui=allow_gui)
        window = self.create_new_task_window(study=study)

        if study.product_contains_strip:
            study.request_strip_fraction_tool()

        return window

    def request_project_from_file(self):
        """ Open a saved study from loading from  file.
        """
        from kromatography.utils.extra_file_dialogs import \
            project_file_requester

        path = project_file_requester()
        if path is not None:
            self.open_project_from_file(path)

    def open_project_from_file(self, path):
        """ Open a saved task from a project file.
        """
        from kromatography.io.task import load_project

        path = os.path.abspath(path)
        self.add_to_recent_files(path)
        already_open = self.activate_window_if_already_open(path)

        if already_open:
            msg = "Project {} already loaded.".format(path)
            logger.info(msg)
        else:
            try:
                task, legacy_file = load_project(path)
            except Exception as e:
                msg = ("The object found in {} didn't load successfully. Error"
                       " was {}".format(path, e))
                logger.exception(msg)
                error(None, msg)
                raise IOError(msg)

            if not isinstance(task, KromatographyTask):
                msg = "The object found in {} is not a {} project but a {}"
                msg = msg.format(path, APP_TITLE, type(task))
                logger.exception(msg)
                error(None, msg)
                raise IOError(msg)

            self._finalize_task_and_open_task_window(task)

            if legacy_file and self.warn_if_old_file:
                from pyface.api import warning
                from ..ui.tasks.kromatography_task import KROM_EXTENSION
                msg = "The file {} doesn't use the newest {} format. It is " \
                      "recommended to re-save the project to ensure future " \
                      "readability."
                msg = msg.format(path, KROM_EXTENSION)
                warning(None, msg)

            if self.auto_close_empty_windows_on_open:
                self.close_empty_windows()

            return task

    def add_to_recent_files(self, path):
        """ Store the project files loaded.
        """
        # Avoid duplicates:
        if path in self.recent_files:
            self.recent_files.remove(path)

        self.recent_files.insert(0, path)

        # Truncate if too many recent files
        if len(self.recent_files) > self.max_recent_files:
            self.recent_files.pop(-1)

    def activate_window_if_already_open(self, path):
        """ Returns if a project file has been opened already. If so, make its
        window active.

        Parameters
        ----------
        path : str
            Absolute path to the project file we are testing.

        Returns
        -------
        bool
            Whether that path was already open.
        """
        window_to_activate = None
        for window in self.windows_created:
            task = window.active_task
            if task.project_filepath == path:
                window_to_activate = window
                # Bring TaskWindow in question to front:
                window.activate()
                break

        return window_to_activate is not None

    def open_about_dialog(self):
        self.about_dialog.open()

    def open_bug_report(self):
        from kromatography.utils.app_utils import build_bug_report_content

        information(None, build_bug_report_content(self),
                    title="Report a bug / Send feedback")

    def open_documentation(self):
        doc_target = join(dirname(kromatography.__file__), "doc", "index.html")
        open_file(doc_target)

    def open_tutorial_files(self):
        tut_target = join(dirname(kromatography.__file__), "data",
                          "tutorial_data")
        open_file(tut_target)

    def open_preferences(self):
        from kromatography.utils.app_utils import get_preferences
        from kromatography.tools.preferences_view import \
            RevealChromatographyPreferenceView

        prefs = get_preferences()
        view = RevealChromatographyPreferenceView(model=prefs)
        view.edit_traits(kind="livemodal")

    def open_software_updater(self):
        from kromatography.tools.update_downloader import UpdateDownloader

        tool = UpdateDownloader()
        # Trigger a check before opening the UI:
        tool.check_button = True
        tool.edit_traits(kind="modal")

    def open_recent_project(self):
        from kromatography.ui.project_file_selector import ProjectFileSelector
        selector = ProjectFileSelector(path_list=self.recent_files)
        ui = selector.edit_traits(kind="livemodal")
        if ui.result:
            if isinstance(selector.selected, basestring):
                selector.selected = [selector.selected]

            for selected in selector.selected:
                self.open_project_from_file(selected)

    # -------------------------------------------------------------------------
    # Menu generation methods
    # -------------------------------------------------------------------------

    def close_empty_windows(self):
        from kromatography.ui.tasks.kromatography_task import is_task_blank
        for window in self.windows_created:
            task = window.active_task
            if is_task_blank(task):
                with self.skip_confirm_on_window_close():
                    window.close()

    def create_new_project_group(self):
        from kromatography.ui.menu_entry_names import (
            NEW_BLANK_PROJECT_MENU_NAME, NEW_PROJECT_FROM_EXPERIMENT_MENU_NAME,
            OPEN_PROJECT_MENU_NAME
        )
        return SGroup(
            Action(name=NEW_BLANK_PROJECT_MENU_NAME,
                   on_perform=self.new_blank_project,
                   image=ImageResource('document-new')),
            Action(name=NEW_PROJECT_FROM_EXPERIMENT_MENU_NAME,
                   accelerator='Ctrl+L',
                   on_perform=self.new_study_from_experimental_study_file,
                   image=ImageResource('applications-science')),
            Action(name=OPEN_PROJECT_MENU_NAME,
                   accelerator='Ctrl+O',
                   on_perform=self.request_project_from_file,
                   image=ImageResource('document-open')),
            id='NewStudyGroup', name='NewStudy',
        )

    def create_recent_project_group(self):
        return SGroup(
            Action(name="Recent Projects...",
                   on_perform=self.open_recent_project,
                   image=ImageResource('document-open-recent.png')),
            id='RecentProjectGroup', name='NewStudy',
        )

    def create_close_group(self):
        return SGroup(
            Action(name='Exit' if IS_WINDOWS else 'Quit',
                   accelerator='Alt+F4' if IS_WINDOWS else 'Ctrl+Q',
                   on_perform=self.exit,
                   image=ImageResource('system-shutdown')),
            id='QuitGroup', name='Quit',
        )

    def create_undo_group(self):
        return SGroup(
            UndoAction(undo_manager=self.undo_manager, accelerator='Ctrl+Z'),
            RedoAction(undo_manager=self.undo_manager,
                       accelerator='Ctrl+Shift+Z'),
            id='UndoGroup', name='Undo'
        )

    def create_copy_group(self):
        return SGroup(
            Action(name='Cut', accelerator='Ctrl+X'),
            Action(name='Copy', accelerator='Ctrl+C'),
            Action(name='Paste', accelerator='Ctrl+V'),
            id='CopyGroup', name='Copy'
        )

    def create_preference_group(self):
        from kromatography.ui.menu_entry_names import PREFERENCE_MENU_NAME
        return SGroup(
            Action(name=PREFERENCE_MENU_NAME,
                   accelerator='Ctrl+,',
                   on_perform=self.open_preferences,
                   image=ImageResource('preferences-system')),
            id='PreferencesGroup', name='Preferences',
        )

    def create_bug_report_group(self):
        from kromatography.ui.menu_entry_names import \
            REPORT_ISSUE_FEEDBACK_MENU_NAME

        group = SGroup(
            Action(name=REPORT_ISSUE_FEEDBACK_MENU_NAME,
                   on_perform=self.open_bug_report,
                   image=ImageResource('mail-mark-important')),
            Action(name='Info about {} {}'.format(APP_FAMILY, APP_TITLE),
                   on_perform=self.open_about_dialog,
                   image=ImageResource('system-help')),
            id='HelpGroup', name='HelpGroup',
        )
        return group

    def create_documentation_group(self):
        group = SGroup(
                Action(name='Show sample input files...',
                       on_perform=self.open_tutorial_files,
                       image=ImageResource('help-browser')),
                Action(name='Open documentation...',
                       on_perform=self.open_documentation,
                       image=ImageResource('help-contents')),
                id='DocsGroup', name='Documentation',
        )
        return group

    def create_update_group(self):
        group = SGroup(
                Action(name='Check for updates...',
                       on_perform=self.open_software_updater,
                       image=ImageResource('system-software-update')),
                id='UpdateGroup', name='App Updater',
        )
        return group

    # -------------------------------------------------------------------------
    #  KromatographyApp interface
    # -------------------------------------------------------------------------

    # -------------------------------------------------------------------------
    #  Private interface
    # -------------------------------------------------------------------------

    def _finalize_task_and_open_task_window(self, task, filename=""):
        """ Connect task to application, sync datasources and job manager and
        open task in a new window.
        """
        from kromatography.utils.datasource_utils import \
            prepare_datasource_catalog
        # Sync the datasources of the project and the study to the
        # application's datasource
        task.project.datasource = self.datasource
        task.project.job_manager = self.job_manager
        task.project.study.datasource = self.datasource
        # Add listeners for the project lists. Task will listen to this to
        # update the UI:
        task.project.add_object_deletion_listeners()

        task.filename = filename
        task.undo_manager = self.undo_manager
        task.extra_actions = self.extra_actions
        task._app = self
        window = self.create_task_window(task)
        if filename:
            task.set_clean_state(True)

        # Add attributes to contribute new entries to the object_catalog
        prepare_datasource_catalog(self.datasource)
        return window

    def _log_application_start(self):
        krom_version = kromatography.__version__
        krom_build = kromatography.__build__
        install_location = abspath(dirname(kromatography.__file__))
        logger.info("")
        logger.info("     **********************************************************")  # noqa
        logger.info("     *  {} application launching...        *".format(APP_TITLE))  # noqa
        logger.info("     *  based on kromatography version {} build {}     *".format(krom_version, krom_build))  # noqa
        logger.info("     *  installed in {} *".format(install_location))
        logger.info("     **********************************************************")  # noqa
        logger.info("")

    def _on_closing_window(self, window, trait, old, new):
        """ Ask before window closing: save the user DS? Save project?
        """
        from kromatography.ui.menu_entry_names import PREFERENCE_MENU_NAME

        if self.datasource.dirty and len(self.windows_created) == 1:
            title = "Save the User Datasource?"

            msg = ("Some changes have been made to the User Data. Do you want"
                   " to save it and make it the new default User Data?")
            res = confirm(None, msg, title=title)
            if res == YES:
                task = window.active_task
                task.save_user_ds()

        # Ask for all window in case people change their mind
        if self.confirm_on_window_close:
            msg = "Are you sure you want to close the project? All un-saved " \
                  "changes will be lost. <br><br>(You can suppress this" \
                  " confirmation in the Preference panel: <i>Edit > {}</i>.)"
            msg = msg.format(PREFERENCE_MENU_NAME)
            response = confirm(None, msg, title="Close the project?")
            if response == NO:
                new.veto = True

    def _setup_logging(self):
        from kromatography.utils.app_utils import get_preferences, \
            initialize_logging

        if self.verbose:
            verbose = True
        else:
            preferences = get_preferences()
            verbose = preferences.app_preferences.console_logging_level <= 10

        self.log_filepath = initialize_logging(verbose=verbose)

    def _prepare_exit(self):
        """ Do any application-level state saving and clean-up.
        """
        from kromatography.utils.app_utils import empty_cadet_input_folder, \
            get_preferences

        if self.job_manager:
            self.job_manager.shutdown()
            self.job_manager = None

        # Lazily load preferences to give a chance to a user to change that
        # parameters after starting:
        preferences = get_preferences()
        if preferences.solver_preferences.auto_delete_solver_files_on_exit:
            empty_cadet_input_folder()

        # Remember the recent files
        preferences.file_preferences.recent_files = self.recent_files
        preferences.to_preference_file()

    # -------------------------------------------------------------------------
    # Traits initialization methods
    # -------------------------------------------------------------------------

    def _splash_screen_default(self):
        from kromatography.ui.image_resources import splash_screen

        splash_screen = SplashScreen(image=splash_screen)
        return splash_screen

    def _extra_actions_default(self):
        addition_list = [
            SchemaAddition(
                id='krom.new_study_group',
                path='MenuBar/File',
                absolute_position='first',
                after='RecentProjectGroup',
                factory=self.create_new_project_group,
            ),
            SchemaAddition(
                id='krom.recent_proj_group',
                path='MenuBar/File',
                before='SaveGroup',
                factory=self.create_recent_project_group,
            ),
            SchemaAddition(
                id='krom.close_group',
                path='MenuBar/File',
                absolute_position='last',
                factory=self.create_close_group,
            ),
            SchemaAddition(
                id='krom.undo_group',
                path='MenuBar/Edit',
                absolute_position='first',
                factory=self.create_undo_group,
            ),
            SchemaAddition(
                id='krom.copy_group',
                path='MenuBar/Edit',
                after='UndoGroup',
                factory=self.create_copy_group,
            ),
            SchemaAddition(
                id='krom.preferences_group',
                path='MenuBar/Edit',
                after='CopyGroup',
                factory=self.create_preference_group,
            ),
            SchemaAddition(
                id='krom.help_group',
                path='MenuBar/Help',
                after='DocsGroup',
                factory=self.create_bug_report_group,
            ),
            SchemaAddition(
                id='krom.help_docs_menu',
                path='MenuBar/Help',
                absolute_position='first',
                factory=self.create_documentation_group,
            ),
            SchemaAddition(
                id='krom.help_update',
                path='MenuBar/Help',
                absolute_position='last',
                factory=self.create_update_group,
            ),
        ]

        return addition_list

    def _datasource_default(self):
        """ Build a DS from the latest stored version if possible. Build a
        default one otherwise.
        """
        from kromatography.utils.app_utils import load_default_user_datasource
        return load_default_user_datasource()[0]

    def _datasource_file_default(self):
        from kromatography.utils.app_utils import load_default_user_datasource
        return load_default_user_datasource()[1]

    def _job_manager_default(self):
        from kromatography.model.factories.job_manager import \
            create_start_job_manager
        from kromatography.utils.app_utils import get_preferences

        preferences = get_preferences()
        job_manager = create_start_job_manager(
            max_workers=preferences.solver_preferences.executor_num_worker
        )
        return job_manager

    def _app_name_default(self):
        return APP_TITLE.title().replace(" ", "")

    def _window_size_default(self):
        from kromatography.utils.app_utils import get_preferences
        prefs = get_preferences()
        ui_prefs = prefs.ui_preferences
        return ui_prefs.app_width, ui_prefs.app_height

    def _about_dialog_default(self):
        from app_common.pyface.ui.about_dialog import AboutDialog
        from kromatography.ui.image_resources import reveal_chrom_logo

        about_msg = copy(ABOUT_MSG)

        return AboutDialog(
            parent=None,
            additions=about_msg,
            html_container=ABOUT_HTML,
            include_py_qt_versions=False,
            title='About {} {}'.format(APP_FAMILY, APP_TITLE),
            image=reveal_chrom_logo,
        )

    def _auto_close_empty_windows_on_open_default(self):
        from kromatography.utils.app_utils import get_preferences
        prefs = get_preferences()
        ui_prefs = prefs.ui_preferences
        return ui_prefs.auto_close_empty_windows_on_open

    def _confirm_on_window_close_default(self):
        from kromatography.utils.app_utils import get_preferences
        prefs = get_preferences()
        ui_prefs = prefs.ui_preferences
        return ui_prefs.confirm_on_window_close

    def _recent_files_default(self):
        from kromatography.utils.app_utils import get_preferences
        preferences = get_preferences()
        return preferences.file_preferences.recent_files

    def _max_recent_files_default(self):
        from kromatography.utils.app_utils import get_preferences
        preferences = get_preferences()
        return preferences.file_preferences.max_recent_files

    @contextmanager
    def skip_confirm_on_window_close(self):
        """ Utility to temporarily skip confirmation when closing a window.
        """
        old = self.confirm_on_window_close
        self.confirm_on_window_close = False
        yield
        self.confirm_on_window_close = old


def instantiate_app(init_files=None, splash_duration=DEFAULT_SPLASH_DURATION,
                    debug=False, user_ds="", **app_traits):
    """ Returns a KromatographyApp instance, optionally around the provided
    initial files.

    Parameters
    ----------
    init_files : list of strings [OPTIONAL]
        List of filenames to open on launch of the application.

    splash_duration : float [OPTIONAL]
        Duration, in seconds, to show the splash screen. Set to .1 sec if
        debug=True. Defaults to 3 seconds.

    debug : bool [OPTIONAL]
        Running in debug mode? If so, verbose is set to True, and
        splash_duration is set to DEBUG_SPLASH_DURATION seconds.

    user_ds : str [OPTIONAL]
        File path to the user data file to load the application with. Leave
        blank to use the default user data file.

    app_traits : dict [OPTIONAL]
        Additional Application traits to set: verbose, confirm_on_window_close,
        ...
    """
    from kromatography.ui.image_resources import reveal_chrom_icon
    from kromatography.utils.app_utils import initialize_cadet_input_folder, \
        initialize_executor_temp_folder, reinitialize_preference_file
    from kromatography.io.api import load_object

    if debug:
        app_traits["verbose"] = True
        splash_duration = DEBUG_SPLASH_DURATION

    # Make sure all needed execution folders exist:
    success = initialize_cadet_input_folder()
    if not success:
        return
    initialize_executor_temp_folder()

    # FIXME: add initialization of the python script folder

    # and that the preference file gets updated with latest content:
    reinitialize_preference_file()

    app = KromatographyApp(initial_files=init_files,
                           splash_screen_duration=splash_duration,
                           icon=reveal_chrom_icon, **app_traits)
    if user_ds:
        app.datasource, _ = load_object(user_ds)
    return app
