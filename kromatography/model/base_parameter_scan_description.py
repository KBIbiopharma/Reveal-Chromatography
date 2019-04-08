""" Describe how a simulation parameter is/should be scanned.
"""
import logging

from traits.api import cached_property, Enum, HasStrictTraits, Instance, List,\
    Property, Str

from kromatography.model.simulation import Simulation

logger = logging.getLogger(__name__)


class BaseParameterScanDescription(HasStrictTraits):
    """ Description of how a simulation parameter should be scanned.

    Warning: this is a base class. Use one of the subclasses instead. See
    :class:`ParameterScanDescription` or
    :class:`RandomParameterScanDescription`.

    Parameters
    ----------
    name : str
        That should be an attribute path of the parameter to scan. Should be
        able to be appended to 'simulation.' and lead to an eval-able string.
        For example: 'binding_model.sma_ka[1]'.
    """
    #: Name/path of the simulation attribute to scan
    name = Enum(Str, values="valid_parameter_names")

    #: List of valid parameter names
    valid_parameter_names = List(Str)

    #: Simulation whose parameter will be scanned (OPTIONAL)
    target_simulation = Instance(Simulation)

    #: Value of the parameter in the target simulation if available
    center_value = Property(depends_on="target_simulation, name")

    def __init__(self, **traits):
        # Make sure the valid_parameter_names is set before the name is set:
        name = traits.pop("name", "")
        if "valid_parameter_names" not in traits:
            traits["valid_parameter_names"] = [name]

        super(BaseParameterScanDescription, self).__init__(**traits)

        if name:
            self.name = name

    @cached_property
    def _get_center_value(self):
        if self.name == "" or not self.target_simulation:
            val = None
        else:
            val = eval("self.target_simulation.{}".format(self.name))
        return val
