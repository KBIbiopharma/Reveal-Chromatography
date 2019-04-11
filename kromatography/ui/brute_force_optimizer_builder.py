""" UI to select a set of target experiments, and design a parameter optimizer.
"""
import logging

from traits.api import Bool, Button, cached_property, Enum, DelegatesTo, \
    HasStrictTraits, Instance, Int, List, on_trait_change, Property, Range, Str
from traitsui.api import Action, CancelButton, EnumEditor, Handler, HGroup, \
    InstanceEditor, Item, Label, RangeEditor, Spring, Tabbed, VGroup

from kromatography.model.study import Study
from kromatography.model.api import LazyLoadingSimulation, Simulation
from kromatography.model.parameter_scan_description import \
    LIMITS, ParameterScanDescription, SMAParameterScanDescription
from kromatography.compute.brute_force_binding_model_optimizer import \
    DEFAULT_REFINING_GRID_NUM_VALUES, DEFAULT_REFINING_GRID_SIZE_FACTOR
from kromatography.compute.brute_force_binding_model_optimizer import \
    BRUTE_FORCE_2STEP_OPTIMIZER_TYPE
from kromatography.compute.cost_functions import ALL_COST_FUNCTIONS
from kromatography.model.factories.binding_model import DEFAULT_SMA_VALUES
from kromatography.compute.brute_force_optimizer import \
    GRID_BASED_OPTIMIZER_TYPE
from kromatography.utils.has_traits_utils import search_parameters_in_sim
from kromatography.model.factories.simulation import \
    build_simulation_from_experiment
from .krom_view import KromView
from .experiment_selector import ExperimentSelector
from .component_selector import ComponentSelector
from .factories.parameter_table_editor import \
    build_regular_parameter_table_editor

# Build the optimizer with lazy sims?
OPTIMIZER_USE_LAZY_SIMS = True

ALL_BINDING_MODEL_PARAM_NAMES = sorted(LIMITS.keys())

logger = logging.getLogger(__name__)

ALL_COST_FUNCTIONS = sorted(ALL_COST_FUNCTIONS.keys())

ALL_BINDING_PARAM_NAMES = sorted(DEFAULT_SMA_VALUES.keys())

NEW_MODEL = "Create new model..."

ALL_OPTIMIZERS = [GRID_BASED_OPTIMIZER_TYPE, BRUTE_FORCE_2STEP_OPTIMIZER_TYPE]

OPTIM_GRID_TYPE = "optimizer_type == '{}'".format(GRID_BASED_OPTIMIZER_TYPE)

OPTIM_2STEP_TYPE = "optimizer_type == '{}'".format(
    BRUTE_FORCE_2STEP_OPTIMIZER_TYPE
)

# Add a create button to any traitsui view that triggers creation and can be
# disabled
CreateButton = Action(name='Create', action="_on_create",
                      enabled_when='can_create')


class OptimizerBuilderHandler(Handler):
    """ Have the create button just close the window, like the OK button.
    """
    def _on_create(self, info):
        res = self.close(info, False)
        self._on_close(info)
        return res


class BruteForceOptimizerBuilder(HasStrictTraits):
    """ Class to support building a brute force optimizer targetting one of
    more experiments.
    """
    # General optimizer parameters --------------------------------------------

    #: Type of the new optimizer being created
    optimizer_type = Enum(ALL_OPTIMIZERS)

    #: Name of the new instance of optimizer being created
    optimizer_name = Str

    #: Target cost function to minimize
    cost_function_name = Enum(ALL_COST_FUNCTIONS)

    #: List of product components to compute the cost for
    component_selector = Instance(ComponentSelector)

    #: List of all available product components
    component_selected = DelegatesTo("component_selector")

    #: Sub-object to select a list of experiment names
    experiment_selector = Instance(ExperimentSelector)

    #: List of experiment names to be targeted for the fitting
    experiment_selected = DelegatesTo("experiment_selector")

    #: Study and its datasource (with known sims, binding & transport models)
    target_study = Instance(Study)

    #: Can an optimizer be created from the current setup?
    can_create = Property(Bool, depends_on="experiment_selected, "
                                           "starting_point_simulation_name, "
                                           "parameter_scans")

    # Initial step parameters (for brute-force optimizer) ---------------------

    #: Name of the simulation to build center point simulations from
    # Center point sims for each step and each group are built from the this
    # and the target experiment the simulation group is targeting.
    starting_point_simulation_name = Str

    #: Name of the solution the resin was in at the start of the simulation
    initial_buffer_name = Enum(values="_all_buffers")

    #: All buffers to pick from for the initial condition state:
    _all_buffers = List

    #: Buffer instance or None, as set by the initial_buffer_name
    initial_buffer = Property(depends_on="initial_buffer_name")

    #: Starting point simulations, one for each target experiment
    starting_point_simulations = List(Instance(Simulation))

    #: List of parameters to scan
    parameter_scans = List(ParameterScanDescription)

    #: List of parameter names that can be selected to be in parameter_scans
    allowed_parameters = Property(List(Str),
                                  depends_on='starting_point_simulations, '
                                             'param_name_filter')

    #: Filter the list of possible parameters to scan
    param_name_filter = Str

    #: Quick access to add a new parameter to scan
    new_parameter_button = Button("New parameter scan")

    # -------------------------------------------------------------------------
    # Refining step parameters (for 2step brute-force optimizer only)
    # -------------------------------------------------------------------------

    #: Switch to allow/disallow the refinement steps after the constant scan
    do_refine = Bool(True)

    #: Spacing for step 1 and up (which refine component parameters)
    refining_step_spacing = Enum("Best", "Linear", "Log")

    #: Size of scanning grid for refining step
    refining_step_num_values = Int(DEFAULT_REFINING_GRID_NUM_VALUES)

    #: Factor in percentage to control size of the refined grid: larger means
    #: larger grid
    refining_factor = Range(value=DEFAULT_REFINING_GRID_SIZE_FACTOR, low=1,
                            high=100)

    def traits_view(self):
        all_sim_names = [sim.name for sim in self.target_study.simulations]
        start_point_sim_editor = EnumEditor(values=all_sim_names)

        possible_cp = self.target_study.simulations[0]
        view = KromView(
            Label("Select an optimizer type and a (set of) experiment(s) to "
                  "optimize against. \nUpdate the list of product components "
                  "if only certain peaks should be compared."),
            HGroup(
                Item("optimizer_name"),
                Spring(),
                Item('optimizer_type'),
                Spring(),
                Item("cost_function_name", label="Cost function")
            ),
            HGroup(
                Item("experiment_selector", editor=InstanceEditor(),
                     style="custom", show_label=False),
                Item("component_selector", editor=InstanceEditor(),
                     style="custom", show_label=False),
            ),
            HGroup(
                Item("starting_point_simulation_name",
                     editor=start_point_sim_editor,
                     label="Starting point simulation",
                     tooltip="Simulation to build optimizer simulations from,"
                             " in addition to the target experiment."),
                Item("initial_buffer_name",
                     label="Override initial buffer with",
                     tooltip="Buffer the resin was in before the first "
                             "simulated step. Leave blank to infer from target"
                             " experiment."),
            ),
            Tabbed(
                *build_2step_view_items(possible_cp),
                visible_when=OPTIM_2STEP_TYPE
            ),
            VGroup(
                *build_general_optim_view_items(possible_cp),
                visible_when=OPTIM_GRID_TYPE,
                show_border=True, label="Scanned Parameters"
            ),
            handler=OptimizerBuilderHandler(),
            buttons=[CancelButton, CreateButton],
            default_button=CreateButton,
            title="Configure Optimizer",
            resizable=True
        )
        return view

    def __init__(self, **traits):
        # FIXME: this is too complicated: consider making listeners more
        # complex to avoid loosing information:

        # Create the object with some fundamental traits, and set the rest
        # afterwards:
        init_traits = {"target_study": traits.pop("target_study")}
        super(BruteForceOptimizerBuilder, self).__init__(**init_traits)
        self.trait_set(**traits)

        # Reset parameter_scans afterwards because setting other traits might
        # erase the parameter_scans
        if "parameter_scans" in traits:
            self.parameter_scans = traits["parameter_scans"]

        if self.experiment_selected:
            self.update_starting_point_simulations()

    # Private interface -------------------------------------------------------

    def _duplicate_starting_point_sims(self, sim0):
        """ Create a set of starting point simulation to build the optimizer
        steps around, one for each target experiment.

        This is done by building the simulation from the experiment, using the
        default starting point simulation for the additional parameters not
        contained in the target experiment: binding and transport models, and
        first and last simulated step.

        Parameters
        ----------
        sim0 : Simulation
            Default simulation to use to construct center point sims for
            parameters not available in the target experiment to model.
        """
        # Collect information about the default center point
        method0 = sim0.method
        fstep = method0.method_steps[0].name
        lstep = method0.method_steps[-1].name

        center_points = []
        target_experiments = [self.target_study.search_experiment_by_name(name)
                              for name in self.experiment_selected]
        for target_exp in target_experiments:
            sim = build_simulation_from_experiment(
                target_exp, sim0.binding_model, sim0.transport_model,
                initial_buffer=self.initial_buffer, fstep=fstep, lstep=lstep,
                # Make clones to avoid interactions between sims:
                discretization=sim0.discretization.clone_traits(),
                solver=sim0.solver.clone_traits(),
            )
            if OPTIMIZER_USE_LAZY_SIMS:
                sim = LazyLoadingSimulation.from_simulation(sim)

            center_points.append(sim)

        return center_points

    # Traits initialization methods -------------------------------------------

    def _optimizer_name_default(self):
        """ Make sure that the optimizer name is not in the list of existing
        optimizers.
        """
        name = "Optimizer0"
        existing_names = [opt.name for opt in
                          self.target_study.analysis_tools.optimizations]
        i = 0
        # FIXME: move this to app_common
        # FIXME: improve to handle i reaching 2 digits.
        while name in existing_names:
            i += 1
            name = name[:-1]
            name += str(i)
        return name

    # Trait listeners ---------------------------------------------------------

    def _optimizer_type_changed(self):
        """ Changed the type of optimizer. Start over.
        """
        self.parameter_scans = []

    def _starting_point_simulation_name_changed(self):
        """ The starting point sim is changing. Start over.
        """
        # this is needed because the new start sim may or may not contain the
        # already selected parameters.
        self.parameter_scans = []

    def _new_parameter_button_fired(self):
        if self.starting_point_simulations:
            first_central_sim = self.starting_point_simulations[0]
        else:
            first_central_sim = None

        if self.optimizer_type == BRUTE_FORCE_2STEP_OPTIMIZER_TYPE:
            param_scan_traits = {
                "valid_parameter_names": ALL_BINDING_MODEL_PARAM_NAMES,
                "target_simulation": first_central_sim
            }
            param_scan = SMAParameterScanDescription(**param_scan_traits)
        elif self.optimizer_type == GRID_BASED_OPTIMIZER_TYPE:
            param_scan_traits = {
                "valid_parameter_names": self.allowed_parameters,
                "target_simulation": first_central_sim
            }
            param_scan = ParameterScanDescription(**param_scan_traits)
        else:
            msg = "Unknown optimizer type: {}".format(self.optimizer_type)
            logger.exception(msg)
            raise NotImplementedError(msg)

        self.parameter_scans.append(param_scan)

    @on_trait_change('starting_point_simulation_name, experiment_selected, '
                     'experiment_selector, target_study', post_init=True)
    def update_starting_point_simulations(self):
        study = self.target_study
        default_starting_point_sim = study.search_simulation_by_name(
            self.starting_point_simulation_name
        )
        center_points = self._duplicate_starting_point_sims(
            default_starting_point_sim
        )
        self.starting_point_simulations = center_points

    def _param_name_filter_changed(self):
        # Filter the name options of existing param_scans. Make sure there is
        # no duplicate but that the name remains in the options:
        for param_scan in self.parameter_scans:
            param_scan.valid_parameter_names = \
                [param_scan.name] + self.allowed_parameters

    def _target_study_changed(self):
        self.component_selector.product = self.target_study.product

    # Trait property getters/setters ------------------------------------------

    @cached_property
    def _get_allowed_parameters(self):
        if self.starting_point_simulations:
            first_cp = self.starting_point_simulations[0]
            return search_parameters_in_sim(first_cp,
                                            name_filter=self.param_name_filter)
        else:
            return []

    def _get_can_create(self):
        return (self.experiment_selected and self.parameter_scans and
                self.starting_point_simulation_name)

    def _build_list_objects_for_type(self, type_id):
        datasource = self.target_study.study_datasource
        all_model_names = datasource.get_object_names_by_type(type_id)
        return all_model_names

    def _get_initial_buffer(self):
        if not self.initial_buffer_name:
            return None
        else:
            return self._get_object_clone_from_name("buffers",
                                                    self.initial_buffer_name)

    def _get_object_clone_from_name(self, type_id, object_name):
        """ Make a clone of the DS object with specified object type and name.
        """
        ds = self.target_study.study_datasource
        obj = ds.get_object_of_type(type_id, object_name)
        clone = obj.clone_traits(copy="deep")
        return clone

    # Trait initialization methods --------------------------------------------

    def _starting_point_simulation_name_default(self):
        # Provide a starting point sim name so that the parameter table
        # editor is correctly initialized with the right columns and is unit
        # aware.
        return self.target_study.simulations[0].name

    def _experiment_selector_default(self):
        return ExperimentSelector(study=self.target_study)

    def _optimizer_type_default(self):
        return GRID_BASED_OPTIMIZER_TYPE

    def __all_buffers_default(self):
        return [""] + self._build_list_objects_for_type("buffers")

    def _component_selector_default(self):
        if not self.target_study:
            return ComponentSelector()
        else:
            return ComponentSelector(product=self.target_study.product)


def build_general_optim_view_items(sim_to_scan=None,
                                   parameter_table_editor=None):
    """ Returns the list of items to display in the optimizer builder view when
    the general grid based optimizer is selected.
    """
    if parameter_table_editor is None:
        parameter_table_editor = build_regular_parameter_table_editor(
            sim_to_scan, support_parallel_params=True
        )

    items = [
        Item("parameter_scans", editor=parameter_table_editor,
             show_label=False),
        HGroup(
            Item("param_name_filter", label="Filter parameters",
                 width=300, visible_when=OPTIM_GRID_TYPE),
            Spring(visible_when=OPTIM_2STEP_TYPE),
            Item("new_parameter_button", show_label=False),
            Spring(),
        ),
    ]
    return items


def build_2step_view_items(sim_to_scan=None):
    """ Returns the list of items to display in the optimizer builder view when
    the 2step cross-component optimizer is selected.
    """
    parameter_table_editor = build_regular_parameter_table_editor(sim_to_scan)
    refining_factor_tooltip = 'Larger value means a smaller parameter space ' \
                              'is scanned around the best model from step 0.'
    spinner_editor = RangeEditor(low=1, high=1000, mode='spinner')

    items = [
        VGroup(
            Label('The constant optimization step scans a large parameter '
                  'space, applying the same binding parameter to all product '
                  'components. \nAny parameter that is not scanned will remain'
                  ' constant, with its value determined by the "starting point'
                  ' simulation".'),
            *build_general_optim_view_items(
                parameter_table_editor=parameter_table_editor
            ), label="Constant Step Parameters"
        ),
        VGroup(
            Label('Refining steps scan, component by component, the '
                  'parameter space around the best models from the constant '
                  'step.\nFor each component, the new grid size is at most '
                  'the length of the grid **spacing** from the '
                  'previous scan.'),
            HGroup(
                Item("do_refine")
            ),
            VGroup(
                Item("refining_step_spacing",
                     label="Scanning strategy"),
                Item("refining_step_num_values",
                     editor=spinner_editor, label="Num. grid points"),
                Item("refining_factor",
                     tooltip=refining_factor_tooltip,
                     label=("Refining grid length (% of prev. step grid "
                            "spacing)")),
                visible_when="do_refine"
            ),
            label="Refining Steps Parameters",
        )
    ]
    return items
