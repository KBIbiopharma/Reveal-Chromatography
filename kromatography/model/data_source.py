""" Interface for a DataSource for chromatography experiment data.

A DataSource can contain both a catalog of objects and a catalog of data
(implemented in the SimpleDataSource). A DataSource offers the ability to
lookup an object or its data based on a type and one of its attribute. That
lookup is done ignoring case and treating an underscore and a space as
identical character. A DataSource offers also a constrained way to add new
entries, checking against existing entries for name collision (or near
collisions).
"""

from abc import abstractmethod
import copy
import logging

from traits.api import Bool, Dict, Instance, List

from app_common.traits.has_traits_utils import is_has_traits_almost_equal

from kromatography.model.api import BindingModel, Buffer, Chemical, \
    Column, ColumnType, Component, DataElement, Method, Product, \
    ProductComponent, Resin, SolutionWithProduct, System, SystemType, \
    TransportModel

# List of entries for the user datasource. The order is used by the ITreeNode
# adapter to control the display order:
SIMPLE_DS_OBJECT_TYPES = ['products', 'product_components', 'system_types',
                          'column_models', 'resin_types', 'chemicals',
                          'components', 'transport_models', 'binding_models']

# List of entries for the study datasource. The order is used by the ITreeNode
# adapter to control the display order:
STUDY_DS_OBJECT_TYPES = ["systems", "columns", "buffers", "loads", "methods",
                         "transport_models", "binding_models"]

logger = logging.getLogger(__name__)


class DataSourceCollisionError(KeyError):
    """ Error raised when trying to insert in a datasource an object that
    collides with an existing entry.
    """
    pass


class DataSourceLookupError(KeyError):
    """ Error raised when trying to retrieve an object from a datasource but 0
    or strictly more than 1 object is found to match criteria specified.
    """
    pass


class DataSourceTypeIDError(KeyError):
    """ Error raised when trying to request a typeID that doesn't exist.
    """
    pass


class DataSource(DataElement):
    """ Interface for a data source.

    FIXME: Fill out the API as part of serialization/DB access.
    """
    # -------------------------------------------------------------------------
    # DataSource interface
    # -------------------------------------------------------------------------

    @abstractmethod
    def get_objects_by_type(self, type_id, filter_by=None):
        """ Return a list of known objects of a given type.

        Parameters
        ----------
        type_id : string
            The type_id for the data. For a DB this could be the table name,
            and for a serialized H5 object, this could be the `type_id`
            of the class.

        filter_by : dict
            Key/value(s) to filter the objects of requested type. By default,
            no filtering is done.
        """

    @abstractmethod
    def get_object_type_ids(self):
        """ Return a list of known object type IDs.
        """

    @abstractmethod
    def set_object_of_type(self, type_id, obj):
        """ Add a new object to the object catalog. Raises an error if the name
        of the object is already an entry in the catalog.
        """

    def _name_default(self):
        return "DataSource: unnamed"


class InMemoryDataSource(DataSource):
    """ General in-memory datasource for any kind of objects to be stored.

    The objects are stored in the :attr:`object_catalog`. The keys of this dict
    are called type_ids and are mapped to a list of objects of that type. To
    monitor these lists easily with Traits listeners, these lists are also
    added to the datasource as direct attributes since one cannot listen to
    changes on the values of a dict. These direct lists are the ones exposed in
    the UI and appended to by the user, so dynamic listeners on these lists are
    needed to make sure the object catalog (which is what is serialized) is
    sync-ed up. In this picture, :attr:`_type_ids_map` contains the mapping
    between the type_ids (the keys in the :attr:`object_catalog`) and the name
    of the list attributes.
    """

    # -------------------------------------------------------------------------
    # InMemoryDataSource interface
    # -------------------------------------------------------------------------

    #: A dictionary mapping type_ids to all objects contained by the datasource
    #: of that type.
    object_catalog = Dict

    #: Flag that the datasource was modified since it was last saved.
    dirty = Bool(False)

    #: Maps the type_ids in the object_catalog to list attribute names if any
    _type_ids_map = Dict

    def __init__(self, **traits):
        super(InMemoryDataSource, self).__init__(**traits)

        self._ensure_all_content_in_object_catalog()
        # Initialize the direct list BEFORE adding listeners to detect
        # dirtiness.
        self._initialize_direct_lists()
        self._listen_to_list_changes()

    def _ensure_all_content_in_object_catalog(self):
        """ Make sure the object catalog is complete.

        If an object catalog was stored before a new key was introduced,
        """
        for type_id in self._type_ids_map:
            if type_id not in self.object_catalog:
                self.object_catalog[type_id] = []

    def _initialize_direct_lists(self):
        for type_id in self.object_catalog:
            attr_name = self._type_ids_map[type_id]
            setattr(self, attr_name, self.object_catalog[type_id])

    # -------------------------------------------------------------------------
    # DataSource interface
    # -------------------------------------------------------------------------

    def make_dirty(self):
        """ Manual action to make the DS dirty. Subclasses must call this when
        appropriate.
        """
        self.dirty = True

    def make_clean(self):
        """ Manual action to make the DS clean. Subclasses must call this when
        appropriate.
        """
        self.dirty = False

    def get_objects_by_type(self, type_id, filter_by=None):
        """ Return a (filtered) list of known objects of a given type.

        Parameters
        ----------
        type_id : str
            Type of object searched for.

        filter_by : dict
            Key/value(s) to filter the objects of requested type. By default,
            no filtering is done.
        """
        # Always copy the catalog to avoid the defaults getting modified
        # downstream.
        if type_id in self.object_catalog:
            data = copy.deepcopy(self.object_catalog[type_id])
        else:
            known_ids = self.object_catalog.keys()
            msg = ("Unknown object type {}. This datasource contains the "
                   "following type_ids: {}".format(type_id, known_ids))
            logger.exception(msg)
            raise DataSourceTypeIDError(msg)

        if filter_by is None:
            return data

        matches = []
        for obj in data:
            filters = []
            for key, val in filter_by.items():
                if isinstance(val, basestring):
                    same = standardise(getattr(obj, key)) == standardise(val)
                    filters.append(same)
                elif isinstance(val, dict):
                    sub_object = getattr(obj, key)
                    for sub_key, sub_val in val.items():
                        same = (standardise(getattr(sub_object, sub_key)) ==
                                standardise(sub_val))
                        filters.append(same)
            if all(filters):
                matches.append(obj)
        return matches

    def get_object_of_type(self, type_id, attr_value, attr_name="name",
                           strict=False):
        """ Retrieve object of given type and attribute from object catalog.

        Note that fuzzy matching is applied by default unless strict is set to
        True. That means that filtering happens loosely, treating _ and spaces
        the same and ignoring letter case.

        Parameters
        ----------
        type_id : str
            Type ID of the object searched for.

        attr_value : str
            Value of the attribute of the object searched for.

        attr_name : str [OPTIONAL]
            Name of the attribute to filter on. Defaults to 'name'.

        strict : bool [OPTIONAL]
            Whether to apply strict or fuzzy object attribute matching.
            Defaults to False.

        Returns
        -------
        ChromatographyData
            Object with the correct name and type_id.

        Raises
        ------
        DataSourceLookupError
            Raised if the request leads to 0 or 2+ candidates.

        Notes
        -----
        TODO: support a more complex filter instead of just a name, though
        allow someone wanting to request just a name to do so simply.

        FIXME: Why not reusing here get_objects_by_type? Something like
        self.get_objects_by_type(type_id, filter_by={'name': object_name})
        """
        self._check_type_id(type_id)

        if strict:
            def transform(x):
                return x
        else:
            transform = standardise

        def match(obj):
            return transform(getattr(obj, attr_name)) == transform(attr_value)

        candidates = [val for val in self.object_catalog[type_id]
                      if match(val)]

        if len(candidates) == 0:
            known_objects = self.get_object_names_by_type(type_id,
                                                          key=attr_name)
            msg = "Datasource '{0}' doesn't contain a {1} with {3} '{2}'. " \
                  "Did you forget to create it? The known {1} are {4}."
            msg = msg.format(self.name, type_id, attr_value, attr_name,
                             known_objects)
            logger.exception(msg)
            raise DataSourceLookupError(msg)

        elif len(candidates) > 1:
            msg = "More than 1 {} found with {} '{}' in datasource '{}'. " \
                  "Make your query more specific or use get_objects_by_type " \
                  "to get a list of candidates."
            msg = msg.format(type_id, attr_name, attr_value, self.name)
            logger.exception(msg)
            raise DataSourceLookupError(msg)

        return candidates[0]

    def get_object_names_by_type(self, type_id, key="name"):
        """ Return the list of names (or another key) for a type_id. """
        return [getattr(val, key) for val in self.object_catalog[type_id]]

    def set_object_of_type(self, type_id, obj):
        """ Add a new object to the object catalog. Raises an error if there is
        already an object in the catalog with the same unique_id or if the
        type_id doesn't already exist.

        Parameters
        ----------
        type_id : str
            Type of object to add. Must be a type already known by the DS.

        obj : ChromatographyData
            Object to add to the datasource.
        """
        self._check_type_id(type_id)

        known_entries = self.get_objects_by_type(type_id,
                                                 filter_by=obj.unique_id)
        if known_entries:
            # It's enough to test equality against the first known entry
            # because each entry will iteratively be tested (as long as this
            # method is used).
            known_obj = known_entries[0]
            equal, msg = is_has_traits_almost_equal(obj, known_obj)

            if not equal:
                msg = ("There is already an object named {} in the {} "
                       "catalog and it is different from the one being "
                       "added ({}).".format(obj.name, type_id, msg))
                logger.exception(msg)
                raise DataSourceCollisionError(msg)
            else:
                logger.debug("Object {} already present".format(obj.name))
                return

        # Appending the new object via the direct list access because that's
        # listened to by the data explorer:
        try:
            attr_name = self._type_ids_map[type_id]
        except KeyError:
            msg = "Failed to find a mapping for type ID {}".format(type_id)
            logger.exception(msg)
            raise DataSourceTypeIDError(msg)
        try:
            getattr(self, attr_name).append(obj)
        except AttributeError as e:
            msg = ("Failed to find the direct object list {} (for type ID "
                   "{}). Error was {}".format(type_id, attr_name, e))
            logger.exception(msg)
            raise DataSourceTypeIDError(msg)

        # Store the sub-objects there is an entry for:
        if type_id == "methods":
            for step in obj.method_steps:
                for solution in step.solutions:
                    if isinstance(solution, Buffer):
                        self.set_object_of_type("buffers", solution)
                    elif isinstance(solution, SolutionWithProduct):
                        self.set_object_of_type("loads", solution)
        elif type_id == "products":
            for component in obj.product_components:
                self.set_object_of_type("product_components", component)

    def get_object_type_ids(self):
        """ Return a list of known object type IDs.
        """
        return self.object_catalog.keys()

    # -------------------------------------------------------------------------
    # InMemoryDataSource interface
    # -------------------------------------------------------------------------

    def direct_list_changed(self):
        """ A change was made to the list attribute specified. Update dirty
        flag and object_catalog.

        Parameters
        ----------
        list_names : str
            Name of the direct list that changed.
        """
        self.resync_object_catalog()
        self.make_dirty()

    def resync_object_catalog(self, type_ids=None):
        """ Sync the object catalog with the list attributes of the DS.

        Parameters
        ----------
        type_ids : list of str
            List of type_ids to resync. By default it will resync all type_ids.
        """
        if type_ids is None:
            type_ids = self.object_catalog.keys()

        for type_id in type_ids:
            attr_name = self._type_ids_map[type_id]
            self.object_catalog[type_id] = getattr(self, attr_name)

    def _listen_to_list_changes(self):
        """ Set state to dirty when the lists of all objects is changed.

        FIXME: add detection of a modification inside one element.
        """
        for type_id, attr_name in self._type_ids_map.items():
            self.on_trait_change(self.direct_list_changed, attr_name)
            self.on_trait_change(self.direct_list_changed,
                                 attr_name + "[]")

    # -------------------------------------------------------------------------
    # Private interface
    # -------------------------------------------------------------------------

    def _check_type_id(self, type_id):
        """ Raises an exception if provided type_id unsupported by DS.

        Parameters
        ----------
        type_id : str
            Name of the type_id to check.

        Raises
        ------
        DataSourceTypeIDError
            If the type_id isn't supported.
        """
        supported_type_ids = self.get_object_type_ids()
        if type_id not in supported_type_ids:
            msg = "Unable to handle objects of type {}. Type IDs supported " \
                  "by datasource {} are {}."
            msg = msg.format(type_id, self.name, supported_type_ids)
            logger.exception(msg)
            raise DataSourceTypeIDError(msg)

    def _name_default(self):
        return "InMemoryDataSource: unnamed"


class InStudyDataSource(InMemoryDataSource):
    """ Implementation of the InMemoryDataSource to store study specific data.

    In addition to the object_catalog, it contains direct access to entries in
    it (used by the data explorer). Note: event though, all these entries are
    dictionaries, they are declared as Any rather than Dict so that they can be
    the same object, rather than wrappers around the target dict.
    """
    buffers = List(Instance(Buffer))

    loads = List(Instance(SolutionWithProduct))

    columns = List(Instance(Column))

    systems = List(Instance(System))

    methods = List(Instance(Method))

    binding_models = List(Instance(BindingModel))

    transport_models = List(Instance(TransportModel))

    def _object_catalog_default(self):
        """ Initialize the object_catalog from the direct list attributes.
        """
        return {type_id: getattr(self, self._type_ids_map[type_id])
                for type_id in STUDY_DS_OBJECT_TYPES}

    def __type_ids_map_default(self):
        """ Returns the default map type_id -> attribute name.
        """
        # Manually build this dict if the names must be different
        return {type_id: type_id for type_id in STUDY_DS_OBJECT_TYPES}

    def _name_default(self):
        return "Study DataSource: unnamed"


class SimpleDataSource(InMemoryDataSource):
    """ Implementation of in-memory version of general user/multi-study DS.

    Used to implement the user datasource, which provides building blocks for
    study to be built. It contains hardcoded default objects to get started,
    but users can contribute, store and load their custom study components.
    """
    # -------------------------------------------------------------------------
    # SimpleDataSource interface
    # -------------------------------------------------------------------------

    #: Direct access to entries in object_catalog (can be listened to)
    products = List(Instance(Product))

    product_components = List(Instance(ProductComponent))

    chemicals = List(Instance(Chemical))

    resin_types = List(Instance(Resin))

    column_models = List(Instance(ColumnType))

    components = List(Instance(Component))

    system_types = List(Instance(SystemType))

    binding_models = List(Instance(BindingModel))

    transport_models = List(Instance(TransportModel))

    @classmethod
    def from_data_catalog(cls, data_catalog, **traits):
        object_catalog = build_object_catalog(data_catalog)
        return cls(object_catalog=object_catalog, **traits)

    # Traits initialization methods -------------------------------------------

    def _object_catalog_default(self):
        return build_object_catalog()

    def _name_default(self):
        return "Simple DataSource"

    def __type_ids_map_default(self):
        """ Returns the default map type_id -> attribute name.
        """
        # Manually build this dict if the names must be different
        return {type_id: type_id for type_id in SIMPLE_DS_OBJECT_TYPES}


def standardise(str_input):
    return str_input.lower().replace(" ", "_")


def is_simple_datasource_blank(datasource):
    """ Is the provided datasource equivalent to the default SimpleDataSource?
    """
    blank_ds = SimpleDataSource()
    return is_has_traits_almost_equal(datasource, blank_ds)[0]


def build_object_catalog(data_catalog=None):
    """ Convert a data_catalog into an object catalog.

    Parameters
    ----------
    data_catalog : dict
        Dictionary mapping object types to data to build them.

    Returns
    -------
    dict
        Dictionary mapping object types to a list of objects to populate a
        SimpleDataSource with.
    """
    from kromatography.model.factories.user_datasource import \
        DataSourceObjectCatalogBuilder

    if data_catalog:
        builder = DataSourceObjectCatalogBuilder(data_catalog=data_catalog)
    else:
        builder = DataSourceObjectCatalogBuilder()

    builder.build_object_catalog()
    return builder.object_catalog
