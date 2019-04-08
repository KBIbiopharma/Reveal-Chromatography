import os
import logging

from traits.api import Button, Instance
from traitsui.api import HGroup, Item, ModelView, Spring, VGroup, View
from traitsui.ui_editors.data_frame_editor import DataFrameAdapter, \
    DataFrameEditor

from kromatography.compute.brute_force_optimizer_step import \
    BruteForceOptimizerStep
from kromatography.ui.factories.parameter_table_editor import \
    build_regular_parameter_table_editor

logger = logging.getLogger(__name__)


class BruteForceOptimizerStepView(ModelView):
    """ View for a brute force optimizer step object.
    """
    #: SimulationGroup to display
    model = Instance(BruteForceOptimizerStep)

    #: Button to export the optimization data to CSV
    export_data_to_csv_button = Button("Export Data To CSV")

    def traits_view(self):
        # Because of the way the DataFrame editor is implemented,
        # the `model.` prefix should not be passed for the update name:
        cost_data_editor = DataFrameEditor(adapter=DataFrameAdapter())

        parameter_table_editor = build_regular_parameter_table_editor(
            support_parallel_params=True)

        view = View(
            VGroup(
                HGroup(
                    Item('model.name', label="Optimizer name",
                         style='readonly'),
                    Spring(),
                    Item('model.optimizer_step_type', style='readonly',
                         label="Optimizer type"),
                    Spring(),
                    Item('model.size', style='readonly',
                         label="Num. simulations"),
                ),
                Item('model.parameter_list', style='readonly',
                     editor=parameter_table_editor),
                Item('model.cost_data', editor=cost_data_editor,
                     label="Cost Data"),
                HGroup(
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
        fpath = os.path.abspath(path)
        self.model.cost_data.to_csv(fpath)
        msg = "Data from optimizer {} saved to {}"
        msg = msg.format(self.model.name, fpath)
        logger.debug(msg)

    # Traits listeners --------------------------------------------------------

    def _export_data_to_csv_button_fired(self):
        from kromatography.utils.extra_file_dialogs import \
            to_csv_file_requester

        path = to_csv_file_requester()
        if path is not None:
            self.do_export_data(path)


if __name__ == "__main__":
    from kromatography.model.tests.sample_data_factories import \
        make_sample_binding_model_optimizer

    model = make_sample_binding_model_optimizer(5).steps[0]
    view = BruteForceOptimizerStepView(model=model)
    view.configure_traits()
