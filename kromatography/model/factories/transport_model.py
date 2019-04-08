import logging

from kromatography.model.transport_model import GeneralRateModel
from kromatography.utils.string_definitions import \
    DEFAULT_TRANSPORT_MODEL_NAME

logger = logging.getLogger(__name__)


def create_transport_model(num_components,
                           transport_model_type='GENERAL_RATE_MODEL', **traits):  # noqa
    """ Create a new Transport model.

    Parameters
    ----------
    num_components : int
        Number of components including the cation component.

    traits : dict
        Additional attributes for the General rate model. In particular it is
        expected to contain a target_product value.

    Default inspired from realistic values.
    """
    if not num_components or num_components < 2:
        msg = "Failed to build a transport model: need at least 2 components."
        logger.exception(msg)
        raise ValueError(msg)

    if "name" not in traits:
        traits["name"] = DEFAULT_TRANSPORT_MODEL_NAME

    if "target_product" not in traits:
        logger.warning("Creating a transport model without a target product!")

    n_prod_comp = num_components - 1

    if transport_model_type == 'GENERAL_RATE_MODEL':
        transport_model = GeneralRateModel(num_components, **traits)
        transport_model.column_porosity = 0.30
        transport_model.bead_porosity = 0.50
        transport_model.axial_dispersion = 6e-8
        # Values below correspond to the cation component and then all product
        # components:
        transport_model.film_mass_transfer = [6.9e-6] + [5.0e-5] * n_prod_comp
        transport_model.pore_diffusion = [7.0e-10] + [1.0e-11] * n_prod_comp
        transport_model.surface_diffusion = [0.0] * num_components
    else:
        msg = ('Transport model: {!r} is not '
               'supported').format(transport_model_type)
        logger.error(msg)
        raise ValueError(msg)

    return transport_model
