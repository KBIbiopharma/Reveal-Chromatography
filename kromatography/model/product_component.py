""" ProductComponent Class Implementation """

from traits.api import Constant, Instance, Str, Tuple

from scimath.units.api import UnitScalar

from kromatography.model.chromatography_data import ChromatographyData

PRODUCT_COMPONENT_TYPE = 'PRODUCT_COMPONENT'


class ProductComponent(ChromatographyData):
    """ Repesents one component of a product.
    """

    # -------------------------------------------------------------------------
    # ProductComponent traits
    # -------------------------------------------------------------------------

    #: Target product, optional
    target_product = Str

    #: Molecular weight (kg/mol)
    molecular_weight = Instance(UnitScalar)

    #: Extinction Coefficient (uses extinction_coefficient_unit as units)
    extinction_coefficient = Instance(UnitScalar)

    # -------------------------------------------------------------------------
    # ChromatographyData traits
    # -------------------------------------------------------------------------

    type_id = Constant(PRODUCT_COMPONENT_TYPE)

    _unique_keys = Tuple(('target_product', 'name'))


if __name__ == '__main__':
    from kromatography.model.tests.example_model_data import \
        ACIDIC_1_PRODUCT_COMPONENT_DATA

    comp = ProductComponent(**ACIDIC_1_PRODUCT_COMPONENT_DATA)
