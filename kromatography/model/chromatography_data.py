import logging

from traits.api import Dict, Property, Tuple

from app_common.model_tools.data_element import DataElement
from app_common.traits.custom_trait_factories import Key

logger = logging.getLogger(__name__)


class ChromatographyData(DataElement):
    """ Base class for all the data objects.

    Provides a base class describing the API for all the data objects in a
    chromatography workflow. These objects are assumed to have two special
    kinds of data:

        * key : refers to identifying data (name, lot id etc.)
        * parameter : a physical quantity (bead diameter etc.)
    """
    # -------------------------------------------------------------------------
    # ChromatographyData interface
    # -------------------------------------------------------------------------

    #: The human readable id for the type of this data (product, resin etc)
    type_id = Key()

    #: The id that uniquely identifies the data to the user. Key-value map
    #: pairs for keys in _unique_keys.
    unique_id = Property(Dict)

    #: Attributes that uniquely identifies an instance in a list of objects.
    #: For objects that are supposed to be uniquely named, the uuid should be
    #: left out in subclasses.
    _unique_keys = Tuple(('name', 'type_id', 'uuid'))

    # -------------------------------------------------------------------------
    # HasTraits interface
    # -------------------------------------------------------------------------

    def __init__(self, **traits):
        try:
            super(ChromatographyData, self).__init__(**traits)
        except TypeError as e:
            klass = self.__class__.__name__
            msg = "Exception while trying to create a {}. Values passed are " \
                  "{}. Error was {}.".format(klass, traits, e)
            logger.exception(msg)
            raise TypeError(msg)

        # Basic validation
        for name in self.trait_names():
            tr = self.trait(name)
            if not tr.is_key:
                continue

            # if the trait is a key trait, make sure it is set
            value = getattr(self, name)
            if value not in ['', None]:
                continue

            # if a key trait is not initialized on construction, raise an
            # error.
            msg = 'Key attribute {!r} of {} must be a valid string, but got {}'
            msg = msg.format(name, self.__class__.__name__, type(name))
            logger.exception(msg)
            raise ValueError(msg)

    def __str__(self):
        return "{} {} (id={})".format(self.type_id.capitalize(), self.name,
                                      id(self))

    # trait getters and setters -----------------------------------------------

    def _get_unique_id(self):
        obj_id = {}
        for key in self._unique_keys:
            val = getattr(self, key)
            if isinstance(val, ChromatographyData):
                val = val.unique_id
            obj_id[key] = val
        return obj_id
