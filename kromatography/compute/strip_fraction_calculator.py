from __future__ import print_function
from logging import getLogger
from numpy import nan

from scimath.units.api import UnitScalar
from traits.api import Button, HasStrictTraits, Instance, on_trait_change, \
    Property

from kromatography.model.api import Experiment, MethodStep, ProductComponent
from kromatography.model.method import StepLookupError
from kromatography.utils.string_definitions import STRIP_COMP_NAME, \
    STRIP_STEP_TYPE, UV_DATA_KEY
from kromatography.utils.units_utils import has_volume_units
from kromatography.utils.chromatography_units import convert_units
from .experiment_performance_parameters import compute_mass_from_abs_data, \
    get_most_contributing_component

logger = getLogger(__name__)


class StripFractionCalculator(HasStrictTraits):
    """ Class to estimate the strip fraction expected from experimental data.

    It is designed with many intermediate
    """
    #: Experiment from which is drawn data & parameters to estimate strip mass
    experim = Instance(Experiment)

    #: Result quantity
    strip_mass_fraction = Instance(UnitScalar)

    #: Volume of load
    loaded_volume = Instance(UnitScalar)

    #: Concentration of product in load
    load_concentration = Instance(UnitScalar)

    #: Mass of product loaded in the column
    loaded_mass = Instance(UnitScalar)

    #: Mass recovered before the strip
    integrated_mass_before_strip = Instance(UnitScalar)

    #: Component from which to guess the average product extinction coefficient
    most_contributing_comp = Instance(ProductComponent)

    #: Average product extinction coefficient
    product_ext_coeff = Instance(UnitScalar)

    #: Event to trigger a reload of the experiment and reset all quantities
    reset = Button("Reload experiment")

    #: Load step object
    _load_step = Property(Instance(MethodStep),
                          depends_on="experim.method.method_steps")

    #: Strip step object
    _strip_step = Property(Instance(MethodStep),
                           depends_on="experim.method.method_steps")

    #: Load step start time: proxy for experim.method_step_boundary_times
    load_start = Property(Instance(UnitScalar),
                          depends_on="experim.method_step_boundary_times")

    #: Strip step start time: : proxy for experim.method_step_boundary_times
    strip_start = Property(Instance(UnitScalar),
                           depends_on="experim.method_step_boundary_times")

    # StripFractionCalculator private interface -------------------------------

    def _react_to_step_start_change(self, old, new):
        """ A step start changed. Apply the shift to the entire experimental
        method step start times for it to remain in sync with step properties.
        """
        if old is None or new is None:
            return

        shift = new - old
        self.experim.method_step_boundary_times = \
            self.experim.method_step_boundary_times + shift

    # Traits listeners --------------------------------------------------------

    def _reset_fired(self):
        """ Reset all values in the calculator by resetting the step boundary
        times and resetting the calculator's experiment.
        """
        self.experim.reset_method_step_boundary_times()
        current_exp = self.experim
        self.experim = None
        self.experim = current_exp

    def _experim_changed(self):
        if self.experim and self.experim.method:
            if self._strip_step is None:
                self.strip_mass_fraction = UnitScalar(nan, units="%")

        self.product_ext_coeff = self._product_ext_coeff_default()

    def __load_step_changed(self):
        load_step = self._load_step
        if load_step is None:
            self.loaded_volume = None
            self.load_concentration = None
            return

        if has_volume_units(load_step.volume):
            loaded_volume = load_step.volume
        else:
            loaded_volume = load_step.volume * self.experim.column.volume

        self.loaded_volume = convert_units(loaded_volume, tgt_unit="liter")
        load_solution = load_step.solutions[0]
        self.load_concentration = load_solution.product_concentration

    @on_trait_change('loaded_volume, load_concentration')
    def load_characteristics_changed(self):
        if self.loaded_volume is None or self.load_concentration is None:
            self.loaded_mass = None
            return

        loaded_mass = self.loaded_volume * self.load_concentration
        # Converted to grams just so that it displays nicely in UI
        self.loaded_mass = convert_units(loaded_mass, tgt_unit="gram")

    @on_trait_change('product_ext_coeff, load_start, strip_start')
    def recompute_integrated_mass(self):
        input_is_none = (
            self.experim is None or self.product_ext_coeff is None or
            self.load_start is None or self.strip_start is None
        )
        if input_is_none:
            self.integrated_mass_before_strip = None
            return

        continuous_data = self.experim.output.continuous_data
        exp_data = continuous_data.get(UV_DATA_KEY, None)
        if exp_data is None:
            self.integrated_mass_before_strip = None
        else:
            self.integrated_mass_before_strip = compute_mass_from_abs_data(
                exp_data, self.product_ext_coeff, self.experim,
                self.load_start, self.strip_start
            )

    @on_trait_change('integrated_mass_before_strip, loaded_mass')
    def recompute_mass_fraction(self):
        input_is_none = (self.integrated_mass_before_strip is None or
                         self.loaded_mass is None)
        if input_is_none:
            self.strip_mass_fraction = UnitScalar(nan, units="%")
            return

        fraction = (1. - self.integrated_mass_before_strip /
                    self.loaded_mass)
        self.strip_mass_fraction = UnitScalar(fraction * 100, units="%")

    # Traits property getters/setters -----------------------------------------

    def _get__load_step(self):
        if self.experim and self.experim.method:
            return self.experim.method.load
        else:
            return None

    def _get__strip_step(self):
        if self.experim is None or self.experim.method is None:
            return

        try:
            return self.experim.method.get_step_of_type(STRIP_STEP_TYPE)
        except StepLookupError:
            msg = "No strip step found."
            logger.warning(msg)
            return None

    def _get_strip_start(self):
        if self.experim and self._strip_step:
            return self.experim.get_step_start_time(self._strip_step)
        else:
            return None

    def _get_load_start(self):
        if self.experim and self._load_step:
            return self.experim.get_step_start_time(self._load_step)
        else:
            return None

    def _set_load_start(self, new):
        old = self.load_start
        self._react_to_step_start_change(old, new)

    def _set_strip_start(self, new):
        old = self.strip_start
        self._react_to_step_start_change(old, new)

    # Traits initialization methods -------------------------------------------

    def _strip_mass_fraction_default(self):
        return UnitScalar(nan, units="%")

    def _most_contributing_comp_default(self):
        # Exclude the strip component
        return get_most_contributing_component(self.experim,
                                               exclude={STRIP_COMP_NAME})

    def _product_ext_coeff_default(self):
        if self.experim is None or self.most_contributing_comp is None:
            return None

        return self.most_contributing_comp.extinction_coefficient
