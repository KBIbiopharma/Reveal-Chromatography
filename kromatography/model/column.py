""" Column and Column model class definitions.
"""
from numpy import pi
import logging

from traits.api import Constant, Instance, Property, Str, Tuple
from scimath.units.api import convert, UnitScalar, UnitArray
from scimath.units.length import centimeter
from scimath.units.volume import cubic_centimeter

from .chromatography_data import ChromatographyData
from .resin import Resin
from ..utils.chromatography_units import convert_units
from app_common.traits.custom_trait_factories import Key, Parameter
from ..utils.units_utils import has_volume_units, unit_scalar_almost_equal

# Module level constants
#: The type-id string for ColumnType
COLUMN_TYPE = 'Column Type'

#: The type-id string for the System
COLUMN = "Packed Column"

logger = logging.getLogger(__name__)


class ColumnType(ChromatographyData):
    """ Represents a possible column type to use for chromatography.
    """
    # -------------------------------------------------------------------------
    # ColumModel traits
    # -------------------------------------------------------------------------

    #: The name of the manufacturer
    manufacturer = Key()

    #: The model number the manufacturer uses
    manufacturer_name = Key()

    #: Diameter of the tube in cm
    diameter = Instance(UnitScalar)

    #: Min and Max bed height in cm
    bed_height_range = Instance(UnitArray)

    #: Bed height adjustment method (typically "Manual" or "Automated")
    bed_height_adjust_method = Str

    # -------------------------------------------------------------------------
    # ChromatographyData traits
    # -------------------------------------------------------------------------

    #: The type of data being represented by this class.
    type_id = Constant(COLUMN_TYPE)

    _unique_keys = Tuple(('name', 'manufacturer_name'))


class Column(ChromatographyData):
    """ Represents a column used in chromatography (column + resin).

    The class will enforce the bed_height to be within the range defined by the
    ColumnType it uses.
    """
    # -------------------------------------------------------------------------
    # Column traits
    # -------------------------------------------------------------------------

    #: Packed column lot ID
    column_lot_id = Str

    #: Column type used
    column_type = Instance(ColumnType)

    #: Resin contained in the Column
    resin = Instance(Resin)

    #: Bed height, typically in cm
    bed_height_actual = Parameter()

    #: Compression Factor (settled vol/packed vol, unit-less)
    compress_factor = Instance(UnitScalar)

    #: Height Equivalent to a Theoretical Plate (HETP, in cm)
    hetp = Instance(UnitScalar)

    #: HETP Asymmetry (dimensionless)
    hetp_asymmetry = Instance(UnitScalar)

    #: Column volume (calculated from column diameter and bed height).
    volume = Property(depends_on=['bed_height_actual', 'column_type.diameter'])

    # -------------------------------------------------------------------------
    # ChromatographyData traits
    # -------------------------------------------------------------------------

    #: The type of data being represented by this class.
    type_id = Constant(COLUMN)

    _unique_keys = Tuple(('column_lot_id', 'column_type', 'resin'))

    # -------------------------------------------------------------------------
    # Private methods
    # -------------------------------------------------------------------------

    def __setattr__(self, attr_name, value):
        if attr_name == "bed_height_actual":
            self._validate_bed_height(value)

        super(Column, self).__setattr__(attr_name, value)

    def _validate_bed_height(self, value):
        """ Raise exception if the value doesn't conform to type's height range
        """
        if self.column_type is None:
            return

        bed_height_min, bed_height_max = self.column_type.bed_height_range
        # FIXME: would be nice for Scimath to make a UnitScalar when extracting
        # from a UnitArray
        range_units = self.column_type.bed_height_range.units
        bed_height_min = UnitScalar(bed_height_min, units=range_units)
        bed_height_max = UnitScalar(bed_height_max, units=range_units)

        if not bed_height_min <= value <= bed_height_max:
            msg = ("The requested bed height ({}) isn't within the range of "
                   "the model [{}-{}]".format(value, bed_height_min,
                                              bed_height_max))
            raise ValueError(msg)

    # Traits initialization methods -------------------------------------------

    def _bed_height_actual_default(self):
        # return the minimum possible height if column_type is given, else 0.0
        if self.column_type is not None:
            bed_height_min, _ = self.column_type.bed_height_range
            range_units = self.column_type.bed_height_range.units
            bed_height_min = UnitScalar(bed_height_min, units=range_units)
            return bed_height_min
        return UnitScalar(0.0, units='cm')

    def _compress_factor_default(self):
        return UnitScalar(0.0, units='1')

    def _hetp_default(self):
        return UnitScalar(0.0, units='cm')

    def _hetp_asymmetry_default(self):
        return UnitScalar(0.0, units='1')

    # Traits property getters/setters -----------------------------------------

    def _get_volume(self):
        """ Calculate the column volume = pi * D^2 * H / 4 in mL/cm^3
        """
        column_vol = (self.column_type.diameter * self.column_type.diameter *
                      pi * self.bed_height_actual / 4.0)

        column_vol = convert_units(column_vol, cubic_centimeter)
        return column_vol

    def _set_volume(self, value):
        """ Back-calculate the column's bed height H to have requested volume.

        To make sure that the volume follows::

            vol = pi * D^2 * H / 4

        the bed height is set to::

            H = 4 * vol / (pi * D^2)

        Note that this may raise an exception if the resulting bed height
        doesn't fall in the range set by the column type.
        """
        #: Do nothing if value requested is already the value of the volume:
        if unit_scalar_almost_equal(value, self.volume):
            return

        if not isinstance(value, UnitScalar):
            msg = "Setting the column volume must be done providing a " \
                  "UnitScalar to specify the unit."
            logger.exception(msg)
            raise ValueError(msg)

        if not has_volume_units(value):
            msg = "Setting the column volume must be done providing a " \
                  "UnitScalar to specify the unit."
            logger.exception(msg)
            raise ValueError(msg)

        diam = self.column_type.diameter
        bed_height_actual = 4. * value / (diam**2 * pi)
        val = convert(
            float(bed_height_actual), from_unit=bed_height_actual.units,
            to_unit=centimeter
        )
        self.bed_height_actual = UnitScalar(val, units=centimeter)
