import numpy as np

from traits.api import Array, HasStrictTraits


class Section(HasStrictTraits):
    """ Inlet concentration profile for each component in section in mM
    """
    # -------------------------------------------------------------------------
    # Section traits
    # -------------------------------------------------------------------------

    #: A vector with constant coefficients for inlet concentrations
    #: (Default: Vector of length ncomp containing zeros) [Range >= 0.0]
    const_coeff = Array(dtype=float, shape=(None,))

    #: A vector with linear coefficients for inlet concentrations
    #: (Default: Vector of length ncomp containing zeros) [Range: Any]
    lin_coeff = Array(dtype=float, shape=(None,))

    #: A vector with quadratic coefficients for inlet concentrations
    #: (Default: Vector of length ncomp containing zeros) [Range: Any]
    quad_coeff = Array(dtype=float, shape=(None,))

    #: A vector with cubic coefficients for inlet concentrations
    #: (Default: Vector of length ncomp containing zeros) [Range: Any]
    cube_coeff = Array(dtype=float, shape=(None,))

    # -------------------------------------------------------------------------
    # Private methods
    # -------------------------------------------------------------------------

    def __init__(self, ncomp, **traits):
        #: Initialize the coefficients: vector of length ncomp containing zeros
        #: if not explicitly initialized.
        for name in ['const_coeff', 'lin_coeff', 'quad_coeff', 'cube_coeff']:
            traits.setdefault(name, np.zeros(ncomp))
        super(Section, self).__init__(**traits)
