""" ProductComponentAssay Class Implementation (just a name for now.)
"""

from traits.api import Constant, Tuple

from kromatography.model.chromatography_data import ChromatographyData

PRODUCT_COMPONENT_ASSAY_TYPE = 'PRODUCT_COMPONENT_ASSAY'


class ProductComponentAssay(ChromatographyData):
    """ Assay class to describe the product's list of component assays.
    """
    # -------------------------------------------------------------------------
    # ChromatographyData traits
    # -------------------------------------------------------------------------

    type_id = Constant(PRODUCT_COMPONENT_ASSAY_TYPE)

    _unique_keys = Tuple(('name',))
