""" Describe how a simulation parameter is/should be scanned if scanned
regularly. Contains an implementation of a general parameter as well as a
specific SMA binding parameter.
"""
import logging
import numpy as np
import re

from scimath.units.api import UnitScalar
from traits.api import Array, Button, cached_property, Enum, Float, List, \
    on_trait_change, Range

from app_common.traits.has_traits_utils import trait_dict

from .simulation_group import SingleParamSimulationDiff
from .base_parameter_scan_description import BaseParameterScanDescription

DEFAULT_KA_LOW_HIGH = (1e-8, 50)

DEFAULT_NU_LOW_HIGH = (0.1, 20)

DEFAULT_SIGMA_LOW_HIGH = (0., 100)

DEFAULT_NUM_VALUES = 5

LIMITS = {
    "sma_ka": DEFAULT_KA_LOW_HIGH,
    "sma_nu": DEFAULT_NU_LOW_HIGH,
    "sma_sigma": DEFAULT_SIGMA_LOW_HIGH,
}

logger = logging.getLogger(__name__)

SPACING_FUNCS = {"Linear": np.linspace, "Log": np.logspace}

TRANSFORM_FUNCS = {"Linear": lambda x: x, "Log": np.log10}


class ParameterScanDescription(BaseParameterScanDescription):
    """ Description of how a simulation parameter should be regularly scanned.

    Attributes
    ----------
    name : str
        That should be an attribute path of the parameter to scan. Should be
        able to be appended to 'simulation.' and lead to an eval-able string.
        For example: 'binding_model.sma_ka[1]'.

    low : float
        Low value to start scanning at.

    high : float
        High value to stop scanning at (included).

    num_values : int [OPTIONAL, default=5]
        Number of values to split the space between low and high.

    spacing : str
        Type of spacing between the values. Choose between 'Linear' and 'Log'.
    """
    #: Lowest value to scan.
    low = Float

    #: Highest value to scan as long as num_values > 1.
    high = Float(1.)

    #: Number of values to scan between low and high
    num_values = Range(value=DEFAULT_NUM_VALUES, low=1, exclude_low=False)

    #: Type of spacing between the scanned values
    spacing = Enum(["Linear", "Log"])

    #: Final values that will be scanned based on all other attributes
    scanned_values = Array

    #: List of parameter to scan simultaneously
    parallel_parameters = List

    #: Button to trigger the selection of parameters to scan simultaneously
    add_parallel_params = Button("View/Edit")

    def __init__(self, **traits):
        super(ParameterScanDescription, self).__init__(**traits)
        self.update_scanned_values()

    @on_trait_change("low, high, num_values, spacing")
    def update_scanned_values(self):
        if self.num_values > 0:
            spacing_func = SPACING_FUNCS[self.spacing]
            transform_func = TRANSFORM_FUNCS[self.spacing]
            low = transform_func(self.low)
            high = transform_func(self.high)
            if self.num_values > 1:
                self.scanned_values = spacing_func(low, high, self.num_values)
            else:
                self.scanned_values = np.array([self.low])

    def to_sim_diffs(self):
        """ Convert the current scan description to a simulation diff.
        """
        diffs = []
        if isinstance(self.center_value, UnitScalar):
            units = self.center_value.units
            for scan_val in self.scanned_values:
                val = UnitScalar(scan_val, units=units)
                diff = SingleParamSimulationDiff(self.name, val)
                diffs.append(diff)
        else:
            for val in self.scanned_values:
                diff = SingleParamSimulationDiff(self.name, val)
                diffs.append(diff)
        return diffs

    # Traits listeners --------------------------------------------------------

    def _add_parallel_params_fired(self):
        """ Launch a selection of additional parameters to include in the scan.
        """
        from kromatography.ui.regular_parameter_list_selector import \
            RegularParameterListSelector

        short_name = self.name.split(".")[-1]

        model = RegularParameterListSelector(
            center_sim=self.target_simulation,
            allow_parallel_params=False,
            num_values_fixed=self.num_values,
            parameter_scans=self.parallel_parameters,
            # FIXME: self.name won't be removed because
            # utils.has_traits_utils.search_parameters_in_chrom_data doesn't
            # yet support excluding extended parameters
            param_names_to_ignore=(self.name, "source_experiment", "output"),
            title="Parameter(s) to scan together with {}".format(short_name)
        )
        ui = model.edit_traits(kind="modal")
        if ui.result:
            for p in model.parameter_scans:
                if len(p.scanned_values) == 0:
                    msg = "Parallel parameter {} has no values: did you " \
                          "forget to set the high and low values? Removing " \
                          "it from the list.".format(p.name)
                    logger.error(msg)

            self.parallel_parameters = [p for p in model.parameter_scans
                                        if len(p.scanned_values) != 0]

    def _num_values_changed(self, new):
        for parallel_param in self.parallel_parameters:
            parallel_param.num_values = new

    @on_trait_change("parallel_parameters[]")
    def validate_parallel_parameters(self):
        for param in self.parallel_parameters:
            if param.num_values != self.num_values:
                msg = "Inconsistent number of values in the parallel " \
                      "parameter {}: found {} but all parallel parameter " \
                      "must have the same number of values as the current " \
                      "one ({} has {} values). This will cause issues or " \
                      "unexpected behavior!"
                msg = msg.format(param.name, param.num_values, self.name,
                                 self.num_values)
                logger.error(msg)
                # Raising error even though in UI it will be swallowed by the
                # traits machinery since inside a listener:
                raise ValueError(msg)


class SMAParameterScanDescription(ParameterScanDescription):
    """ Custom param descriptions for SMA models.

    Compared to a ParameterScanDescription, it has simplified parameter
    name/path and suggests low and high based on the parameter name.
    """

    def to_param_scan_desc(self):
        """ Convert to regular, eval-able ParameterScanDescription.
        """
        attrs = trait_dict(self)
        # Change the name to be the full extended name: Use `[1:]` since we
        # are configuring a ConstantOptimizerStep.
        attrs["name"] = full_param_name_from_short_name(self.name)
        valid_parameter_names = attrs["valid_parameter_names"]
        attrs["valid_parameter_names"] = [full_param_name_from_short_name(name)
                                          for name in valid_parameter_names]
        return ParameterScanDescription(**attrs)

    # Traits listener methods -------------------------------------------------

    def _name_changed(self):
        limits = LIMITS[self.name]
        self.low, self.high = limits

    # Traits property getters/setters -----------------------------------------

    @cached_property
    def _get_center_value(self):
        try:
            val = super(SMAParameterScanDescription, self)._get_center_value()
        except AttributeError as e:
            # Probably creating a ParameterDescription with a short name
            msg = "Unable to compute the center value for parameter {}. " \
                  "Error was '{}'.".format(self.name, e)
            logger.debug(msg)
            val = None

        return val

    # Traits initialization methods -------------------------------------------

    def _valid_parameter_names_default(self):
        return sorted(LIMITS.keys())


def full_param_name_from_short_name(short_name):
    """ Convert short SMAParamScanDescription name to full one to be eval-ed.
    """
    return "binding_model.{}[1:]".format(short_name)


def extract_short_name_from_param_scan(param):
    """ Extract the parameter name from its path.

    Parameters
    ----------
    param : Instance(ParameterScanDescription)
        Parameter to extract the name from its extended name.

    Examples
    ---------
    >>> extract_short_name_from_param_scan('binding_model.sma_ka[1]')
    sma_ka
    """
    pattern = '\w+.(\w+)'
    match = re.search(pattern, param.name)
    if match is None:
        msg = ("Failed to match the parameter name {} to the expected "
               "binding parameter pattern {}.".format(param.name, pattern))
        logger.warning(msg)
        return

    return match.groups()[0]
