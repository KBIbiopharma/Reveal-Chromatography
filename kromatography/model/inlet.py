import numpy as np

from traits.api import Array, HasStrictTraits, Instance, List

from app_common.traits.custom_trait_factories import PositiveInt
from .section import Section


class Inlet(HasStrictTraits):
    """ Inlet information for the simulation
    """
    # -------------------------------------------------------------------------
    # Section traits
    # -------------------------------------------------------------------------

    #: Number of sections in the simulation
    #: (Default: NA) [Range >= 1]
    nsec = PositiveInt()

    #: A vector with simulation times at which inlet function is discontinous;
    #: including start and end times (units = seconds)
    #: (Default: Vector of length nsec + 1 containing zeros) [Range >= 0.0]
    section_times = Array(dtype=float, shape=(None,))

    #: A vector indicating continuity of each section transition
    #: 0 (discontinuous) or 1 (continuous)
    #: (Default: Vector of length nsec-1 containing zeros) [Range: 0 or 1]
    section_continuity = Array(dtype=int, shape=(None,))

    #: A vector containing nsec Section class objects
    #: (Default: Empty Vector ) [Range: NA]
    section = List(Instance(Section))

    # -------------------------------------------------------------------------
    # Private methods
    # -------------------------------------------------------------------------

    def __init__(self, num_components, num_sections, **traits):
        traits['nsec'] = num_sections
        traits.setdefault('section_times', np.zeros(num_sections + 1))
        traits.setdefault('section_continuity', np.zeros(num_sections - 1))
        # Create a distinct Section object for each section:
        traits.setdefault('section', [Section(num_components)
                                      for _ in range(num_sections)])
        super(Inlet, self).__init__(**traits)
