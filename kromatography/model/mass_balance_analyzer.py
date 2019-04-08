""" Tool to compare mass loaded both from method information and from
loaded continuous data of an experiment.
"""
import logging

from traits.api import Bool, Float, HasStrictTraits, Instance, Property
from scimath.units.api import UnitScalar
from traitsui.api import Item
from chaco.api import ArrayPlotData, Plot
from enable.api import ComponentEditor
from chaco.tools.api import BetterSelectingZoom, PanTool

from app_common.scimath.units_utils import has_volume_units, \
    unitarray_to_unitted_list, units_almost_equal

from kromatography.model.experiment import Experiment
from kromatography.model.x_y_data import XYData
from kromatography.compute.experiment_performance_parameters import \
    compute_mass_from_abs_data
from kromatography.utils.string_definitions import UV_DATA_KEY
from kromatography.utils.chromatography_units import column_volumes, \
    convert_units, g_per_liter_resin
from kromatography.utils.traitsui_utils import KromView


logger = logging.getLogger(__name__)


class MassBalanceAnalyzer(HasStrictTraits):
    """ Tool to compare loaded mass from continuous data to the method/solution
    information.
    """
    #: Target information we are evaluating mass balance for
    target_experiment = Instance(Experiment)

    #: Time before which to truncate experiment data
    time_of_origin = Instance(UnitScalar)

    #: Continuous UV data to evaluate loaded mass from (passed separately to
    #: support doing analysis while building an exp)
    continuous_data = Instance(XYData)

    #: Loaded mass, as computed from method information
    mass_from_method = Instance(UnitScalar)

    #: Loaded mass, as computed from UV continuous data
    mass_from_uv = Instance(UnitScalar)

    #: Current load product concentration in target experiment
    current_concentration = Property(Instance(UnitScalar))

    #: Current load step volume in target experiment
    current_volume = Property(Instance(UnitScalar))

    #: Threshold for relative difference to define the data as imbalanced
    balance_threshold = Float

    #: Whether the target experiment's data is balanced (in agreement)
    balanced = Bool

    # View elements -----------------------------------------------------------

    #: Plot of the UV data
    plot = Instance(Plot)

    #: Data container for the plot
    plot_data = Instance(ArrayPlotData)

    # Traits methods ----------------------------------------------------------

    def __init__(self, **traits):
        if "target_experiment" not in traits:
            msg = "A target experiment is required to create a {}"
            msg = msg.format(self.__class__.__name__)
            logger.exception(msg)
            raise ValueError(msg)

        super(MassBalanceAnalyzer, self).__init__(**traits)
        use_exp_data = (self.continuous_data is None and
                        self.target_experiment.output is not None)

        # If the tool is created for a fully created experiment, extract the
        # continuous data from the experiment,
        if use_exp_data:
            data_dict = self.target_experiment.output.continuous_data
            self.continuous_data = data_dict[UV_DATA_KEY]

    def traits_view(self):
        view = KromView(
            Item("plot", editor=ComponentEditor(), show_label=False)
        )
        return view

    # Public interface --------------------------------------------------------

    def analyze(self):
        """ Analyze all available loads, and compare to experiments cont. data.

        Returns
        -------
        list
            Returns list of load names that are not balanced.
        """
        product = self.target_experiment.product
        if len(product.product_components) > 1:
            msg = "Unable to analyze the loaded mass for multi-component " \
                  "products, since we don't have a product extinction coeff."
            logger.exception(msg)
            raise ValueError(msg)

        msg = "Analyzing mass balance for {}".format(
            self.target_experiment.name)
        logger.debug(msg)

        self.mass_from_method = self.loaded_mass_from_method()
        self.mass_from_uv = self.loaded_mass_from_uv()

        if self.mass_from_uv is None:
            self.balanced = True
            return

        diff = abs(self.mass_from_method - self.mass_from_uv)
        rel_diff = diff/self.mass_from_method
        msg = "Loaded mass computed from method and UV are different by " \
              "{:.3g}%".format(float(rel_diff)*100)
        logger.debug(msg)

        self.balanced = float(rel_diff) <= self.balance_threshold

    def loaded_mass_from_method(self):
        """ Returns loaded product mass in grams, as compute from method data.
        """
        vol = self.current_volume
        if units_almost_equal(vol, column_volumes):
            vol = float(vol) * self.target_experiment.column.volume
        elif has_volume_units(vol):
            pass
        else:
            msg = "Unexpected unit for the load step volume: {}"
            msg = msg.format(vol.units.label)
            logger.exception(msg)
            raise NotImplementedError(msg)

        mass = vol * self.current_concentration
        return convert_units(mass, tgt_unit="gram")

    def loaded_mass_from_uv(self):
        """ Returns loaded product mass in grams, as compute from UV data.
        """
        if not self.continuous_data:
            return

        data = self.continuous_data
        product = self.target_experiment.product
        ext_coeff = product.product_components[0].extinction_coefficient
        method_step_times = self.target_experiment.method_step_boundary_times
        t_stop = UnitScalar(method_step_times[-1],
                            units=method_step_times.units)
        mass = compute_mass_from_abs_data(data, ext_coeff=ext_coeff,
                                          experim=self.target_experiment,
                                          t_start=self.time_of_origin,
                                          t_stop=t_stop)
        return convert_units(mass, tgt_unit="gram")

    # Adjustment methods ------------------------------------------------------

    def compute_loaded_vol(self, tgt_units=column_volumes):
        """ Compute the load step volume that would match the UV data at
        constant load solution concentration.

        Returns
        -------
        UnitScalar
            Load step volume, in CV, that would be needed to match the UV data.
        """
        if tgt_units not in [column_volumes, g_per_liter_resin]:
            msg = "Supported target units are CV and g/Liter of resin but " \
                  "got {}.".format(tgt_units.label)
            logger.debug(msg)
            raise ValueError(msg)

        target_mass = self.mass_from_uv
        col_volume = self.target_experiment.column.volume
        concentration = self.current_concentration
        vol = target_mass / concentration / col_volume
        # Test equality on the labels since CV and g_per_liter_resin are equal
        # from a derivation point of view (dimensionless)
        if tgt_units.label == g_per_liter_resin.label:
            vol = float(vol * concentration)
            vol = UnitScalar(vol, units=g_per_liter_resin)
        else:
            vol = UnitScalar(vol, units=column_volumes)

        return vol

    def compute_concentration(self):
        """ Compute the load solution concentration that would match the UV
        data at constant load step volume.

        Returns
        -------
        UnitScalar
            Load solution concentration, in g/L, that would be needed to match
            the UV data.
        """
        target_mass = self.mass_from_uv
        vol = self.current_volume
        if units_almost_equal(vol, column_volumes):
            vol = float(vol) * self.target_experiment.column.volume

        concentration = target_mass / vol
        return convert_units(concentration, tgt_unit="g/L")

    # Traits property getters/setters -----------------------------------------

    def _get_current_volume(self):
        load_step = self.target_experiment.method.load
        return load_step.volume

    def _get_current_concentration(self):
        load_sol = self.target_experiment.method.load.solutions[0]
        comp_concs = load_sol.product_component_concentrations
        return unitarray_to_unitted_list(comp_concs)[0]

    # Traits listeners --------------------------------------------------------

    def _continuous_data_changed(self):
        if self.plot_data is None:
            return

        self.plot_data.update_data(x=self.continuous_data.x_data,
                                   y=self.continuous_data.y_data)

    # Traits initialization methods -------------------------------------------

    def _balance_threshold_default(self):
        from kromatography.utils.app_utils import get_preferences
        prefs = get_preferences()
        return prefs.file_preferences.exp_importer_mass_threshold

    def _plot_default(self):
        self.plot_data = ArrayPlotData(x=self.continuous_data.x_data,
                                       y=self.continuous_data.y_data)
        plot = Plot(self.plot_data)
        plot.plot(("x", "y"))
        x_units = self.continuous_data.x_metadata["units"]
        y_units = self.continuous_data.y_metadata["units"]
        plot.index_axis.title = "Time ({})".format(x_units)
        plot.value_axis.title = "UV Absorption ({})".format(y_units)
        # Add zoom and pan tools to the plot
        zoom = BetterSelectingZoom(component=plot, tool_mode="box",
                                   always_on=False)
        plot.overlays.append(zoom)
        plot.tools.append(PanTool(component=plot))
        return plot
