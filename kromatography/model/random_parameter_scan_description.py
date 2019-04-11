""" Describe how a simulation parameter is/should be scanned if scanned
regularly. Contains an implementation of a general parameter as well as a
specific SMA binding parameter.
"""
import logging
from numpy import random
from types import BuiltinFunctionType

from traits.api import Enum, Float, Tuple

from .base_parameter_scan_description import BaseParameterScanDescription

logger = logging.getLogger(__name__)


def collect_numpy_distros():
    """ Automatically collect all random number generation functions in numpy.
    """
    distros = []
    skip = ["get_state", "set_state"]
    for name in dir(random):
        candidate = (str.islower(name) and not name.startswith("_") and
                     isinstance(getattr(random, name), BuiltinFunctionType) and
                     name not in skip)
        if candidate:
            distros.append(name)
    return distros


# The 2 most common distributions to be first, capitalized, and
FAMILIAR_DISTROS = ["Uniform", "Gaussian"]


class RandomParameterScanDescription(BaseParameterScanDescription):
    """ Description of how a simulation parameter should be regularly scanned.

    Parameters
    ----------
    name : str
        That should be an attribute path of the parameter to scan. Should be
        able to be appended to 'simulation.' and lead to an eval-able string.
        For example: 'binding_model.sma_ka[1]'.

    distribution : str
        Type of random distribution to use to generate random values. Choose
        between "Uniform" and "Gaussian", or one of the numpy functions
        contained in the :mod:`numpy.random` module.

    dist_param1 : float
        First parameter to describe the distribution used to sample the
        parameter.

    dist_param2 : float
        High value to stop scanning at (included).

    additional_params : tuple
        Additional parameters needed to describe the distribution. Not needed
        for 'Uniform' or 'Gaussian'.
    """
    #: Type of random distribution to draw random values from to scan parameter
    distribution = Enum(FAMILIAR_DISTROS + collect_numpy_distros())

    #: First parameter to describe the distribution. Corresponds to 'mean' for
    #: 'Gaussian' distribution to 'low' (inclusive) for 'Uniform' distribution.
    dist_param1 = Float

    #: First parameter to describe the distribution. Corresponds to
    #: 'standard deviation' for 'Gaussian' distribution to 'high' (exclusive)
    #: for 'Uniform' distribution.
    dist_param2 = Float

    #: Additional parameters to describe the distribution. Used only for
    #: distributions more complex than "Uniform" or "Gaussian".
    additional_params = Tuple
