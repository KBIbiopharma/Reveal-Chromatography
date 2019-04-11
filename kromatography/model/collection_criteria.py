from traits.api import Constant, Enum

from .chromatography_data import ChromatographyData
from app_common.traits.custom_trait_factories import Key, ParameterFloat

#: The type-id for this class.
COLLECTION_CRITERIA = "COLLECTION CRITERIA"

#: The list of allowed start and stop collect types
ALLOWED_START_COLLECT_TYPES = [
    "Fixed Volume", "Fixed Absorbance", "Percent Peak Maximum"
]

ALLOWED_STOP_COLLECT_TYPES = [
    "Fixed Volume", "Fixed Absorbance", "Percent Peak Maximum"
]


# FIXME: Add allowed keywords if needed.
# FIXME: Add wavelength for absorbance based start and stop collection criteria
# (default to 280 nm).
# FIXME: Add units for start and stop collection target based on type.
class CollectionCriteria(ChromatographyData):
    """ Represents a criteria used for starting/stoping collection of product
    during the chromatography process.
    """
    # -------------------------------------------------------------------------
    # CollectionCriteria traits
    # -------------------------------------------------------------------------

    #: The methodology used to signal start collecting
    start_collection_type = Key(Enum(ALLOWED_START_COLLECT_TYPES))

    #: When to start collecting
    start_collection_target = ParameterFloat

    #: When to look for target to be reached? While ascending to peak?
    start_collection_while = Enum(["Ascending", "Descending"])

    #: The methodology used to signal stop collecting
    stop_collection_type = Key(Enum(ALLOWED_STOP_COLLECT_TYPES))

    #: When to stop collecting
    stop_collection_target = ParameterFloat

    #: When to look for target to be reached? While descending from peak?
    stop_collection_while = Enum(["Descending", "Ascending"])

    # -------------------------------------------------------------------------
    # ChromatographyData traits
    # -------------------------------------------------------------------------

    #: The type of data being represented by this class.
    type_id = Constant(COLLECTION_CRITERIA)

    def _start_collection_target_default(self):
        return 0.0

    def _stop_collection_target_default(self):
        return 0.0
