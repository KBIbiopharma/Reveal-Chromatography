import numpy as np

from traits.api import Array, Enum, HasStrictTraits, Instance

from app_common.traits.custom_trait_factories import PositiveInt
from .weno import Weno


DISCRETIZATION_TYPES = ["DEFAULT_DISCRETIZATION"]


class Discretization(HasStrictTraits):
    """ Discretization parameters.
    """
    # -------------------------------------------------------------------------
    # Discretization traits
    # -------------------------------------------------------------------------

    #: Number of column (axial) discretization cells
    #: (Default: 50) [Range: >=1]
    ncol = PositiveInt(50, exclude_low=True)

    #: Number of particle (radial) discretization cells
    #: (Default: 5) [Range: >=1]
    npar = PositiveInt(5, exclude_low=True)

    #: Specifies the discretization scheme inside the particles
    #: (default: EQUIDISTANT_PAR)
    #: [Range: EQUIDISTANT_PAR, EQUIVOLUME_PAR, USER_DEFINED_PAR]
    par_disc_type = Enum(['EQUIDISTANT_PAR', 'EQUIVOLUME_PAR',
                          'USER_DEFINED_PAR'])

    #: Type of reconstruction method for fluxes
    #: (default: WENO) [Range: WENO]
    reconstruction = Enum(['WENO'])

    #: A vector with node coordinates for the cell boundaries
    #: (default: NA) [Range: 0-1] [Length: NPAR+1]
    par_disc_vector = Array(dtype=float, shape=(None,))

    #: Weno class instance
    weno = Instance(Weno, args=())

    # -------------------------------------------------------------------------
    # Private methods
    # -------------------------------------------------------------------------

    def _par_disc_vector_default(self):
        return np.zeros(self.npar+1, dtype='float64')
