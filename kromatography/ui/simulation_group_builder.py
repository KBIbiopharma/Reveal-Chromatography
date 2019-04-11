""" Classes and utilities to create a SimulationGroup around a center point
simulation.
"""
import logging
import numpy as np

from traits.api import Bool, Button, cached_property, Enum, HasStrictTraits, \
    Instance, Int, List, Property, Str
from traitsui.api import Action, CancelButton, Handler, HGroup, Item, Spring, \
    VGroup

from .krom_view import KromView
from kromatography.model.simulation import Simulation
from kromatography.model.study import Study
from kromatography.model.factories.simulation_group import \
    param_scans_to_sim_group
from kromatography.model.simulation_group import GROUP_TYPES, \
    SIM_GROUP_GRID_TYPE, SIM_GROUP_MC_TYPE
from kromatography.model.parameter_scan_description import \
    BaseParameterScanDescription, ParameterScanDescription
from kromatography.model.random_parameter_scan_description import \
    RandomParameterScanDescription
from kromatography.utils.has_traits_utils import search_parameters_in_sim
from .factories.parameter_table_editor import \
    build_mc_parameter_table_editor, build_regular_parameter_table_editor
from .simulation_group_model_view import GROUP_NAME_WIDTH

logger = logging.getLogger(__name__)

# Default values for the group size when choosing a Monte-Carlo type group
DEFAULT_MC_GROUP_SIZE = 50

DEFAULT_NEW_GROUP_NAME = "New Simulation Group"


# Add a create button to any traitsui view that triggers creation and can be
# disabled
CreateButton = Action(name='Create', action="_on_create",
                      enabled_when='can_create')


class SimulationGroupBuilderHandler(Handler):
    """ Have the create button just close the window, like the OK button. The
    actual create will happen in the calling code.
    """
    def _on_create(self, info):
        res = self.close(info, False)
        self._on_close(info)
        return res


class SimulationGroupBuilder(HasStrictTraits):
    """ Class to build a SimulationGroup around a Simulation object.
    """
    #: Study and its datasource (with known sims, binding & transport models)
    target_study = Instance(Study)

    #: Name of the future simulation group
    group_name = Str(DEFAULT_NEW_GROUP_NAME)

    #: Type of simulation group to create
    group_type = Enum(GROUP_TYPES)

    #: Size of the future group (grid type only, not controllable by the user)
    _group_size = Property(Int, depends_on="parameter_scans.num_values, "
                                           "_requested_group_size")

    #: Size of the future MC group (controllable by the user)
    _requested_group_size = Int(DEFAULT_MC_GROUP_SIZE)

    #: Simulation to clone and modify to create all simulations in future group
    center_point_simulation = Property(
        Instance(Simulation), depends_on="center_point_simulation_name"
    )

    #: Name of the source simulation (center_point_simulation)
    center_point_simulation_name = Enum(values="_sim_names")

    #: Possible simulation names for the group seed
    _sim_names = List(Str)

    #: List of parameters to scan
    parameter_scans = List(BaseParameterScanDescription)

    #: Type of parameter descriptions based the group type (grid vs random)
    param_klass = Property(depends_on="group_type")

    #: Filter the list of possible parameters to scan
    param_name_filter = Str

    #: List of parameter names that can be selected to be in parameter_scans
    allowed_parameters = Property(List(Str),
                                  depends_on="center_point_simulation_name, "
                                             "param_name_filter")

    #: Button to trigger the addition of a new parameter to scan
    new_parameter_button = Button("New parameter scan")

    #: Store simulations on disk rather than in memory?
    lazy_loading = Bool(True)

    #: Delete simulation and CADET file once a simulation is run?
    auto_delete_run_sims = Bool()

    #: Can an optimizer be created from the current setup?
    can_create = Property(Bool, depends_on="center_point_simulation, "
                                           "allowed_parameters")

    def __init__(self, **traits):
        # Control the order which the object is built so that the information
        # passed isn't lost:

        center_point_simulation = traits.pop("center_point_simulation", None)
        parameter_scans = traits.pop("parameter_scans", None)

        super(SimulationGroupBuilder, self).__init__(**traits)

        if center_point_simulation:
            self.center_point_simulation = center_point_simulation

        if parameter_scans:
            self.parameter_scans = parameter_scans

    def traits_view(self):
        """ Build the valid values for each parameters, and build the view.
        """
        if self.center_point_simulation is None:
            msg = ("Unable to build the UI of a SimulationGroupBuilder "
                   "without a center_point_simulation")
            logger.exception(msg)
            raise ValueError(msg)

        regular_parameter_table_editor = build_regular_parameter_table_editor(
            self.center_point_simulation, support_parallel_params=True,
        )
        is_regular_grid = "group_type == '{}'".format(SIM_GROUP_GRID_TYPE)
        group_size_grid_tooltip = ""
        mc_parameter_table_editor = build_mc_parameter_table_editor(
            self.center_point_simulation
        )
        is_mc_group = "group_type == '{}'".format(SIM_GROUP_MC_TYPE)
        view = KromView(
            VGroup(
                HGroup(
                    Item("group_name", label="Group name",
                         width=GROUP_NAME_WIDTH),
                    Spring(),
                    Item("group_type"),
                    Spring(),
                    Item("_group_size", style="readonly", label="Group size",
                         visible_when=is_regular_grid,
                         tooltip=group_size_grid_tooltip),
                    Item("_requested_group_size", label="Group size",
                         visible_when=is_mc_group),
                ),
                Item("center_point_simulation_name",
                     label="Source simulation"),
                Item("parameter_scans", editor=regular_parameter_table_editor,
                     label="Parameters", visible_when=is_regular_grid),
                Item("parameter_scans", editor=mc_parameter_table_editor,
                     label="Parameters", visible_when=is_mc_group),
                HGroup(
                    Item("param_name_filter", label="Filter parameters",
                         width=300),
                    Item("new_parameter_button", show_label=False),
                    Spring(),
                ),
                HGroup(
                    Spring(),
                    Item("lazy_loading",
                         label="Store simulations on disk?",
                         tooltip="Check to conserve memory (RAM). Slower "
                                 "to access simulations."),
                    Item("auto_delete_run_sims",
                         label="Delete run simulations?",
                         tooltip="Delete the simulation object and the "
                                 "CADET file once the simulation has run. "
                                 "Check for very large groups and/or limited "
                                 "available storage.",
                         enabled_when="lazy_loading")
                ),
            ),
            handler=SimulationGroupBuilderHandler(),
            buttons=[CancelButton, CreateButton],
            title="Configure Simulation Group",
            width=1000, height=400
        )

        return view

    def build_group(self):
        """ Build the SimulationGroup.
        """
        group = param_scans_to_sim_group(
            self.group_name, self.parameter_scans,
            self.center_point_simulation, group_type=self.group_type,
            lazy_loading=self.lazy_loading, group_size=self._group_size,
            auto_delete_run_sims=self.auto_delete_run_sims
        )
        return group

    # Traits property getters/setters -----------------------------------------

    def _get_can_create(self):
        can_create = self.center_point_simulation and self.parameter_scans
        return can_create

    @cached_property
    def _get_center_point_simulation(self):
        if self.target_study:
            return self.target_study.search_simulation_by_name(
                self.center_point_simulation_name
            )

    def _set_center_point_simulation(self, sim):
        if sim:
            self.center_point_simulation_name = sim.name

    @cached_property
    def _get_allowed_parameters(self):
        return search_parameters_in_sim(self.center_point_simulation,
                                        name_filter=self.param_name_filter)

    @cached_property
    def _get_param_klass(self):
        if self.group_type == SIM_GROUP_GRID_TYPE:
            return ParameterScanDescription
        elif self.group_type == SIM_GROUP_MC_TYPE:
            return RandomParameterScanDescription
        else:
            msg = "Unsupported group type ({}). Supported values are {}"
            msg = msg.format(self.group_type, GROUP_TYPES)
            logger.exception(msg)
            raise NotImplementedError(msg)

    @cached_property
    def _get__group_size(self):
        if self.group_type == SIM_GROUP_MC_TYPE:
            return self._requested_group_size

        if not self.parameter_scans:
            return 0
        return np.prod([param.num_values for param in self.parameter_scans])

    # Traits listeners --------------------------------------------------------

    def _center_point_simulation_name_changed(self):
        self.parameter_scans = []

    def _group_type_changed(self):
        self.parameter_scans = []

    def _new_parameter_button_fired(self):
        param_scan_traits = {"valid_parameter_names": self.allowed_parameters,
                             "target_simulation": self.center_point_simulation}

        param_scan = self.param_klass(**param_scan_traits)
        self.parameter_scans.append(param_scan)

    def _param_name_filter_changed(self):
        # Filter the name options of existing param_scans. Make sure there is
        # no duplicate but that the name remains in the options:
        for param_scan in self.parameter_scans:
            param_scan.valid_parameter_names = \
                [param_scan.name] + self.allowed_parameters

    # Traits initializers -----------------------------------------------------

    def _center_point_simulation_name_default(self):
        return self.target_study.simulations[0].name

    def __sim_names_default(self):
        if self.target_study:
            return [sim.name for sim in self.target_study.simulations]
        else:
            return []
