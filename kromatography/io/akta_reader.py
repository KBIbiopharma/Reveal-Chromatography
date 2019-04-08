""" AKTAReader class and all utilities and entry points to read AKTA files.

These files contain the recorded time series of various quantities like UV
(a proxy for concentration), pH, conductivity, .... These timeseries are not
necessarily aligned, and each measurement is therefore stored together with the
times it was recorded at.
"""
from collections import OrderedDict
import logging
import numpy as np
from os.path import basename, isfile, splitext
import pandas as pd
import re

from traits.api import Bool, Dict, Either, Float, HasStrictTraits, Instance, \
    Int, on_trait_change, Property, Str

from app_common.std_lib.sys_utils import format_tb

from kromatography.utils.str_utils import get_dtype, sanitize_str_list, \
    str_list_mostly_float, strip_decode_strings
from kromatography.utils.string_definitions import UV_DATA_KEY

logger = logging.getLogger(__name__)

# NOTE: For now, just use the standard names and search pattern as used in
# the Legacy code.
# FIXME: We could identify the type of file found, and have different search
# pattern for each file type.
DATA_NAME_SEARCH_PATTERNS = {
    UV_DATA_KEY: r'(UV.*280)',
    'conductivity': r'(COND$)',
    'concentration': r'(CONC$)',
    'pH': r'(pH$)',
    'flow': r'(FLOW$)',
    'fraction': r'(FRACTIONS?$)',
    'log_book': r'(Log(book)?$)',
    'temperature': r'(TEMP$)',
}

DATA_TYPES = DATA_NAME_SEARCH_PATTERNS.keys()

# The time can be measure with time units or with volume units since a lot of
# experimentalists measure time by the amount (volume) of liquid that has gone
# through the chromatography device.
VALID_TIME_UNITS = ['ml', 'mL', 'milliliter', 'milli-liter', 'millilitre',
                    'milli-litre', 'CV', 'min', 'minutes', 'seconds', 's',
                    'sec']

# Number of lines to preview, to search for the row with the start of the data
AKTA_PREVIEW_SIZE = 7


class AktaReadError(ValueError):
    pass


def read_akta(akta_fname, data_type, **header_row_info):
    """ Read the content of an AKTA file (pure ascci or CSV) into an ndarray.

    Parameters
    -----------
    akta_fname : str
        File path to the ASCII file to read.

    data_type : str
        Column type requested (uv, conductivity, ...). Must be present in the
        reader's list of available column types.

    header_info : dict
        Optional arguments about where to find the headers and the data. The
        following entries can be present:

    header_row_index : None or int
        Row index at which to read the column types (UV, conductivity, ...).
        If None, the number will be guessed.

    unit_row_index : None or int
        Row index at which to read the units for the data. (min, sec, ...).
        If None, the number will be guessed.

    data_row_index : None or int
        Row index at which to start reading the data. If None, the number will
        be guessed.

    Return
    ------
    output_data : dict
        Dictionary containing numpy arrays with a set of x values and y values.
        These arrays are assumed to be mapped to keys of the form 'time_NAME'
        and NAME where NAME describes the type of data stored.
    """
    reader = AKTAReader(file_path=akta_fname, **header_row_info)
    logger.info("{} contains the following headers: "
                "{}".format(akta_fname, reader.available_column_types))
    x_key = 'time_' + data_type
    output_data = reader.get_data([x_key, data_type])
    return output_data


class AKTAReader(HasStrictTraits):
    """ Reader for the AKTA file format.

    The reader is a lazy loader and only loads metadata on initialization.
    The actual data can be requested using the :meth:`get_data` API method.

    Examples
    --------
    >>> from kromatography.io.akta_reader import AKTAReader
    >>> reader = AKTAReader("path/to/file.asc")
    >>> reader.header_info
    OrderedDict([('uv', {'units': u'mAU', 'dtype': 'float', 'column_index': 3,
                  'header_name': u'***', 'name': 'uv'}),
                 ('time_uv', {'units': u'min', 'dtype': 'float',
                  'column_index': 2, 'header_name': u'**:10_UV2_280nm',
                  'name': 'time_uv'}),...])
    >>> # No data yet:
    >>> reader.data
    {}
    >>> # Collect all data and return the UV column
    >>> reader.get_data("uv")
    {'uv': array([  9.50000000e-02,   1.76000000e-01,   ...}
    >>> reader.data.keys()
    [u'time_concentration',
     u'time_uv',
     u'time_pH',
     u'uv',
     u'time_conductivity',
     u'flow',
     u'time_flow',
     u'concentration',
     u'pH',
     u'conductivity',
     ...]
    """

    #: The path to the AKTA file.
    file_path = Str

    #: Row index containing column names. If `None`, value is inferred
    header_row_index = Either(None, Int(0))

    #: Delimiter for data name fields in file. If `None` then, fields split on
    #: whitespace.
    header_delimiter = Either(None, Str)

    #: Row index containing units header. If `None`, value is inferred
    unit_row_index = Either(None, Int(1))

    #: Delimiter for unit fields in file. If `None`, fields split on whitespace
    unit_delimiter = Either(None, Str)

    #: Row index of first data entry. If `None`, value is inferred.
    data_row_index = Either(None, Int(2))

    #: Delimiter for the data fields in the AKTA file. If `None`, fields split
    #: on whitespace
    data_delimiter = Either(None, Str)

    #: Map of data types to the metadata associated with column in file.
    header_info = Instance(OrderedDict)

    #: Dict mapping expected data types to regex patterns to find them.
    col_name_patterns = Dict(DATA_NAME_SEARCH_PATTERNS)

    #: The complete and cached dictionary containing all data
    data = Dict

    #: Recorded time that should be set as the time origin. Ignored by default.
    time_of_origin = Float(0.)

    #: A list of all columns available in the AKTA file
    available_column_types = Property

    #: A list of the dataset available (1 col for data and 1 col for time axis)
    available_dataset_types = Property

    #: Raise an exception when 2 column are found to be of the same data type?
    raise_on_collision = Bool(True)

    def __init__(self, file_path=None, **traits):
        if not isfile(file_path):
            msg = 'Invalid file path {!r}'.format(file_path)
            logger.exception(msg)
            raise ValueError(msg)

        file_ext = splitext(basename(file_path))[-1]

        # try to set default based on the file-type
        trait_defaults = {}
        if file_ext == '.asc':
            trait_defaults['header_delimiter'] = '\t'
            trait_defaults['unit_delimiter'] = '\t'
            trait_defaults['data_delimiter'] = '\t'
        elif file_ext == '.csv':
            trait_defaults['header_delimiter'] = ','
            trait_defaults['unit_delimiter'] = ','
            trait_defaults['data_delimiter'] = ','
        else:
            msg = ("AKTA files with extension {} are not yet supported. Please"
                   " provide a .asc or a .csv file.".format(file_ext))
            logger.exception(msg)
            raise IOError(msg)

        # NOTE: any values passed by the user take precedence
        for key, val in trait_defaults.items():
            if key not in traits:
                traits[key] = val

        super(AKTAReader, self).__init__(file_path=file_path, **traits)
        self._read_header_info()

    # API Methods -------------------------------------------------------------

    def get_data(self, column_names=None):
        """ Extract the data columns specified as a dict of NumPy array.

        Note that the dictionary cannot as-is be fed into pd.DataFrame to
        analyze it because arrays are typically of different length. So a
        manual merge of this data is required.

        Parameters
        ----------
        column_names : str or list(str) [OPTIONAL]
            Name of list of names of columns requested. Leave unset to get all
            data.

        Returns
        -------
        dict
            Returns a dict mapping column names to the corresponding numpy
            array containing the data found.

        Raises
        ------
        KeyError
            If being request a column that isn't found in the AKTA file.
        """
        if not self.data:
            try:
                self.collect_all_data()
            except Exception as e:
                msg = "Failed to load the data content of AKTA file {}. " \
                      "Error was {}.".format(self.file_path, e)
                logger.exception(msg + format_tb())
                raise AktaReadError(msg)

        if isinstance(column_names, basestring):
            column_names = [column_names]

        if column_names is None:
            return self.data.copy()
        else:
            return {key: self.data[key] for key in column_names}

    # Supporting methods ------------------------------------------------------

    def collect_all_data(self):
        """ Collect all available data as described by the file header.

        Resulting content is stored as the `data` attribute.
        """
        fname = self.file_path
        header_info = self.header_info
        column_names = header_info.keys()

        cols = [header_info[key]['column_index'] for key in column_names]
        # Make sure these cols and names are sorted correctly, because
        # read_table doesn't keep the order set by usecols.
        order = np.array(cols).argsort()
        column_names = list(np.array(column_names)[order])
        cols.sort()

        df = pd.read_table(
            fname, skiprows=self.data_row_index, names=column_names,
            delimiter=self.data_delimiter,
            usecols=cols,
            skipinitialspace=True
        )
        data = df.replace('^\s*$', np.nan, regex=True).dropna(how="all")

        self.data = {key: data[key].values.astype(header_info[key]['dtype'])
                     for key in column_names}
        self.remove_nan_from_data()
        if self.time_of_origin:
            self.reset_akta_data_time_origin()

    def remove_nan_from_data(self):
        """ Remove all missing values from datasets found.
        """
        for datatype in self.available_dataset_types:
            time_key = "time_" + datatype
            time_arr = self.data[time_key]
            var_arr = self.data[datatype]
            if self.header_info[datatype]['dtype'] == 'float':
                missing_values = np.isnan(var_arr)
            elif self.header_info[datatype]['dtype'] == 'str':
                missing_values = var_arr == 'nan'
            else:
                continue

            missing_times = np.isnan(time_arr)
            if not np.all(missing_times == missing_values):
                msg = "The time and values for dataset {} are not aligned. " \
                      "Review needed!".format(datatype)
                logger.warning(msg)
                continue

            self.data[time_key] = self.data[time_key][~missing_times]
            self.data[datatype] = self.data[datatype][~missing_times]

    def _get_available_column_types(self):
        return self.header_info.keys()

    def _get_available_dataset_types(self):
        return [col for col in self.available_column_types
                if not col.startswith("time_")]

    @on_trait_change('col_name_patterns', post_init=True)
    def _read_header_info(self):
        """ Read and/or infer metadata for the columns in the AKTA file.

        Returns an `OrderedDict` with an entry for each column in the AKTA
        file. The keys are the parsed data field names and the values are
        dictionaries containing metadata for the column.
        """
        # Read enough lines to find the beginning of the data
        with open(self.file_path, 'r') as fp:
            start_lines = [
                fp.readline().strip('\n\r') for ii in range(AKTA_PREVIEW_SIZE)
            ]

        starts = [self.header_row_index, self.unit_row_index,
                  self.data_row_index]
        if not all(starts):
            self.header_row_index, self.unit_row_index, self.data_row_index = \
                _infer_header_rows(start_lines, self.header_delimiter)

        # Extract column names, units and first data
        header_names = strip_decode_strings(
            start_lines[self.header_row_index].split(self.header_delimiter)
        )
        header_units = strip_decode_strings(
            start_lines[self.unit_row_index].split(self.unit_delimiter)
        )
        sample_data = strip_decode_strings(
            start_lines[self.data_row_index].split(self.data_delimiter)
        )

        # Adjust empty entries from headers
        sanitize_str_list(header_names)
        sanitize_str_list(header_units)
        if len(header_names) % 2 != 0:
            header_names.append('')

        # Check header length compared to units and data
        len_head = len(header_names)
        len_units = len(header_units)
        len_data = len(sample_data)
        if len_head != len_units != len_data:
            msg = "The number of headers, units and data found in {} are " \
                  "different: {} vs {} vs {}."
            msg = msg.format(self.file_path, len_head, len_units, len_data)
            logger.exception(msg)
            raise ValueError(msg)

        # deduce column order of data pairs (time, data)
        if header_units is not None:
            # FIXME: it would be good to use scimath to parse the units, if the
            # units are reliable !
            if header_units[1] in VALID_TIME_UNITS:
                time_column = 1
                data_column = 0
            else:
                # default case.
                time_column = 0
                data_column = 1

        # deduce types, and dtypes
        header_info = OrderedDict()
        for ii in range(0, len(header_names), 2):
            data_field_info = {}
            data_col_ind = ii + data_column
            column_type = _parse_column_type(
                header_names[ii], col_name_patterns=self.col_name_patterns
            )
            data_field_info['column_index'] = data_col_ind
            data_field_info['header_name'] = header_names[ii]
            data_field_info['name'] = column_type
            data_field_info['dtype'] = get_dtype(sample_data[data_col_ind])
            data_field_info['units'] = header_units[data_col_ind]
            if column_type in header_info:
                msg = "AKTA file column {} was found to be of type {} but " \
                      "another column was found with the same type: {}. " \
                      "Adjust the AKTAReader's col_name_patterns."
                msg = msg.format(header_names[ii], column_type,
                                 header_info[column_type]['header_name'])
                if self.raise_on_collision:
                    logger.exception(msg)
                    raise AktaReadError(msg)
                else:
                    logger.warning(msg + "The resulting header_info will "
                                         "crash the excel reader. DO NOT USE.")
                    header_info[column_type] = [header_info[column_type],
                                                data_field_info]
            else:
                header_info[column_type] = data_field_info

            time_field_info = {}
            time_col_ind = ii + time_column
            time_field_info['column_index'] = time_col_ind
            time_field_info['header_name'] = header_names[time_col_ind]
            time_field_info['name'] = 'time_{}'.format(column_type)
            time_col_dtype = get_dtype(sample_data[time_col_ind])
            if time_col_dtype != "float":
                msg = ("The time column was expected to contain float but type"
                       " {} was found.".format(time_col_dtype))
                logger.info(msg)
            time_field_info['dtype'] = time_col_dtype
            time_field_info['units'] = header_units[time_col_ind]
            header_info[time_field_info['name']] = time_field_info

        self.header_info = header_info

    def reset_akta_data_time_origin(self):
        """ Reset the time origin to a certain time recoded by the AKTA.

        Every data entry that ends up before the new origin is thrown away.
        Useful to modify the AKTA data when the file contains values before the
        load step.
        """
        if not self.data:
            # No data to apply the time shift to
            return

        msg = "Shifting all datasets of AKTA file {} by {}."
        msg = msg.format(self.file_path, self.time_of_origin)
        logger.info(msg)

        if not validate_time_of_origin(self, self.time_of_origin):
            msg = "The time of origin selected {} doesn't appear in the time" \
                  " line of the logbook."
            msg = msg.format(self.time_of_origin)
            logger.warning(msg)

        for datatype in self.available_dataset_types:
            time_name = "time_" + datatype
            time_array = self.data[time_name]
            shifted_time = time_array - self.time_of_origin
            values_to_keep = shifted_time >= 0.
            shifted_time_after_load = shifted_time[values_to_keep]
            self.data[time_name] = shifted_time_after_load
            self.data[datatype] = self.data[datatype][values_to_keep]


def validate_time_of_origin(reader, time):
    """ Returns whether the time provided is listed in logbook's time array.

    Note: if there is no logbook found, the value is always considered valid.

    Parameters
    ----------
    reader : AKTAReader
        AKTA reader around the log data to instrospect.

    time : float or UnitScalar
        Time to search in the log.
    """
    if 'time_log_book' not in reader.header_info:
        msg = "No logbook found in {}".format(reader.file_path)
        logger.debug(msg)
        return True

    log_book_data = reader.get_data('time_log_book')
    time_arr = log_book_data.get('time_log_book', None)
    if time_arr is None:
        return True

    # If time was UnitScalar, convert to float for testing:
    time = float(time)

    # Validate the time value passed
    idx_array = np.where(np.abs(time_arr - time) < 1e-9)[0]
    valid = len(idx_array) > 0
    return valid


def _infer_header_rows(start_lines, header_delimiter):
    """ Look through all lines of text, split into fields, and return the row
    numbers for the headers, units and first data row.
    """
    # Skip the first rows, not to get fooled by a row that looks like data at
    # the top of the AKTA file. There has to be a row of headers (and typically
    # a row of units) before data starts:
    for i, row in enumerate(start_lines[1:]):
        fields = strip_decode_strings(row.split(header_delimiter))
        if str_list_mostly_float(fields):
            return i-1, i, i+1

    msg = ("None of the rows of the header was identified as the row of data. "
           "Defaulting to 1, 2, 3 for the headers, units, and data. Reading "
           "might fail. Rows were {}.".format(start_lines))
    logger.error(msg)
    return 1, 2, 3


def _parse_column_type(header_name, col_name_patterns=None):
    """ Parse the column type from the name of the AKTA column header.
    """
    if col_name_patterns is None:
        col_name_patterns = DATA_NAME_SEARCH_PATTERNS

    candidates = []
    for column_type, pattern in col_name_patterns.items():
        if not pattern:
            continue

        # If the AKTA setting was run and the pattern is the column name, use
        # that:
        if pattern == header_name:
            return column_type
        # Otherwise, search for a partial match:
        if re.search(pattern, header_name, flags=re.I):
            candidates.append(column_type)

    if len(candidates) == 1:
        return candidates[0]
    elif len(candidates) >= 2:
        msg = "The regex pattern to detect the type of column {} is ambigious"\
              ": it could be the following types: {}. Please read the AKTA " \
              "file with more precise column detection patterns"
        msg = msg.format(header_name, candidates)
        logger.error(msg)
        raise AktaReadError(msg)
    else:
        # Didn't detect the type: return the column name
        name = header_name
        if ":" in name:
            name = header_name.split(":")[-1]

        msg = ('Could not find the continuous data type for the header '
               '{}. Setting type as {}').format(header_name, name)
        logger.warning(msg)
        return name
