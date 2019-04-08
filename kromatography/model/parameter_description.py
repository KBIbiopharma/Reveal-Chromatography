
from traits.api import Float, HasStrictTraits, Str

from kromatography.model.factories.binding_model import DEFAULT_SMA_VALUES


class ParameterDescription(HasStrictTraits):
    """ Description of a fixed simulation parameter.

    Parameters
    ----------
    name : str
        That should be an attribute path of the parameter to scan. Should be
        able to be appended to 'simulation.' and lead to an eval-able string.
        For example: 'binding_model.sma_ka[1]'.
    """
    #: Name/path of the simulation attribute to scan
    name = Str

    value = Float


class SMAParameterDescription(ParameterDescription):
    """ Custom param descriptions for SMA models which ajusts the default value
    based on the parameter name.
    """
    def _name_changed(self):
        self.value = DEFAULT_SMA_VALUES[self.name]
