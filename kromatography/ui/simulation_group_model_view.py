import logging
import pandas as pd
from os.path import splitext

from traits.api import Bool, Button, DelegatesTo, Enum, Instance, List, \
    Property
from traitsui.api import HGroup, Item, ModelView, Spring, VGroup, View
from traitsui.ui_editors.data_frame_editor import DataFrameEditor

from kromatography.utils.traitsui_utils import KromView
from kromatography.model.simulation_group import MULTI_SIM_RUNNER_CREATED, \
    SIM_COL_NAME, SimulationGroup
from kromatography.ui.adapters.df_with_outputs_df_editor_adapter import \
    DataFrameWithColumnOutputsAdapter

logger = logging.getLogger(__name__)

INVERTED_SUFFIX = " (inversed)"

GROUP_NAME_WIDTH = 300


class SimulationGroupView(ModelView):
    """ View for a SimulationGroup object.
    """
    #: SimulationGroup to display
    model = Instance(SimulationGroup)

    #: Button to export the data to CSV
    export_data_to_csv_button = Button("Export Data To CSV")

    #: Button to open the DataFrame analyzer tool
    analyze_button = Button("Analyze Data")

    #: Button to launch a run of all simulations
    run_button = Button("Run Simulation Group")

    can_run = Property(Bool, depends_on="model.run_status")

    has_run = DelegatesTo("model")

    sort_by = Enum(values='sort_by_possible')

    sort_by_possible = List

    def traits_view(self):
        group_data = self.model.group_data
        output_num = len(self.model.perf_params)
        sim_group_df_editor = build_df_editor_grid_data(group_data, output_num)

        view = View(
            VGroup(
                HGroup(
                    Item('model.name', width=GROUP_NAME_WIDTH),
                    Spring(),
                    Item('model.center_point_simulation_name',
                         label="Source Simulation", style='readonly'),
                    Spring(),
                    Item('model.size', style='readonly',
                         tooltip="Number of simulations in the group"),
                    Spring(),
                    Item('model.type', style='readonly'),
                ),
                VGroup(
                    Item('sort_by', label="Sort table by"),
                    Item('model.group_data', editor=sim_group_df_editor,
                         show_label=False),
                    label="Output data", show_border=True
                ),
                HGroup(
                    Item('run_button', show_label=False,
                         enabled_when='can_run'),
                    Spring(),
                    Item('model.run_status', style="readonly", label="Status"),
                    Item('model.percent_run', style='readonly',
                         label="Completion"),
                    Spring(),
                    Item('analyze_button', show_label=False),
                    Item('export_data_to_csv_button', show_label=False),
                ),
            ),
            resizable=True,
        )

        return view

    # Public interface methods ------------------------------------------------

    def do_export_data(self, file_path):
        if splitext(file_path)[1] != ".csv":
            file_path += ".csv"

        self.model.group_data.to_csv(file_path)
        msg = "Saved data from SimulationGroup {} to {}"
        msg = msg.format(self.model.name, file_path)
        logger.debug(msg)

    # Traits listeners --------------------------------------------------------

    def _export_data_to_csv_button_fired(self):
        from kromatography.utils.extra_file_dialogs import \
            to_csv_file_requester

        path = to_csv_file_requester()
        if path is not None:
            self.do_export_data(path)

    def _run_button_fired(self):
        self.model.cadet_request = True

    def _analyze_button_fired(self):
        from app_common.pandas_tools.dataframe_analyzer_model_view import \
            DataFrameAnalyzer, DataFrameAnalyzerView

        model = DataFrameAnalyzer(source_df=self.model.group_data)
        view = DataFrameAnalyzerView(model=model, include_plotter=True,
                                     fonts="Courrier 11", view_klass=KromView)
        view.edit_traits(kind="livemodal")

    def _sort_by_changed(self, new):
        """ Sort the model's dataframe based on request.
        """
        data = self.model.group_data
        if not isinstance(data, pd.DataFrame) or len(data) == 0:
            return

        if new.endswith(INVERTED_SUFFIX):
            col_name = new[:-len(INVERTED_SUFFIX)]
            ascending = False
        else:
            col_name = new
            ascending = True

        self.model.group_data = data.sort_values(by=col_name,
                                                 ascending=ascending)

    # Traits property getters/setters -----------------------------------------

    def _get_can_run(self):
        return self.model.run_status == MULTI_SIM_RUNNER_CREATED

    # Traits initialization methods -------------------------------------------

    def _sort_by_possible_default(self):
        """Support sorting the DF by any of its column including in reverse
        order.
        """
        all_cols = list(self.model.group_data.columns)
        possible = []
        for col_name in all_cols:
            possible.append(col_name)
            possible.append(col_name + INVERTED_SUFFIX)

        return possible


def build_df_editor_grid_data(group_data, num_outputs):
    """ Build a dataframe editor for grid data.
    """
    adapter = DataFrameWithColumnOutputsAdapter(num_outputs=num_outputs,
                                                df_attr_name="group_data")
    formats = {SIM_COL_NAME: "%s"}
    for key in group_data:
        if SimulationGroup.col_is_output(key):
            formats[key] = "%.3f"
        elif key != SIM_COL_NAME:
            formats[key] = "%g"

    # Because of the way the DataFrame editor is implemented,
    # the `model.` prefix should not be passed for the update name:
    sim_group_df_editor = DataFrameEditor(
        adapter=adapter, formats=formats, update="group_data_updated_event"
    )
    return sim_group_df_editor
