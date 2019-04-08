from traits.api import Enum, HasStrictTraits

from app_common.traits.custom_trait_factories import PositiveInt


class Sensitivity(HasStrictTraits):
    """ Sensitivities to be computed by solver.
    """
    # -------------------------------------------------------------------------
    # Sensitivity traits
    # -------------------------------------------------------------------------

    #: Number of sensitivities to be computed
    #: (Default: 0) [Range: >=0]
    nsens = PositiveInt(0)

    #: Method used for computation of sensitivities; algorithmic
    #: differentiation (ad1) or
    #: finite difference of order 1-4 (fd1, fd2, fd3, fd4)
    #: (Default: ad1) [Range: ad1, fd1, fd2, fd3, fd4]
    sens_method = Enum(["ad1", "fd1", "fd2", "fd3", "fd4"])
