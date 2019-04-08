import logging

from traits.api import Bool, HasStrictTraits, Instance, Property, Str
from traitsui.api import Action, CancelButton, Handler, HGroup, \
    InstanceEditor, Item, Label, OKCancelButtons, RangeEditor, Tabbed, VGroup

from app_common.traitsui.common_traitsui_groups import make_window_title_group

from kromatography.utils.traitsui_utils import KromView
from kromatography.utils.preferences import AppPreferenceGroup, \
    FilePreferenceGroup, RevealChromatographyPreferences, \
    SolverPreferenceGroup, UIPreferenceGroup
from kromatography.utils.app_utils import get_preference_file
from kromatography.solve.slurm_cadet_executor import check_slurm_installed

logger = logging.getLogger(__name__)

save_button = Action(name='Save', action="do_save_preferences")

factory_reset_button = Action(name='Factory Reset',
                              action="do_reset_preferences")

spinner_editor = RangeEditor(low=1, high=100, mode='spinner')


class AppPreferencesView(HasStrictTraits):
    model = Instance(AppPreferenceGroup)

    view = KromView(
        VGroup(
            Item("object.model.user_ds_folder", label="User data storage"),
            Item("object.model.python_script_folder",
                 label="Python scripts storage"),
        ),
    )


class FilePreferencesView(HasStrictTraits):
    model = Instance(FilePreferenceGroup)

    view = KromView(
        VGroup(
            HGroup(
                Item("object.model.max_recent_files", editor=spinner_editor,
                     label="Num. Recent Projects (requires restart)",
                     tooltip="Maximum number of recent project paths to "
                             "remember."),
            ),
            HGroup(
                Item("object.model.exp_importer_mass_threshold",
                     label="Experiment import mass balance threshold",
                     tooltip="Max relative mass difference to warn during "
                             "experiment import"),
            ),
        ),
    )


class UIPreferencesView(HasStrictTraits):
    model = Instance(UIPreferenceGroup)

    view = KromView(
        VGroup(
            VGroup(
                Label("(Requires restart)"),
            ),
            Item("object.model.confirm_on_window_close",
                 label="Confirm on project close?"),
            Item("object.model.auto_close_empty_windows_on_open",
                 label="Auto close empty projects?",
                 tooltip="Auto close empty projects when opening a new one?"),
            Item("object.model.app_width", label="Default app window width"),
            Item("object.model.app_height", label="Default app window height"),
        )
    )


class SolverPreferencesView(HasStrictTraits):
    model = Instance(SolverPreferenceGroup)

    def traits_view(self):
        # Build the view such that the SLURM stuff isn't visible if not
        # available on the machine
        elements = [
            VGroup(
                Item("object.model.solver_binary_path",
                     label="Cadet executable"),
                Item("object.model.input_file_location",
                     label="CADET input folder"),
                Item("object.model.executor_num_worker", editor=spinner_editor,
                     label="Cadet num. workers (requires restart)"),
                Item("object.model.cadet_num_threads", editor=spinner_editor,
                     label="Cadet num. threads"),
                Item('object.model.auto_delete_solver_files_on_exit'),
            )
        ]
        executable = self.model.slurm_binary
        if check_slurm_installed(executable=executable):
            elements[0].label = "General"
            elements.append(
                VGroup(
                    Item("object.model.use_slurm_scheduler",
                         tooltip="Submit solver run to SLURM scheduler"),
                    Item("object.model.slurm_binary",
                         visible_when="object.model.use_slurm_scheduler",
                         width=300, tooltip="Command to submit SLURM jobs"),
                    Item("object.model.slurm_partition",
                         visible_when="object.model.use_slurm_scheduler",
                         width=300,
                         tooltip="SLURM scheduler partition to submit jobs."),
                    Item("object.model.slurm_job_name",
                         visible_when="object.model.use_slurm_scheduler",
                         width=300, tooltip="SLURM scheduler job name."),
                    label="SLURM scheduler",
                )
            )

            elements = [Tabbed(*elements)]

        return KromView(*elements)


class RevealChromatographyPreferenceViewHandler(Handler):
    """ Handler for the view to control the behavior of the custom buttons.

    FIXME: Move to app_common since fully general?
    """
    def do_save_preferences(self, info):
        prefs = info.object.model
        prefs.to_preference_file()
        prefs.dirty = False
        if not info.object.standalone:
            info.ui.dispose()

    def do_reset_preferences(self, info):
        info.object.factory_reset()

    def object_dirty_changed(self, info):
        if info.initialized:
            if info.object.dirty:
                info.ui.title += "*"
            else:
                info.ui.title = info.ui.title[:-1]


class RevealChromatographyPreferenceView(HasStrictTraits):
    """ View to edit an instance of RevealChromatographyPreferences.
    """
    model = Instance(RevealChromatographyPreferences)

    app_pref_view = Property(Instance(AppPreferencesView), depends_on="model")

    file_pref_view = Property(Instance(FilePreferencesView),
                              depends_on="model")

    ui_prefs_view = Property(Instance(UIPreferencesView), depends_on="model")

    solver_prefs_view = Property(Instance(SolverPreferencesView),
                                 depends_on="model")

    instructions = Str

    dirty = Property(Bool, depends_on="model:dirty")

    standalone = Bool(False)

    def _get_dirty(self):
        return self.model.dirty

    def default_traits_view(self):
        if self.standalone:
            std_buttons = OKCancelButtons
        else:
            std_buttons = [CancelButton]

        view = KromView(
            VGroup(
                make_window_title_group(title="User Preferences",
                                        include_blank_spaces=False),
                Item("instructions", style="readonly", resizable=True,
                     show_label=False),
                Tabbed(
                    Item("ui_prefs_view", editor=InstanceEditor(),
                         style="custom", label="Interface", show_label=False),
                    Item("file_pref_view", editor=InstanceEditor(),
                         style="custom", label="File loading",
                         show_label=False),
                    Item("app_pref_view", editor=InstanceEditor(),
                         style="custom",
                         # even though the group's label is not shown in the
                         # UI, it needs to be set to set the tab name:
                         label="Application", show_label=False),
                    Item("solver_prefs_view",
                         editor=InstanceEditor(), style="custom",
                         label="Solver", show_label=False),
                ),
            ),
            buttons=[save_button, factory_reset_button] + std_buttons,
            handler=RevealChromatographyPreferenceViewHandler(),
            default_button=save_button,
            width=700,
            title="Edit Reveal Chromatography Preferences",
        )
        return view

    def _get_app_pref_view(self):
        return AppPreferencesView(model=self.model.app_preferences)

    def _get_ui_prefs_view(self):
        return UIPreferencesView(model=self.model.ui_preferences)

    def _get_solver_prefs_view(self):
        return SolverPreferencesView(model=self.model.solver_preferences)

    def _get_file_pref_view(self):
        return FilePreferencesView(model=self.model.file_preferences)

    def factory_reset(self):
        self.model = RevealChromatographyPreferences(
            preference_filepath=get_preference_file()
        )

    def _instructions_default(self):
        return "Most preferences will take effect as soon as the preferences" \
               " are saved. No need to restart the application unless " \
               "specified."


if __name__ == '__main__':
    from kromatography.utils.app_utils import get_preferences

    prefs = get_preferences()
    view = RevealChromatographyPreferenceView(model=prefs)
    view.configure_traits()
