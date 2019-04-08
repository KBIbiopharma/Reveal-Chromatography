from traits.api import Enum, HasStrictTraits, Int

from app_common.traits.custom_trait_factories import PositiveFloat, PositiveInt


class SchurSolver(HasStrictTraits):
    """ Schur Solver parameters.
    """
    # -------------------------------------------------------------------------
    # Schur Solver traits
    # -------------------------------------------------------------------------

    #: Type of Gram-Schmidt orthogonalization (1-Classical GS (default),
    #: 2-Modified GS)
    gs_type = Enum([1, 2])

    #: Defines the size of the iterative linear SPGMR solver
    #: (Default: 0) [Range: 0-NCOL]
    max_krylov = Int(0)

    #: Maximum number of restarts in the GMRES algorithm. If lack of memory
    #: is not an issue, better use a larger Krylov space than restarts
    #: (default: 0) [Range: >=0]
    max_restarts = PositiveInt(0)

    #: Schur safety factor; Influences the tradeof between linear iterations
    #: and nonlinear error control; see IDAS guide 2.1, 5 (default: 1.0e-8)
    #: [Range: >=0]
    schur_safety = PositiveFloat(1.0e-8)
