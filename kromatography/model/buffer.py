from traits.api import Constant, Tuple

from kromatography.model.solution import Solution

#: the type id for Buffer
BUFFER_TYPE = 'BUFFER'


class Buffer(Solution):
    """ A Solution with a name but not containing Product
    """

    # -------------------------------------------------------------------------
    # Buffer traits
    # -------------------------------------------------------------------------

    # -------------------------------------------------------------------------
    # ChromatographyData traits
    # -------------------------------------------------------------------------

    #: The type of data being represented by this class
    type_id = Constant(BUFFER_TYPE)

    #: The attributes that identify the data in this object uniquely in a
    #: collection of components
    _unique_keys = Tuple(('name',))
