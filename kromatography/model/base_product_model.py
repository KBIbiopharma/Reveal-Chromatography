import logging

from traits.api import Int, List, Property, Str

from kromatography.model.chromatography_data import ChromatographyData

logger = logging.getLogger(__name__)


class BaseProductModel(ChromatographyData):
    """ Base class for binding and transport models, describing the behavior of
    a Product's components.
    """
    #: Name of the product this object describes the binding of
    target_product = Str

    #: Component names. Useful for building a view for the model.
    #: Auto-generated if not provided.
    component_names = List(Str)

    #: Total number of components, including cation.
    num_comp = Int

    #: Number of product components described
    num_prod_comp = Property(Int, depends_on="num_comp")

    def __init__(self, num_comp=None, num_prod_comp=None, **traits):
        """ Create new SMA binding model targeting specific product.

        Parameters
        ----------
        num_comp : int [OPTIONAL]
            Number of component the binding model describes, including the
            cation component. If unspecified, computed from `num_prod_comp`.

        num_prod_comp : int [OPTIONAL]
            Number of product components. The binding model created will
            contain parameters for these as well as an additional cation
            component. Ignored if `num_comp` is specified.

        traits : dict
            Additional parameters for the new binding model. The only required
            parameter is a name.
        """
        num_comp = validate_inputs(num_comp, num_prod_comp, traits)
        traits["num_comp"] = num_comp
        super(BaseProductModel, self).__init__(**traits)


def validate_inputs(num_comp, num_prod_comp, traits):
    """ Validate that the arguments to create a product model are valid.
    """
    if num_comp is None:
        if isinstance(num_prod_comp, int):
            num_comp = num_prod_comp + 1
        elif num_prod_comp is None:
            msg = "The number of component (or product component) hasn't" \
                  " been specified. Aborting the creation of binding " \
                  "model {}.".format(traits.get("name", ""))
            logger.exception(msg)
            raise ValueError(msg)
        else:
            msg = "The number of component (or product component) must " \
                  "be an integer but a {} was provided."
            msg = msg.format(type(num_prod_comp))
            logger.exception(msg)
            raise ValueError(msg)

    # Make sure that the component information is consistent
    component_names = traits.get("component_names")

    if component_names and num_comp != len(component_names):
        msg = "Incompatible number of product component names: expected " \
              "{} and got {}.".format(num_comp, len(component_names))
        logger.exception(msg)
        raise ValueError(msg)

    # Make sure that the component information is consistent
    component_names = traits.get("component_names")

    if component_names and num_comp != len(component_names):
        msg = "Incompatible number of product component names: expected " \
              "{} and got {}.".format(num_comp, len(component_names))
        logger.exception(msg)
        raise ValueError(msg)

    return num_comp
