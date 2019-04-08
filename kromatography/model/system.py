""" Systems classes (type and specific implementation) to describe the machine
implementing and recording the measurements during the Chromatography process.
"""
from traits.api import Constant, Instance, Int, Str
from scimath.units.api import UnitScalar, UnitArray

from .chromatography_data import ChromatographyData
from app_common.traits.custom_trait_factories import Key

# Module level constants
#: The type-id string for SystemType
SYSTEM_TYPE = 'System Type'

#: The type-id string for the System
SYSTEM = 'Chromatography System'


class SystemType(ChromatographyData):
    """ Represents a particular type of chromatography system, as provided by
    manufacturers.
    """
    # -------------------------------------------------------------------------
    # ColumModel traits
    # -------------------------------------------------------------------------

    #: The name of the manufacturer
    manufacturer = Key()

    #: The name the manufacturer uses.
    manufacturer_name = Str()

    #: The (min, max) flow rates for the system.
    flow_range = Instance(UnitArray)

    #: The number of inlets
    num_inlets = Int

    #: The number of channels
    num_channels = Int

    # -------------------------------------------------------------------------
    # ChromatographyData traits
    # -------------------------------------------------------------------------
    #: The user visible type-id for the class.
    type_id = Constant(SYSTEM_TYPE)


class System(ChromatographyData):
    """ Represents the actual physical chromatography system used in the study.

    An actual system is setup with a specific system type, and a specific set
    of holdup volume and absorbance path length based on the setup.
    """

    #: The id for the chromatography system.
    system_number = Str()

    #: Calibration factor for the UV absorbance results, usually in centimeter.
    abs_path_length = Instance(UnitScalar)

    #: The amount of hold-up volume.
    holdup_volume = Instance(UnitScalar)

    #: The type of the chromatography system.
    system_type = Instance(SystemType)

    # -------------------------------------------------------------------------
    # ChromatographyData traits
    # -------------------------------------------------------------------------
    #: The user visible type-id for the class.
    type_id = Constant(SYSTEM_TYPE)
