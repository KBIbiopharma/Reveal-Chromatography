from traits.api import Constant, Enum, Int, List, Property, Tuple

from kromatography.model.chromatography_data import ChromatographyData
from kromatography.model.component import Component
from app_common.traits.custom_trait_factories import Key, Parameter


#: The type id for a chemical.
CHEMICAL_TYPE = 'CHEMICAL'


class Chemical(ChromatographyData):
    """ Represents a chemical compound, that is a list of (chemical) components
    in a given state.

    Parameters
    ----------
    name : str
        Name of the compound.

    state : str in {"Solid", "Liquid"}
        State the compound is in. Set to 'Solid' by default.

    component_list : list of Component
        List of components the chemical compound is made of.

    component_atom_count : list of int
        List of counts of each component to build the compound. All set to 1 if
        not provided.
    """
    # FIXME: In the future, it would be nice to be able to compute the
    # molecular weight from the component list and count...

    # -------------------------------------------------------------------------
    # Chemical traits
    # -------------------------------------------------------------------------

    #: The physical state the compound is in.
    state = Key(Enum(["Solid", "Liquid"]))

    #: Formula for the compound
    formula = Property

    #: The molecular weight, assumed to be in g/mol.
    molecular_weight = Parameter()

    #: List of components. Needed at construction.
    component_list = List(Component)

    #: List of atom counts for each component.
    component_atom_counts = List(Int)

    # -------------------------------------------------------------------------
    # ChromatographyData traits
    # -------------------------------------------------------------------------

    #: The type of data being represented by this class.
    type_id = Constant(CHEMICAL_TYPE)

    #: How to identify 1 kind of chemical?
    _unique_keys = Tuple(('type_id', 'formula', 'state'))

    # -------------------------------------------------------------------------
    # Methods
    # -------------------------------------------------------------------------

    def _get_formula(self):
        str_comps = [str(num) + comp.name for comp, num in
                     zip(self.component_list, self.component_atom_counts)]
        return "+".join(str_comps)
