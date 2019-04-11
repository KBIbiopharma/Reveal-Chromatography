import os
from os.path import join, split, splitext
import logging

from traits.api import Any, Bool, Dict, Instance, on_trait_change, Property, \
    Str, Unicode
from apptools.undo.api import ICommandStack, IUndoManager
from pyface.api import error, ImageResource, information, OK
from pyface.tasks.api import PaneItem, SplitEditorAreaPane, Splitter, Task, \
    TaskLayout
from pyface.tasks.action.api import DockPaneToggleGroup, SGroup, SMenu, \
    SMenuBar, SToolBar, TaskWindowAction

from app_common.model_tools.data_element import DataElement
from app_common.pyface.monitored_actions import action_monitoring, \
    MonitoredTaskAction as TaskAction
from app_common.pyface.ui.extra_file_dialogs import FileDialogWithMemory
from app_common.model_tools.data_editor import DataElementEditor

from kromatography.model.kromatography_project import KromatographyProject
from kromatography.plotting.model_factories import build_chromatogram_model
from kromatography.plotting.animation_plot import \
    build_animation_plot_model
from kromatography.ui.branding import APP_FAMILY, APP_TITLE
from kromatography.ui.chromatogram_model_view import ChromatogramModelView
from kromatography.ui.menu_entry_names import STRIP_TOOL_NAME

KROM_EXTENSION = ".chrom"

KROM_WILDCARD = "{1} Projects (*{0})|*{0}".format(KROM_EXTENSION, APP_TITLE)

KROM_DS_EXTENSION = ".chromds"

KROM_DS_WILDCARD = "{1} User Datasource (*{0})|*{0}".format(KROM_DS_EXTENSION,
                                                            APP_TITLE)

ICON_SIZE = (22, 22)

logger = logging.getLogger(__name__)


class KromatographyTask(Task):
    """ Task providing central pane & dock panes to view a KromatographyProject
    """

    # -------------------------------------------------------------------------
    # 'Task' interface
    # -------------------------------------------------------------------------

    id = 'krom.kromatography_task'

    name = Str

    # -------------------------------------------------------------------------
    # 'UndoableTask' interface
    # -------------------------------------------------------------------------

    #: The task's command stack for Undo/Redo
    command_stack = Instance(ICommandStack)

    #: The global undo manager for the application
    undo_manager = Instance(IUndoManager)

    # -------------------------------------------------------------------------
    # 'KromatographyTask' interface
    # -------------------------------------------------------------------------

    #: 'Project' filepath storing the current task (to store UI elements too)
    project_filepath = Unicode

    #: Project to support the GUI.
    project = Instance(KromatographyProject)

    # -------------------------------------------------------------------------
    # 'KromatographyTask' private interface
    # -------------------------------------------------------------------------

    #: hook to the central pane
    central_pane = Instance(SplitEditorAreaPane)

    #: Map between the object displayed in the central pane and editors for it
    # Note: there could be several editors for the same object. For example, a
    # simulation might be open, for there might be a chrom plot and an
    # animation plot open for it too.
    central_pane_editor_map = Dict

    # Other panes -------------------------------------------------------------

    datasource_pane = Instance('kromatography.ui.tasks.data_source_pane.'
                               'DataSourceDockPane')

    study_data_pane = Instance('kromatography.ui.tasks.study_browser_pane.'
                               'StudyDataDockPane')

    performance_param_pane = Instance(
        'kromatography.ui.tasks.performance_param_pane.PerformanceParamPane')

    job_manager_pane = Instance('app_common.encore.job_manager_pane.'
                                'JobManagerPane')

    #: Flags to analyze if certain objects exist
    simulations_exist = Property(Bool,
                                 depends_on="project.study.simulations[]")

    experiments_exist = Property(Bool,
                                 depends_on="project.study.experiments[]")

    experiments_and_sim_exist = Property(
        Bool, depends_on="simulations_exist, experiments_exist"
    )

    simulation_groups_exist = Property(
        Bool, depends_on="project.study.analysis_tools.simulation_grids[]"
    )

    _strip_component_exist = Property(Bool, depends_on="project.study.product")

    #: Handle on the application object which created the task
    _app = Instance('kromatography.app.krom_app.KromatographyApp')

    #: View class for the active central pane tab editor
    _view_central_pane = Property(Any, depends_on="central_pane.active_editor")

    #: Is the view class for active central pane tab editor a plot?
    _central_pane_is_plot = Property(Bool, depends_on="_view_central_pane")

    # -------------------------------------------------------------------------
    # 'Task' interface methods
    # -------------------------------------------------------------------------

    def create_central_pane(self):
        """ Create an DataViews pane as the main task UI.
        """
        self.central_pane = SplitEditorAreaPane()
        return self.central_pane

    def create_dock_panes(self):
        """ Create all dock panes for the main task UI """
        from kromatography.ui.tasks.data_source_pane import \
            DataSourceDockPane
        from kromatography.ui.tasks.study_browser_pane import StudyDataDockPane
        from kromatography.ui.tasks.performance_param_pane import \
            PerformanceParamPane
        from app_common.encore.job_manager_pane import \
            JobManagerPane

        self.datasource_pane = DataSourceDockPane(
            datasource=self.project.datasource
        )
        self.study_data_pane = StudyDataDockPane(
            study=self.project.study
        )
        self.performance_param_pane = PerformanceParamPane(
            study=self.project.study
        )
        self.job_manager_pane = JobManagerPane(
            job_manager=self._app.job_manager,
            name='Cadet Job Manager', run_time_result_key="run time"
        )

        return [self.datasource_pane, self.study_data_pane,
                self.performance_param_pane, self.job_manager_pane]

    def activated(self):
        """ Actions to be taken once the task panes have been created and the
        window has been created:
        1. Ensure that the command stack is the active command stack
        2. Open a view on the project's study
        """
        super(KromatographyTask, self).activated()

        # Set up the undo infrastructure
        self.command_stack.undo_manager = self.undo_manager
        self.undo_manager.active_stack = self.command_stack
        self.is_activated = True

        # Open the current project's study
        self.edit_object_in_central_pane(self.project.study)
        if self.project.study.experiments:
            self.new_model_calibration_plot()

    def prepare_destroy(self):
        self.job_manager_pane.prepare_destroy()

    # -------------------------------------------------------------------------
    # 'KromatographyTask' interface methods
    # -------------------------------------------------------------------------

    def edit_object_in_central_pane(self, obj, factory=None, uuid_to_map=None):
        """ Select appropriate editor to visualize/edit Traits object in the
        central pane.

        Parameters
        ----------
        obj : any
            Object to be edited in the central pane.

        factory : type [OPTIONAL]
            Class used to build the editor.

        uuid_to_map : UUID
            UUID of the object to track as holding the data for the resulting
            editor. If/when that object gets deleted, the corresponding editor
            will get closed.
        """
        if factory is None:
            if isinstance(obj, DataElement):
                factory = DataElementEditor
            else:
                msg = "No editor yet for a {}".format(type(obj))
                logger.error(msg)
                raise NotImplementedError(msg)

        editor = self.central_pane.edit(obj, factory=factory)
        if editor.obj_view:
            # Provide the modelView with access to the task in case of need:
            editor.obj_view._task = self

        # Track whose uuid we should associate with this editor (so that if
        # that object gets deleted, this editor gets closed)
        if uuid_to_map is None:
            uuid_to_map = obj.uuid

        if uuid_to_map not in self.central_pane_editor_map:
            self.central_pane_editor_map[uuid_to_map] = []

        self.central_pane_editor_map[uuid_to_map].append(editor)

    def close_central_pane_for_object(self, obj_info):
        """ Close the central pane editor(s) for specified edited_object.
        """
        editors = self.central_pane_editor_map.pop(obj_info["uuid"], None)
        if editors is None:
            return

        for editor in editors:
            try:
                self.central_pane.remove_editor(editor)
            except Exception as e:
                msg = "Failed to remove editor for object {} (type {}). " \
                      "Error was {}."
                msg = msg.format(obj_info["name"], obj_info["type"], e)
                logger.warning(msg)

    # Serialization methods ---------------------------------------------------

    def save_request(self):
        """ Save current project to a new file.
        """
        dlg_attrs = {'title': 'Save Project', 'action': 'save as',
                     'wildcard': KROM_WILDCARD}
        # If the project already has
        if self.project_filepath:
            curr_folder, curr_filename = split(self.project_filepath)
            dlg_attrs["default_directory"] = curr_folder
            dlg_attrs["default_filename"] = curr_filename

        file_dialog = FileDialogWithMemory(**dlg_attrs)
        file_dialog.open()

        if file_dialog.return_code == OK:
            path = file_dialog.path
            self.save_project_as(path=path)

    def save_project_as(self, path=""):
        """ Store the current task to the filepath provided and set project
        file path.
        """
        from kromatography.io.task import save_project

        if not path:
            msg = "Attempted to save a project but no file path provided " \
                  "(found '{}').".format(path)
            logger.error(msg)
            return False

        save_project(path, self)

    def save(self):
        """ Store the current task to its file path.
        """
        from kromatography.io.reader_writer import save_object

        if not self.project_filepath:
            self.save_request()
            return

        save_object(self.project_filepath, self)

    def save_user_ds(self):
        """ Store the user datasource to a new timed local file.
        """
        from kromatography.utils.app_utils import \
            save_user_datasource_to

        save_user_datasource_to(self.project.datasource)
        self.project.datasource.make_clean()

    def request_export_user_ds(self):
        """ Store the user datasource to a new timed local file.
        """
        from kromatography.utils.app_utils import save_user_datasource_to

        file_dialog = FileDialogWithMemory(
            title='Export User Data',
            action='save as',
            wildcard=KROM_DS_WILDCARD
        )
        file_dialog.open()

        if file_dialog.return_code == OK:
            path = file_dialog.path
            basepath, path_ext = splitext(path)
            if path_ext != KROM_DS_EXTENSION:
                path = basepath + KROM_DS_EXTENSION

            save_user_datasource_to(self.project.datasource, filepath=path)

    # New object creation methods ---------------------------------------------

    def new_simulation_from_datasource(self):
        """ Create a new simulation from DataSource data.
        """
        self.project.study.request_new_simulation_from_datasource(
            self.project.datasource
        )

    def new_simulation_from_experiments(self):
        """ Add new simulations mirroring experiment(s) in the current study.
        """
        self.project.study.request_new_simulations_from_experiments()

    def new_simulation_grid(self):
        """ Build a SimulationGroup around a center point simulation
        """
        grid = self.project.study.request_new_simulation_group()
        if grid is not None:
            self.edit_object_in_central_pane(grid)

    # Configuration tool methods ----------------------------------------------

    def open_strip_fraction_editor(self):
        """ Open the editor for strip fractions. """
        self.project.study.request_strip_fraction_tool()

    # Run launch methods ------------------------------------------------------

    def run_simulations(self, sims=None):
        """ Submit the selected simulations to CADET and update them with
        its output.
        """
        self.project.study.run_simulations(self.project.job_manager, sims=sims)

    def run_simulation_groups(self, group=None):
        """ Submit the selected SimulationGroup to CADET and update its
        simulations with output once run.
        """
        self.project.study.run_simulation_group(self.project.job_manager,
                                                sim_group=group)

    def run_optimizer(self, optimizer):
        """ Submit passed optimizer to run.
        """
        self.project.study.run_optimizer(self.project.job_manager, optimizer)

    def new_optimizer(self):
        """ Create a new optimizer.
        """
        optim = self.project.study.create_new_optimizer()
        if optim is not None:
            self.edit_object_in_central_pane(optim)

    # New plot creation methods -----------------------------------------------

    def new_animation_plot(self):
        from kromatography.ui.tasks.plot_editors import \
            AnimationPlotEditor

        result = build_animation_plot_model(self.project.study)
        if result:
            animation_plot_model, source_sim_uuid = result
            self.edit_object_in_central_pane(animation_plot_model,
                                             factory=AnimationPlotEditor,
                                             uuid_to_map=source_sim_uuid)

    def new_model_calibration_plot(self):
        """ Open a general chromatogram window to compare simulations and
        experiments to each other.
        """
        from kromatography.ui.tasks.plot_editors import ChromatogramPlotEditor

        study = self.project.study
        chromatogram_model = build_chromatogram_model(study)
        self.edit_object_in_central_pane(chromatogram_model,
                                         factory=ChromatogramPlotEditor,
                                         uuid_to_map=study.uuid)

    # Python execution methods ------------------------------------------------

    def request_run_python_script(self):
        """ Prompt the user to select a python script, and run it if dialog
        isn't cancelled.
        """
        from kromatography.tools.python_script_file_selector import \
            PythonScriptFileSelector

        selector = PythonScriptFileSelector()
        # Live modal so that changes to the known_scripts doesn't lead to
        # TraitErrors when the copy object is build and eval-ed in the context.
        ui = selector.edit_traits(kind="livemodal")
        if ui.result:
            self.run_python_script(selector.filepath, selector.code)

    def run_python_script(self, path="", code=""):
        """ Run the content of the python file in-process.

        Parameters
        ----------
        path : str [OPTIONAL]
            Path to the script file. Cannot be empty if the code is empty.

        code : str [OPTIONAL]
            Content of the script file. Cannot be empty if the path is empty.
        """
        from kromatography.tools.python_script_runner import PythonScriptRunner

        if not code:
            if not path:
                msg = "Cannot run any script as neither a path nor code has" \
                      " been provided (path={}, code={}).".format(path, code)
                logger.exception(msg)
                raise ValueError(msg)

            code = open(path).read()

        script = PythonScriptRunner(code=code, task=self, app=self._app,
                                    path=path)
        try:
            output = script.run()
        except Exception as e:
            msg = "Failed to run the script {}: error as {}"
            msg = msg.format(path, e)
            logger.exception(msg)
            error(None, msg)
        else:
            msg = "Script {} ran successfully with the following output:\n\n{}"
            msg = msg.format(path, output)
            information(None, msg)

        logger.debug(msg)

    def request_launch_python_console(self, confirm_on_exit=True):
        """ Launch the qt_console as a separate process.

        TODO: Make this an in-process, in-app terminal.
        """
        import sys
        from subprocess import PIPE, Popen
        from app_common.std_lib.sys_utils import get_bin_folder, IS_WINDOWS

        if IS_WINDOWS:
            # For some reason, the OSX command doesn't work in all installed
            # environments on Windows...
            prefix = sys.prefix
            cmd = [
                join(prefix, "pythonw.exe"),
                join(prefix, "Scripts", "jupyter-qtconsole-script.pyw")
            ]
        else:
            executable = join(get_bin_folder(), "jupyter")
            cmd = [executable, "qtconsole"]

        if not confirm_on_exit:
            cmd.append("--no-confirm-exit")

        try:
            Popen(cmd, stdout=PIPE, stderr=PIPE)
        except Exception as e:
            msg = "Jupyter Qtconsole has failed to launch with error {}"
            msg = msg.format(e)
            logger.debug(msg)

    # Listeners to trigger actions --------------------------------------------

    @on_trait_change('project:study:simulations:plot_request, '
                     'project:study:analysis_tools:simulation_grids:plot_request, '  # noqa
                     'project:study:analysis_tools:simulation_grids:simulations:plot_request, '  # noqa
                     'project:study:analysis_tools:optimizations:optimal_simulations:plot_request')  # noqa
    def trigger_plot_simulation(self, obj, name, new):
        """ Open chromatogram for simulation/SimulationGroup that was requested
        """
        from kromatography.ui.tasks.plot_editors import \
            ChromatogramPlotEditor
        from kromatography.model.simulation import Simulation

        with action_monitoring("Plotting Simulation/Simulation group"):
            if isinstance(obj, Simulation):
                kw = {"sims": [obj]}
            else:
                kw = {"sim_group": obj}

            chrome_model = build_chromatogram_model(self.project.study, **kw)

        self.edit_object_in_central_pane(chrome_model,
                                         factory=ChromatogramPlotEditor,
                                         uuid_to_map=obj.uuid)

    @on_trait_change('project:study:simulations:cadet_request')
    def trigger_run_simulation(self, obj, name, new):
        with action_monitoring("Running CADET on simulation"):
            self.run_simulations([obj])

    @on_trait_change('project:study:analysis_tools:simulation_grids:'
                     'cadet_request, '
                     'project:study:analysis_tools:monte_carlo_explorations:'
                     'cadet_request')
    def trigger_run_simulation_group(self, obj, name, new):
        with action_monitoring("Running CADET on simulation group"):
            self.run_simulation_groups(obj)

    @on_trait_change('project:study:analysis_tools:optimizations:'
                     'cadet_request')
    def trigger_run_optimizer(self, obj, name, new):
        with action_monitoring("Running CADET on optimizer"):
            self.run_optimizer(obj)

    @on_trait_change("project:deleted_objects[]")
    def update_central_pane_tabs(self, obj, attr, _, deleted_obj_info):
        for info in deleted_obj_info:
            self.close_central_pane_for_object(info)

    # app level requests ------------------------------------------------------

    def open_proj_file(self):
        self._app.request_project_from_file()

    def open_recent_projects(self):
        self._app.open_recent_project()

    # Plot control methods ----------------------------------------------------

    def _get__view_central_pane(self):
        no_active_view = (self.central_pane is None or
                          self.central_pane.active_editor is None)
        if no_active_view:
            return None

        return self.central_pane.active_editor.traits_ui.context['object']

    def _get__central_pane_is_plot(self):
        if self._view_central_pane is None:
            return False

        return isinstance(self._view_central_pane, ChromatogramModelView)

    def show_hide_legend(self):
        plot_view = self._view_central_pane
        plot_view._show_legend = not plot_view._show_legend

    def show_hide_plot_controls(self):
        plot_view = self._view_central_pane
        plot_view._show_control = not plot_view._show_control

    # Trait listeners ---------------------------------------------------------

    @on_trait_change('project_filepath, project.study.exp_study_filepath')
    def update_name(self):
        self.name = self._build_name()
        if self.window is not None:
            self.window.title = self.name

    # traits defaults ---------------------------------------------------------

    def _name_default(self):
        return self._build_name()

    def _tool_bars_default(self):
        # No accelerators here: they are added to menu entries

        tool_bars = [
            # General action toolbar
            SToolBar(
                TaskAction(name="Open recent projects",
                           method="open_recent_projects",
                           tooltip="Open recent project(s)",
                           image=ImageResource("document-open-recent.png")),
                TaskAction(name='Open project file',
                           method='open_proj_file',
                           tooltip='Open project file',
                           image=ImageResource('document-open')),
                TaskAction(name='Save current project',
                           method='save',
                           tooltip='Save current project',
                           image=ImageResource('document-save')),
                TaskAction(name='Save user data',
                           method='save_user_ds',
                           tooltip='Save user data',
                           image=ImageResource('drive-harddisk')),
                image_size=ICON_SIZE, show_tool_names=False),

            SToolBar(
                TaskAction(name='New simulation(s) from experiment(s)',
                           method='new_simulation_from_experiments',
                           tooltip='New simulation(s) from experiment(s)',
                           image=ImageResource('kchart')),
                TaskAction(name='Run simulation(s)',
                           method='run_simulations',
                           tooltip='Run simulation(s)',
                           enabled_name='simulations_exist',
                           image=ImageResource('arrow-right')),
                TaskAction(name='Run simulation grid(s)',
                           tooltip='Run simulation grid(s)',
                           method='run_simulation_groups',
                           enabled_name='simulation_groups_exist',
                           image=ImageResource('arrow-right-double')),
                image_size=ICON_SIZE, show_tool_names=False),

            # Plot action toolbar
            SToolBar(
                TaskAction(name='Plot all simulations',
                           method='new_model_calibration_plot',
                           tooltip='Plot all simulations',
                           image=ImageResource('office-chart-line')),
                TaskAction(name='Show/hide plot controls',
                           method='show_hide_plot_controls',
                           tooltip='Show/hide plot controls',
                           image=ImageResource('format-list-unordered'),
                           enabled_name='_central_pane_is_plot'),
                TaskAction(name='Show/hide plot legend',
                           method='show_hide_legend',
                           tooltip='Show/hide plot legend',
                           image=ImageResource('preferences-activities'),
                           enabled_name='_central_pane_is_plot'),
                image_size=ICON_SIZE, show_tool_names=False)
        ]
        return tool_bars

    def _menu_bar_default(self):
        menu_bar = SMenuBar(
            SMenu(
                SMenu(
                    SGroup(
                        TaskAction(name='New Simulation',
                                   method='new_simulation_from_datasource',
                                   image=ImageResource('office-chart-pie')),
                        TaskAction(name='New Simulation from Experiment',
                                   method='new_simulation_from_experiments',
                                   image=ImageResource('kchart'),
                                   accelerator='Ctrl+N'),
                        id='NewSimulationGroup', name='NewSimulationGroup',
                    ),
                    id='NewMenu', name='&New Simulation'
                ),
                SGroup(
                    TaskAction(name='Save Project',
                               accelerator='Ctrl+S',
                               method='save',
                               image=ImageResource('document-save')),
                    TaskAction(name='Save Project As...',
                               accelerator='Ctrl+Shift+S',
                               method='save_request',
                               image=ImageResource('document-save-as')),
                    id='SaveGroup', name='SaveGroup'),
                SGroup(
                    TaskAction(name='Save User Data',
                               method='save_user_ds',
                               image=ImageResource('drive-harddisk')),
                    TaskAction(name='Export User Data As...',
                               method='request_export_user_ds',
                               image=ImageResource('document-import')),
                    id='SaveUserDataGroup', name='SaveUserDataGroup',
                ),
                SGroup(
                    TaskWindowAction(
                        name='Close',
                        accelerator='Ctrl+W',
                        method='close',
                    ),
                    id='CloseGroup', name='CloseGroup',
                ),
                id='File', name='&File'),
            SMenu(
                id='Edit', name='&Edit'),
            SMenu(DockPaneToggleGroup(),
                  id='View', name='&View'),
            SMenu(
                SGroup(
                    TaskAction(name='Parameter Explorer',
                               accelerator='Ctrl+Shift+N',
                               method='new_simulation_grid',
                               enabled_name='simulations_exist'),
                    TaskAction(name='Parameter Optimizer',
                               accelerator='Ctrl+Shift+M',
                               method='new_optimizer',
                               enabled_name='experiments_and_sim_exist'),
                    id='ParamExplorationGroup', name='ParamExplorationGroup',
                ),
                SGroup(
                    TaskAction(name='Run Simulations',
                               method='run_simulations',
                               accelerator='Ctrl+R',
                               enabled_name='simulations_exist',
                               image=ImageResource('arrow-right')),
                    TaskAction(name='Run Simulation Group',
                               method='run_simulation_groups',
                               accelerator='Ctrl+Shift+R',
                               enabled_name='simulation_groups_exist',
                               image=ImageResource('arrow-right-double')),
                    id='RunSimulationGroup', name='RunSimulationGroup',
                ),
                SGroup(
                    TaskAction(name='Plot Chomatogram(s)',
                               method='new_model_calibration_plot',
                               accelerator='Ctrl+P',
                               image=ImageResource('office-chart-line')),
                    TaskAction(name='Particle data animation',
                               method='new_animation_plot'),
                    id='PlotsGroup', name='PlotsGroup',
                ),
                SGroup(
                    TaskAction(name=STRIP_TOOL_NAME,
                               method='open_strip_fraction_editor',
                               enabled_name='_strip_component_exist'),
                    id='ConfigurationGroup', name='ConfigurationGroup',
                ),
                SGroup(
                    TaskAction(name='Custom Python script...',
                               accelerator='Ctrl+I',
                               method='request_run_python_script',
                               tooltip='Modify the current project with '
                                       'custom script.',
                               image=ImageResource('text-x-python')),
                    TaskAction(name='Interactive Python console...',
                               accelerator='Ctrl+J',
                               tooltip="(Jupyter) Python console to "
                                       "interactively explore Reveal's code "
                                       "and develop new tools/scripts.",
                               method='request_launch_python_console',
                               image=ImageResource('ipython_icon')),
                    id='RunPythonGroup', name='RunPythonGroup'
                ),
                id='Tools', name='&Tools',
            ),
            SMenu(
                id='Help', name='&Help'
            )
        )
        return menu_bar

    def _default_layout_default(self):
        """ Control where to place each dock panes.
        """
        bottom_height = 270

        return TaskLayout(
            id=self.id,
            left=Splitter(PaneItem('krom.data_source_pane'),
                          PaneItem('krom.study_data_pane'),
                          orientation='vertical'),
            bottom=Splitter(PaneItem('krom.performance_param_pane',
                                     height=bottom_height),
                            PaneItem('common.job_manager_pane',
                                     height=bottom_height, width=250),
                            orientation='horizontal')
        )

    def _undo_manager_default(self):
        from apptools.undo.api import UndoManager

        undo_manager = UndoManager()
        return undo_manager

    def _command_stack_default(self):
        from app_common.apptools.undo.single_clean_state_command_stack import\
            SingleCleanStateCommandStack

        command_stack = SingleCleanStateCommandStack(
            undo_manager=self.undo_manager
        )
        return command_stack

    # traits property getters/setters -----------------------------------------

    def _get_experiments_exist(self):
        return len(self.project.study.experiments) > 0

    def _get_simulations_exist(self):
        return len(self.project.study.simulations) > 0

    def _get_experiments_and_sim_exist(self):
        return self.experiments_exist and self.simulations_exist

    def _get_simulation_groups_exist(self):
        return len(self.project.study.analysis_tools.simulation_grids) > 0

    def _get__strip_component_exist(self):
        return self.project.study.product_contains_strip

    # -------------------------------------------------------------------------
    # 'KromatographyTask' private interface methods
    # -------------------------------------------------------------------------

    def _build_name(self):
        title = APP_FAMILY + " " + APP_TITLE
        if self.project_filepath:
            title += ": {}".format(self.project_filepath)

        study_path_exists = (self.project and self.project.study and
                             self.project.study.exp_study_filepath)
        if study_path_exists:
            basename = os.path.basename(self.project.study.exp_study_filepath)
            title += " ({})".format(basename)
        return title


def is_task_blank(task):
    """ Has the task provided been modified in any way by the GUI?

    We check if the project_filepath has been set, if new tabs have been
    opened, and if the task's components has been modified in any way.

    NOTE: this is not bullet proof to be used in a scripting layers, as there
    are many ways to modify a task without this function detecting it. This is
    to be used to detect any changes that a user can make to a task USING THE
    APPLICATION's GRAPHICAL INTERFACE.

    Parameters
    ----------
    task : KromatographyTask
        Task to analyze.
    """
    if task.project_filepath:
        return False

    window = task.window
    if window is not None and len(window.central_pane.editors) > 1:
        return False

    if task.project and not task.project.is_blank:
        return False

    return True
