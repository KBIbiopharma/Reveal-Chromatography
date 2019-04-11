""" Defines the base class for simulations and experiments, and the experiment
implementation.
"""
import logging
from numpy import nan

from scimath.units.api import UnitArray, UnitScalar
from traits.api import Constant, Instance, on_trait_change, Property

from .chromatography_data import ChromatographyData
from .chromatography_results import ChromatographyResults
from .column import Column
from .method import Method
from .solution_with_product import SolutionWithProduct
from .system import System

#: The string constant for the Experiment type-id
EXPERIMENT_TYPE = 'Experiment'

logger = logging.getLogger(__name__)


class _BaseExperiment(ChromatographyData):
    """ Base class for a chromatography experiment or simulation model.
    """

    #: The column used/modeled by the experiment.
    column = Instance(Column)

    #: The method (sequence of method steps) used in the experiment.
    method = Instance(Method)

    #: Product being analyzed if any
    product = Property(depends_on="method")

    #: The results from the experiment.
    output = Instance(ChromatographyResults)

    #: Computed start times for each method steps (and final stop time)
    #: (same time of origin as AKTA/chromatograms)
    method_step_boundary_times = Instance(UnitArray)

    # Public interface --------------------------------------------------------

    @on_trait_change("method.method_steps.flow_rate, "
                     "method.method_steps.volume, method.offline_steps[]",
                     post_init=True)
    def reset_method_step_boundary_times(self):
        """ Recompute the step boundary times from the method description and
        import settings.
        """
        self.method_step_boundary_times = \
            self._method_step_boundary_times_default()

    def get_step_start_time(self, searched_step):
        """ Search for the start time of a given step.
        """
        steps = self.method.method_steps
        start_times = self.method_step_boundary_times
        for step, start_time in zip(steps, start_times):
            if step is searched_step:
                return UnitScalar(start_time, units=start_times.units)

        msg = "Step {} not found in {}".format(searched_step.name,
                                               self.name)
        logger.exception(msg)
        raise KeyError(msg)

    # Traits property getters/setters -----------------------------------------

    def _get_product(self):
        if self.method and self.method.method_steps:
            for step in self.method.method_steps:
                if step.solutions:
                    for solution in step.solutions:
                        if isinstance(solution, SolutionWithProduct):
                            return solution.product

        msg = "No solution with product found in the method of {}. Unable " \
              "to set the product it describes.".format(self.name)
        logger.error(msg)
        return None

    # Traits initialization methods -------------------------------------------

    def _method_step_boundary_times_default(self):
        from kromatography.utils.simulation_utils import \
            calculate_step_start_times

        if not self.method:
            return

        # Step start times based on volumes and flow rates:
        start_times = calculate_step_start_times(self)
        # Remove offline step durations if any:
        for i, step in enumerate(self.method.method_steps):
            if step.name in self.method.offline_steps:
                step_stop_time = UnitScalar(start_times[i + 1],
                                            units=start_times.units)
                start_times = start_times - step_stop_time
            else:
                break

        return start_times


class Experiment(_BaseExperiment):
    """ Represents a physical chromatography experiment.
    """
    #: The chromatography system used/modeled by the experiment.
    system = Instance(System)

    #: Fraction of the mass loaded in the column that elutes after pooling step
    strip_mass_fraction = Instance(UnitScalar)

    # -------------------------------------------------------------------------
    # ChromatographyData traits
    # -------------------------------------------------------------------------

    #: The user visible type-id for the class.
    type_id = Constant(EXPERIMENT_TYPE)

    def _strip_mass_fraction_changed(self, old, new):
        """ Strip fraction was recomputed. Update load solution.

        Load solution updated so that the component concentration computations
        will use that fraction. If the method raises an exception, set value
        from load solution to remain in sync.
        """
        if self.method is None:
            return

        if len(self.method.load.solutions) > 1:
            msg = "Load step with more than 1 solution isn't supported."
            logger.exception(msg)
            raise NotImplementedError(msg)

        load = self.method.load.solutions[0]
        try:
            load.strip_mass_fraction = new
        except ValueError as e:
            msg = "Strip fraction failed to be set to {}. Error was {}. " \
                  "Reverting.".format(new, e)
            logger.error(msg)

            self.strip_mass_fraction = old

    # Trait initialization methods --------------------------------------------

    def _strip_mass_fraction_default(self):
        """ Compute strip fraction if strip component and strip step.
        """
        from kromatography.compute.experiment_performance_parameters import \
            compute_strip_fraction
        from kromatography.utils.string_definitions import STRIP_COMP_NAME, \
            STRIP_STEP_TYPE

        if self.method is None:
            return UnitScalar(nan, units="%")

        strip_step = STRIP_STEP_TYPE in [step.name for step in
                                         self.method.method_steps]
        strip_comp = STRIP_COMP_NAME in self.product.product_component_names

        if strip_step and strip_comp:
            return compute_strip_fraction(self)
        else:
            return UnitScalar(nan, units="%")

    def _method_step_boundary_times_default(self):
        times = super(Experiment, self)._method_step_boundary_times_default()
        if times is None:
            return

        if self.output:
            holdup_vol = self.output.import_settings["holdup_volume"]
            manual_shift = self.output.import_settings["time_of_origin"]
        else:
            holdup_vol = manual_shift = UnitScalar(0, units="min")

        shifted_start_times = times - holdup_vol - manual_shift
        return shifted_start_times
