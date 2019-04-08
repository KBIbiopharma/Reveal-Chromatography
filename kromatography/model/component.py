from traits.api import Constant, Instance, Tuple
from scimath.units.api import UnitScalar

from kromatography.model.chromatography_data import ChromatographyData

#: the type id for component
COMPONENT_TYPE = 'COMPONENT'


class Component(ChromatographyData):
    """ Represents the properties associated with a component.
    """
    # -------------------------------------------------------------------------
    # Component traits
    # -------------------------------------------------------------------------

    #: The charge of the component (e.g. Sodium is -1)
    charge = Instance(UnitScalar)

    #: The negative logarithm of the acidity constant of the component
    pKa = Instance(UnitScalar)

    # -------------------------------------------------------------------------
    # ChromatographyData traits
    # -------------------------------------------------------------------------

    #: The type of data being represented by this class
    type_id = Constant(COMPONENT_TYPE)

    #: The attributes that identify the data in this object uniquely in a
    #: collection of components
    _unique_keys = Tuple(('name',))
