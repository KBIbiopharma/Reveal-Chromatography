""" Largest component insit the CADET input class that gets translated into the
HDF5 input file.

Consequently, the class names, attribute names and units that contained in this
class and its children are set by the specs of the version of CADET using the
generated input file.
"""
import logging
import numpy as np

from traits.api import Array, HasStrictTraits
from scimath.units.api import convert
from scimath.units.length import meter
from scimath.units.time import second

from app_common.traits.custom_trait_factories import PositiveFloat
from ..utils.units_utils import is_volumetric_flow_rate, volume_to_depth, \
    volumetric_flow_rate_to_linear

logger = logging.getLogger(__name__)

# When a fake gradient needs to be created to keep the pH profile
# differentiable, this duration represents the time, in seconds, for that fake
# gradient:
EPS = 1.e-3


class CADETPhExternalProfile(HasStrictTraits):
    """ The CADET external folder/object to contain the pH profile for
    pH-dependent binding models.
    """
    # -------------------------------------------------------------------------
    # CADETExternal traits
    # -------------------------------------------------------------------------

    #: A vector with the pH values at various points in time (time set by
    #: ext_prof_delta).
    #: (Default:N/A) [Range: >=0]
    ext_profile = Array(dtype=float, shape=(None, ))

    #: A vector with the time deltas at which the pH changes. Unit: seconds.
    #: (Default:N/A) [Range: >=0]
    ext_prof_delta = Array(dtype=float, shape=(None, ))

    #: The superficial flow velocity of the above profiles. Unit: meter/second.
    #: (Default:N/A) [Range: >0]
    ext_velocity = PositiveFloat(0., exclude_low=True)

    @classmethod
    def from_simulation(cls, sim):
        """ Compute the profiles and instantiate a CADETExternal.
        """
        column = sim.column

        # Initial array values
        step0 = sim.method.method_steps[0]
        step0_ph = float(step0.solutions[0].pH)
        step0_velocity = get_step_velocity(step0, column)

        # Initialization of the profiles to build
        init_ph = sim.method.initial_buffer.pH
        column_length = convert(column.bed_height_actual, to_unit=meter,
                                from_unit=column.bed_height_actual.units)
        ph_values = [init_ph, step0_ph]
        depth_deltas = [0., float(column_length)]
        for step in sim.method.method_steps:
            step_depth = volume_to_depth(step.volume, column=column,
                                         to_unit="meter")
            step_velocity = get_step_velocity(step, column)

            # If a step flows N times faster, we model this by making its
            # duration N times smaller.
            step_depth *= step0_velocity / step_velocity

            if len(step.solutions) == 0:
                msg = "Step with no solution not supported"
                raise NotImplementedError(msg)

            # Deal with the transition from the previous step
            start_step_ph = float(step.solutions[0].pH)
            transition_needed = ph_values[-1] != start_step_ph
            if transition_needed:
                # Create a fake gradient of pH since CADET requires pH profile
                # to be differentiable
                depth_deltas.append(EPS)
                ph_values.append(start_step_ph)
                step_depth -= EPS

            # Deal with the contributions from this step:
            num_solutions = len(step.solutions)
            if num_solutions == 1:
                end_step_ph = start_step_ph
            elif num_solutions == 2:
                # 2 solutions during gradient elution when the buffer
                # composition goes from 1 solution to the other:
                end_step_ph = float(step.solutions[1].pH)
            else:
                msg = "Found a step with more than 2 solutions. Don't know " \
                      "how to compute the pH profile in that case."
                logger.exception(msg)
                raise NotImplementedError(msg)

            ph_values.append(end_step_ph)
            depth_deltas.append(step_depth)

        ext_profile = np.array(ph_values, dtype="float64")
        ext_prof_delta = np.array(depth_deltas, dtype="float64")

        return cls(ext_profile=ext_profile, ext_prof_delta=ext_prof_delta,
                   ext_velocity=step0_velocity)


def get_step_velocity(step, column=None):
    """ Extract the step linear superficial velocity (flow_rate), in m/s.
    """
    if is_volumetric_flow_rate(step.flow_rate):
        step_velocity = volumetric_flow_rate_to_linear(
            step.flow_rate, column.column_type.diameter, to_unit="m/s"
        )
    else:
        step_velocity = convert(step.flow_rate, from_unit=step.flow_rate.units,
                                to_unit=meter/second)
    return float(step_velocity)
