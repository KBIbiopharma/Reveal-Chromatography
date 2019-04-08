import numpy as np
from logging import getLogger

from traits.api import Constant, Dict, Enum, List, Tuple

from kromatography.model.base_product_model import BaseProductModel
from app_common.traits.custom_trait_factories import ParameterArray, \
    PositiveFloatParameter

logger = getLogger(__name__)

LANGMUIR_BINDING_MODEL = 'MULTI-COMPONENT LANGMUIR MODEL'

PH_LANGMUIR_BINDING_MODEL = 'pH-DEPENDENT LANGMUIR MODEL'

STERIC_BINDING_MODEL = 'STERIC MASS ACTION'

PH_STERIC_BINDING_MODEL = 'pH-DEPENDENT STERIC MASS ACTION'

BINDING_MODEL_TYPE = 'BindingModel'


class BindingModel(BaseProductModel):
    """ Base class for all binding models.
    """
    #: The type of binding model (e.g. STERIC_MASS_ACTION) used for the
    #: chromatography simulation.
    model_type = Enum(values="all_model_types")

    all_model_types = List

    #: Kinetic rate expression or isotherm
    is_kinetic = Enum([0, 1])

    # ChromatographyData traits -----------------------------------------------

    #: The type of data being represented by this class
    type_id = Constant(BINDING_MODEL_TYPE)

    #: Attributes that identify an instance uniquely in a collection
    _unique_keys = Tuple(('target_product', 'name'))

    def _all_model_types_default(self):
        return BINDING_MODEL_TYPES


class StericMassAction(BindingModel):
    """ Steric Mass Action (SMA) Binding Model.
    """
    # -------------------------------------------------------------------------
    # Steric Mass Action binding model traits
    # -------------------------------------------------------------------------

    #: A vector with adsorption rate constants in the steric mass action model
    sma_ka = ParameterArray

    #: A vector with desorption rate constants in the steric mass action model
    sma_kd = ParameterArray

    #: Stationary phase capacity (monovalent salt counterions); The total
    #: number of binding sites available on the resin surface
    sma_lambda = PositiveFloatParameter(0.0)

    #: A vector with characteristic charges of the protein; The number of sites
    #: nu that the protein interacts with on the resin surface
    sma_nu = ParameterArray

    #: A vector with steric factors of the protein; The number of sites sigma
    #: on the surface that are shielded by the protein and prevented from
    #: exchange with the salt counteri- ons in solution
    sma_sigma = ParameterArray

    # -------------------------------------------------------------------------
    # BindingModel traits
    # -------------------------------------------------------------------------

    #: The type of binding model.
    model_type = Constant(STERIC_BINDING_MODEL)

    # List of attribute names that CADET expects in the HDF5 input file.
    _cadet_input_keys = List(['sma_lambda', 'sma_nu', 'is_kinetic',
                              'sma_sigma', 'sma_kd', 'sma_ka'])

    # Steric Mass Action binding model methods --------------------------------

    def __init__(self, num_comp=None, num_prod_comp=None, **traits):
        """ Create new SMA binding model targeting specific product.

        Parameters
        ----------
        num_comp : int [OPTIONAL]
            Number of component the binding model describes, including the
            cation component. If unspecified, computed from `num_prod_comp`.

        num_prod_comp : int [OPTIONAL]
            Number of product components. The binding model created will
            contain parameters for these as well as an additional cation
            component. Ignored if `num_comp` is specified.

        traits : dict
            Additional parameters for the new binding model. The only required
            parameter is a name.
        """
        super(StericMassAction, self).__init__(
            num_comp=num_comp, num_prod_comp=num_prod_comp, **traits
        )

        defaults = {'sma_ka': 1, 'sma_kd': 1, 'sma_nu': 5, 'sma_sigma': 100}
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


class PhDependentStericMassAction(StericMassAction):
    """ pH dependent steric Mass Action (SMA) Binding Model.

    Note that this class inherits the parameters sma_ka, sma_nu, sma_sigma, but
    these values in this model don't represent the center value anymore but the
    constant term in the pH dependence. if nominal pH is 5 during the
    experiment, the effective ka will be::

        ka = exp(sma_ka + sma_ka_ph * pH + sma_ka_ph2 * pH**2)

    Similarly for the other parameters::

        kd = exp(sma_kd + sma_kd_ph * pH + sma_kd_ph2 * pH**2)

        sigma = sma_sigma + sma_sigma_ph * pH + sma_sigma_ph2 * pH**2

        nu = sma_nu + sma_nu_ph * pH + sma_nu_ph2 * pH**2

    """
    # -------------------------------------------------------------------------
    # pH-dependent Steric Mass Action binding model traits
    # -------------------------------------------------------------------------

    #: A vector with pH linear dependence of adsorption rate constants
    sma_ka_ph = ParameterArray

    #: Vector with pH quadratic dependence of adsorption rate constants
    sma_ka_ph2 = ParameterArray

    #: Vector with pH linear dependence of desorption rate constants
    sma_kd_ph = ParameterArray

    #: Vector with pH quadratic dependence of desorption rate constants
    sma_kd_ph2 = ParameterArray

    #: Vector with pH linear dependence of characteristic charges of protein
    sma_nu_ph = ParameterArray

    #: Vector with pH quadratic dependence of characteristic charges of protein
    sma_nu_ph2 = ParameterArray

    #: Vector with pH linear dependence of steric factors of the protein
    sma_sigma_ph = ParameterArray

    #: Vector with pH linear dependence of steric factors of the protein
    sma_sigma_ph2 = ParameterArray

    # -------------------------------------------------------------------------
    # BindingModel traits
    # -------------------------------------------------------------------------

    #: The type of binding model.
    model_type = Constant(PH_STERIC_BINDING_MODEL)

    #: Mapping of attribute names to what CADET expects in the HDF5 input file.
    _cadet_input_keys = Dict

    # -------------------------------------------------------------------------
    # PhDependentStericMassAction methods
    # -------------------------------------------------------------------------

    def __init__(self, num_comp=None, num_prod_comp=None, **traits):
        """ Create a new pH dependent binding model.

        See parent class for docstring.
        """
        super(PhDependentStericMassAction, self).__init__(
            num_comp=num_comp, num_prod_comp=num_prod_comp, **traits
        )

        # Initialize the coefficients: vector of length ncomp containing zeros
        ph_dep_attrs = ['sma_ka_ph', 'sma_ka_ph2', 'sma_kd_ph', 'sma_kd_ph2',
                        'sma_nu_ph', 'sma_nu_ph2', 'sma_sigma_ph',
                        'sma_sigma_ph2']
        for attr_name in ph_dep_attrs:
            if getattr(self, attr_name) is None:
                self.trait_set(**{attr_name: np.zeros(self.num_comp)})

    def __cadet_input_keys_default(self):
        return {'sma_lambda': 'extsmaph_lambda', 'sma_nu': 'extsmaph_nu',
                'is_kinetic': 'is_kinetic', 'sma_sigma': 'extsmaph_sigma',
                'sma_kd': 'extsmaph_kd', 'sma_ka': 'extsmaph_ka',
                'sma_ka_ph': 'extsmaph_ka_e', 'sma_ka_ph2': 'extsmaph_ka_ee',
                'sma_kd_ph': 'extsmaph_kd_e', 'sma_kd_ph2': 'extsmaph_kd_ee',
                'sma_nu_ph': 'extsmaph_nu_p', 'sma_nu_ph2': 'extsmaph_nu_pp',
                'sma_sigma_ph': 'extsmaph_sigma_p',
                'sma_sigma_ph2': 'extsmaph_sigma_pp'}


class Langmuir(BindingModel):
    """ Multi-Component Langmuir Binding Model.
    """
    # Langmuir binding model traits -------------------------------------------

    #: Adsorption rate constant coefficients in the MCL Langmuir model
    mcl_ka = ParameterArray

    #: Desorption rate denominator coefficients in the MCL Langmuir model
    mcl_kd = ParameterArray

    #: Maximum adsorption capacity coefficients in the MCL Langmuir model
    mcl_qmax = ParameterArray

    # BindingModel traits -----------------------------------------------------

    #: The type of binding model.
    model_type = Constant(LANGMUIR_BINDING_MODEL)

    _cadet_input_keys = List

    def __cadet_input_keys_default(self):
        return ['is_kinetic', 'mcl_ka', 'mcl_kd', 'mcl_qmax']

    # Langmuir binding model methods ------------------------------------------

    def __init__(self, num_comp=None, num_prod_comp=None, **traits):
        """ Create new Langmuir binding model targeting a specific product.

        See parent class for docstring.
        """
        super(Langmuir, self).__init__(
            num_comp=num_comp, num_prod_comp=num_prod_comp, **traits
        )

        for attr_name in self._cadet_input_keys:
            if attr_name == "is_kinetic":
                continue

            # Initialize the coefficients: vector of length ncomp containing
            # zeros
            if getattr(self, attr_name) is None:
                if attr_name == "mcl_kd":
                    self.trait_set(**{attr_name: np.ones(self.num_comp)})
                else:
                    self.trait_set(**{attr_name: np.zeros(self.num_comp)})

    # Traits property getters/setters -----------------------------------------

    def _get_num_prod_comp(self):
        """ In the case of Langmuir, there is no cation component. """
        return self.num_comp

    # Traits initializer methods ----------------------------------------------

    def _component_names_default(self):
        prod_comp_names = ['Component' + str(i)
                           for i in range(self.num_comp)]
        return prod_comp_names


class ExternalLangmuir(Langmuir):
    """ Langmuir Binding Model w/ parameters depending on an external profile.
    """
    # Additional external Langmuir binding model traits -----------------------

    #: All vectors with adsorption rate constant coefficients in the External
    #: Function Langmuir model
    extl_ka_t = ParameterArray
    extl_ka_tt = ParameterArray
    extl_ka_ttt = ParameterArray

    #: All vectors with desorption rate constant coefficients in the External
    #: Function Langmuir model
    extl_kd_t = ParameterArray
    extl_kd_tt = ParameterArray
    extl_kd_ttt = ParameterArray

    #: All vectors with maximum adsorption capacity coefficients in the
    #: External Function Langmuir model
    extl_qmax_t = ParameterArray
    extl_qmax_tt = ParameterArray
    extl_qmax_ttt = ParameterArray

    # BindingModel traits -----------------------------------------------------

    #: The type of binding model.
    model_type = Constant(PH_LANGMUIR_BINDING_MODEL)

    _cadet_input_keys = Dict

    def __cadet_input_keys_default(self):
        return {'is_kinetic': 'is_kinetic', 'mcl_ka': 'extl_ka',
                'extl_ka_t': 'extl_ka_t', 'extl_ka_tt': 'extl_ka_tt',
                'extl_ka_ttt': 'extl_ka_ttt', 'mcl_kd': 'extl_kd',
                'extl_kd_t': 'extl_kd_t', 'extl_kd_tt': 'extl_kd_tt',
                'extl_kd_ttt': 'extl_kd_ttt', 'mcl_qmax': 'extl_qmax',
                'extl_qmax_t': 'extl_qmax_t', 'extl_qmax_tt': 'extl_qmax_tt',
                'extl_qmax_ttt': 'extl_qmax_ttt'}

    def __init__(self, num_comp=None, num_prod_comp=None, **traits):
        """ Create a new pH dependent binding model.

        See parent class for docstring.
        """
        super(ExternalLangmuir, self).__init__(
            num_comp=num_comp, num_prod_comp=num_prod_comp, **traits
        )

        # Initialize the coefficients: vector of length ncomp containing zeros
        ph_dep_attrs = ['extl_ka_t', 'extl_ka_tt', 'extl_ka_ttt', 'extl_kd_t',
                        'extl_kd_tt', 'extl_kd_ttt', 'extl_qmax_t',
                        'extl_qmax_tt', 'extl_qmax_ttt']
        for attr_name in ph_dep_attrs:
            if getattr(self, attr_name) is None:
                self.trait_set(**{attr_name: np.zeros(self.num_comp)})


KLASS_MAP = {STERIC_BINDING_MODEL: StericMassAction,
             PH_STERIC_BINDING_MODEL: PhDependentStericMassAction,
             LANGMUIR_BINDING_MODEL: Langmuir,
             PH_LANGMUIR_BINDING_MODEL: ExternalLangmuir}

BINDING_MODEL_TYPES = [STERIC_BINDING_MODEL, PH_STERIC_BINDING_MODEL,
                       LANGMUIR_BINDING_MODEL, PH_LANGMUIR_BINDING_MODEL]
