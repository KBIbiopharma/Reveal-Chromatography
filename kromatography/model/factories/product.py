
from logging import getLogger

from scimath.units.api import UnitScalar

from kromatography.model.product_component import ProductComponent
from kromatography.utils.string_definitions import STRIP_COMP_NAME
from kromatography.utils.chromatography_units import \
    extinction_coefficient_unit, kilogram_per_mol

logger = getLogger(__name__)


def add_strip_to_product(source_prod, strip_mol_weight=0., strip_ext_coef=0.):
    """ Build a new product to create a version which contains a strip comp.

    Parameters
    ----------
    source_prod : Product
        Product to copy and add a strip component to.

    strip_mol_weight : float or UnitScalar
        Molecular weight of the future strip component to be added.

    strip_ext_coef : float or UnitScalar
        Extinction coefficient of the future strip component to be added.

    Returns
    -------
    tuple
        New Product instance created as the copy of the input product and the
        newly created strip ProductComponent instance.
    """
    # Input validation/transformation
    if isinstance(strip_ext_coef, float):
        strip_ext_coef = UnitScalar(strip_ext_coef,
                                    units=extinction_coefficient_unit)
    if isinstance(strip_mol_weight, float):
        strip_mol_weight = UnitScalar(strip_mol_weight, units=kilogram_per_mol)

    new_prod = source_prod.copy()
    strip_comp = ProductComponent(
        name=STRIP_COMP_NAME,
        target_product=new_prod.name,
        extinction_coefficient=strip_ext_coef,
        molecular_weight=strip_mol_weight
    )
    for comp in new_prod.product_components:
        comp.target_product = new_prod.name

    new_prod.product_components.append(strip_comp)
    new_prod.product_component_assays.append(STRIP_COMP_NAME)
    new_prod.product_component_concentration_exps = \
        new_prod.product_component_concentration_exps.apply(
            lambda x: x + " * (100 - Strip) / 100")
    new_prod.product_component_concentration_exps[STRIP_COMP_NAME] = \
        "product_concentration * {} / 100".format(STRIP_COMP_NAME)

    return new_prod, strip_comp
