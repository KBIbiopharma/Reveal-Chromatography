from traits.api import Constant, Enum, Instance, List, on_trait_change, Str, \
    Tuple
from scimath.units.api import UnitScalar

from .chromatography_data import ChromatographyData
from .solution import Solution
from ..utils.chromatography_units import cm_per_hr, column_volumes
from app_common.traits.custom_trait_factories import Key, Parameter
from ..utils.string_definitions import PRE_EQ_STEP_TYPE, EQ_STEP_TYPE, \
    LOAD_STEP_TYPE, INJECTION_STEP_TYPE, WASH_STEP_TYPE, STEP_ELUT_STEP_TYPE, \
    GRADIENT_ELUT_STEP_TYPE, STRIP_STEP_TYPE, CLEAN_STEP_TYPE, \
    REGENERATION_STEP_TYPE, STORE_STEP_TYPE

#: The type-id for this class
METHOD_STEP_TYPE = "METHOD STEP"

#: The list of allowed method step types
ALLOWED_METHOD_STEP_TYPES = [
    PRE_EQ_STEP_TYPE,
    EQ_STEP_TYPE,
    LOAD_STEP_TYPE,
    INJECTION_STEP_TYPE,
    WASH_STEP_TYPE,
    STEP_ELUT_STEP_TYPE,
    GRADIENT_ELUT_STEP_TYPE,
    STRIP_STEP_TYPE,
    CLEAN_STEP_TYPE,
    REGENERATION_STEP_TYPE,
    STORE_STEP_TYPE,
]


class MethodStep(ChromatographyData):
    """ Represents a chromatography method step.
    """
    # -------------------------------------------------------------------------
    # MethodStep traits
    # -------------------------------------------------------------------------

    #: The step type
    step_type = Key(Enum(ALLOWED_METHOD_STEP_TYPES))

    #: Liquid involved in chromatography step. Can be a Buffer or a Load.
    # Typically, there is 1 solution per step, occasionally 2.
    solutions = List(Instance(Solution))

    #: Flow rate of solution, typically in cm/hr
    flow_rate = Parameter()

    #: Volume of solution involved (in Column Volume CVs)
    volume = Parameter()

    # Name of first solution. Used for quick description of a step
    _solutions0_name = Str

    # Name of second solution. Used for quick description of a step
    _solutions1_name = Str

    # -------------------------------------------------------------------------
    # ChromatographyData traits
    # -------------------------------------------------------------------------

    #: The type of data being represented by this class.
    type_id = Constant(METHOD_STEP_TYPE)

    _unique_keys = Tuple(('name',))

    def _flow_rate_default(self):
        return UnitScalar(0.0, units=cm_per_hr)

    def _volume_default(self):
        return UnitScalar(0.0, units=column_volumes)

    @on_trait_change("solutions[]")
    def update_solution_names(self):
        """
        """
        if len(self.solutions) >= 1:
            self._solutions0_name = self.solutions[0].name
        if len(self.solutions) >= 2:
            self._solutions1_name = self.solutions[1].name
