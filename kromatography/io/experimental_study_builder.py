""" This class builds a Study model from user inputs (Excel file) and a catalog
of standard/pre-configured data.
"""

# NOTES
# -----
# The current version (first iteration) is simply to read in the data and
# configure all the data models needed to run a simulation. Very little effort
# has been spent into creating clean abstractions. However the various tasks
# are identified and modularized.
#
# The next iteration should focus on creating the abstractions needed for
# a clean implementation.
#
#
# Some issues
# ===========
#
# * The keys for the various data attributes are hardcoded.
#
#     We need to define a standardized set of keys and define mapping between
#     these sets. The mapping would be different for user-inputs, stored data,
#     simulation data.
#
# * The units need to be handled more robustly.
#
#     Again, it would be good to define allowed units and enforce them.
#     This requires being able to parse the units in the inputs without
#     ambiguity.
#
# * Need an API for querying from the catalog (user-local or remote DB)
#
# * Sometimes, the user-inputs do not map directly to a data input but requires
# further processing.
#
#     For now, this is handled on a case-by-case basis and is pretty much
#     hardcoded.
#
# * Perhaps standardize the layout for the output from ExcelReader
#
# * Need a validator/corrector for the excel file that uses the catalog data.
#
#     This is to detect/correct errors in key names (e.g. assay names used for
#     a product etc.).

from collections import defaultdict
import numpy as np
from os.path import basename, dirname, join
import logging

from scimath.units.unit_scalar import UnitScalar, UnitArray
from traits.api import Bool, Dict, HasStrictTraits, Instance, Str

from app_common.std_lib.sys_utils import format_tb

from kromatography.model.buffer_prep import BufferPrep
from kromatography.model.x_y_data import XYData
from kromatography.model.chromatography_results import ExperimentResults
from kromatography.model.performance_data import PerformanceData
from kromatography.model.collection_criteria import CollectionCriteria
from kromatography.model.data_source import DataSource
from kromatography.model.api import Column, Experiment, Method, MethodStep, \
    Product, Solution, SolutionWithProduct, System
from kromatography.model.experimental_study import ExperimentalStudy
import kromatography.utils.chromatography_units as chr_units
from kromatography.utils.units_utils import unitted_list_to_array
from kromatography.utils.string_definitions import FRACTION_TOTAL_DATA_KEY, \
    STRIP_COMP_NAME

from .experiment_builder_utils import continuous_data_from_akta, \
    shift_fraction_data_by_holdup_vol
from .excel_reader import BaseExcelReader, ExcelReadError, MISSING_VALUES
from .excel_reader_selector import ExcelInputReaderSelector


logger = logging.getLogger(__name__)

# FIXME: This mapping is ad-hoc. We need a cleaner way to map keys and units
# between the different translations (inputs -> model, experiment -> CADET)
# A map from a model type-id to the relevant key from the excel file.
DATA_ATTRIBUTE_EXCEL_KEY_MAP = {
    'resin': {
        'resin_lot_id': 'lot_id',
        'resin_type': 'name',
        'resin_ligand_density': 'ligand_density',
        'resin_avg_bead_diameter': 'average_bead_diameter',
    },
    'column': {
        'packed_column_lot_id': 'column_lot_id',
        'column_packed_bed_height': 'bed_height_actual',
        'HETP': 'hetp',
        'asymmetry': 'hetp_asymmetry',
        'compression_factor': 'compress_factor'
    },
    'system': {
        'system_name': 'name',
        'absorbance_detector_pathlength': 'abs_path_length',
        'system_id': 'system_number',
        'holdup_volume': 'holdup_volume',
    },
}


# FIXME: ideally this should be read/parsed from the excel file.
# For now, just assuming the units for the data to be the default units
# as the defaults were chosen based on this data.
# FIXME: Also, keys were created in an ad-hoc fashion due to time pressure.
# Again, this mapping and the data-key -> attribute mapping above need to
# abstracted in a cleaner fashion.
DEFAULT_UNITS_MAP = {
    'resin_ligand_density': chr_units.milli_molar,
    'resin_avg_bead_diameter': 'um',
    'column_packed_bed_height': 'cm',
    'asymmetry': 'cm',
    'HETP': 'cm',
    'column_diameter': 'cm',
    'compression_factor': chr_units.dimensionless.dimensionless,
    # Buffer class
    'buffer_density': chr_units.gram_per_liter,
    'buffer_concentration': chr_units.molar,
    'buffer_volume': chr_units.milliliter,
    'buffer_conductivity': chr_units.mS_per_cm,
    'buffer_temperature': 'celsius',
    'buffer_pH': 'dimensionless',
    'chemical_stock_concentrations': 'g',
    'chemical_density': chr_units.gram_per_milliliter,
    # Chemical class
    'chemical_solid_amount': 'g',
    'chemical_liquid_amount': chr_units.milliliter,
    'chemical_liquid_density': chr_units.milliliter,
    # Load class
    'load_density': chr_units.gram_per_liter,
    'load_product_concentration': chr_units.gram_per_liter,
    'load_volume': chr_units.milliliter,
    'load_conductivity': chr_units.mS_per_cm,
    'load_temperature': 'celsius',
    'load_pH': 'dimensionless',
    'load_product_assay_values': chr_units.assay_unit,
    'load_impurity_assay_values': chr_units.assay_unit,
    'load_chemical_concentrations': chr_units.milli_molar,
    # System class
    'absorbance_detector_pathlength': 'cm',
    'holdup_volume': chr_units.milliliter,
    # MethodStep class
    'method_flow_rate': chr_units.cm_per_hr,
    'method_volume': chr_units.column_volumes,
    # Fraction Data
    'fraction_product_concentration': chr_units.gram_per_liter
}


class ExperimentalStudyBuilder(HasStrictTraits):
    """ Builds an ExperimentalStudy from an Excel file and a Datasource.
    """
    # FIXME: Take all the _build_** methods and make them factory functions.

    #: Path to input file to build the study from
    input_file = Str

    #: The object providing access to known/stored Chromatography data.
    data_source = Instance(DataSource)

    #: The object providing access to known/stored Chromatography data.
    excel_reader = Instance(BaseExcelReader)

    #: The raw data loaded from the Excel file
    excel_data = Dict

    #: The product studied in the experimental study
    product = Instance(Product)

    #: The system found in the experimental study
    system = Instance(System)

    #: The column found in the experimental study
    column = Instance(Column)

    #: All buffers found in the experimental study
    buffers = Dict(Str, Instance(Solution))

    #: All loads found in the experimental study
    loads = Dict(Str, Instance(Solution))

    #: All solutions found in the experimental study
    solutions = Dict(Str, Instance(Solution))

    #: Dict of experiments loaded
    experiments = Dict(Str, Experiment)

    #: Output study generated
    study = Instance(ExperimentalStudy)

    #: Prompt the user to control settings AKTA files must be parsed with?
    allow_akta_gui = Bool(True)

    def read_excel_data(self):
        selector = ExcelInputReaderSelector(filepath=self.input_file)
        self.excel_reader = selector.build_excel_reader(
            data_source=self.data_source
        )
        self.excel_data = self.excel_reader.get_all_data()

    def build_study(self):
        """ Returns a complete Study model from all the ExcelReader data.

        Returns
        -------
        ExperimentalStudy
            If the load is successful, the returned value is the experimental
            study built from Excel file components.

        Raises
        ------
        ExcelReadError
            Raised when any part of the study fails to load.
        """
        input_file = self.input_file

        if not self.excel_data:
            self.read_excel_data()

        sections = ['product', 'column', 'system', 'buffers', 'loads']
        for attr_name in sections:
            try:
                method = getattr(self, "_build_" + attr_name)
                value = method()
                setattr(self, attr_name, value)
            except Exception as e:
                msg = "Failed to load the {} data of the input file " \
                      "{}. Error was {}."
                msg = msg.format(attr_name, input_file, e)
                logger.exception(msg + format_tb())
                raise ExcelReadError(msg)

        # initialize container for all solutions
        self.solutions = {}
        self.solutions.update(self.buffers)
        self.solutions.update(self.loads)

        try:
            self.experiments = self._build_experiments()
        except Exception as e:
            msg = "Failed to load the experiments data of the input file " \
                  "{}. Error was {}."
            msg = msg.format(input_file, e)
            logger.exception(msg + format_tb())
            raise ExcelReadError(msg)

        try:
            self.study = self._build_study()
        except Exception as e:
            msg = "Failed to finalize all the components of the input file " \
                  "{} into a study. Error was {}."
            msg = msg.format(input_file, e)
            logger.exception(msg + format_tb())
            raise ExcelReadError(msg)

        return self.study

    # -------------------------------------------------------------------------
    # Private methods
    # Pattern for all build_**: Load data from Excel, convert name into
    # datasource entry, update data from Excel data if something has been
    # modified.
    # -------------------------------------------------------------------------

    def _build_product(self):
        general_data = self.excel_data['general_data']
        product_name = general_data['product_name']
        product = self.data_source.get_object_of_type('products', product_name)
        return product

    def _build_column(self):
        """ Build a column object from the column data in study Excel file.

        This requires to build the resin, then the column system, and then the
        column itself.
        """
        column_data = self.excel_data['column_data']
        ds = self.data_source

        # Create resin --------------------------------------------------------

        resin_type_name = column_data['resin_type']
        # FIXME: lookup should be done based on resin name and lot id instead
        # of just name.
        resin = ds.get_object_of_type('resin_types', resin_type_name)

        # Create ColumnType ---------------------------------------------------

        # get the column model for the given system number
        column_type_name = column_data['column_model']
        column_type = ds.get_object_of_type('column_models', column_type_name)

        # Create Column -------------------------------------------------------

        column_user_data = self._get_model_data_from_excel_data(
            'column', column_data
        )
        # FIXME: should this be enforced on the model ?
        column_user_data['name'] = column_user_data['column_lot_id']
        column = Column(resin=resin, column_type=column_type,
                        **column_user_data)
        return column

    def _build_system(self):
        ds = self.data_source
        # get excel data for the section related to System data.
        system_data = self.excel_data['system_data']
        # initialize SystemType by looking up the type id from the catalog.
        system_type_key = system_data.pop('system_type')
        system_type = ds.get_object_of_type('system_types', system_type_key)

        # The Excel data does not directly provide the holdup_volume.
        # The entries need to be summed to get the total holdup_volume.
        hold_up_vols = [val for key, val in system_data.items()
                        if key.startswith('holdup_')]
        system_data['holdup_volume'] = np.sum(hold_up_vols)

        # translate the excel data to unitted model traits
        system_data = self._get_model_data_from_excel_data(
            'system', system_data
        )

        # initialize a System object.
        system = System(system_type=system_type, **system_data)
        return system

    def _build_buffers(self):
        """ Build a Buffer instance from buffer data in the study Excel file.

        1. Create each chemical present in the buffer and collect its density,
        and concentration.
        2. Group all that information inside a new Buffer object.
        """
        buffers = {}
        for name, solution_data in self.excel_data['buffer_prep_data'].items():
            chemicals = []
            chemical_amounts = []
            chemical_stock_concentrations = []
            chemical_data = solution_data['chemical_dict']
            chemical_objects = self._build_chemicals(chemical_data)
            for chem_name, chem_data in chemical_data.items():
                chemical = chemical_objects[chem_name]
                chemicals.append(chemical)

                # NOTE: these are UnitArrays
                chemical_stock_concentrations.append(
                    chem_data['concentration']
                )

                # NOTE: this is List(UnitScalar) as amount can have different
                # units depending on the state of the chemical.
                chem_state = chemical.state.lower()
                chemical_amounts.append(self._get_unitted_value(
                    'chemical_{}_{}'.format(chem_state, 'amount'),
                    chem_data['amount']
                ))

            # NOTE: create the UnitArrays
            chemical_stock_concentrations = self._get_unitted_value(
                'chemical_{}'.format('stock_concentrations'),
                chemical_stock_concentrations
            )

            traits = {}
            for key in ['volume', 'pH', 'conductivity', 'temperature',
                        'source', 'name', 'description', 'density']:
                traits[key] = self._get_unitted_value(
                    'buffer_' + key, solution_data[key]
                )
            # BUG: ExcelReader (returned as an INT)
            traits['lot_id'] = str(solution_data['lot_id'])

            buffer_prep = BufferPrep(
                chemicals=chemicals,
                chemical_amounts=chemical_amounts,
                chemical_stock_concentrations=chemical_stock_concentrations,
                **traits
            )

            buffers[name] = buffer_prep.build_buffer()

        return buffers

    def _build_loads(self):
        load_solutions = {}
        ds = self.data_source

        for name, load_data in self.excel_data['load_data'].items():
            # pop data entries that need to be processed for initializing
            # some of the model traits.
            imp_assays = load_data.pop('impurity_assay_dict')
            prod_comp_assays = load_data.pop('product_component_assay_dict')
            chem_comp_concs = load_data.pop(
                'chemical_component_concentration_dict'
            )

            traits = {}
            for key, val in load_data.items():
                traits[key] = self._get_unitted_value('load_' + key, val)

            # use the product for the current study to get the component
            # and impurity assay information.
            product = self.product

            product_assay_values = []
            for assay_name in product.product_component_assays:
                # Strip product component cannot be present in load solutions
                if assay_name == STRIP_COMP_NAME:
                    assay_conc = 0.0
                else:
                    assay_conc = prod_comp_assays[assay_name]

                product_assay_values.append(assay_conc)

            product_assay_values = self._get_unitted_value(
                'load_product_assay_values', product_assay_values
            )

            # initialize impurity assays
            imp_assay_values = []
            for assay_name in product.impurity_assays:
                imp_assay_values.append(imp_assays[assay_name])

            imp_assay_values = self._get_unitted_value(
                'load_impurity_assay_values',
                imp_assay_values
            )

            # initialize chemical components
            chemical_components = []
            chem_comp_concentrations = []
            for comp_name, comp_conc in chem_comp_concs.items():
                comp = ds.get_object_of_type('components', comp_name)
                chemical_components.append(comp)
                chem_comp_concentrations.append(comp_conc)

            chem_comp_concentrations = self._get_unitted_value(
                'load_chemical_concentrations', chem_comp_concentrations
            )

            load_solution = SolutionWithProduct(
                product=product,
                product_component_assay_values=product_assay_values,
                impurity_assay_values=imp_assay_values,
                chemical_components=chemical_components,
                chemical_component_concentrations=chem_comp_concentrations,
                **traits
            )
            load_solutions[name] = load_solution

        return load_solutions

    def _build_chemicals(self, chemical_data):
        """ Convert a dict of chemical data into a dict of Chemical instances.
        """
        # load all chemical and component information
        chemicals = {}
        ds = self.data_source

        # initialize the Chemical objects for the keys in `chemical_data`.
        for name, data in chemical_data.items():
            chemical = ds.get_object_of_type('chemicals', name)

            # FIXME: duplicate info or needs to be updated ?
            if chemical.state != data['state']:
                msg = ('The `state` of the chemical specified in the Excel '
                       'input ({!r}) is different from what is specified in '
                       'the datasource {} ({!r}). The state specified in the '
                       'Excel data is ignored.')
                msg = msg.format(data['state'], ds.name, chemical.state)
                logger.warning(msg)

            chemicals[name] = chemical

        return chemicals

    def _build_experiments(self):
        """ Build experiments from all components, including continuous data.

        Note: To make the continuous data comparable to simulations, its time
        axis is shifted to remove all hold up volume, to make it as if the
        measurements (UV, conductivity, ...) are made right outside the column.
        """
        experiments = {}
        for name, experiment in self.excel_data['experiment_data'].items():
            msg = "Loading experiment {}".format(name)
            logger.debug(msg)

            method_data = experiment['method_data']

            if not method_data['collection_criteria']:
                collection_criteria = None
            else:
                collection_criteria = CollectionCriteria(
                    name='collection_{}'.format(name),
                    **method_data['collection_criteria']
                )

            collection_step_number = method_data['collection_step_number']
            method_steps = []
            for method_step in method_data['steps']:
                # The excel data has the names of the solutions used in
                # a method step. So lookup the names from the list of
                # solutions (both loads and buffers) in this study.
                solution_names = method_step.pop('solution_names')
                solutions = [self.solutions[key] for key in solution_names
                             if key not in MISSING_VALUES]

                # create unitted data for initializing model.
                unitted_step_data = {}
                for key, val in method_step.items():
                    # FIXME: special-casing can be removed once we parse units
                    # properly.
                    # NOTE: The volume for LOAD step is specified in terms
                    # of g/(L of resin). Must divide by product concentration
                    # in the load solution to get the volume in CV like the
                    # other steps:
                    if method_step['step_type'] == 'Load' and key == 'volume':
                        prod_conc = solutions[0].product_concentration
                        val /= prod_conc[()]

                    unitted_step_data[key] = self._get_unitted_value(
                        'method_' + key, val
                    )
                # FIXME: We need a way to assign method_steps.step_type
                # initialize the MethodStep
                step = MethodStep(solutions=solutions, **unitted_step_data)
                method_steps.append(step)

            # Initialize the Method for the experiment
            run_type = method_data['run_type']
            method = Method(
                method_steps=method_steps,
                collection_step_number=collection_step_number,
                collection_criteria=collection_criteria,
                run_type=run_type,
                name=name,
            )
            # Build the experiment outputs (cont data from AKTA and fraction
            # and performance parameters from excel
            experiment = Experiment(
                name=name, system=self.system,
                column=self.column, method=method
            )

            try:
                output = self._build_experiment_output(name, experiment)
            except Exception as e:
                msg = ("Failed to load the experiment output for {}. Error was"
                       " {}. Traceback was\n{}".format(name, e, format_tb()))
                logger.error(msg)
                output = None

            # Finalize the experiment
            experiment.output = output
            experiments[name] = experiment
        return experiments

    def _build_experiment_output(self, name, target_experiment=None):
        """ Build the experiment results for a given experiment name.

        Parameters
        ----------
        name : str
            Name of the experiment to extract the results from.

        target_experiment : Experiment
            Experiment implemented to compare output data to method data.

        Returns
        -------
        ExperimentResults
            Result object containing fraction data, and all continuous data. If
            no data is specified, the returned Result object contains empty
            dictionaries for the missing data (continuous and/or fraction).
        """
        expt_data = self.excel_data['experiment_data'][name]

        # initialize the continuous data from the AKTA files.
        akta_fname = expt_data['continuous_data']
        if akta_fname is not None:
            # Assumes that the akta file path is relative to the Excel file:
            dir_name = dirname(self.excel_reader.file_path)
            akta_fname = join(dir_name, basename(akta_fname))
            continuous_data, settings = self._build_continuous_data(
                akta_fname, target_experiment
            )
        else:
            zero_min = UnitScalar(0., units="minute")
            continuous_data = {}
            settings = {"time_of_origin": zero_min,
                        "holdup_volume": zero_min}

        fraction_data = self._build_fraction_data(
            expt_data['fraction_data'],
            time_of_origin=settings["time_of_origin"],
            target_experiment=target_experiment
        )

        # Initialize the experiment performance results
        raw_perf_data = expt_data['performance_parameter_data']
        if raw_perf_data:
            performance_data = self._build_performance_data(raw_perf_data,
                                                            name)
        else:
            performance_data = None

        results = ExperimentResults(
            name=name,
            fraction_data=fraction_data,
            continuous_data=continuous_data,
            performance_data=performance_data,
            import_settings=settings
        )
        return results

    def _build_fraction_data(self, fraction_data, time_of_origin=None,
                             target_experiment=None):
        """ Convert fraction data from Excel fraction sheet into a fraction
        data dictionary to describe ChromatographyResults.

        Parameters
        ----------
        fraction_data : dict
            Data loaded from Excel.

        time_of_origin : UnitScalar [OPTIONAL]
            User specified custom time shift to apply to the data, if the
            experimental output wasn't recorded starting at the desired start.
        """
        if fraction_data is None:
            return {}

        if time_of_origin is None:
            time_of_origin = UnitScalar(0., units="minute")

        # Faction times at which product is sampled and analyzed:
        frac_time = []
        # Component concentration at each fraction time:
        frac_comp_conc = defaultdict(list)
        # Total concentration of product, corrected from extinction at each
        # fraction time:
        frac_prod_absorbances = []

        product = self.product
        for fraction in fraction_data:
            prod_comp_assays = fraction.pop('product_component_assay_dict')
            # FIXME: read units instead of guessing
            total_concentration = self._get_unitted_value(
                'fraction_product_concentration',
                fraction['total_concentration']
            )
            conc_units = total_concentration.units

            # To compute the product concentrations in the fraction,
            # we must first compute the concentration of each product component
            # then multiply each by their respective extinction coefficient
            # finally sum these values together

            # FIXME: Fraction component concentrations shoud be calculated in
            #        SolutionWithProduct.  This is probably unnecessary --
            #        Look into later.
            namespace = {}
            namespace.update(prod_comp_assays)
            namespace["product_concentration"] = float(total_concentration)
            prod_comp_conc = [eval(expression, namespace) for expression
                              in product.product_component_concentration_exps]

            frac_component_concs = UnitArray(prod_comp_conc, units=conc_units)
            # Total concentration, corrected by the components' extinction coef
            ext_coefs = [comp.extinction_coefficient
                         for comp in product.product_components]
            ext_coef_array = unitted_list_to_array(ext_coefs)
            # This converts the component concentration to absorption
            frac_component_absorb = frac_component_concs * ext_coef_array
            tot_prod_absorbance = sum(frac_component_absorb)
            frac_prod_absorbances.append(tot_prod_absorbance)

            frac_time.append(fraction['time'])
            for ii, comp_name in enumerate(product.product_component_names):
                frac_comp_conc[comp_name].append(frac_component_absorb[ii])

        # Apply the user defined origin shift:
        # Warning: this leads to all fraction XYData sharing the same array!
        frac_time = np.array(frac_time, dtype='float64') - time_of_origin[()]
        frac_prod_absorbances = np.array(frac_prod_absorbances,
                                         dtype='float64')

        fraction_outputs = {}
        for key, data in frac_comp_conc.items():
            fraction_outputs[key] = XYData(
                name=key,
                x_data=frac_time,
                # FIXME: read units instead of guessing
                x_metadata={"time_of_origin": time_of_origin,
                            "units": "min"},
                y_data=data,
                # FIXME: read units instead of guessing
                y_metadata={"Description": "Absorbances for product "
                                           "components {}".format(key),
                            "units": "AU/cm"},
            )

        fraction_outputs[FRACTION_TOTAL_DATA_KEY] = XYData(
            name=FRACTION_TOTAL_DATA_KEY,
            x_data=frac_time,
            # FIXME: read units instead of guessing
            x_metadata={"time_of_origin": time_of_origin,
                        "units": "min"},
            y_data=frac_prod_absorbances,
            # FIXME: read units instead of guessing
            y_metadata={"Description": "Sum of absorbances per unit path "
                                       "length for all product components.",
                        "units": "AU/cm"},
        )

        shift_fraction_data_by_holdup_vol(fraction_outputs, target_experiment)
        return fraction_outputs

    def _build_continuous_data(self, akta_fname, target_experiment=None):
        """ Load all timeseries from AKTA file. These files typically contain a
        time_** and a ** column. They are stored together in a XYData object.

        Parameters
        ----------
        akta_fname : str
            Filename for AKTA file.

        target_experiment : Experiment
            Experimental method implemented to compare output data to method
            data.

        Returns
        -------
        continuous_data : dict
            Dictionary of XYData with all timeseries contained.

        akta_settings : dict
            Settings to read the AKTA file. Contains the time shift if any, and
            the regex used to select file columns for each dataset types.
        """
        from kromatography.ui.akta_file_setting_selector import \
            AKTAFileSettingSelector

        import_settings = {"akta_fname": akta_fname,
                           "time_of_origin": UnitScalar(0., units="min")}

        settings_selector = AKTAFileSettingSelector(
            akta_filepath=akta_fname, target_experiment=target_experiment
        )
        if self.allow_akta_gui:
            ui = settings_selector.edit_traits(kind="livemodal")
            settings_selected = ui.result
            if settings_selected:
                # Optionally modify some parameters of the experiment method to
                # reconcile mass balance discrepancies:
                settings_selector.apply_strategy()
        else:
            settings_selected = True

        if settings_selected:
            import_settings["time_of_origin"] = \
                settings_selector.time_of_origin
            import_settings["col_name_patterns"] = \
                settings_selector.col_name_patterns
            continuous_data = continuous_data_from_akta(import_settings,
                                                        target_experiment)
        else:
            msg = "AKTA settings window cancelled: there won't be any " \
                  "continuous data loaded from {}".format(akta_fname)
            logger.warning(msg)
            continuous_data = {}

        return continuous_data, import_settings

    def _build_performance_data(self, perf_data, name):
        """
        FIXME: Needed for the design space plot when we display
        that information when changing the start and stop for taking the pool.
        Probably need a Pool class that knows how to compute that data.
        """

        if perf_data is None:
            return

        product = self.product
        product_concentration = UnitScalar(perf_data["pool_concentration"],
                                           units='g/L')
        pool_volume = UnitScalar(perf_data["pool_volume"], units="CV")
        pH = UnitScalar(perf_data["pH"], units="")
        conductivity = UnitScalar(perf_data["conductivity"], units='mS/cm')
        step_yield = UnitScalar(perf_data["step_yield"], units='%')

        # Build product purity assay data based on product assays
        prod_comp_assays = perf_data.pop('product_component_assay_dict')
        product_assay_values = []
        for assay_name in product.product_component_assays:
            if assay_name == STRIP_COMP_NAME:
                assay_fraction = 0.0
            else:
                assay_fraction = prod_comp_assays[assay_name]

            product_assay_values.append(assay_fraction)

        product_assay_values = UnitArray(product_assay_values, units='g/L')

        # Build impurity assay data based on product impurity assays
        impurity_comp_assays = perf_data.pop('impurity_assay_dict')
        impurity_assay_values = []
        for assay_name in product.impurity_assays:
            impurity_assay_values.append(
                impurity_comp_assays[assay_name])

        impurity_assay_values = UnitArray(impurity_assay_values, units="%")

        pool = SolutionWithProduct(
            name='{}_Pool'.format(name),
            source="Experiment",
            lot_id="unknown",
            solution_type="Pool",
            product=self.product,
            product_concentration=product_concentration,
            product_component_assay_values=product_assay_values,
            impurity_assay_values=impurity_assay_values,
            pH=pH,
            conductivity=conductivity,
        )

        performance_data = PerformanceData(
            name='{}_Performance_Data'.format(name),
            pool_volume=pool_volume,
            pool=pool,
            step_yield=step_yield
        )

        return performance_data

    def _build_study(self):
        """ Put together all components of the Excel file and build the
        ExperimentalStudy instance.
        """
        general_data = self.excel_data['general_data']
        study = ExperimentalStudy(
            name=general_data['study_name'],
            filepath=self.excel_reader.file_path,
            datasource=self.data_source,
            study_id=general_data['study_id'],
            study_type=general_data['study_type'],
            study_purpose=general_data['study_purpose'],
            study_site=general_data['site'],
            experimentalist=str(general_data['experimentalist'])
        )
        study.add_experiments(self.experiments.values())
        return study

    # -------------------------------------------------------------------------
    # private helper methods
    # -------------------------------------------------------------------------
    def _get_model_data_from_excel_data(self, type_id, excel_group_data):
        """ Build model data (with units) from flat Excel data given by Excel
        loader.
        """
        key_map = DATA_ATTRIBUTE_EXCEL_KEY_MAP[type_id]
        return {
            data_key: self._get_unitted_data(excel_key, excel_group_data)
            for excel_key, data_key in key_map.items()
        }

    def _get_unitted_data(self, key, data):
        """ Extract unitted data from Excel.

        Parameters
        ----------
        key : str
            Name of the attribute, as stored in the Excel file.

        data : dict
            Excel data that contains the key.
        """
        value = data[key]
        unit_key = key
        return self._get_unitted_value(unit_key, value)

    def _get_unitted_value(self, unit_key, value):
        """ Convert value from Excel file to a proper instance of Str,
        UnitScalar or UnitArray.

        FIXME: This assumes that value can only be a str, a scalar or a
        list/array.
        """
        if isinstance(value, basestring):
            return value

        # Hack to figure out if the value is a scalar or a list of things.
        try:
            len(value)
        except:
            unit_klass = UnitScalar
        else:
            unit_klass = UnitArray

        data_units = DEFAULT_UNITS_MAP[unit_key]
        value = unit_klass(value, units=data_units)
        return value
