""" Product Class Implementation. In chromatography, the product is the most
important material, since it is the set of components that the chromatography
is set to produce. Note that that might differ from the finaly product that the
drug being manufactured will contain, since there are multiple chromatography
steps during the purification process.
"""
from __future__ import division

from sympy import solve, var
import pandas as pd
import logging

from scimath.units.unit_scalar import UnitScalar
from traits.api import cached_property, Constant, Instance, Int, List, \
    Property, Str, Tuple

from kromatography.model.chromatography_data import ChromatographyData
from kromatography.model.product_component import ProductComponent
from app_common.traits.custom_trait_factories import Key

logger = logging.getLogger(__name__)

# Name of the blank (unset) product
BLANK_PRODUCT_NAME = "NO PRODUCT SET"

#: Type id for product
PRODUCT_TYPE = 'PRODUCT'

#: Classes of molecules whose concentrations are computed from assays
COMPONENT_GROUPS = ['product_component', 'impurity']

# List of bad names known to collide with during execution of sympy's solve.
BAD_COMPONENT_NAMES = {"Product": "PRODUCT", "product": "PRODUCT",
                       "Basic": "BASIC"}

# Name of the total product concentration in concentration expression
PROD_CONCENTRATION_VARNAME = 'product_concentration'


class ExpressionComputationError(ValueError):
    """ Specific exception raised when sympy's solver fails to invert
    concentration expressions.
    """
    pass


class Product(ChromatographyData):
    """Represents a product, which is made up of components, impurities, and
    amino acids.

    The product stores the expressions needed to compute the concentration of
    each component, which are used by :class:`SolutionWithProduct` for the
    actual computation, since the solution's overall concentration is needed.
    """

    # -------------------------------------------------------------------------
    # Product traits
    # -------------------------------------------------------------------------

    #: User notes about the product's origin, purpose, ...
    description = Str

    #: The type of product
    product_type = Key()

    #: List of components this product is composed of
    product_components = List(Instance(ProductComponent))

    #: List of component names. Built from the product_components list
    product_component_names = Property(List(Str),
                                       depends_on='product_components')

    #: List of assay names to compute the concentrations of each component
    product_component_assays = List(Str)

    #: Expressions to compute the concentration of each product_component
    #: given the product's concentration and assays results. This should be a
    #: Pandas Series indexed on the component names, and containing string
    #: expressions. Each string should be an eval-able expression involving the
    #: 'product_component_assays' as well as the total `product_concentration`.
    #: (e.g. 'product_concentration * CEX_Acidic_2 / 100')
    product_component_concentration_exps = Instance(pd.Series)

    #: Expressions to compute the assay of each product_component
    #: given the product's component concentration. Each string
    #: should be a valid Python expression that can use the names
    #: in the 'product_component_names' attribute
    #: as well as the name `product_concentration`
    product_component_assay_exps = Property(
        Instance(List(Str)),
        depends_on='product_component_concentration_exps'
    )

    #: List of impurities in the product
    impurity_names = List(Str)

    #: List of the assay names for each impurity
    impurity_assays = List(Str)

    #: Expressions to compute the concentration of each impurity
    #: given the product's concentration and impurity assays. This should be a
    #: Pandas Series indexed on the component names, and containing string
    #: expressions. Each string should be an eval-able expression that can use
    #: the names in the 'impurity_assays' attribute as well as the name
    #: `product_concentration`.
    impurity_concentration_exps = Instance(pd.Series)

    #: Expressions to compute the assay of each product_component given the
    #: product's component concentration. Each string should be a valid Python
    #: expression that can use the names in the 'product_component_names'
    #: attribute as well as the name `product_concentration`
    impurity_assay_exps = Property(
        Instance(List(Str)),
        depends_on='impurity_concentration_exps'
    )

    #: Iso-electric point of the product (in pH unit)
    pI = Instance(UnitScalar)

    # FIXME: Later we may want to consider making a AminoAcid class (issue #33)
    #: List of titrating amino acids in the product
    amino_acids = List(Str)

    # FIXME: Later we may want to consider making a AminoAcid class (issue #33)
    #: Number of each amino acid in the product
    amino_acid_numbers = List(Int)

    #: Number of components the product contains
    num_components = Property(Int, depends_on='product_components')

    # -------------------------------------------------------------------------
    # ChromatographyData traits
    # -------------------------------------------------------------------------

    #: The type of data being represented by this class.
    type_id = Constant(PRODUCT_TYPE)

    #: How to identify a particular product
    _unique_keys = Tuple(('name',))

    # -------------------------------------------------------------------------
    # Product Methods
    # -------------------------------------------------------------------------

    def __init__(self, **traits):
        # Convert lists of str concentration expression to series if needed
        if "product_component_concentration_exps" in traits:
            values = traits["product_component_concentration_exps"]
            if isinstance(values, list):
                index = [comp.name for comp in traits["product_components"]]
                traits["product_component_concentration_exps"] = \
                    pd.Series(values, index=index)

        if "impurity_concentration_exps" in traits:
            values = traits["impurity_concentration_exps"]
            if isinstance(values, list):
                traits["impurity_concentration_exps"] = \
                    pd.Series(values, index=traits["impurity_names"])

        super(Product, self).__init__(**traits)

        # If the component's target product wasn't set, it is set here.
        # Otherwise, its target product is checked:
        for comp in self.product_components:
            if comp.target_product == "":
                comp.target_product = self.name
            elif comp.target_product != self.name:
                msg = "Trying to build product {} with component {} " \
                      "targeting product {}."
                msg = msg.format(self.name, comp.name, comp.target_product)
                logger.exception(msg)
                raise ValueError(msg)

        if traits["name"] == BLANK_PRODUCT_NAME:
            return

        #: check for each set of attributes, the same number was given
        component_attrs = [self.product_components,
                           self.product_component_concentration_exps]
        impurity_attrs = [self.impurity_names, self.impurity_assays,
                          self.impurity_concentration_exps]
        amino_acid_attrs = [self.amino_acids,
                            self.amino_acid_numbers]
        for group in [component_attrs, impurity_attrs, amino_acid_attrs]:
            self._check_lists_lengths(group)

        # Check each expression in product_component_concentration_exps and
        # impurity_concentration_exps
        self._check_expressions()

        self._sanitize_component_names()

    def get_component_with_name(self, name):
        """ Returns component with specified name.

        Raises
        ------
        KeyError:
            If the name requested isn't a valid component name.
        """
        all_names = []
        for comp in self.product_components:
            all_names.append(comp.name)
            if comp.name == name:
                return comp

        msg = "No product component with name {} in product {}. Available " \
              "components names are: {}".format(name, self.name, all_names)
        logger.exception(msg)
        raise KeyError(msg)

    # Private interface -------------------------------------------------------

    def _sanitize_component_names(self):
        """ Change component/impurity names that would break the sympy solver.
        """
        for comp in self.product_components:
            if comp.name in BAD_COMPONENT_NAMES:
                comp.name = BAD_COMPONENT_NAMES[comp.name]

        for i, impurity_name in enumerate(self.impurity_names):
            if impurity_name in BAD_COMPONENT_NAMES:
                self.impurity_names[i] = BAD_COMPONENT_NAMES[comp.name]

    def _check_lists_lengths(self, lists):
        """ Raises ValueError if lists not all same length
        """
        if len(lists) == 0:
            return
        first_length = len(lists[0])
        if any(len(l) != first_length for l in lists):
            msg = ("Attempting to create product {} with lists of different "
                   "lengths ({}).".format(self.name, lists))
            logger.exception(msg)
            raise ValueError(msg)

    def _check_expressions(self):
        """ Check that component concentration expressions to be eval-able.

        Raises
        ------
        ValueError:
            If expressions inside the object's '*_exps' attrs are not valid
            python expressions involving the 'product_concentration' and the
            product's assays.
        """
        for comp_group in COMPONENT_GROUPS:
            exps = getattr(self, comp_group + '_concentration_exps')
            if len(exps) == 0:
                continue
            valid_names = [PROD_CONCENTRATION_VARNAME]
            valid_names += getattr(self, comp_group + '_assays')
            namespace = {name: 1 for name in valid_names}
            for exp in exps:
                try:
                    eval(exp, namespace)
                except NameError as e:
                    msg = "Concentration expression {} is invalid. Does it " \
                          "only involve operations, and the known product " \
                          "concentration and  assays ({})? (Original error " \
                          "was {}.)".format(exp, valid_names, e)
                    logger.exception(msg)
                    raise ValueError(msg)

    # Traits property getters/setters -----------------------------------------

    def _get_assay_exps(self, component_group):
        """ Returns a list of expressions representing the inverse
        'component_group'_concentration_exps (i.e. solved for
        'component_group'_assays)
        """
        expressions = getattr(self, component_group + "_concentration_exps")
        if expressions is None:
            return

        names = getattr(self, component_group + "_names")
        concentration_exps_lhs = [exp + ' - ' + comp for (exp, comp) in
                                  zip(list(expressions), names)]

        unknown_variables = [var(variable) for variable in
                             getattr(self, component_group + "_assays")]
        try:
            temp_assay_exps = solve(concentration_exps_lhs, unknown_variables,
                                    warn=True)
        except TypeError as e:
            msg = ("Sympy's solve function failed with error {}. It could be "
                   "due to a badly chosen component/impurity name that "
                   "collides during solver execution. Expressions are {}.")
            msg = msg.format(e, concentration_exps_lhs)
            logger.exception(msg)
            raise ExpressionComputationError(msg)

        if isinstance(temp_assay_exps, dict):
            assay_exps = \
                [str(temp_assay_exps[var(assay)])
                 for assay in getattr(self, component_group + "_assays")]
        else:
            assay_exps = [str(exp) for exp in temp_assay_exps]

        return assay_exps

    @cached_property
    def _get_product_component_assay_exps(self):
        return self._get_assay_exps(component_group="product_component")

    @cached_property
    def _get_impurity_assay_exps(self):
        return self._get_assay_exps(component_group="impurity")

    @cached_property
    def _get_num_components(self):
        return len(self.product_components)

    @cached_property
    def _get_product_component_names(self):
        return [comp.name for comp in self.product_components]

    # Traits initialization method --------------------------------------------

    def _impurity_concentration_exps_default(self):
        return pd.Series([])

    def _product_component_concentration_exps_default(self):
        return pd.Series([])


def make_blank_product():
    return Product(name=BLANK_PRODUCT_NAME, product_type="UNKNOWN")


if __name__ == '__main__':
    from kromatography.model.tests.example_model_data import PRODUCT_DATA, \
        Prod001_comp1, Prod001_comp2, Prod001_comp3

    prod = Product(
        product_components=[Prod001_comp1, Prod001_comp2, Prod001_comp3],
        **PRODUCT_DATA
    )
