"""Base ExcelReader class - provides API for the data contained in the Excel
input file (for a given study) for all versions.
"""

import logging
from os.path import basename, isfile
import json
import pyexcel
import pyexcel.ext.xls  # import needed to handle xls file
import pyexcel.ext.xlsx  # import needed to handle xlsx file

from traits.api import Any, Dict, HasStrictTraits, Instance, List, Property, \
    Str

from app_common.std_lib.sys_utils import format_tb

from kromatography.model.data_source import DataSource

logger = logging.getLogger(__name__)

MISSING_VALUES = ['', 'NA', 'N/A']

# Excel input version, as a tuple of python indices
INPUT_VERSION_CELL_COORDINATES = (0, 4)

# Version of the reader that is currently recommended
CURRENT_INPUT_VERSION = 2

# Column index where data content starts
SECTION_HEADER_COL = 0
SUBSECTION_HEADER_COL = SECTION_HEADER_COL + 1
CONTENT_NAME_COL = 1
CONTENT_UNIT_COL = 2
FIRST_CONTENT_COL = 3

# Section names:
GENERAL_SECTION_NAME = 'General Study Information'
SYSTEM_SECTION_NAME = 'Chromatography System Information'
COLUMN_SECTION_NAME = 'Chromatography Column Information'
LOAD_SECTION_NAME = 'Load Information'
BUFFER_SECTION_NAME = 'Buffer Information'
METHOD_SECTION_NAME = 'Method Information'
COLL_CRIT_SECTION_NAME = "Collection criteria information"
PERFORMANCE_SECTION_NAME = 'Performance Parameters'
FRACTION_SECTION_NAME = 'Fraction Data'
CONTINIUOUS_SECTION_NAME = 'Continuous Data'


class ExcelReadError(ValueError):
    pass


class StepNotFoundError(ValueError):
    pass


class BaseExcelReader(HasStrictTraits):
    """ Base reader for the Reveal input Excel file to build an Experimental
    study.
    """

    # FIXME reader currently allows for sections of excel to appear
    # out of order and with a variable number of white space lines in
    # between BUT assumes the rows in each section are fixed

    #: path to excel file
    file_path = Str

    #: Datasource to validate Excel entries against
    data_source = Instance(DataSource)

    #: Product data, loaded from Datasource
    product = Property(Dict)

    #: List of labels to search a value for in each section.
    section_labels = Dict

    #: List of labels to search a value for in each section
    general_section_name = Str(GENERAL_SECTION_NAME)

    general_section_labels = List

    system_section_name = Str(SYSTEM_SECTION_NAME)

    system_section_labels = List

    column_section_name = Str(COLUMN_SECTION_NAME)

    column_section_labels = List

    buffer_section_name = Str(BUFFER_SECTION_NAME)

    buffer_labels = List

    load_section_name = Str(LOAD_SECTION_NAME)

    load_labels = List

    method_section_name = Str(METHOD_SECTION_NAME)

    method_labels = List

    performance_section_name = Str(PERFORMANCE_SECTION_NAME)

    coll_crit_section_name = Str(COLL_CRIT_SECTION_NAME)

    fraction_section_name = Str(FRACTION_SECTION_NAME)

    continuous_section_name = Str(CONTINIUOUS_SECTION_NAME)

    #: A local cache for excel sheets.
    _sheets = Dict(Str, Any)

    def __init__(self, file_path=None, **traits):
        if not isfile(file_path):
            msg = 'Invalid file path {!r}'.format(file_path)
            logger.exception(msg + format_tb())
            raise ValueError(msg)

        super(BaseExcelReader, self).__init__(file_path=file_path, **traits)

    # Reader Public interface --------------------------------------------

    def get_all_data(self):
        input_filename = basename(self.file_path)

        all_data = {}

        sections = ['general_data', 'system_data', 'column_data', 'load_data',
                    'buffer_prep_data', 'experiment_data']
        for data_type in sections:
            try:
                method = getattr(self, "get_" + data_type)
                all_data[data_type] = method()
            except Exception as e:
                msg = "Failed to parse the {} part of the input file " \
                      "{}. Error was {}."
                data_type_str = data_type.replace("_", " ")
                msg = msg.format(data_type_str, input_filename, e)
                logger.exception(msg + format_tb())
                raise ExcelReadError(msg)

        return all_data

    def print_all_data(self):
        """ Pretty prints all the data
        """
        all_data = self.get_all_data()
        print(json.dumps(all_data, indent=4))

    # Section collection methods ----------------------------------------------

    def get_general_data(self):
        """ Returns dictionary of General Experiment Information data
        """
        return self._get_flat_section_data(self.general_section_name)

    def get_system_data(self):
        """ Returns dictionary of Chromatography System Information data
        """
        return self._get_flat_section_data(self.system_section_name)

    def get_column_data(self):
        """ Returns dictionary of Chromatography Column Information data
        """
        return self._get_flat_section_data(self.column_section_name)

    def get_experiment_data(self):
        """ Returns dictionary of runs with key as their name from the excel.

        Includes sections Method Information, Performance Parameters, Fraction
        Data, and Continuous data from excel file.
        """
        sheet = self._get_sheet()

        # find start of experiment data (where method section starts)
        section_start = self._get_section_index(sheet,
                                                self.method_section_name)

        # determine number of columns in section
        num_columns = self._get_section_last_col(sheet, section_start)

        # read buffers in one by one and store in dict by name
        experiment_data = {}

        # each column is a separate run
        for col in range(3, num_columns):
            run_data = {}

            method_section_start = self._get_section_index(
                sheet, self.method_section_name
            )
            run_data['method_data'] = self._get_method_data(
                sheet, method_section_start, col
            )

            perf_param_section_start = self._get_section_index(
                sheet, self.performance_section_name
            )
            run_data['performance_parameter_data'] = \
                self._get_performance_parameter_data(
                    sheet, perf_param_section_start, col
            )

            fraction_section_start = self._get_section_index(
                sheet, self.fraction_section_name
            )
            run_data['fraction_data'] = self._get_fraction_data(
                sheet, fraction_section_start, col
            )

            continuous_section_start = self._get_section_index(
                sheet, self.continuous_section_name
            )
            run_data['continuous_data'] = self._get_continuous_data(
                    sheet, continuous_section_start, col
            )

            exp_name = run_data['method_data']['experiment_name']
            experiment_data[exp_name] = run_data

        return experiment_data

    def _get_next_step(self, sheet, step_ind, col_ind):
        """ Returns data for "Step i". Starts looking at (row,col) ==
        (0, 1) downward, and collects everything until it
        hits "Step (i+1)" or a blank cell. Returns ValueError if no
        "Step i" exists
        """
        col1_names = map(unicode.strip, map(unicode, sheet.column[1]))
        try:
            row_start = col1_names.index(
                'Step {} Name'.format(str(step_ind))
            )
        except ValueError:
            msg = "Not able to find the first row for 'Step {}'."
            msg = msg.format(str(step_ind))
            raise StepNotFoundError(msg)

        step_name = sheet[row_start, col_ind]
        step = {'name': step_name, 'solution_names': []}
        j = row_start
        while True:
            cell_name = sheet[j, CONTENT_NAME_COL].lower().strip()
            cell_value = sheet[j, col_ind]
            valid_solution_name = (cell_name in ['buffer name', 'load name'] and  # noqa
                                   cell_value not in MISSING_VALUES)
            if valid_solution_name:
                step['solution_names'].append(cell_value)
            elif cell_name == 'step type':
                step['step_type'] = cell_value
            elif cell_name == 'step volume':
                step['volume'] = float(cell_value)
            elif cell_name == 'step flow rate':
                step['flow_rate'] = float(cell_value)
            elif cell_name in ['step {} name'.format(str(step_ind + 1)), '']:
                return step
            else:
                pass
            j += 1

    def _get_fraction_data(self, sheet, section_start, col):
        """ Returns list of fraction data or None if not there.

        All component assays that are not present in the Excel tab will be
        given a fraction of 0%.
        """
        product_component_assays = self.product.product_component_assays
        fracs_analyzed = sheet[section_start + 1, col].strip()
        if fracs_analyzed.lower() == 'no':
            return None

        frac_sheet_name = sheet[section_start + 2, col]
        fraction_data = []
        frac_sheet = self._get_sheet(sheet_name=frac_sheet_name)
        fractions_start = self._get_section_index(frac_sheet,
                                                  'Fraction Number')

        # Check if product component assays given, and if names match
        header_row = frac_sheet.row[fractions_start]
        if '' in header_row:
            header_row_len = header_row.index('')
        else:
            header_row_len = len(header_row)
        header_row = header_row[:header_row_len]
        has_product_assays = header_row_len >= 4
        if has_product_assays:
            # Make sure Excel assay list match product specs
            num_prod_assays = len(product_component_assays)
            excel_assay_list = header_row[3:3 + num_prod_assays]
            excel_assays = set(excel_assay_list)
            prod_assays = set(product_component_assays)
            if excel_assays != product_component_assays:
                extra_assays = excel_assays - prod_assays
                missing_assays = prod_assays - excel_assays
                msg = ("Assays does not match assays in product in fraction "
                       "data tab {}.".format(frac_sheet_name))
                if extra_assays:
                    msg += (" Excel contains the following extra assays not "
                            "listed in the product: {}".format(extra_assays))
                    logger.exception(msg)
                    raise LookupError(msg)

                if missing_assays:
                    msg += (" Excel file is missing {}. We will assume that "
                            "the have no contributions to fraction "
                            "data.".format(missing_assays))
                    logger.info(msg)

        # Build fraction_data list
        missing_data_contributions = {assay: 0. for assay in missing_assays}
        fractions_end = len(frac_sheet.column[0])
        for i in range(fractions_start + 2, fractions_end):
            time = frac_sheet[i, 1]
            if isinstance(time, str) and time.strip() == "":
                continue
            fraction = {'time': time,
                        'total_concentration': frac_sheet[i, 2]}
            if has_product_assays:
                fraction['product_component_assay_dict'] = {}
                for j, assay_name in enumerate(excel_assay_list):
                    fraction['product_component_assay_dict'][assay_name] = \
                            float(frac_sheet[i, 3+j])
                # Missing assays will contribute for 0% at each fraction time
                fraction['product_component_assay_dict'].update(
                    missing_data_contributions
                )

            fraction_data.append(fraction)

        return fraction_data

    def _get_continuous_data(self, sheet, section_start, col):
        """Returns string representing relative path to continuous data
        if there
        """
        if sheet[section_start + 1, col] in MISSING_VALUES:
            continuous_data = None
        else:
            continuous_data = sheet[section_start + 1, col]
        return continuous_data

    # General Reader Private interface ----------------------------------------

    def _get_sheet(self, sheet_name=None):
        """ Return a sheet from the managed excel file.

        Uses a cached lookup to avoid loading overhead from pyexcel lib.
        """
        if sheet_name is None:
            cached_name = 'default'
        else:
            cached_name = sheet_name

        cache = self._sheets
        # look up the sheet in the cache, and load the sheet into the cache
        # if missing
        if cached_name not in cache:
            cache[cached_name] = pyexcel.get_sheet(file_name=self.file_path,
                                                   sheet_name=sheet_name)
        return cache[cached_name]

    def _get_flat_section_data(self, section_name,
                               content_col=FIRST_CONTENT_COL, sheet_name=None):
        """ Collect section data from continuous cells into a dict.

        Parameters
        ----------
        section_name : str
            Name of the section to read

        content_col : int [OPTIONAL]
            Column index the section has its data. Defaults to
            FIRST_CONTENT_COL.

        sheet_name : str or None [OPTIONAL]
            Name of the sheet/tab to load data from. Leave to None to load the
            first sheet.
        """
        sheet = self._get_sheet(sheet_name)
        section_start = self._get_section_index(sheet, section_name) + 1
        label_info_list = self.section_labels[section_name]

        data = self._get_continuous_cells(label_info_list, section_start,
                                          content_col, sheet)

        return data

    def _get_continuous_cells(self, label_info_list, section_start,
                              content_col, sheet):
        """ Extract sequential data into a dict labeled with specific labels.

        Parameters
        ----------
        label_info_list : list
            List of strings or 2-tuple with a str and a callable to label and
            optionally transform the value read.

        section_start : int
            Index of first row in the sheet to be read.

        content_col : int
            Index of column to read.

        sheet : pyexcel.Sheet
            Sheet to read data from.
        """
        data = {}
        for i, label_info in enumerate(label_info_list):
            if isinstance(label_info, tuple):
                label, transform = label_info
            else:
                label = label_info
                transform = str

            data[label] = transform(sheet[section_start + i, content_col])

        return data

    def _get_section_index(self, sheet, section_header):
        """Returns row index of sheet where section_header is found,
        if contained in the first column, else ValueError. Not that the value
        is the (Excel row number - 1) since Excel starts counting at 1.
        """
        headers_found = []
        length = len(sheet.array)

        for i in range(length):
            entry = sheet[i, SECTION_HEADER_COL].strip()
            if entry:
                headers_found.append(entry)
                if entry.startswith(section_header):
                    return i

        msg = "Can't find expected header {}. Headers found: {}."
        msg = msg.format(section_header, headers_found)
        logger.exception(msg)
        raise ValueError(msg)

    def _get_subsection_index(self, sheet, subsection_header,
                              search_from=0, search_until=None):
        """ Returns row index of sheet where subsection_header is found,
        optionally within a certain range of rows in the sheet.

        Note that case is ignored.

        Raises
        ------
        ValueError if the subsection header is not found. Note that the value
        is the (Excel row number - 1) since Excel starts counting at 1.
        """
        if search_until is None:
            search_until = len(sheet.array)

        for i in range(search_from, search_until):
            entry = sheet[i, SUBSECTION_HEADER_COL].strip()
            if entry.lower() == subsection_header.lower():
                return i

        msg = "Can't find expected subsection header {}."
        msg = msg.format(SUBSECTION_HEADER_COL)
        logger.exception(msg)
        raise ValueError(msg)

    def _get_section_last_col(self, sheet, section_start):
        """Returns the number of columns in given section, starting from
        fourth column. If not valid section, raises ValueError
        """
        i = FIRST_CONTENT_COL
        while sheet[section_start + 1, i] not in ['', None]:
            i += 1
        return i

    # HasTraits initializations -----------------------------------------------

    def _data_source_default(self):
        from kromatography.utils.app_utils import load_default_user_datasource
        return load_default_user_datasource()[0]

    def _section_labels_default(self):
        return {self.general_section_name: self.general_section_labels,
                self.system_section_name: self.system_section_labels,
                self.column_section_name: self.column_section_labels}

    # HasTraits property getters/setters --------------------------------------

    def _get_product(self):
        """Sets the product for the ExcelReader to be the value from the
        SimpleDataSource that corresponds to product_name given in the
        Excel file.
        """
        sheet = self._get_sheet()

        # find General Experiment Information section
        section_start = self._get_section_index(
            sheet, self.general_section_name
        )

        product_name = sheet[section_start + 1, 3]
        try:
            product = self.data_source.get_objects_by_type(
                'products', filter_by={'name': product_name}
            )[0]
        except IndexError:
            known_products = self.data_source.get_object_names_by_type(
                'products'
            )
            msg = ("Given product name {} not found in datasource. Known "
                   "products are: {}".format(product_name, known_products))
            logger.exception(msg)
            raise ValueError(msg)

        return product
