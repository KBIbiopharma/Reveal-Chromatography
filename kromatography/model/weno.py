from traits.api import Enum, HasStrictTraits

from app_common.traits.custom_trait_factories import PositiveFloat


class Weno(HasStrictTraits):
    """ Weno discretization parameters.
    """
    # -------------------------------------------------------------------------
    # Weno discretization traits
    # -------------------------------------------------------------------------

    #: Boundary model type: 0 = Lower WENO order (stable), 1 = Zero weights
    #: (unstable for small Dax), 2 = Zero weights for p != 0 (stable?),
    #: 3 = Large ghost points (Default: 0) [Range: 0, 1, 2, 3]
    boundary_model = Enum([0, 1, 2, 3])

    #: WENO epsilon
    #: (Default: 1.0e-6) [Range: >=0]
    weno_eps = PositiveFloat(1e-6)

    #: WENO Order: 1 = standard upwind scheme, 2, 3; also called WENO K
    #: (default: 3) [Range: 1, 2, 3]
    weno_order = Enum([1, 2, 3])

    # -------------------------------------------------------------------------
    # Private methods
    # -------------------------------------------------------------------------

    def _weno_order_default(self):
        return 3
