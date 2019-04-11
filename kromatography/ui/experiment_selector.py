from traits.api import HasStrictTraits, Instance, List, Str
from traitsui.api import Item, ListStrEditor, OKCancelButtons

from kromatography.model.study import Study
from kromatography.utils.traitsui_utils import KromView


class ExperimentSelector(HasStrictTraits):
    """ Class to support select a set of experiments from a study
    """
    study = Instance(Study)

    experiment_selected = List(Str)

    experiment_name_available = List(Str)

    view = KromView(
        Item("experiment_name_available",
             editor=ListStrEditor(
                title='Experiment List',
                selected="experiment_selected",
                multi_select=True,
                editable=False
             ),
             show_label=False),
        buttons=OKCancelButtons,
        title="Select experiments"
    )

    def _experiment_name_available_default(self):
        return [exp.name for exp in self.study.experiments]
