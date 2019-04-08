
import logging

from traits.api import Constant, Enum, Instance, Int, List, Property, Str, \
    Tuple

from ..utils.string_definitions import LOAD_STEP_TYPE
from app_common.traits.custom_trait_factories import Key
from .chromatography_data import ChromatographyData
from .collection_criteria import CollectionCriteria
from .method_step import MethodStep
from .solution import Solution

#: The type-id for this class.
METHOD_TYPE = "METHOD"

#: Value for the pooling step number that is treated as not set:
UNSET = -1

#: The list of allowed method types.
#: 'UNDEFINED' reserved for initial Method creation from scratch
#: FIXME - add check later to make sure user doesn't select it
ALLOWED_METHOD_RUN_TYPES = [
    "UNDEFINED", "Pulse Injection", "Pulse Gradient", "Gradient Elution",
    "Step Elution", "Flow Through", "Frontal Elution"
]

logger = logging.getLogger(__name__)


class StepLookupError(ValueError):
    pass


class Method(ChromatographyData):
    """ Represents a chromatography method, i.e. a sequence of `MethodSteps`.

    TODO: This class should really be subclassed into a ExperimentMethod and a
    SimulationMethod and move in the latter the initial_buffer and its name.
    That class would also be better to host some of the attributes of the
    Simulation such as first_simulated_step, last_simulated_step and
    step_indices map.
    """

    # -------------------------------------------------------------------------
    # Method traits
    # -------------------------------------------------------------------------

    #: The method type
    run_type = Key(Enum(ALLOWED_METHOD_RUN_TYPES))

    #: List of steps to implement the method
    method_steps = List(Instance(MethodStep))

    #: The initial solution in the column before first (simulated) method step
    initial_buffer = Instance(Solution)

    #: Provide a name attribute for easy access to the initial_buffer name
    initial_buffer_name = Property(Str, depends_on="initial_buffer")

    #: The number of the method step which creates the pool with the product.
    collection_step_number = Int(UNSET)

    #: The criteria to start and stop collection during the method.
    collection_criteria = Instance(CollectionCriteria)

    #: Number of steps in the method
    num_steps = Property(Int, depends_on='method_steps')

    #: Load step among all steps
    load = Property(Instance(MethodStep), depends_on='method_steps')

    #: List of steps not described by continuous data
    # Some steps are listed at the beginning of the method, but the AKTA traces
    # start afterwards.
    offline_steps = List(Str)

    # -------------------------------------------------------------------------
    # ChromatographyData traits
    # -------------------------------------------------------------------------

    #: The type of data being represented by this class.
    type_id = Constant(METHOD_TYPE)

    _unique_keys = Tuple(('name',))

    # -------------------------------------------------------------------------
    # Method interface
    # -------------------------------------------------------------------------

    def get_step_of_type(self, step_type, handle_not_unique="raise",
                         collect_step_num=False):
        """ Returns step of type 'step_type' among the method_steps if present.

        Parameters
        ----------
        step_type : str
            Type of the step searched for. Must be one of the type list in
            kromatography.models.method_step.ALLOWED_METHOD_STEP_TYPES.

        handle_not_unique : str
            Strategy to handle cases where there is not step with the property
            requested, or multiple steps with the property requested. Support
            values are 'raise' or 'warn'.

        collect_step_num : bool
            Return the step number together with the step object?

        Returns
        -------
        step (or list of steps if handle_not_unique == 'warn') for which the
        attribute has the value requested. If collect_step_num is on, instead
        of a step, a tuple with the step and its number in the step list is
        returned.
        """
        return self.get_step_of_attr("step_type", step_type,
                                     handle_not_unique=handle_not_unique,
                                     collect_step_num=collect_step_num)

    def get_step_of_name(self, step_name, handle_not_unique="raise",
                         collect_step_num=False):
        """ Returns step with name 'step_name' among the method_steps if present.

        Parameters
        ----------
        step_name : str
            Name of the step searched for.

        handle_not_unique : str
            Strategy to handle cases where there is not step with the property
            requested, or multiple steps with the property requested. Support
            values are 'raise' or 'warn'.

        collect_step_num : bool
            Return the step number together with the step object?

        Returns
        -------
        step (or list of steps if handle_not_unique == 'warn') for which the
        attribute has the value requested. If collect_step_num is on, instead
        of a step, a tuple with the step and its number in the step list is
        returned.
        """
        return self.get_step_of_attr(
            "name", step_name, handle_not_unique=handle_not_unique,
            collect_step_num=collect_step_num
        )

    def get_step_of_attr(self, attr_name, attr_value,
                         handle_not_unique="raise", collect_step_num=False):
        """ Search for the step with a certain values for a certain attribute.

        Parameters
        ----------
        attr_name : str
            Name of the step attribute to test.

        attr_value : any
            Value to search for in the attribute selected.

        handle_not_unique : str
            Strategy to handle cases where there is not step with the property
            requested, or multiple steps with the property requested. Support
            values are 'raise' or 'warn'.

        collect_step_num : bool
            Return the step number together with the step object?

        Returns
        -------
        step (or list of steps if handle_not_unique == 'warn') for which the
        attribute has the value requested. If collect_step_num is on, instead
        of a step, a tuple with the step and its number in the step list is
        returned.
        """
        candidates = [(step, i) for i, step in enumerate(self.method_steps)
                      if getattr(step, attr_name) == attr_value]

        if len(candidates) > 1:
            values = [getattr(step, attr_name) for step, _ in candidates]

            msg = ("There is more than 1 step with {} = {} (values found are "
                   "{}). You may want to extract manually.")
            msg = msg.format(attr_name, attr_value, values)
            if handle_not_unique == 'raise':
                logger.exception(msg)
                raise StepLookupError(msg)
            else:
                logger.warning(msg)
                if collect_step_num:
                    return candidates
                else:
                    # Strip out the enum counter
                    return [step for step, step_num in candidates]

        elif len(candidates) == 0:
            values = [getattr(step, attr_name) for step in self.method_steps]
            msg = ("No step with {} = {} found in the method: available values"
                   " are {}.".format(attr_name, attr_value, values))
            if handle_not_unique == 'raise':
                logger.exception(msg)
                raise StepLookupError(msg)
            else:
                logger.warning(msg)
        else:
            if collect_step_num:
                return candidates[0]
            else:
                # Strip out the enum counter
                return candidates[0][0]

    # Private interface -------------------------------------------------------

    def __init__(self, **traits):
        super(Method, self).__init__(**traits)

        # Make sure that step names are unique:
        step_names = [step.name for step in self.method_steps]
        if len(set(step_names)) < len(self.method_steps):
            msg = "Unable to create a {} with redundant step names (found {})."
            msg = msg.format(self.__class__.__name__, step_names)
            logger.exception(msg)
            raise ValueError(msg)

    def __str__(self):
        val = "Method {} (id={}):".format(self.name, id(self))
        for step in self.method_steps:
            val += "\n    |_ {}".format(str(step))
        return val

    # Traits property getters -------------------------------------------------

    def _get_initial_buffer_name(self):
        if self.initial_buffer:
            return self.initial_buffer.name
        else:
            return ""

    def _get_num_steps(self):
        return len(self.method_steps)

    def _get_load(self):
        return self.get_step_of_type(LOAD_STEP_TYPE)

    # Traits initialization methods -------------------------------------------

    def _collection_criteria_default(self):
        return CollectionCriteria(name="New collection criteria")
