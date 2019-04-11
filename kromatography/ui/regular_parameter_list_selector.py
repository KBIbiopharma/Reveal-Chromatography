
import logging

from traits.api import Bool, Button, cached_property, HasStrictTraits, \
    Instance, Int, List, Property, Tuple, Str
from traitsui.api import HGroup, Item, OKCancelButtons, Spring, VGroup

from ..model.simulation import Simulation
from ..model.parameter_scan_description import ParameterScanDescription
from ..utils.traitsui_utils import KromView
from ..utils.has_traits_utils import search_parameters_in_sim
from .factories.parameter_table_editor import \
    build_regular_parameter_table_editor

logger = logging.getLogger(__name__)


class RegularParameterListSelector(HasStrictTraits):
    """ Tool and UI to select a list of parameter scans.

    Can be used to build a simulation group, an optimizer, or a select a list
    of scans to do in parallel.
    """
    #: Target simulation that will be scanned. Used to set the list of
    #: scan-able parameters
    center_sim = Instance(Simulation)

    #: Parameters to remove from the list of options
    param_names_to_ignore = Tuple

    #: Include editor to set parallel parameters
    allow_parallel_params = Bool

    #: Value to fix the number of values for each scan if any.
    num_values_fixed = Int

    #: List of parameters to scan
    parameter_scans = List(ParameterScanDescription)

    #: Filter the list of possible parameters to scan
    param_name_filter = Str

    #: List of parameter names that can be selected to be in parameter_scans
    allowed_parameters = Property(List(Str),
                                  depends_on="center_sim, param_name_filter, "
                                             "param_names_to_ignore")

    #: Button to trigger the addition of a new parameter to scan
    new_parameter_button = Button("New parameter scan")

    #: Optional title if the component is drawn in its own window
    title = Str

    def traits_view(self):
        parameter_table_editor = build_regular_parameter_table_editor(
            self.center_sim, num_values_fixed=bool(self.num_values_fixed),
            support_parallel_params=self.allow_parallel_params
        )
        view = KromView(
            VGroup(
                Item("parameter_scans", editor=parameter_table_editor,
                     show_label=False),
                HGroup(
                    Item("param_name_filter", label="Filter parameters",
                         width=300),
                    Item("new_parameter_button", show_label=False),
                    Spring(),
                ),
                label="Select parameters", show_border=True
            ),
            buttons=OKCancelButtons,
            title=self.title,
            width=700,
        )
        return view

    @cached_property
    def _get_allowed_parameters(self):
        return search_parameters_in_sim(self.center_sim,
                                        exclude=self.param_names_to_ignore,
                                        name_filter=self.param_name_filter)

    def _new_parameter_button_fired(self):
        param_scan_traits = {"valid_parameter_names": self.allowed_parameters,
                             "target_simulation": self.center_sim}
        if self.num_values_fixed:
            param_scan_traits["num_values"] = self.num_values_fixed

        param_scan = ParameterScanDescription(**param_scan_traits)
        self.parameter_scans.append(param_scan)

    def _param_name_filter_changed(self):
        # Filter the name options of existing param_scans. Make sure there is
        # no duplicate but that the name remains in the options:
        for param_scan in self.parameter_scans:
            param_scan.valid_parameter_names = \
                [param_scan.name] + self.allowed_parameters

    def _param_names_to_ignore_default(self):
        return "source_experiment", "output"
