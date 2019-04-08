
import numpy as np

from traits.api import Constant, Enum, Tuple

from kromatography.model.base_product_model import BaseProductModel
from app_common.traits.custom_trait_factories import ParameterArray, \
    PositiveFloatParameter

GRM_TRANSPORT_MODEL = 'GENERAL_RATE_MODEL'
TRANSPORT_MODEL_TYPES = [GRM_TRANSPORT_MODEL]
TRANSPORT_MODEL_TYPE = "TransportModel"


class TransportModel(BaseProductModel):
    """ Base Transport model class.
    """
    #: The type of transport model (e.g. GENERAL_RATE_MODEL) used for the
    #: chromatography simulation.
    model_type = Enum(TRANSPORT_MODEL_TYPES)

    # -------------------------------------------------------------------------
    # ChromatographyData traits
    # -------------------------------------------------------------------------

    #: The type of data being represented by this class
    type_id = Constant(TRANSPORT_MODEL_TYPE)

    #: Attributes that identify an instance uniquely in a collection
    _unique_keys = Tuple(('target_product', 'name'))


class GeneralRateModel(TransportModel):
    """ General Rate Model transport model.

    Note that this general implementation assumes that in addition to the
    product components, there is an additional cation component that may be
    modeled by CADET. In the case this is combined with a Langmuir type binding
    model, the transport parameters for that cation component will be ignored
    and striped out when passing to CADET since it is not modeled.
    """
    # -------------------------------------------------------------------------
    # GeneralRateModel traits
    # -------------------------------------------------------------------------

    #: The column porosity
    column_porosity = PositiveFloatParameter(0.3)

    #: The bead/resin porosity
    bead_porosity = PositiveFloatParameter(0.5)

    #: Axial dispersion coefficient (m2/s)
    axial_dispersion = PositiveFloatParameter(6.0e-8)

    #: A vector with film diffusion coefficients
    film_mass_transfer = ParameterArray

    #: A vector with particle diffusion coefficients
    pore_diffusion = ParameterArray

    #: A vector with particle surface diffusion coefficients
    surface_diffusion = ParameterArray

    # TransportModel traits ---------------------------------------------------

    #: The type of transport model.
    model_type = Constant(GRM_TRANSPORT_MODEL)

    # GeneralRateModel method -------------------------------------------------

    def __init__(self, num_comp=None, num_prod_comp=None, **traits):
        """ Create a new GeneralRateModel type transport model.

        See parent class for docstring.
        """
        super(GeneralRateModel, self).__init__(
            num_comp=num_comp, num_prod_comp=num_prod_comp, **traits
        )

        # Initialize the array data if not explicitly passed.
        defaults = {'film_mass_transfer': 5e-5, 'pore_diffusion': 1e-11,
                    'surface_diffusion': 0}
        for attr_name, val in defaults.items():
            if getattr(self, attr_name) is None:
                self.trait_set(**{attr_name: np.ones(self.num_comp) * val})

    # Traits property getters/setters -----------------------------------------

    def _get_num_prod_comp(self):
        return self.num_comp - 1

    # Traits initializers -----------------------------------------------------

    def _component_names_default(self):
        prod_comp_names = ['Component' + str(i)
                           for i in range(1, self.num_comp)]
        return ["Cation"] + prod_comp_names
