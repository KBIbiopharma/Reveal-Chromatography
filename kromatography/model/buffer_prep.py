import logging

from scimath.units.unit_scalar import UnitScalar, UnitArray
from traits.api import Constant, Instance, List, Property, Str, Tuple

from kromatography.model.api import Parameter
from kromatography.model.chromatography_data import ChromatographyData
from kromatography.model.buffer import Buffer
from kromatography.model.chemical import Chemical
from kromatography.model.component import Component
from kromatography.utils.chromatography_units import milli_molar

#: the type id for BufferPrep
BUFFER_PREP_TYPE = 'BUFFER_PREP'

logger = logging.getLogger(__name__)


class BufferPrep(ChromatographyData):
    """ Class to create a Buffer instance via chemicals where chemical
    components and their concentrations will be computed from mass and volume
    information.

    FIXME: unit conversions hard-coded: replace with dynamic unit management.
    """
    # -------------------------------------------------------------------------
    # BufferPrep traits
    # -------------------------------------------------------------------------

    #: User description of the buffer to be created
    description = Str

    #: The source of the buffer prep
    source = Str()

    #: lot id of buffer prep
    lot_id = Str()

    #: FIXME we can potentially ignore this, it is a string in the excel file
    #: we currently haven't needed to read in yet, so not used
    # #: Description of make-up of buffer prep
    # composition_string = Str

    #: The chemicals contained by the buffer prep
    chemicals = List(Chemical)

    #: The amounts (g or mL, depending on state) of each chemical
    chemical_amounts = List(UnitScalar)

    #: The stock concentrations (M i.e. mol/L) of each chemical
    chemical_stock_concentrations = Instance(UnitArray)

    #: The volume (mL) of the buffer prep
    volume = Parameter()

    #: the density of the buffer prep
    density = Parameter()

    #: the conductivity of the buffer prep
    conductivity = Instance(UnitScalar)

    #: the pH of the buffer prep
    pH = Parameter()

    #: the temperature of the buffer prep
    temperature = Instance(UnitScalar)

    #: The concentrations (M) of each chemical in the buffer prep.
    chemical_concentrations = Property(
        Instance(UnitArray),
        depends_on=['chemicals',
                    'chemical_amounts',
                    'volume',
                    'chemical_stock_concentrations']
    )

    #: The list of chemicals in the buffer prep.
    chemical_components = Property(
        List(Component),
        depends_on=['chemicals']
    )

    #: The concentrations (M) of each chemical component in the buffer prep.
    chemical_component_concentrations = Property(
        Instance(UnitArray),
        depends_on=['chemical_components',
                    'chemicals',
                    'chemical_concentrations']
    )

    # -------------------------------------------------------------------------
    # ChromatographyData traits
    # -------------------------------------------------------------------------

    #: The type of data being represented by this class
    type_id = Constant(BUFFER_PREP_TYPE)

    #: The attributes that identify the data in this object uniquely in a
    #: collection of components
    _unique_keys = Tuple(('name',))

    def __init__(self, **traits):
        super(BufferPrep, self).__init__(**traits)

        chemical_lists = [
            self.chemicals,
            self.chemical_amounts,
            self.chemical_stock_concentrations,
        ]
        self._check_lists_lengths(chemical_lists)

    def _get_chemical_components(self):
        components = []
        comp_names = []
        for chemical in self.chemicals:
            for component in chemical.component_list:
                if component.name not in comp_names:
                    components.append(component)
                    comp_names.append(component.name)
        return components

    def _get_chemical_concentrations(self):
        # Check dependent attributes are initialized.
        is_valid = (self.chemicals is not None and
                    self.chemical_amounts is not None and
                    self.chemical_stock_concentrations is not None)
        if not is_valid:
            return None

        concentrations = []
        for i, chemical in enumerate(self.chemicals):
            if chemical.state == 'Solid':
                conc = self.chemical_amounts[i] / chemical.molecular_weight \
                    / self.volume * 1e6
            elif chemical.state == 'Liquid':
                conc = self.chemical_amounts[i] * \
                    self.chemical_stock_concentrations[i] / self.volume * 1e3
            else:
                msg = "Unrecognizeable state {} for chemical {}".format(
                    chemical.state, chemical.name)
                logger.exception(msg)
                raise ValueError(msg)

            concentrations.append(conc)
        return UnitArray(concentrations, units=milli_molar)

    def _get_chemical_component_concentrations(self):
        # Check dependent attributes are initialized.
        is_valid = (self.chemical_components is not None and
                    self.chemicals is not None and
                    self.chemical_concentrations is not None)
        if not is_valid:
            return None

        component_concentrations = [0.0] * len(self.chemical_components)
        comp_names = [c.name for c in self.chemical_components]
        for i, chemical in enumerate(self.chemicals):
            for ii, component in enumerate(chemical.component_list):
                comp_conc = self.chemical_concentrations[i] * \
                    chemical.component_atom_counts[ii]
                comp_index = comp_names.index(component.name)
                component_concentrations[comp_index] += comp_conc
        return UnitArray(component_concentrations, units=milli_molar)

    def _check_lists_lengths(self, lists):
        """Raises ValueError if lists not all same length
        """
        if len(lists) == 0:
            return
        first_length = len(lists[0])
        if any(len(l) != first_length for l in lists):
            msg = "lists not all same length:{!r}".format(lists)
            logger.exception(msg)
            raise ValueError(msg)

    def build_buffer(self):
        """ Builds a Buffer object from the BufferPrep information.
        """
        buffer_data = {
            'name': self.name,
            'source': self.source,
            'lot_id': self.lot_id,
            'description': self.description,
            'density': self.density,
            'conductivity': self.conductivity,
            'pH': self.pH,
            'temperature': self.temperature,
            'chemical_components': self.chemical_components,
            'chemical_component_concentrations':
                self.chemical_component_concentrations
        }
        return Buffer(**buffer_data)

if __name__ == '__main__':
    from kromatography.model.tests.example_model_data import \
        BUFFER_PREP_ELUTION

    bufferprep = BufferPrep(**BUFFER_PREP_ELUTION)
    buff = bufferprep.build_buffer()
