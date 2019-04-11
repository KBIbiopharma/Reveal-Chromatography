""" Supporting calculation functions for binding model parameter optimization.
"""
import logging
from numpy import nan, trapz

logger = logging.getLogger(__name__)


def calc_trailing_slope(x_data, y_data, low_trigger_fraction=0.2,
                        high_trigger_fraction=0.8):
    """ Returns slope on the back side of the peak between two points.

    First point is the first value below the high trigger (starting search from
    the peak). Second point is the first value below the low trigger (starting
    from first point): (y2-y1)/(x2-x1) .

    Uses linear interpolation to estimate where we're at the actual trigger
    value to reduce sensitivity to low resolution of fraction data. Includes
    some protection for non-ideal data that drops straight to a zero slope
    (making interpolation hard).

    Parameters
    ----------
    y_data : array
        Data we're computing the trailing slope for.

    x_data : array
        Time values along which y_data is provided.

    low_trigger_fraction : float
        Fraction of the data max above which to compute the trailing slope.

    high_trigger_fraction : float
        Fraction of the data max below which to compute the trailing slope.
    """
    peak_max = y_data.max()
    index_max = y_data.argmax()

    y_high_trigger = high_trigger_fraction * peak_max
    y_low_trigger = low_trigger_fraction * peak_max

    index_back_high_trigger = find_index_of_first_value_below(
        y_data, index_max, +1, y_high_trigger
    )
    index_back_low_trigger = find_index_of_first_value_below(
        y_data, index_back_high_trigger, +1, y_low_trigger
    )

    peak_at_end = (index_back_high_trigger + 1 >= len(y_data) or
                   index_back_low_trigger + 1 >= len(y_data))
    if peak_at_end:
        msg = "Peak found at end of the dataset: unable to compute trailing " \
              "slope."
        logger.warning(msg)
        return nan

    # linearly interpolate the times to hit the trigger values
    # high trigger estimate
    y2 = y_data[index_back_high_trigger + 1]
    y1 = y_data[index_back_high_trigger]
    x2 = x_data[index_back_high_trigger + 1]
    x1 = x_data[index_back_high_trigger]

    if y2 - y1 == 0:
        msg = ("Poor estimate of backside slope.  Using 0.0 as slope estimate "
               "to avoid division by 0")
        logger.warning(msg)
        return nan

    x_high_estimate = (y_high_trigger - y1) / (y2 - y1) * (x2 - x1) + x1

    # low trigger estimate
    y2 = y_data[index_back_low_trigger + 1]
    y1 = y_data[index_back_low_trigger]
    x2 = x_data[index_back_low_trigger + 1]
    x1 = x_data[index_back_low_trigger]

    # interpolate where we cross the low threshold
    if y1 > y2:  # normal case, decreasing value
        x_low_estimate = (y_low_trigger - y1) / (y2 - y1) * (x2 - x1) + x1
    else:
        # special case, flat or trace starts increasing, don't interpolate,
        # just use first point below trigger
        x_low_estimate = x1

    # todo - think about how to handle a scenario where the data cuts off
    # before we drop to low_trigger... need to handle?
    delta_y = y_low_trigger - y_high_trigger
    delta_x = x_low_estimate - x_high_estimate
    trailing_slope = delta_y / delta_x
    return trailing_slope


def calc_peak_center_of_mass(x_data, y_data):
    """ Calculates the location of the center of mass for peak:
    integral(x*y*dx)/integral(y*dx).
    """
    return trapz(x_data * y_data, x_data) / trapz(y_data, x_data)


def calc_peak_timing(x_data, y_data):
    """ Returns the x value corresponding to y's maximum. If the peak is flat,
    the first instance where the maximum is reached will be returned.
    """
    return x_data[y_data.argmax()]


def find_index_of_first_value_below(y_data, start_index, step, trigger):
    """ Given a starting location in an array, returns index of first value
    less than the trigger.

    Parameters
    ----------
    y_data : array
        Data we're searching.

    start_index : int
        Starting point within ydata.

    step: int
        Indicates direction to search (sign), and step size (abs value).

    trigger : float
        Value we're testing against
    """
    i = start_index

    for j in range(0, len(y_data)):
        if y_data[i] <= trigger:
            return i

        i = i + step

        if i <= 0:
            # return start of array if we haven't hit the trigger by the start
            return 0

        if i >= len(y_data) - 1:
            # next test will be last element or exceed array bounds: return end
            # of array if we haven't hit the trigger by the end
            return len(y_data) - 1
