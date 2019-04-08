from unittest import skipIf, TestCase
from os.path import isfile
from contextlib import contextmanager

from pyface.tasks.action.schema import GroupSchema
from pyface.tasks.action.task_action import TaskWindowAction
from pyface.ui.qt4.util.gui_test_assistant import GuiTestAssistant

from app_common.apptools.testing_utils import temp_fname
from app_common.pyface.monitored_actions import MonitoredTaskAction
from app_common.std_lib.filepath_utils import attempt_remove_file

from kromatography.app.krom_app import KromatographyApp
from kromatography.ui.tasks.kromatography_task import is_task_blank, \
    KromatographyTask, KROM_EXTENSION
from kromatography.model.tests.sample_data_factories import make_sample_study
from kromatography.model.factories.simulation import \
    build_simulation_from_experiment
from kromatography.model.tests.sample_data_factories import \
    make_sample_simulation_group
from kromatography.model.factories.job_manager import create_start_job_manager
from kromatography.model.kromatography_project import KromatographyProject
from kromatography.model.study import make_blank_study
from kromatography.model.data_source import SimpleDataSource
from kromatography.model.simulation_group import SimulationGroup
from kromatography.utils.app_utils import IS_WINDOWS
from kromatography.utils.preferences import reset_preferences
from kromatography.model.tests.sample_data_factories import make_sample_app

APP_START_TIME = 1200

APP_WINDOW_METHODS = ["close"]


class TestKromatographyTaskMenu(TestCase):

    def setUp(self):
        self.task = KromatographyTask()

    def test_menu_actions(self):
        entries = [schema.name for schema in self.task.menu_bar.items]
        expected = {"&File", "&Edit", "&View", "&Tools", "&Help"}
        self.assertEqual(set(entries), expected)

    def test_file_menu_actions(self):
        groups = self.get_menu_group_names_from("File")
        expected_groups = {'&New Simulation', 'SaveGroup', 'SaveUserDataGroup',
                           'CloseGroup'}
        self.assertEqual(set(groups), expected_groups)

    def test_tools_menu_actions(self):
        groups = self.get_menu_group_names_from("Tools")
        expected_groups = {'RunSimulationGroup', 'ParamExplorationGroup',
                           'PlotsGroup', 'RunPythonGroup', 'ConfigurationGroup'
                           }
        self.assertEqual(set(groups), expected_groups)

    def test_actions_are_monitored(self):
        menu_entries = [schema.name for schema in self.task.menu_bar.items]
        for menu_entry in menu_entries:
            groups = self.get_menu_groups_from(menu_entry[1:])
            for grp in groups:
                for element in grp.items:
                    if isinstance(element, GroupSchema):
                        for action in element.items:
                            self.assertIsInstance(action, MonitoredTaskAction)
                            self.assertTrue(hasattr(self.task, action.method))
                    else:
                        # Ignoring the close action since that's monitored by
                        # the Application object.
                        self.assertIsInstance(element, (MonitoredTaskAction,
                                                        TaskWindowAction))
                        if element.method not in APP_WINDOW_METHODS:
                            self.assertTrue(hasattr(self.task, element.method))

    def test_toolbars(self):
        self.assertEqual(len(self.task.tool_bars), 3)

        toolbar = self.task.tool_bars[0]
        expected = [u'Open recent projects', u'Open project file',
                    u'Save current project', u'Save user data']
        self.assertEqual([item.name for item in toolbar.items], expected)

        toolbar = self.task.tool_bars[1]
        expected = [u'New simulation(s) from experiment(s)',
                    u'Run simulation(s)', u'Run simulation grid(s)']
        self.assertEqual([item.name for item in toolbar.items], expected)

        toolbar = self.task.tool_bars[2]
        expected = [u'Plot all simulations', u'Show/hide plot controls',
                    u'Show/hide plot legend']
        self.assertEqual([item.name for item in toolbar.items], expected)

        for toolbar in self.task.tool_bars:
            for item in toolbar.items:
                self.assertIsInstance(item, MonitoredTaskAction)
                self.assertTrue(hasattr(self.task, item.method))

    # Helper methods ----------------------------------------------------------

    def get_menu_groups_from(self, menu_entry):
        if not menu_entry.startswith("&"):
            menu_entry = "&" + menu_entry
        menu = [schema for schema in self.task.menu_bar.items
                if schema.name == menu_entry][0]
        return menu.items

    def get_menu_group_names_from(self, menu_entry):
        groups = self.get_menu_groups_from(menu_entry)
        return [grp.name for grp in groups]


class TestKromatographyTaskRunRequest(GuiTestAssistant, TestCase):

    @classmethod
    def setUpClass(cls):
        cls.job_manager = create_start_job_manager(max_workers=2)

    @classmethod
    def tearDownClass(cls):
        cls.job_manager.shutdown()

    def setUp(self):
        super(TestKromatographyTaskRunRequest, self).setUp()
        self.datasource = SimpleDataSource()
        self.task = KromatographyTask()

        self.study2 = make_sample_study(num_exp=1)
        project_data = dict(study=self.study2, datasource=self.datasource,
                            job_manager=self.job_manager)
        project = KromatographyProject(**project_data)
        self.task2 = KromatographyTask(project=project)

    def test_simulations_exist(self):
        task = self.task2
        study = self.study2
        # The properties are correct
        self.assertFalse(task.simulations_exist)
        # The menu entry disabled
        sim_group_menu = get_run_simulation_group(task)
        self.assertFalse(sim_group_menu.items[0].enabled)

        sim = build_sim_from_study(study)
        study.simulations.append(sim)
        self.assertTrue(task.simulations_exist)

    def test_simulation_groups_exist(self):
        task = self.task2
        study = self.study2
        # The properties are correct
        self.assertFalse(task.simulation_groups_exist)
        sim_group_menu = get_run_simulation_group(task)
        # The menu entry is disabled
        self.assertFalse(sim_group_menu.items[1].enabled)

        sim = build_sim_from_study(study)
        sim_gp = SimulationGroup(center_point_simulation=sim, name="Group0")
        study.analysis_tools.simulation_grids.append(sim_gp)
        self.assertTrue(task.simulation_groups_exist)

    def test_simulation_run_request(self):
        task = self.task2
        study = self.study2
        job_manager = task.project.job_manager
        sim = build_sim_from_study(study)
        study.simulations.append(sim)

        with self.assertTraitChanges(job_manager, "_pending_jobs[]", 1):
            sim.cadet_request = True

    def test_simulation_group_run_request(self):
        task = self.task2
        study = self.study2
        job_manager = task.project.job_manager
        sim = build_sim_from_study(study)
        group = make_sample_simulation_group(cp=sim)
        study.analysis_tools.simulation_grids.append(group)

        with self.assertTraitChanges(job_manager, "_pending_jobs[]", 1):
            group.cadet_request = True

    def test_update_name_when_update_path(self):
        with self.assertTaskNameChanges(self.task):
            self.task.project_filepath = "x"

        with self.assertTaskNameChanges(self.task2):
            self.task2.project_filepath = "x"

        with self.assertTaskNameChanges(self.task2):
            self.task2.project.study.exp_study_filepath = "x"

    # Helper methods ----------------------------------------------------------

    @contextmanager
    def assertTaskNameChanges(self, task):
        initial_name = task.name
        yield
        new_name = task.name
        self.assertNotEqual(initial_name, new_name)


class TestKromatographyTasPlotRequest(GuiTestAssistant, TestCase):

    def setUp(self):
        GuiTestAssistant.setUp(self)
        self.study2 = make_sample_study(num_exp=1)

    @skipIf(IS_WINDOWS, "Skipping because failing on Jenkins")
    def test_simulation_plot_request(self):
        """Test that plot requests on simulations, simulation groups or
        simulations inside a group trigger an editor of the central pane to
        open.
        """
        study = self.study2
        sim = build_sim_from_study(study)
        study.simulations.append(sim)
        self.assertPlotRequestTriggersCentralPane(study, sim)

    @skipIf(IS_WINDOWS, "Skipping because failing on Jenkins")
    def test_sim_group_plot_request(self):
        study = self.study2
        sim = build_sim_from_study(study)
        group = make_sample_simulation_group(cp=sim)
        study.analysis_tools.simulation_grids.append(group)
        self.assertPlotRequestTriggersCentralPane(study, group)

    @skipIf(IS_WINDOWS, "Skipping because failing on Jenkins")
    def test_sim_in_sim_group_plot_request(self):
        study = self.study2
        sim = build_sim_from_study(study)
        group = make_sample_simulation_group(cp=sim)
        study.analysis_tools.simulation_grids.append(group)
        group.initialize_simulations()
        sim2 = group.simulations[0]
        self.assertPlotRequestTriggersCentralPane(study, sim2)

    # Helper methods ----------------------------------------------------------

    def assertPlotRequestTriggersCentralPane(self, study, sim_like_obj):
        """ Assert that plot_request invoked on a simulation-like object
        triggers a change in the app's central pane if the object is attached
        to the study the application is built around.

        Parameters
        ----------
        study : Study
            Study the object belongs to.

        sim_like_obj : Simulation or SimulationGroup
            Simulation-like object whose plot_request event is triggered and
            tested.
        """
        exceptions = []
        assertions = []

        def assert_respond_plot_requests(app, obj):
            window = app.windows_created[0]
            central_pane = window.central_pane
            # Try/except block to make sure that the gui event loop stops no
            # matter what.
            try:
                with self.assertTraitChanges(central_pane, "editors[]", 1):
                    obj.plot_request = True

                # Make sure the simulation's uuid was stored in the the editor
                # map:
                task = window.active_task
                self.assertIn(obj.uuid, task.central_pane_editor_map)

                # Finally make sure that if the simulation like object is
                # removed, the central pane editor is removed.
                analysis_tools = study.analysis_tools
                if obj in study.simulations:
                    with self.assertTraitChanges(central_pane, "editors[]", 1):
                        study.simulations.remove(obj)
                elif obj in study.analysis_tools.simulation_grids:
                    with self.assertTraitChanges(central_pane, "editors[]", 1):
                        analysis_tools.simulation_grids.remove(obj)
                elif obj in analysis_tools.simulation_grids[0].simulations:
                    with self.assertTraitChanges(central_pane, "editors[]", 1):
                        first_grid = analysis_tools.simulation_grids[0]
                        first_grid.simulations.remove(obj)

                self.assertNotIn(obj.uuid, task.central_pane_editor_map)

            except AssertionError as e:
                assertions.append(e)
            except Exception as e:
                exceptions.append(e)
            finally:
                self.gui.stop_event_loop()

        # We need to create an application around the task/study so that
        # windows and central panes are created.
        reset_preferences()
        app = KromatographyApp(initial_studies=[study],
                               splash_screen_duration=0)
        self.gui.invoke_after(APP_START_TIME, assert_respond_plot_requests,
                              app, sim_like_obj)
        app.run()

        # This will only run once gui.stop_event_loop is called.
        self.assertEqual(assertions, [])
        if exceptions:
            raise exceptions[0]


class TestKromatographyTaskSaveProject(TestCase):
    def setUp(self):
        self.datasource = SimpleDataSource()
        self.task = KromatographyTask()

    def test_save_task(self):
        filename = "testing_tempfile_kromatography" + KROM_EXTENSION
        task = self.task
        with temp_fname(filename):
            task.save_project_as(filename)
            self.assertTrue(isfile(filename))

    def test_save_task_wrong_ext(self):
        filename_wrong_ext = "testing_tempfile_kromatography2.WRONG_EXT"
        task = self.task

        with temp_fname(filename_wrong_ext):
            task.save_project_as(filename_wrong_ext)
            self.assertFalse(isfile(filename_wrong_ext))
            correct_file = filename_wrong_ext + KROM_EXTENSION
            self.assertTrue(isfile(correct_file))
            attempt_remove_file(correct_file)

    def test_save_task_no_ext(self):
        filename_no_ext = "testing_tempfile_kromatography3"
        task = self.task

        with temp_fname(filename_no_ext):
            task.save_project_as(filename_no_ext)
            self.assertFalse(isfile(filename_no_ext))
            correct_file = filename_no_ext + KROM_EXTENSION
            self.assertTrue(isfile(correct_file))
            attempt_remove_file(correct_file)


class TestIsTaskBlank(TestCase):
    """ Test is_task_blank function. Exercise changing everything that is not
    covered by the is_blank study attribute.
    """
    def setUp(self):
        self.datasource = SimpleDataSource()
        proj_data = dict(study=make_blank_study(), datasource=self.datasource)
        project = KromatographyProject(**proj_data)
        self.task = KromatographyTask(project=project)

        self.study2 = make_sample_study(num_exp=1)
        proj_data = dict(study=self.study2, datasource=self.datasource)
        project = KromatographyProject(**proj_data)
        self.task2 = KromatographyTask(project=project)

    def test_unmodified_task(self):
        self.assertTrue(is_task_blank(self.task))
        self.assertFalse(is_task_blank(self.task2))

    def test_add_experiment(self):
        study = self.task.project.study
        study.experiments.append(self.study2.experiments[0])
        self.assertFalse(is_task_blank(self.task))

    def test_add_sim(self):
        from kromatography.model.tests.sample_data_factories import \
            make_sample_simulation

        study = self.study2
        sim = make_sample_simulation()
        study.simulations.append(sim)
        self.assertFalse(is_task_blank(self.task2))

    def test_modify_product(self):
        study = self.task.project.study
        study.product.name = "Prod001"
        self.assertFalse(is_task_blank(self.task))

    def test_append_to_study_ds(self):
        from kromatography.model.tests.sample_data_factories import \
            make_sample_binding_model

        mod = make_sample_binding_model()
        self.study2.study_datasource.binding_models.append(mod)
        self.assertFalse(is_task_blank(self.task2))


def get_run_simulation_group(task):
    """ Collect the Run Simulation Group entry in the Tools menu.

    Parameters
    ----------
    task : KromatographyTask
        Task to extract the menu structure from.

    Returns
    -------
    Menu schema with the run simulation tools.
    """
    tools_schema = [schema for schema in task.menu_bar.items
                    if schema.name == "&Tools"][0]
    sim_group_menu = tools_schema.items[1]
    assert sim_group_menu.name == 'RunSimulationGroup'
    return sim_group_menu


def build_sim_from_study(study, exp_idx=0):
    sim = build_simulation_from_experiment(study.experiments[exp_idx],
                                           fstep='whatever name',
                                           lstep='Gradient Elution')
    return sim
