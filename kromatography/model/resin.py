from traits.api import Constant, Instance, Str, Tuple
from scimath.units.api import UnitScalar

from app_common.traits.custom_trait_factories import Key, Parameter

from .chromatography_data import ChromatographyData


#: The type id for resin.
RESIN_TYPE = 'RESIN'


class Resin(ChromatographyData):
    """ Represents the properties associated with a sample of resin.
    """
    # -------------------------------------------------------------------------
    # Resin traits
    # -------------------------------------------------------------------------

    #: The lot/batch id for this sample of resin
    lot_id = Str()

    #: The type of the resin.
    resin_type = Key()

    #: The name/id of the ligand in this sample of resin.
    ligand = Str()

    #: The average diameter (um) of the beads in this sample of resin.
    average_bead_diameter = Parameter()

    #: The density of the ligand (mM) in this sample of resin.
    ligand_density = Parameter()

    #: FIXME: better doc : This seems like some kind of normalized
    #: (wrt bed height / compaction factor) porosity.
    settled_porosity = Instance(UnitScalar)

    # -------------------------------------------------------------------------
    # ChromatographyData traits
    # -------------------------------------------------------------------------

    #: The type of data being represented by this class.
    type_id = Constant(RESIN_TYPE)

    #: The attributes that identify the data in this object uniquely in a
    #: collection of resins.
    _unique_keys = Tuple(('name', 'lot_id', 'resin_type', 'type_id'))
