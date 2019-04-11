# FIXME: scimath bug #55: eval operations in this module fail with future
# division
# from __future__ import division
import logging
import numpy as np

from scimath.units.api import UnitArray, UnitScalar
from scimath.units.dimensionless import percent
from traits.api import Constant, Enum, Event, Instance, Property, TraitError, \
    Tuple

from app_common.traits.custom_trait_factories import Key, Parameter, \
    ParameterUnitArray

from ..utils.string_definitions import STRIP_COMP_NAME
from ..utils.units_utils import unit_almost_equal, unitarray_to_unitted_list, \
    unitted_list_to_array
from .solution import Solution
from .product import Product

# the type id for SolutionWithProduct
SOLUTIONWITHPRODUCT_TYPE = 'SOLUTION_WITH_PRODUCT'

ALLOWED_COMPONENT_GROUPS = ['product_component', 'impurity']

logger = logging.getLogger(__name__)


class SolutionWithProduct(Solution):
    """ Represents the properties associated with a component.

    FIXME: Break the code here into a Pool subclass and a Load so that we don't
    constantly test on solution_type.
    """
    # -------------------------------------------------------------------------
    # SolutionWithProduct traits
    # -------------------------------------------------------------------------

    #: The type of solution (load, frac, pool)
    solution_type = Key(Enum(['Load', 'Pool', 'Fraction']))

    #: The product associated with the solution.
    product = Instance(Product)

    #: The concentration (g/liter) of the product in the solution.
    product_concentration = Parameter()

    #: Concentration ratio for each product component in %
    product_component_purities = Property(
        Instance(UnitArray),
        depends_on='product_concentration, product,'
                   '_product_component_concentrations'
    )

    #: The values for the product component assays (attribute of Product class)
    product_component_assay_values = ParameterUnitArray()

    #: The assay value specifically for the strip component (if any) since
    #: treated differently.
    strip_mass_fraction = Property(Parameter,
                                   depends_on='product_component_assay_values,'
                                              ' _strip_fraction_updated')

    #: Event to trigger to notify that the strip fraction was modified, since
    #: that can be done under Traits radars by modifying an element of an array
    _strip_fraction_updated = Event

    #: The concentrations of each product component in the solution.
    product_component_concentrations = Property(
        Instance(UnitArray),
        depends_on='solution_type, product_concentration, product, '
                   'product_component_assay_values'
    )

    #: shadow trait for product_component_concentrations to allow user
    #: to allow set it
    _product_component_concentrations = Instance(UnitArray)

    #: The values for the impurity assays (attribute of the Product class).
    impurity_assay_values = Instance(UnitArray)

    #: The concentrations of each impurity in the solution.
    impurity_concentrations = Property(
        Instance(UnitArray),
        depends_on='solution_type, product_concentration, '
                   'impurity_assay_values, product'
    )

    #: shadow trait for impurity_concentrations to allow user to set it
    _impurity_concentrations = Instance(UnitArray)

    # -------------------------------------------------------------------------
    # ChromatographyData traits
    # -------------------------------------------------------------------------

    #: The type of data being represented by this class
    type_id = Constant(SOLUTIONWITHPRODUCT_TYPE)

    #: The attributes that identify the data in this object uniquely in a
    #: collection of components
    _unique_keys = Tuple(('name',))

    # Trait property getters/setters ----------------------------

    def _set_product_component_concentrations(self, x):
        if self.solution_type == 'Pool':
            self._product_component_concentrations = x

    def _validate_product_component_concentrations(self, x):
        """ Checks number of items in x equal to product_component_names
        in product.
        """
        if len(x) != len(self.product.product_component_names):
            msg = ('product_component_concentrations should have same length'
                   ' as product.product_component_names')
            logger.exception(msg)
            raise TraitError(msg)
        return x

    def _get_product_component_concentrations(self):
        """ Returns computed product_component_concentrations when solution_type
        is 'Load' or 'Fraction', otherwise returns the user-defined
        _product_component_concentrations
        """
        solution_type = self.solution_type
        if solution_type == 'Pool':
            return self._product_component_concentrations
        else:
            return self.compute_concentrations('product_component',
                                               self.product)

    def _set_impurity_concentrations(self, x):
        if self.solution_type == 'Pool':
            self._impurity_concentrations = x

    def _validate_impurity_concentrations(self, x):
        """ checks number of items in x equal to product_component_names
            in product
        """
        if len(x) != len(self.product.impurity_names):
            msg = ('impurity_concentrations should have same length as '
                   'product.impurity_names')
            logger.exception(msg)
            raise TraitError(msg)
        return x

    def _get_impurity_concentrations(self):
        """ Returns computed impurity_concentrations when solution_type
        is 'Load' or 'Fraction', otherwise returns the user-defined
        _impurity_concentrations
        """
        solution_type = self.solution_type
        if solution_type == 'Pool':
            return self._impurity_concentrations
        else:
            return self.compute_concentrations('impurity', self.product)

    def _get_product_component_purities(self):
        from kromatography.utils.chromatography_units import convert_units
        if self.solution_type == 'Pool':
            concentrations = self._product_component_concentrations
        else:
            concentrations = self.product_component_concentrations

        if concentrations is None or self.product_concentration is None:
            return

        return convert_units(concentrations / self.product_concentration,
                             tgt_unit="%")

    # -------------------------------------------------------------------------
    # SolutionWithProduct Methods
    # -------------------------------------------------------------------------

    # FIXME: should this be a `@has_units` method ?
    def compute_concentrations(self, component_group, product):
        """ Returns a list of UnitScalars representing the concentrations of
        each component in the SolutionWithProduct object calling this method.

        Parameters
        ----------
        component_group: str
            The group to compute the concentrations for.
            Is either 'product_component' or 'impurity'

        product : Product
            Instance of the Product class

        Returns
        -------
        concentrations : UnitArray
            The concentrations of the individual components for the the
            group specified by `component_group`. The units for
            `concentrations` is decided by the user specified expressions
            in `<component_group>_concentration_exps`.
        """
        if component_group not in ALLOWED_COMPONENT_GROUPS:
            msg = 'The argument `component_group` must be one of {}'.format(
                ALLOWED_COMPONENT_GROUPS)
            logger.exception(msg)
            raise ValueError(msg)

        exps = getattr(product, component_group + '_concentration_exps')
        if len(exps) == 0:
            return None

        assay_names = getattr(product, component_group + '_assays')
        assay_values = getattr(self, component_group + '_assay_values')
        if assay_names is None or assay_values is None:
            return None

        namespace = dict(zip(assay_names, assay_values))
        namespace['product_concentration'] = self.product_concentration
        concentrations = [eval(exp, namespace) for exp in exps]
        first_conc = concentrations[0]
        all_units_identical = all(unit_almost_equal(conc, first_conc)
                                  for conc in concentrations)
        if not all_units_identical:
            all_units = [conc.units for conc in concentrations]
            msg = ('The units for all the component concentrations must be '
                   'identical: {!r}').format(all_units)
            logger.exception(msg)
            raise ValueError(msg)

        return UnitArray(concentrations, units=first_conc.units)

    def compute_assays(self, component_group, product):
        """ Returns fractions of assays computed from the product's
        components/impurities concentrations.

        Parameters
        ----------
        component_group : str
            The group to compute the concentrations for. Either
            'product_component' or 'impurity'.

        product : Product
            Product contained in the solution, whose assays are being computed.
        """
        if component_group not in ALLOWED_COMPONENT_GROUPS:
            msg = 'The argument `component_group` must be one of {}'
            msg = msg.format(ALLOWED_COMPONENT_GROUPS)
            logger.exception(msg)
            raise ValueError(msg)

        concentrations = getattr(self, component_group + '_concentrations')
        concentrations = unitarray_to_unitted_list(concentrations)
        namespace = dict(zip(getattr(product, component_group + '_names'),
                             concentrations))
        namespace['product_concentration'] = self.product_concentration
        exps = getattr(product, component_group + '_assay_exps')
        fractions = [eval(exp, namespace) for exp in exps]
        return unitted_list_to_array(fractions)

    # Traits initialization methods -------------------------------------------

    def _product_concentration_default(self):
        return UnitScalar(0.0, units="g/liter")

    # Traits property getters/setters -----------------------------------------

    def _get_strip_mass_fraction(self):
        # get the assay value for the Strip assay
        if STRIP_COMP_NAME in self.product.product_component_assays:
            strip_idx = self.product.product_component_assays.index(
                STRIP_COMP_NAME
            )
        else:
            return UnitScalar(np.nan, units="%")

        assay_values = self.product_component_assay_values
        val = assay_values[strip_idx]
        return UnitScalar(val, units=assay_values.units)

    def _set_strip_mass_fraction(self, value):
        if self.product_component_assay_values is None:
            return

        wrong_unit = (isinstance(value, UnitScalar) and
                      not unit_almost_equal(value, percent))
        if wrong_unit:
            unit_label = value.units.label
            if not unit_label:
                unit_label = repr(value.units)

            msg = "Strip fraction must be a percentage but the units of the " \
                  "value provided was {}.".format(unit_label)
            logger.error(msg)
            raise ValueError(msg)

        if STRIP_COMP_NAME in self.product.product_component_assays:
            strip_idx = self.product.product_component_assays.index(
                STRIP_COMP_NAME
            )
        else:
            return

        self.product_component_assay_values[strip_idx] = float(value)
        # Notify UIs and other objects trying to listen on this:
        self._strip_fraction_updated = True
