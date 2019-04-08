import logging
import copy

from traits.api import Dict, HasTraits, List

from kromatography.model.data_source import InMemoryDataSource, standardise
from kromatography.model.product import Product
from kromatography.model.product_component import ProductComponent
from kromatography.model.resin import Resin
from kromatography.model.component import Component
from kromatography.model.chemical import Chemical
from kromatography.model.system import SystemType
from kromatography.model.column import ColumnType

# User DS types and corresponding constructors
CONSTRUCTORS = {'products': Product,
                'product_components': ProductComponent,
                'resin_types': Resin,
                'column_models': ColumnType,
                'components': Component,
                'system_types': SystemType,
                'chemicals': Chemical,
                }

logger = logging.getLogger(__name__)


class DataSourceObjectCatalogBuilder(InMemoryDataSource):
    """ Build an object catalog for a UserDataSource from one of the default
    data catalog that ship with kromatography. Used to initialize the user
    datasource when users start.

    Note that
    """
    #: Dict containing data for known types of objects needed for a study
    data_catalog = Dict

    #: Dict containing objects for known types of objects needed for a study
    object_catalog = Dict

    #: List of object types to create, in order they need to be built.
    ordered_object_types = List

    def __init__(self, **traits):
        HasTraits.__init__(self, **traits)

    # Data getter methods -----------------------------------------------------

    def get_data_by_type(self, type_id, key=('name', None)):
        """ Returns the data to build an object of type type_id, that match the
        key value passed as key attr. The lookup on the key is done by ignoring
        letter case and treating `_` and spaces the same (standardize).

        TODO: support passing a list of keys.
        """
        # Copy the data to avoid the defaults getting modified downstream.
        data = copy.deepcopy(self.data_catalog[type_id])

        key_name, key_val = key
        if key_val is None:
            return data
        else:
            matches = [val for val in data
                       if standardise(val[key_name]) == standardise(key_val)]
            if len(matches) > 1:
                msg = ("More than 1 data entry of type {} and with {}~{} was "
                       "found.".format(type_id, key_name, key_val))
                logger.warning(msg)
            elif len(matches) == 0:
                msg = "No data entry of type {} and with {}~{} was found."
                logger.warning(msg.format(type_id, key_name, key_val))

            return matches

    def get_data_of_type(self, type_id, obj_name):
        """ Returns the data for type type_id, that match the provided name.

        This relies on the fact that there can be only 1 object of a given type
        with a given name.
        """
        return self.get_data_by_type(type_id, key=('name', obj_name))

    # Build methods -----------------------------------------------------------

    def build_object_catalog(self):
        """ Convert the catalog (which contains data) into a catalog of objects
        """
        # Building all objects from data catalog, in specific order to respect
        # dependencies.
        for type_id in self.ordered_object_types:
            objects = self.build_all_objects_for_type(type_id)
            self.object_catalog[type_id] = objects

    def build_all_objects_for_type(self, object_type):
        objects = []
        try:
            all_object_data = self.get_data_by_type(object_type)
        except KeyError:
            # Type that doesn't have data
            all_object_data = []

        for object_data in all_object_data:
            obj = self.build_object_from_data(object_type, object_data)
            objects.append(obj)

        return objects

    # -------------------------------------------------------------------------
    # Constructors for 1 object
    # -------------------------------------------------------------------------

    def build_object_from_data(self, object_type, object_data):
        """ General object builder from stored data.
        """
        if object_type == 'chemicals':
            return self.build_chemical_from_data(object_data)
        elif object_type == 'products':
            return self.build_product_from_data(object_data)
        else:
            return CONSTRUCTORS[object_type](**object_data)

    def build_chemical_from_data(self, chemical_data):
        """ Custom object builder from stored chemical data.
        """
        comp_names = chemical_data.pop('component_names')
        try:
            chemical_data['component_list'] = [
                self.get_object_of_type('components', comp)
                for comp in comp_names
                ]
        except KeyError as e:
            msg = ("Failed to load one of the components ({}) from all "
                   "(chemical) components of the datasource. Did you populate "
                   "the component objects before the chemicals? Error was "
                   "{}.".format(e))
            logger.exception(msg)
            raise KeyError(msg)

        return Chemical(**chemical_data)

    def build_product_from_data(self, product_data):
        """ Custom object builder from stored product data.
        """
        product_name = product_data["name"]

        def collect_product_comp(component_name):
            """ Lookup component based on the product name and the component
            name.
            """
            # FIXME: support multiple key filters in get_objects_by_type so
            # that we can have a key containing both the component_name and the
            # target_product
            key = {'target_product': product_name}
            objects = self.get_objects_by_type('product_components',
                                               filter_by=key)
            candidates = [obj for obj in objects if obj.name == component_name]
            if len(candidates) == 0:
                available_obj = [obj.name for obj in objects]
                msg = ("Failed to load one of the product components ({}) from"
                       " all product components of the datasource ({}). Did "
                       "you populate the product component objects before the "
                       "products?".format(component_name, available_obj))
                logger.exception(msg)
                raise KeyError(msg)
            else:
                return candidates[0]

        comp_names = product_data.pop('product_components')
        product_data['product_components'] = [collect_product_comp(comp)
                                              for comp in comp_names]
        return Product(**product_data)

    # Traits initialization methods -------------------------------------------

    def _ordered_object_types_default(self):
        # This list will be used to build all objects from data catalog. Must
        # be done in specific order to respect object dependencies.
        all_object_entries = ["product_components", "products", "components",
                              "chemicals", "resin_types", "column_models",
                              "system_types", "binding_models",
                              "transport_models"]
        return all_object_entries

    def _data_catalog_default(self):
        """ Collect the default data catalog based on whether the internal or
        only the external one is available.
        """
        try:
            # This version contains KBI specific information and is excluded
            # from the version of the software that ships to external customers
            from kromatography.data_internal.data_source_content import \
                DATA_CATALOG
            msg = "Initializing the data from the internal data catalog"
            logger.warning(msg)
        except ImportError:
            from kromatography.data_release.data_source_content import \
                DATA_CATALOG
            msg = "Initializing the data from the external data catalog"
            logger.warning(msg)

        return DATA_CATALOG
