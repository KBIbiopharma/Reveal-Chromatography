from scimath.units.unit_scalar import UnitArray, UnitScalar

from traits.api import Instance, List, Property, Str

from app_common.traits.custom_trait_factories import Parameter, \
    ParameterUnitArray
from kromatography.model.chromatography_data import ChromatographyData
from kromatography.model.component import Component


class Solution(ChromatographyData):
    """ Base class for the solution like objects.

    NOTE: `type_id` is not specified for this class as this is not meant to
    be instantiated.
    """
    #: The lot id of the solution
    description = Str()

    #: The source of the solution
    source = Str()

    # FIXME: This is not defined from Fraction / Pool !
    #: The lot id of the solution
    lot_id = Str()

    #: The density of the solution
    density = Instance(UnitScalar)

    #: The conductivity of the solution
    conductivity = Instance(UnitScalar)

    #: The pH of the solution
    pH = Parameter()

    #: The temperature of the solution
    temperature = Instance(UnitScalar)

    #: The list of chemical components in the solution.
    chemical_components = List(Component)

    #: The concentrations (M) of each chemical component in the buffer.
    chemical_component_concentrations = ParameterUnitArray

    #: The concentration of the cations (positively charged ions) in the
    #: solution.
    cation_concentration = Property(
        Instance(UnitArray),
        depends_on=['chemical_components',
                    'chemical_component_concentrations']
    )

    #: The concentration of the anions (negatively charged ions) in the
    #: solution.
    anion_concentration = Property(
        Instance(UnitArray),
        depends_on=['chemical_components',
                    'chemical_component_concentrations']
    )

    def _get_cation_concentration(self):
        # Note that all ionic components are currently stored as
        # `chemical_components`.

        #: Pool instances from simulations will not have this
        if self.chemical_component_concentrations is None:
            return None

        components = self.chemical_components
        concentrations = self.chemical_component_concentrations
        cation_concs = [
            conc for comp, conc in zip(components, concentrations.tolist())
            if comp.charge > 0
        ]
        return UnitScalar(sum(cation_concs), units=concentrations.units)

    def _get_anion_concentration(self):
        # Note that all ionic components are currently stored as
        # `chemical_components`.

        #: Pool instances from simulations will not have this
        if self.chemical_component_concentrations is None:
            return None

        components = self.chemical_components
        concentrations = self.chemical_component_concentrations
        anion_concs = [
            conc for comp, conc in zip(components, concentrations.tolist())
            if comp.charge < 0
        ]
        return UnitScalar(sum(anion_concs), units=concentrations.units)

    def _conductivity_default(self):
        return UnitScalar(0.0, units="mS/cm")

    def _pH_default(self):
        return UnitScalar(0.0, units="1")
