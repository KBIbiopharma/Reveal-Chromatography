import logging
import numpy as np

from kromatography.model.binding_model import BINDING_MODEL_TYPES, \
    PH_STERIC_BINDING_MODEL, STERIC_BINDING_MODEL, KLASS_MAP, \
    LANGMUIR_BINDING_MODEL, PH_LANGMUIR_BINDING_MODEL
from kromatography.utils.string_definitions import \
    DEFAULT_BINDING_MODEL_NAME, DEFAULT_PH_BINDING_MODEL_NAME

logger = logging.getLogger(__name__)

# Keq = Ka/Kd, so by default, setting Kd to 1, to make Keq and Ka the same
# quantity
DEFAULT_SMA_VALUES = {'sma_ka': 0.001, 'sma_kd': 1., 'sma_nu': 5.0,
                      'sma_lambda': 646, 'sma_sigma': 5.0}

DEFAULT_PH_SMA_VALUES = {'sma_ka': 5.0, 'sma_ka_ph': -2.0, "sma_ka_ph2": 0.0,
                         'sma_kd': 1.0, 'sma_kd_ph': 0.0, "sma_kd_ph2": 0.0,
                         'sma_nu': 5.0, 'sma_nu_ph': -1.0,
                         'sma_sigma': 5.0, 'sma_sigma_ph': 0.0,
                         'sma_lambda': 646}

DEFAULT_LANG_VALUES = {'mcl_ka': 1., 'mcl_kd': 1., 'mcl_qmax': 5.}

DEFAULT_EXT_LANG_VALUES = {'mcl_ka': 1., 'extl_ka_t': 0., 'extl_ka_tt': 0.,
                           'extl_ka_ttt': 0., 'mcl_kd': 1., 'extl_kd_t': 0.,
                           'extl_kd_tt': 0., 'extl_kd_ttt': 0.,
                           'mcl_qmax': 5., 'extl_qmax_t': 0.,
                           'extl_qmax_tt': 0., 'extl_qmax_ttt': 0.}

DEFAULT_VALUES = {STERIC_BINDING_MODEL: DEFAULT_SMA_VALUES,
                  PH_STERIC_BINDING_MODEL: DEFAULT_PH_SMA_VALUES,
                  LANGMUIR_BINDING_MODEL: DEFAULT_LANG_VALUES,
                  PH_LANGMUIR_BINDING_MODEL: DEFAULT_EXT_LANG_VALUES}

SMA_TYPES = [STERIC_BINDING_MODEL, PH_STERIC_BINDING_MODEL]


def create_binding_model(num_components, model_type=STERIC_BINDING_MODEL,
                         **traits):
    """ Create binding model w/ default values inspired from realistic models.

    Parameters
    ----------
    num_components : int
        Number of components including the cation/salt component.

    model_type : str
        Type of binding model to create. Must be one of the values listed in
        :py:`kromatography.model.binding_model.BINDING_MODEL_TYPES`.

    traits : dict
        Additional attributes for the binding model to be created with.
    """
    # There has to be at least 1 real product component:
    min_num_comps = 2 if model_type in SMA_TYPES else 1
    if not num_components or num_components < min_num_comps:
        msg = "Failed to build a binding model: need at least {} components."
        logger.exception(msg.format(min_num_comps))
        raise ValueError(msg.format(min_num_comps))

    if "name" not in traits:
        if model_type == STERIC_BINDING_MODEL:
            traits["name"] = DEFAULT_BINDING_MODEL_NAME
        else:
            traits["name"] = DEFAULT_PH_BINDING_MODEL_NAME

    if "target_product" not in traits:
        logger.warning("Creating a binding model without a target product!")

    if model_type not in BINDING_MODEL_TYPES:
        msg = 'Binding model: {!r} is not supported'.format(model_type)
        logger.exception(msg)
        raise ValueError(msg)

    klass = KLASS_MAP[model_type]
    binding_model = klass(num_components, **traits)
    binding_model.is_kinetic = 0

    if model_type in SMA_TYPES:
        n_prod_comp = num_components - 1
        binding_model.sma_lambda = DEFAULT_SMA_VALUES["sma_lambda"]
        # Values below correspond to the cation component and then all product
        # components:
        for param in ["sma_nu", "sma_sigma", "sma_ka", "sma_kd"]:
            default_val = DEFAULT_VALUES[model_type][param]
            value = [0.0] + [default_val] * n_prod_comp
            setattr(binding_model, param, np.array(value))

        if model_type == PH_STERIC_BINDING_MODEL:
            ph_params = ["sma_ka_ph", "sma_ka_ph2", "sma_kd_ph", "sma_kd_ph2",
                         "sma_nu_ph", "sma_sigma_ph"]
            for param in ph_params:
                prod_comp_val = DEFAULT_PH_SMA_VALUES[param]
                value = [0.0] + [prod_comp_val] * n_prod_comp
                setattr(binding_model, param, np.array(value))
    else:
        n_prod_comp = num_components
        for param in ['mcl_ka', 'mcl_kd', 'mcl_qmax']:
            default_val = DEFAULT_VALUES[model_type][param]
            value = [default_val] * n_prod_comp
            setattr(binding_model, param, np.array(value))

        if model_type == PH_LANGMUIR_BINDING_MODEL:
            params = ['extl_ka_t', 'extl_ka_tt', 'extl_ka_ttt', 'extl_kd_t',
                      'extl_kd_tt', 'extl_kd_ttt', 'extl_qmax_t',
                      'extl_qmax_tt', 'extl_qmax_ttt']

            for param in params:
                default_val = DEFAULT_VALUES[model_type][param]
                value = [default_val] * n_prod_comp
                setattr(binding_model, param, np.array(value))

    return binding_model
