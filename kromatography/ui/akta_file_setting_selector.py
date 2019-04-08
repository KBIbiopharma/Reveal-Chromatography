""" UI to allow a user to select the settings of the AKTA reader to parser
successfully an AKTA file.
"""
from os.path import basename
import logging

from traits.api import Bool, Dict, Enum, HasStrictTraits, Instance, Int, List,\
    on_trait_change, Property, Regex, Str
from traitsui.api import CodeEditor, EnumEditor, HGroup, InstanceEditor, Item,\
    Label, OKCancelButtons, RangeEditor, Tabbed, TableEditor, VGroup
from traitsui.table_column import ObjectColumn
from scimath.units.api import UnitScalar

from app_common.traitsui.unit_scalar_editor import UnitScalarEditor
from app_common.std_lib.os_utils import get_ctrl

from kromatography.utils.chromatography_units import convert_units, \
    g_per_liter_resin
from kromatography.io.akta_reader import AKTAReader, AktaReadError, \
    DATA_NAME_SEARCH_PATTERNS, DATA_TYPES, validate_time_of_origin
from kromatography.model.mass_balance_analyzer import MassBalanceAnalyzer
from kromatography.model.experiment import Experiment
from kromatography.model.method import StepLookupError
from kromatography.io.experiment_builder_utils import \
    continuous_data_from_akta
from kromatography.utils.traitsui_utils import KromView
from kromatography.utils.string_definitions import UV_DATA_KEY

logger = logging.getLogger(__name__)

# List of dataset types that must be match for the AKTA settings to be
# acceptable
REQUIRED_TYPES = [UV_DATA_KEY]

DO_NOTHING = "Do nothing"

UPDATE_LOAD_CONC = "Update load solution concentration (MANUAL)"

UPDATE_LOAD_VOL = "Update load step volume (AUTOMATIC)"

DO_NOTHING_OUTPUT = "No mass balance adjustment"


class NamePattern(HasStrictTraits):
    """ Proxy class to display the AKTAFileSettingSelector.col_name_patterns in
    a table.
    """

    #: Type of a column if it confirms to the regex type_regex
    dataset_type = Enum(DATA_TYPES)

    #: Regex a column name must conform to to be of type dataset_type
    type_regex = Regex

    #: Name(s) of the actual columns in the file that match the regex
    matching_col_name = Str

    #: reader with all default settings
    akta_reader = Instance(AKTAReader)

    #: True if the regex leads to more than 1 column matching the data type
    collision = Bool

    @on_trait_change('akta_reader.header_info')
    def update_col_name(self):
        no_header = (self.akta_reader is None or
                     self.dataset_type not in self.akta_reader.header_info)
        if no_header:
            self.matching_col_name = ""
            return

        if not self.type_regex:
            self.matching_col_name = ""
            return

        col_info = self.akta_reader.header_info[self.dataset_type]
        if isinstance(col_info, dict):
            self.matching_col_name = col_info['header_name']
            self.collision = False
        else:
            # Multiple columns are matching
            candidates = [col['header_name'] for col in col_info]
            self.matching_col_name = candidates[0]
            self.collision = True


class AKTAFileSettingSelector(HasStrictTraits):
    """ UI to customize how to import experiment continuous data.

    This has 3 components:
      1. Whether to apply a time shift to the time information of the AKTA file
      2. How to map AKTA column names to column types the app is looking for
      3. How to handle mass balance discrepancy if any, between the UV data and
         the experiment method data.
    """
    #: AKTA file to parse
    akta_filepath = Str

    #: Experiment the AKTA data is loaded for (used to study mass balance)
    target_experiment = Instance(Experiment)

    #: Name of the target experiment
    experiment_name = Property(Str, depends_on="target_experiment")

    #: Name of the step the AKTA time of origin is the beginning of
    akta_start_method_step = Enum(values="_all_step_names")

    #: List of all method step names
    _all_step_names = Property(List(Str), depends_on="target_experiment")

    #: Whether the target experiment is about a single product component
    # (Mass balance can only be analyzed for pure protein cases)
    pure_protein_exp = Property(Bool, depends_on="target_experiment")

    #: reader with current settings
    akta_reader = Instance(AKTAReader)

    #: Raw content of the file
    file_preview = Property(Str, depends_on='akta_filepath, length_of_preview')

    #: Number of lines from the AKTA file to show in preview
    length_of_preview = Int(100)

    #: Value of AKTA recorded time that should become the time origin
    time_of_origin = Instance(UnitScalar)

    #: Regex that a column name must conform to be of a certain type.
    col_name_patterns = Dict(DATA_NAME_SEARCH_PATTERNS)

    #: List of all column names found in the AKTA file
    all_col_names = Property(List(Str), depends_on="akta_reader")

    #: Proxy for col_name_patterns to be displayed as a table
    patterns_as_list = List(NamePattern)

    #: Stored AKTA import settings for use to import experiment
    import_settings = Dict

    #: Analyze if the experiment data is compatible from a mass balance POV
    mass_bal_analyzer = Instance(MassBalanceAnalyzer)

    #: Is experiment data is compatible from a mass balance POV
    mass_balanced = Bool(True)

    #: Error message if regex patterns don't find a required type or find more
    #: than 1 columns.
    pattern_error_msg = Str

    #: Error message if the time of origin chosen isn't in the logbook time.
    origin_error_msg = Str

    #: Error message if the mass data isn't consistent
    mass_bal_msg = Str

    #: Name of the possible mass balance strategies
    mass_bal_strategy = Enum([DO_NOTHING, UPDATE_LOAD_VOL,
                              UPDATE_LOAD_CONC])

    #: Description of the consequence of the selected strategy
    mass_bal_strategy_msg = Str(DO_NOTHING_OUTPUT)

    # Traits methods ----------------------------------------------------------

    def __init__(self, **kwargs):
        super(AKTAFileSettingSelector, self).__init__(**kwargs)
        self.initialize_settings()

    def initialize_settings(self):
        """ Initialize models and messages to display from default settings.
        """
        self.update_pattern_error_msg()
        self._update_method_time_alignment()
        self.update_settings()

    def traits_view(self):
        col_pattern_editor = build_col_name_editor(self.all_col_names)
        filename = basename(self.akta_filepath)
        spinner_editor = RangeEditor(low=5, high=9999, mode='spinner')
        time_orig = 'AKTA time from which to import AKTA data and name' \
                    ' of the corresponding step (typically the load).'
        search_instructions = 'Hit {}-f to search for a word'
        search_instructions = search_instructions.format(get_ctrl())

        view = KromView(
            Tabbed(
                VGroup(
                    VGroup(
                        Label(time_orig),
                        HGroup(
                            Item('time_of_origin', editor=UnitScalarEditor(),
                                 show_label=False),
                            Item("akta_start_method_step",
                                 label="Method step @ t=0"),
                        ),
                        Item('origin_error_msg', emphasized=True,
                             visible_when='origin_error_msg',
                             style='readonly', label="Note"),
                        show_border=True, label="Time of origin"
                    ),
                    VGroup(
                        Item('patterns_as_list', editor=col_pattern_editor,
                             show_label=False, height=200),
                        Item('pattern_error_msg', emphasized=True,
                             visible_when='pattern_error_msg',
                             style='readonly', label="Error"),
                        show_border=True, label="AKTA Column Types"
                    ),
                    label="AKTA File Settings"
                ),
                VGroup(
                    Item('file_preview', editor=CodeEditor(),
                         show_label=False, tooltip=search_instructions),
                    VGroup(Item('length_of_preview', editor=spinner_editor)),
                    show_border=True,
                    label="AKTA File Preview".format(filename),
                ),
                VGroup(
                    # Information used to evaluate the loaded product mass
                    Item("mass_bal_analyzer", editor=InstanceEditor(),
                         style="custom", show_label=False),
                    VGroup(
                        HGroup(
                            Item("mass_bal_msg", emphasized=True,
                                 style='readonly', show_label=False),
                        ),
                        Item("mass_bal_strategy",
                             label="Adjustment strategy",
                             enabled_when="not mass_balanced"),
                        HGroup(
                            Item("mass_bal_strategy_msg", emphasized=True,
                                 style='readonly', show_label=False,
                                 enabled_when="not mass_balanced"),
                        ),
                        visible_when="target_experiment and pure_protein_exp"
                    ),
                    label="UV and Mass Balance",
                ),
            ),
            buttons=OKCancelButtons,
            title="Experiment Importer: {}".format(self.experiment_name),
            width=900,
        )

        return view

    # Public interface --------------------------------------------------------

    def evaluate_mass_balance(self):
        """ Compare the loaded product mass from the method and UV information.
        """
        self.mass_bal_analyzer.analyze()
        self.mass_balanced = self.mass_bal_analyzer.balanced
        self.update_mass_balance_msg()

    def update_mass_balance_msg(self):
        if not self.mass_balanced:
            mass_from_method = float(self.mass_bal_analyzer.mass_from_method)
            mass_from_uv = float(self.mass_bal_analyzer.mass_from_uv)
            msg = "WARNING: Product mass information inconsistent: method " \
                  "information indicates {:.3g} grams is loaded, \nwhile UV " \
                  "data indicates {:.3g} grams is loaded."
            msg = msg.format(mass_from_method, mass_from_uv)
            self.mass_bal_msg = msg
        else:
            self.mass_bal_msg = "Product mass information consistent."

    def apply_strategy(self):
        if self.mass_bal_strategy == UPDATE_LOAD_CONC:
            step = self.target_experiment.method.load
            step.volume = self.mass_bal_analyzer.compute_loaded_vol()
            msg = "Load step volume for {} overwritten to {} {}."
            msg = msg.format(self.target_experiment.name, float(step.volume),
                             step.volume.units.label)
            logger.debug(msg)
        else:
            logger.debug("No automatic change requested.")

    def reanalyze_mass_balance(self):
        """ Recollect data and launch mass balance analysis with new settings.

        FIXME: no need to recompute both values: only the UV one is needed.
        We should invalidate just the one that needs re-computation
        """
        data = continuous_data_from_akta(self.import_settings,
                                         self.target_experiment)
        self.mass_bal_analyzer.continuous_data = data[UV_DATA_KEY]
        self.mass_bal_analyzer.time_of_origin = \
            self.import_settings["time_of_origin"]
        if self.pure_protein_exp:
            self.evaluate_mass_balance()

    # Private interface -------------------------------------------------------

    def _build_conc_strategy_msg(self):
        conc = self.mass_bal_analyzer.current_concentration
        target = self.mass_bal_analyzer.compute_concentration()
        msg = "Load solution product concentration should be adjusted from " \
              "{:.4g} {} to {:.4g} g/L. \nWARNING: This CANNOT be done " \
              "automatically and should be done manually in the input (Excel)"\
              " file."
        msg = msg.format(float(conc), conc.units.label, float(target))
        self.mass_bal_strategy_msg = msg

    def _build_volume_strategy_msg(self):
        conc = self.mass_bal_analyzer.current_concentration
        vol = convert_units(self.mass_bal_analyzer.current_volume,
                            tgt_unit=g_per_liter_resin, concentration=conc)
        target = self.mass_bal_analyzer.compute_loaded_vol(
            tgt_units=g_per_liter_resin)
        msg = "Clicking 'OK' will automatically adjust the Load step volume " \
              "so the load rate changes from {0:.4g} {1} to {2:.4g} {1}."
        msg = msg.format(float(vol), vol.units.label, float(target))
        self.mass_bal_strategy_msg = msg

    def update_pattern_error_msg(self):
        """ The error message should be empty unless a needed curve hasn't been
        found.
        """
        self.pattern_error_msg = ""
        for data_type in REQUIRED_TYPES:
            if data_type not in self.akta_reader.header_info:
                err_msg = "No {} column has been found. Select a column that "\
                          "contains that data. "
                err_msg = err_msg.format(data_type)
                self.pattern_error_msg += err_msg

    def _update_method_time_alignment(self):
        """ Store the offline step information in the experiment.

        Needed to compute the loaded mass from UV data correctly.
        """
        # Store what steps are described in the method but not in the AKTA
        method = self.target_experiment.method
        method.offline_steps = []
        for step in method.method_steps:
            if step.name != self.akta_start_method_step:
                method.offline_steps.append(step.name)
            else:
                break

    # Traits listeners --------------------------------------------------------

    def _mass_bal_msg_changed(self):
        self.import_settings["mass_balance_status"] = self.mass_bal_msg

    def _mass_bal_strategy_changed(self):
        self.import_settings["mass_balance_strategy"] = \
            self.mass_bal_strategy_msg

        if self.mass_bal_strategy == UPDATE_LOAD_VOL:
            msg = "Strategy is to adjust the load step volume"
            logger.debug(msg)
            self._build_volume_strategy_msg()
        elif self.mass_bal_strategy == UPDATE_LOAD_CONC:
            msg = "Strategy is to adjust the load solution protein " \
                  "concentration."
            logger.debug(msg)
            self._build_conc_strategy_msg()
        else:
            msg = "Strategy is to do nothing"
            logger.debug(msg)

    def _mass_bal_strategy_msg_changed(self):
        self.import_settings["mass_balance_strategy"] = \
            self.mass_bal_strategy_msg

    def _akta_start_method_step_changed(self):
        self.import_settings["step_of_origin"] = self.akta_start_method_step
        self._update_method_time_alignment()
        self.reanalyze_mass_balance()

    @on_trait_change("col_name_patterns[]", post_init=True)
    def update_settings(self):
        self.import_settings = {
            "akta_fname": self.akta_filepath,
            "time_of_origin": self.time_of_origin,
            "step_of_origin": self.akta_start_method_step,
            "col_name_patterns": self.col_name_patterns,
            "mass_balance_status": self.mass_bal_msg,
            "mass_balance_strategy": self.mass_bal_strategy_msg
        }
        self.reanalyze_mass_balance()

    @on_trait_change('patterns_as_list.matching_col_name')
    def rebuild_col_name_patterns(self):
        new_type_name_map = {patt.dataset_type: patt.matching_col_name
                             for patt in self.patterns_as_list}
        self.col_name_patterns.update(new_type_name_map)
        # Update reader (triggers a reload the akta file with the new regex)
        try:
            self.akta_reader.col_name_patterns = self.col_name_patterns
        except AktaReadError:
            # current set leads to errors. Ignore as it is hopefully not the
            # final choice
            pass

        self.update_pattern_error_msg()

    def _time_of_origin_changed(self):
        """ Update error message for ToO, and recompute mass balance if needed.
        """
        self.origin_error_msg = ''
        if not validate_time_of_origin(self.akta_reader, self.time_of_origin):
            msg = "The time of origin selected doesn't appear in the time " \
                  "line of the logbook. Please check."
            self.origin_error_msg = msg

        self.import_settings["time_of_origin"] = self.time_of_origin
        self.mass_bal_analyzer.time_of_origin = self.time_of_origin
        self.reanalyze_mass_balance()

    # Traits property getters/setters -----------------------------------------

    def _get_pure_protein_exp(self):
        if self.target_experiment is None:
            return False

        return len(self.target_experiment.product.product_components) == 1

    def _get_file_preview(self):
        with open(self.akta_filepath, "Ur") as f:
            lines = f.readlines()[:self.length_of_preview]
        lines = map(str.strip, lines)
        return "\n".join(lines)

    def _get_all_col_names(self):
        col_names = [data['header_name'] for key, data in
                     self.akta_reader.header_info.items()
                     if not key.startswith("time_")]
        return col_names

    def _get__all_step_names(self):
        if self.target_experiment is None:
            return []

        return [step.name for step in
                self.target_experiment.method.method_steps]

    def _get_experiment_name(self):
        if self.target_experiment is None:
            return "No experiment"
        else:
            return self.target_experiment.name

    # Traits initialization methods -------------------------------------------

    def _patterns_as_list_default(self):
        patterns = []
        for key, val in self.col_name_patterns.items():
            patt = NamePattern(dataset_type=key, type_regex=val,
                               akta_reader=self.akta_reader)

            patt.update_col_name()
            patterns.append(patt)

        return patterns

    def _akta_reader_default(self):
        return AKTAReader(file_path=self.akta_filepath,
                          raise_on_collision=False,
                          col_name_patterns=self.col_name_patterns)

    def _mass_bal_analyzer_default(self):
        return MassBalanceAnalyzer(
            target_experiment=self.target_experiment
        )

    def _time_of_origin_default(self):
        # FIXME: read the unit off of the AKTA file
        return UnitScalar(0., units="min")

    def _akta_start_method_step_default(self):
        if not self.target_experiment.method.method_steps:
            msg = "No method steps found for experiment {}: unable to align " \
                  "the AKTA and method information."
            msg = msg.format(self.experiment_name)
            logger.exception(msg)
            raise ValueError(msg)

        try:
            return self.target_experiment.method.load.name
        except StepLookupError:
            msg = "No load step found in the method for experiment {}."
            logger.warning(msg.format(self.experiment_name))
            return self.target_experiment.method.method_steps[0].name


def build_col_name_editor(all_col_names):
    """ Build a table editor to edit a list of NamePatterns.
    """
    editor = TableEditor(
        columns=[
            ObjectColumn(name='dataset_type', style='readonly'),
            ObjectColumn(name='matching_col_name', label='Column name',
                         editor=EnumEditor(values=[""]+all_col_names))
        ],
        editable=True,
        sortable=False,
        deletable=False,
    )
    return editor
