""" Largest component insit the CADET input class that gets translated into the
HDF5 input file.

Consequently, the class names, attribute names and units that contained in this
class and its children are set by the specs of the version of CADET using the
generated input file.
"""
import numpy as np

from traits.api import Array, Enum, HasStrictTraits, Instance

from app_common.traits.custom_trait_factories import PositiveFloat, PositiveInt
from .binding_model import BindingModel, LANGMUIR_BINDING_MODEL, \
    PH_STERIC_BINDING_MODEL, STERIC_BINDING_MODEL, PH_LANGMUIR_BINDING_MODEL
from .inlet import Inlet
from .cadet_ph_external_profile import CADETPhExternalProfile


# Mapping between binding model types and the absorption type CADET expects:
ALL_CADET_TYPES = {STERIC_BINDING_MODEL: 'STERIC_MASS_ACTION',
                   PH_STERIC_BINDING_MODEL: 'EXTERNAL_STERIC_MASS_ACTION_PH',
                   LANGMUIR_BINDING_MODEL: 'MULTI_COMPONENT_LANGMUIR',
                   PH_LANGMUIR_BINDING_MODEL: 'EXTERNAL_LANGMUIR'}


class CADETModel(HasStrictTraits):
    """ The CADET model parameters to be stored in the HDF5 input file.

    NOTES
    -----
    Keep in mind:

        * This class is primarily used for creating the input parameters to the
          CADET simulator.
        * The attributes here correspond to the H5 nodes under `/input/model`.
        * The units have to be in SI units. For more details, see the CADET
          documentation.
    """
    # -------------------------------------------------------------------------
    # CADETModel traits
    # -------------------------------------------------------------------------

    #: Specifies the type of binding model
    adsorption_type = Enum(ALL_CADET_TYPES.values())

    #: Axial dispersion coefficient(m2/s)
    #: [Range: >=0]
    col_dispersion = PositiveFloat(6e-8)

    #: Column length (m)
    #: (default: 0.20) [Range: > 0]
    col_length = PositiveFloat(0.20, exclude_low=True)

    #: Column porosity
    #: [Range: > 0]
    col_porosity = PositiveFloat(0.35)

    #: Number of chemical components in the chromatographic media
    #: [Range: > 0]
    ncomp = PositiveInt(exclude_low=True)

    #: A vector with film diffusion coefficients (m/2) [len(ncomp)]
    #: (Default:N/A) [Range: >=0]
    film_diffusion = Array(dtype=float, shape=(None, ))

    #: A vector with initial concentrations for each comp. in the bulk mobile
    #: phase (mmol/m3)[len(ncomp)]
    #: (Default:N/A) [Range: >=0]
    init_c = Array(dtype=float, shape=(None, ))

    #: Same as INIT_C but for the bead liquid phase (optional, INIT_C is used
    #: if left out). (mmol/m3) [len(ncomp)]
    #: (Default:N/A) [Range: >=0]
    init_cp = Array(dtype=float, shape=(None, ))

    #: Same as INIT_C but for the bound phase (mmol/m3) [len(ncomp)]
    #: (Default:N/A) [Range: >=0]
    init_q = Array(dtype=float, shape=(None, ))

    #: A vector with particle di usion coefficients (m2/s) [len(ncomp)]
    #: (Default: NA) [Range: >=0]
    par_diffusion = Array(dtype=float, shape=(None, ))

    #: A vector with particle surface diffusion cofficients (m2/s)
    #: [len(ncomp)]
    #: (Default: NA) [Range: >=0]
    par_surfdiffusion = Array(dtype=float, shape=(None, ))

    #: Particle porosity
    #: (Default: 0.5) [Range: > 0]
    par_porosity = PositiveFloat(0.5, exclude_low=True)

    #: Particle Radius
    #: (Default: 4.5e-5) [Range: > 0]
    par_radius = PositiveFloat(4.5e-5, exclude_low=True)

    #: A vector of Interstitial velocity of the mobile phase (m/2)
    #: [len(nsec)]
    #: (Default: NA) [Range: >=0]
    velocity = Array(dtype=float, shape=(None, ))

    #: Binding Model
    adsorption = Instance(BindingModel)

    #: Inlet
    inlet = Instance(Inlet)

    #: External pH dependence profile
    external = Instance(CADETPhExternalProfile)

    def __init__(self, num_components, num_sections, **traits):
        # Initialize any array traits that are not explicitly passed to the
        # constructor
        self.ncomp = num_components
        ncomp_arr_traits = ['film_diffusion', 'init_c',  'init_cp', 'init_q',
                            'par_diffusion', 'par_surfdiffusion']
        for name in ncomp_arr_traits:
            traits.setdefault(name, np.zeros(num_components))

        nsec_arr_traits = ['velocity']
        for name in nsec_arr_traits:
            traits.setdefault(name, np.zeros(num_sections))

        # Initialize the Inlet object if not explicitly passed.
        traits.setdefault('inlet', Inlet(num_components, num_sections))

        super(CADETModel, self).__init__(**traits)
