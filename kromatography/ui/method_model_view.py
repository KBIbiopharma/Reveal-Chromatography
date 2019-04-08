import re
import logging

from pyface.api import information
from traits.api import Instance, Int, on_trait_change, Property, Str
from traitsui.api import EnumEditor, HGroup, Item, Label, ModelView, \
    OKCancelButtons, RangeEditor, TableEditor, VGroup, View
from traitsui.table_column import ObjectColumn

from app_common.traitsui.unit_scalar_editor import \
    UnitScalarEditor
from app_common.traitsui.unit_scalar_column import \
    UnitScalarColumn
from kromatography.model.data_source import DataSourceLookupError, \
    InStudyDataSource
from kromatography.model.method import Method
from kromatography.model.method_step import MethodStep


logger = logging.getLogger(__name__)


class MethodModelView(ModelView):
    """ View for the Method, Method Step and Collection Criteria Models.
    """

    # -------------------------------------------------------------------------
    # ModelView interface
    # -------------------------------------------------------------------------

    #: Method to be viewed
    model = Instance(Method)

    #: (study)datasource containing all known solutions
    datasource = Instance(InStudyDataSource)

    #: Button to display the details about the initial buffer:
    initial_buffer_name = Property(Str, depends_on="model.initial_buffer")

    #: List of solution names available in the datasource
    _known_solution_names = Property(depends_on="datasource")

    #: Proxy for model's collection_step_number, adding 1 to it
    # Created to allow users to specify the pooling step number starting to
    # count at 1, which is more natural for most people
    _collection_step_num_off1 = Property(
        Int, depends_on='model.collection_step_number')

    # Total number of steps
    _num_steps = Property(Int, depends_on='model.method_steps[]')

    def default_traits_view(self):
        step_editor = build_method_step_table_editor(
            self._known_solution_names
        )
        items = [
            HGroup(
                Item("model.name", label="Method Name", width=200),
                Item("model.run_type", label="Method Type")
            ),
            VGroup(
                HGroup(
                    Item("initial_buffer_name", label="Initial buffer",
                         style="readonly",
                         tooltip="Buffer the column is in before first step."),
                ),
                Label("Right-click inside the table to add a new method"
                      " step:"),
                Item("model.method_steps", editor=step_editor,
                     show_label=False),
                label="Step Sequence", show_border=True
            )
        ]

        if self.model.collection_criteria:
            step_num_editor = RangeEditor(low=1, high_name='_num_steps',
                                          mode='spinner')
            collection_criteria_group = VGroup(
                Item("_collection_step_num_off1", editor=step_num_editor,
                     label="Pooling step",
                     tooltip="Number of the step that creates the pool. Use "
                             "index of row in Method Steps table above"),
                HGroup(
                    Item("model.collection_criteria.start_collection_type",
                         label="Start Collect Type"),
                    Item("model.collection_criteria.start_collection_target",
                         label="Start Collect Target"),
                    Item("model.collection_criteria.start_collection_while",
                         label="Start Collect While"),
                ),
                HGroup(
                    Item("model.collection_criteria.stop_collection_type",
                         label="Stop Collect Type"),
                    Item("model.collection_criteria.stop_collection_target",
                         label="Stop Collect Target"),
                    Item("model.collection_criteria.stop_collection_while",
                         label="Stop Collect While"),
                ),
                label="Collection Criteria", show_border=True
            )
        else:
            collection_criteria_group = VGroup(
                Label("No collection criteria"),
                label="Collection Criteria", show_border=True
            )

        items.append(collection_criteria_group)

        view = View(VGroup(*items),
                    resizable=True,
                    buttons=OKCancelButtons,
                    title="Configure method")

        if self._known_solutions == []:
            msg = ("There are no known solutions. You can still create steps,"
                   " but won't be able to select the solutions it involves.")
            logger.info("Created a MethodView with incomplete data. " + msg)
            information(None, msg)

        return view

    # -------------------------------------------------------------------------
    # Traits interface
    # -------------------------------------------------------------------------

    def __init__(self, model, **traits):
        super(MethodModelView, self).__init__(model, **traits)

        # Update _known_solutions if needed and possible
        if self._known_solutions == [] and self.model.method_steps:
            logger.info("Didn't provide a list of known solutions. Deriving it"
                        " from the list of steps found.")
            self._known_solutions = \
                extract_list_of_solutions(self.model.method_steps)

    @on_trait_change("model:method_steps:[_solutions0_name, _solutions1_name]")
    def update_solutions(self, obj, trait, new):
        step = obj

        try:
            solution = self.datasource.get_object_of_type("buffers", new)
        except DataSourceLookupError:
            # No buffer found: let's look for a load:
            try:
                solution = self.datasource.get_object_of_type("loads", new)
            except DataSourceLookupError:
                msg = ("Failed to find the selected solution {} in the "
                       "datasource.".format(new))
                raise ValueError(msg)

        solution = solution.clone_traits()

        solution_num = _get_solution_num(trait)
        if step.solutions is None:
            step.solutions = []

        if solution_num >= len(step.solutions):
            # In the case >, this will switch their choice to be the first
            # solution
            step.solutions.append(solution)
        else:
            step.solutions[solution_num] = solution

    # Traits property getters/setters -----------------------------------------

    def _get_initial_buffer_name(self):
        if self.model.initial_buffer:
            return self.model.initial_buffer.name
        else:
            return "None"

    def _get__collection_step_num_off1(self):
        return self.model.collection_step_number + 1

    def _set__collection_step_num_off1(self, value):
        self.model.collection_step_number = value - 1

    def _get__known_solution_names(self):
        """ Extract all solution names found in a (study) datasource.
        """
        ds = self.datasource
        if ds:
            buffer_list = ds.get_objects_by_type("buffers")
            load_list = ds.get_objects_by_type("loads")
            known_solutions = buffer_list + load_list
        else:
            # FIXME Work around because no access to the datasource in central
            # pane: collect all solution names found in the model.
            known_solutions = extract_list_of_solutions(
                self.model.method_steps
            )

        return list({getattr(sol, 'name', '') for sol in known_solutions})

    def _get__num_steps(self):
        return len(self.model.method_steps)


def build_method_step_table_editor(known_solution_names=None):
    """ Build a custom table editor to control a list of MethodSteps
    """
    if known_solution_names is None:
        known_solution_names = []

    editor = TableEditor(
        columns=[
            ObjectColumn(name='name', label="Step Name"),
            ObjectColumn(name='step_type', label='Step Type'),
            ObjectColumn(name='_solutions0_name', label='Solution A',
                         editor=EnumEditor(values=known_solution_names)),
            ObjectColumn(name='_solutions1_name', label='Solution B',
                         editor=EnumEditor(values=known_solution_names)),
            UnitScalarColumn(name='flow_rate', label='Flow Rate',
                             editor=UnitScalarEditor()),
            UnitScalarColumn(name='volume', label='Volume',
                             editor=UnitScalarEditor()),
        ],
        deletable=True,
        auto_size=True,
        row_factory=MethodStep,
        row_factory_kw={"name": "New Step"},
        show_toolbar=True,
        sortable=False,
    )
    return editor


def _get_solution_num(trait_name):
    """ Recover the solution number from the provided trait name.

    The trait name provided is of the form "_solutions<NUM>_name", with NUM
    being 0 or 1. Return NUM as an integer.
    """
    patt = "_solutions(\d)_name"
    m = re.match(patt, trait_name)
    return int(m.groups()[0])


def extract_list_of_solutions(method_steps):
    """ Extract the list of unique solutions involved in a list of MethodStep.
    """
    solutions = []
    for step in method_steps:
        solutions += step.solutions
    solutions = list(set(solutions))
    return solutions
