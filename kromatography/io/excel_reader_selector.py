"""
Class to select and create the appropriate ExcelReader for an Excel input file
for Reveal Chromatography.
"""
import logging
import pyexcel
import pyexcel.ext.xls  # import needed to handle xls file
import pyexcel.ext.xlsx  # import needed to handle xlsx file

from traits.api import HasStrictTraits, Str

from .excel_reader import ExcelReader
from .excel_reader_v1 import ExcelReaderV1

logger = logging.getLogger(__name__)

MISSING_VALUES = ['', 'NA', 'N/A']

# Excel input version, as a tuple of python indices
INPUT_VERSION_CELL_COORDINATES = (0, 4)

VERSION_READER_MAP = {1: ExcelReaderV1,
                      2: ExcelReader}


class ExcelInputReaderSelector(HasStrictTraits):
    """ Class to identify Excel input version & build appropriate ExcelReader.
    """
    #: Path to the xls or xlsx file to analyze
    filepath = Str

    def build_excel_reader(self, **traits):
        klass = self.select_excel_reader_klass()
        return klass(file_path=self.filepath, **traits)

    def select_excel_reader_klass(self):
        """ Pre-load an Excel input file to determine which ExcelReader to use to
        read the data.
        """
        excel_input_version = self.get_excel_input_version()
        return VERSION_READER_MAP[excel_input_version]

    def get_excel_input_version(self):
        """ Returns the version number of an Excel input file to Reveal.
        """
        sheet = pyexcel.get_sheet(file_name=self.filepath)
        version = sheet.cell_value(*INPUT_VERSION_CELL_COORDINATES)
        if version:
            return version
        else:
            return 1
