""" Utilities around unit conversion and unit management.
"""
import logging

from scimath.units.api import convert, unit_parser, UnitArray, UnitScalar
from scimath.units.length import m
from scimath.units.time import second
from scimath.units.unit import InvalidConversion
import numpy as np

import kromatography.utils.chromatography_units as chr_units

logger = logging.getLogger(__name__)

parse_unit = unit_parser.parse_unit


def unitted_list_to_array(unitted_list):
    """ Returns a UnitArray given a list of UnitScalars.

    FIXME: replace raising an exception by doing a value conversion.
    """
    first_units = unitted_list[0].units
    other_units = [val.units for val in unitted_list[1:]]
    for unit in other_units:
        # Test works even between a SmartUnit and a Unit
        if not unit_almost_equal(unit, first_units):
            all_units = [u.label for u in [first_units] + other_units]
            msg = ("Not all units identical: got {}".format(all_units))
            logger.exception(msg)
            raise ValueError(msg)

    return UnitArray([float(val) for val in unitted_list], units=first_units)


def unitarray_to_unitted_list(uarr):
    """ Convert a UnitArray to a list of UnitScalars.
    """
    values = uarr.tolist()
    return [UnitScalar(val, units=uarr.units) for val in values]


def vol_to_time(volume, flow_rate, column=None, to_unit="minute"):
    """ Convert a volume to a time, using a flow rate.

    Parameters
    ----------
    volume : UnitScalar
        Volume to convert to a time.

    flow_rate : UnitScalar
        Flow rate used to convert a volume to a time.

    column : Column [OPTIONAL]
        Column the volume is flowing through. From that object are read the
        diameter and colume of the column for unit conversion if needed.

    to_unit : str [OPTIONAL, default: minutes]
        Target time unit. Must be parsable by scimath's unit parser.

    Returns
    -------
    float
        Value of the time needed for the provided volume to flow through the
        column.
    """
    if not isinstance(volume, UnitScalar):
        raise ValueError("The volume provided should be a UnitScalar.")
    elif volume.units == chr_units.column_volumes:
        volume = float(volume) * column.volume

    # Convert a linear flow rate into a volumetric flow rate
    if not is_volumetric_flow_rate(flow_rate):
        diam = column.column_type.diameter
        flow_rate = linear_flow_rate_to_volumetric(flow_rate, diam)

    # Compute the time
    time = volume / flow_rate
    if to_unit:
        # Convert to target unit
        time = convert(time, from_unit=time.units, to_unit=parse_unit(to_unit))
    return float(time)


def volume_to_depth(volume, column, to_unit="meters"):
    """ Translate a volume of fluid into a depth in infinitely long column.
    """
    if volume.units != chr_units.column_volumes:
        volume = convert(volume, from_unit=volume.units,
                         to_unit=column.volume.units)
        volume *= column.volume

    volume = float(volume)
    depth = volume * column.bed_height_actual
    if to_unit:
        depth = convert(depth, from_unit=depth.units,
                        to_unit=parse_unit(to_unit))
    return float(depth)


def time_to_volume(time, flow_rate, column=None, to_unit="CV"):
    """ Convert a flow time to a volume, assuming a specified flow rate.

    Parameters
    ----------
    time : UnitScalar
        Time of flow.

    flow_rate : UnitScalar
        Flow rate.

    column : Column [OPTIONAL]
        Column in which the flow occur. Only needed if providing linear flow
        rate, or if the output unit must be CV.

    to_unit : str
        String representation of the output unit.

    Returns
    -------
    UnitScalar
        Volume that flowed during the specified time.
    """
    if not isinstance(time, UnitScalar):
        msg = "The time provided should be a UnitScalar."
        logger.exception(msg)
        raise ValueError(msg)

    if not is_volumetric_flow_rate(flow_rate):
        diam = column.column_type.diameter
        flow_rate = linear_flow_rate_to_volumetric(flow_rate, diam)

    volume = time * flow_rate

    if to_unit:
        if to_unit == "CV":
            volume = UnitScalar(float(volume / column.volume), units="CV")
        else:
            # Convert to target unit
            parse_unit = unit_parser.parse_unit
            volume = convert(volume, from_unit=volume.units,
                             to_unit=parse_unit(to_unit))
    return volume


def is_volumetric_flow_rate(flow_rate):
    """ Test whether a flow rate (UnitScalar) has a unit of a volume per time.
    """
    try:
        convert(flow_rate, from_unit=flow_rate.units, to_unit=m**3/second)
        return True
    except InvalidConversion:
        return False


def is_linear_flow_rate(flow_rate):
    """ Test whether a flow rate (UnitScalar) has a unit of a volume per time.
    """
    try:
        convert(flow_rate, from_unit=flow_rate.units, to_unit=m/second)
        return True
    except InvalidConversion:
        return False


def has_volume_units(vol):
    try:
        convert(vol, from_unit=vol.units, to_unit=m**3)
        return True
    except InvalidConversion:
        return False


def has_mass_units(units):
    if isinstance(units, (UnitScalar, UnitArray)):
        units = units.units

    return units.derivation == (0, 1, 0, 0, 0, 0, 0)


def linear_flow_rate_to_volumetric(linear_flow_rate, diam, to_unit=""):
    """ Convert a linear flow rate in a column of diameter diam to a volumetric
    flow rate.
    """
    vol_flow_rate = (np.pi * diam ** 2 / 4.) * linear_flow_rate
    if to_unit:
        parse_unit = unit_parser.parse_unit
        from_unit = vol_flow_rate.units
        to_unit = parse_unit(to_unit)
        vol_flow_rate_val = convert(float(vol_flow_rate), from_unit=from_unit,
                                    to_unit=to_unit)
        vol_flow_rate = UnitScalar(vol_flow_rate_val, units=to_unit)
    return vol_flow_rate


def volumetric_flow_rate_to_linear(vol_flow_rate, diam, to_unit=""):
    """ Convert a linear flow rate in a column of diameter diam to a volumetric
    flow rate.
    """
    linear_flow_rate = vol_flow_rate / (np.pi * diam ** 2 / 4.)
    if to_unit:
        parse_unit = unit_parser.parse_unit
        from_unit = linear_flow_rate.units
        to_unit = parse_unit(to_unit)
        linear_flow_rate_val = convert(float(linear_flow_rate),
                                       from_unit=from_unit, to_unit=to_unit)
        linear_flow_rate = UnitScalar(linear_flow_rate_val, units=to_unit)

    return linear_flow_rate


def volumetric_CV_flow_rate_to_volumetric_flow_rate(vol_cv_flow_rate, column,
                                                    to_unit=None):
    """ Convert a volumetric flow rate using the CV unit to a physical unit.

    Parameters
    ----------
    vol_cv_flow_rate : UnitScalar
        Fow rate in column volume unit CV per unit time.

    column : Column
        Column object the flow happens in.

    to_unit : str or Unit
        Unit of the result flow rate.

    Returns
    -------
    float
        Flow rate in SI compatible unit.
    """
    if to_unit is None:
        to_unit = m**3/second
    elif isinstance(to_unit, basestring):
        to_unit = unit_parser.parse_unit(to_unit)

    si_flow_rate = vol_cv_flow_rate * column.volume
    return chr_units.convert_units(si_flow_rate, tgt_unit=to_unit)


def unit_scalar_almost_equal(x1, x2, eps=1e-9):
    """ Returns whether 2 UnitScalars are almost equal.

    Parameters
    ----------
    x1 : UnitScalar
        First unit scalar to compare.

    x2 : UnitScalar
        Second unit scalar to compare.

    eps : float
        Absolute precision of the comparison.
    """
    if not isinstance(x1, UnitScalar):
        msg = "x1 is supposed to be a UnitScalar but a {} was passed."
        msg = msg.format(type(x1))
        logger.exception(msg)
        raise ValueError(msg)

    if not isinstance(x2, UnitScalar):
        msg = "x2 is supposed to be a UnitScalar but a {} was passed."
        msg = msg.format(type(x2))
        logger.exception(msg)
        raise ValueError(msg)

    a1 = float(x1)
    try:
        a2 = convert(float(x2), from_unit=x2.units, to_unit=x1.units)
    except InvalidConversion:
        return False
    return np.abs(a1 - a2) < eps


def unit_almost_equal(unit_1, unit_2, eps=1e-9):
    """ Returns whether the units of the 2 values provided are almost equal.

    Parameters
    ----------
    unit_1 : SmartUnit or UnitScalar or UnitArray
        First unit or unitted object to compare.

    unit_2 : SmartUnit or UnitScalar or UnitArray
        First unit or unitted object to compare.
    """
    if isinstance(unit_1, (UnitScalar, UnitArray)):
        unit_1 = unit_1.units
    if isinstance(unit_2, (UnitScalar, UnitArray)):
        unit_2 = unit_2.units

    if abs(unit_1.offset - unit_2.offset) > eps:
        return False

    if abs(unit_1.value - unit_2.value) > eps:
        return False

    if unit_1.derivation != unit_2.derivation:
        return False

    return True
