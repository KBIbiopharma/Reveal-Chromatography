import logging
import os
import pandas as pd

from traits.api import Button, Enum, Instance, List
from traitsui.api import HGroup, Item, ListStrEditor, ModelView, RangeEditor, \
    Spring, VGroup, View
from traitsui.ui_editors.data_frame_editor import DataFrameEditor

from kromatography.utils.string_definitions import MULTI_SIM_RUNNER_CREATED
from kromatography.compute.brute_force_optimizer import BruteForceOptimizer
from kromatography.ui.adapters.df_with_outputs_df_editor_adapter import \
    DataFrameWithColumnOutputsAdapter
from kromatography.compute.experiment_optimizer_step import ALL_COST_COL_NAME
from kromatography.ui.optimizer_cost_function_explorer import \
    OptimizerCostFunctionExplorer

logger = logging.getLogger(__name__)

INVERTED_SUFFIX = " (inversed)"


class BruteForceOptimizerView(ModelView):
    """ View for a brute-force binding model optimizer object.
    """
    #: Optimizer to display
    model = Instance(BruteForceOptimizer)

    #: Button to export the optimization data to CSV
    export_data_to_csv_button = Button("Export Data To CSV")

    #: Button to launch a run of all optimizer steps
    run_button = Button("Launch optimizer")

    #: Column name along which to sort the optimizer data
    sort_by = Enum(values='sort_by_possible')

    #: List of possible values to sort the optimizer data by
    sort_by_possible = List

    #: Button to open cost function controls: displays the parameters and costs
    view_edit_cost_function_button = Button("View/Edit cost function")

    def traits_view(self):
        adapter = DataFrameWithColumnOutputsAdapter(df_attr_name="cost_data",
                                                    num_outputs=1)
        cost_data_editor = DataFrameEditor(adapter=adapter)

        experiment_list_editor = ListStrEditor(title="Target experiments",
                                               editable=False)
        component_list_editor = ListStrEditor(title="Target components",
                                              editable=False)
        parameter_editor = ListStrEditor(title="Target parameters",
                                         editable=False)
        spinner_editor = RangeEditor(low=1, high=1000, mode='spinner')

        # To disable the run button once the optimizer is running:
        model_created = "model.status == '{}'".format(MULTI_SIM_RUNNER_CREATED)

        view = View(
            VGroup(
                HGroup(
                    Item('model.name', label="Optimizer name"),
                    Spring(),
                    Item('model.type', style='readonly',
                         label="Optimizer type"),
                    Spring(),
                    Item('model.num_steps', style='readonly',
                         label="Num. steps"),
                    Spring(),
                    Item('model.size', style='readonly',
                         label="Num. simulations"),
                ),
                HGroup(
                    Item('model.target_experiment_names',
                         editor=experiment_list_editor,
                         show_label=False, style='readonly'),
                    Spring(),
                    Item('model.target_components',
                         editor=component_list_editor,
                         show_label=False, style='readonly'),
                    Spring(),
                    Item('model.scanned_param_names', editor=parameter_editor,
                         show_label=False, style='readonly'),
                    Spring(),
                    VGroup(
                        Spring(),
                        Item('view_edit_cost_function_button',
                             show_label=False),
                        Spring(),
                    ),
                    label="Inputs", show_border=True
                ),
                VGroup(
                    Item('sort_by', label="Sort table by"),
                    Item('model.cost_data', editor=cost_data_editor,
                         show_label=False),
                    label="Output data", show_border=True,
                ),
                Item('model.num_optimal_simulations', editor=spinner_editor,
                     label='Number of optimal simulations to save'),
                HGroup(
                    Item('run_button', show_label=False,
                         enabled_when=model_created),
                    Spring(),
                    Item('model.status', style='readonly'),
                    Item('model.percent_run', style='readonly',
                         label="Completion"),
                    Spring(),
                    Item('export_data_to_csv_button', show_label=False,
                         enabled_when='model.has_run'),
                ),
            ),
            resizable=True,
        )

        return view

    # Method interface --------------------------------------------------------

    def do_export_data(self, path):
        """ Export optimizer data to provided file path.
        """
        file_path = os.path.abspath(path)
        if os.path.splitext(file_path)[1] != ".csv":
            file_path += ".csv"

        self.model.cost_data.to_csv(file_path)
        msg = "Data from optimizer {} saved to {}"
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

    def _view_edit_cost_function_button_fired(self):
        cost_function_explorer = OptimizerCostFunctionExplorer(
            optimizer=self.model
        )
        cost_function_explorer.edit_traits(kind='livemodal')

    # Sorting methods ---------------------------------------------------------

    def _sort_by_possible_default(self):
        """Support sorting the DF by any of its column including in reverse
        order.
        """
        all_cols = self.model.cost_data_cols
        possible = []
        for col_name in all_cols:
            possible.append(col_name)
            possible.append(col_name + INVERTED_SUFFIX)

        return possible

    def _sort_by_changed(self, new):
        """ Sort the model's dataframe based on request.
        """
        data = self.model.cost_data
        if not isinstance(data, pd.DataFrame) or len(data) == 0:
            return

        if new.endswith(INVERTED_SUFFIX):
            col_name = new[:-len(INVERTED_SUFFIX)]
            ascending = False
        else:
            col_name = new
            ascending = True

        self.model.cost_data = data.sort_values(by=col_name,
                                                ascending=ascending)

    def _sort_by_default(self):
        return ALL_COST_COL_NAME
