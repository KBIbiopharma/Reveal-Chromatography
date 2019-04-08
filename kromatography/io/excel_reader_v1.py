""" This module contains the DEPRECATED reader for the first version of the
Excel input file for Reveal. Refer to excel_reader for the reader for the most
recent format.
"""
import logging
from warnings import warn

from traits.api import Constant, Str

from .base_excel_reader import BaseExcelReader, CONTENT_NAME_COL, \
    CURRENT_INPUT_VERSION, FIRST_CONTENT_COL, MISSING_VALUES

logger = logging.getLogger(__name__)


class ExcelReaderV1(BaseExcelReader):
    """ Reader for version 1 of the Excel input file format (DEPRECATED).
    """
    _excel_version = Constant(1)

    general_section_name = Str('General Experiment Information')

    def __init__(self, file_path=None, **traits):
        msg = "This version (1) of the Excel input file is DEPRECATED, and " \
              "shouldn't be used anymore. Please more your data to the " \
              "newest format version ({})".format(CURRENT_INPUT_VERSION)
        logger.warning(msg)
        warn(msg, DeprecationWarning)

        super(ExcelReaderV1, self).__init__(file_path=file_path, **traits)

    def get_load_data(self):
        """Returns dictionary of loads with key as their name from the excel.
        """
        product_component_assays = self.product.product_component_assays
        impurity_assays = self.product.impurity_assays

        sheet = self._get_sheet()

        # find load section
        section_start = self._get_section_index(sheet, self.load_section_name)

        # determine number of columns in section
        num_columns = self._get_section_last_col(sheet, section_start)

        offsets = self._get_load_data_offsets(section_start)

        # read loads in one by one and store in dict by name
        load_data = {}
        for col in range(3, num_columns):
            # Metadata subsection
            load = {'solution_type': 'Load'}

            labels = ['name', 'source', 'lot_id',
                      ('product_concentration', float)]
            adl_data = self._get_continuous_cells(labels, offsets['metadata'],
                                                  col, sheet)
            load.update(adl_data)

            # Product component assay subsection
            product_component_assay_dict = {}
            first_assay_row = offsets['product_component_names']
            excel_product_component_assays = [
                sheet[first_assay_row + e, 1]
                for e in range(len(product_component_assays))
                ]
            for e, excel_assay in enumerate(excel_product_component_assays):
                if excel_assay not in product_component_assays:
                    msg = ("Assay {} not found in product definition. Known "
                           "assays are {}.")
                    msg = msg.format(excel_assay, product_component_assays)
                    logger.exception(msg)
                    raise LookupError(msg)

                product_component_assay_dict[excel_assay] = \
                    float(sheet[offsets['product_component_names'] + e, col])

            load['product_component_assay_dict'] = product_component_assay_dict

            # impurity assay subsection
            impurity_assay_dict = {}
            excel_impurity_assays = [
                sheet[offsets['impurity_names'] + e, 1]
                for e in range(len(impurity_assays))
                ]
            for e, excel_assay in enumerate(excel_impurity_assays):
                if excel_assay not in impurity_assays:
                    msg = ("Assay {} does not found in product definition. "
                           "Known assays are {}.")
                    msg = msg.format(excel_assay, impurity_assays)
                    logger.exception(msg)
                    raise LookupError(msg)

                impurity_assay_dict[excel_assay] = \
                    float(sheet[offsets['impurity_names'] + e, col])

            load['impurity_assay_dict'] = impurity_assay_dict

            # Read in chemical components in the load
            chem_comp_concentrations = {}
            i = 0
            while True:
                name_offset = offsets['chemical_components'] + i
                if not sheet[name_offset, 1].lower().startswith("component"):
                    break
                comp_name = sheet[name_offset, col]
                comp_concentration = float(sheet[name_offset + 1, col])
                chem_comp_concentrations[comp_name] = comp_concentration
                i += 2

            load['chemical_component_concentration_dict'] = \
                chem_comp_concentrations

            # Rest of load data subsection
            load_props_offset = offsets['chemical_components'] + i
            labels = [('density', float), ('conductivity', float),
                      ('pH', float), ('temperature', float)]
            adl_data = self._get_continuous_cells(labels, load_props_offset,
                                                  col, sheet)
            load.update(adl_data)

            load_data[load['name']] = load

        return load_data

    def get_buffer_prep_data(self):
        """Returns dictionary of buffers with key as their name from the excel.
        """
        sheet = self._get_sheet()

        # find buff[section
        section_start = self._get_section_index(
            sheet, self.buffer_section_name
        )

        # determine number of columns in section
        last_column = self._get_section_last_col(sheet, section_start)

        # read buffers in one by one and store in dict by name
        buffer_prep_data = {}

        solid_subheader = "Solid Additions"
        solid_subsection_start = self._get_subsection_index(
            sheet, solid_subheader, search_from=section_start
        )
        # Increment by 1 for skiping the sub-header row
        solid_subsection_start += 1

        liquid_subheader = "Liquid Additions"
        liquid_subsection_start = self._get_subsection_index(
            sheet, liquid_subheader, search_from=section_start
        )
        # Increment by 1 for skiping the sub-header row
        liquid_subsection_start += 1

        num_solids = (liquid_subsection_start - solid_subsection_start) // 2
        liquid_subsection_end = self._get_subsection_index(
            sheet, "Buffer Volume", search_from=liquid_subsection_start
        )
        num_liquids = (liquid_subsection_end - liquid_subsection_start) // 3

        for col in range(FIRST_CONTENT_COL, last_column):
            logger.debug("Reading buffer in column {}...".format(col))
            labels = ['name', 'source', 'description', 'lot_id',
                      ('density', float)]
            buff = self._get_continuous_cells(labels, section_start + 1,
                                              col, sheet)

            buff['chemical_dict'] = {}
            for num_chem in range(num_solids):
                chem_start = solid_subsection_start + num_chem * 2
                name = sheet[chem_start, col].strip()
                if name in MISSING_VALUES:
                    continue
                amount = float(sheet[chem_start + 1, col])
                buffer_chemical = {'amount': amount, 'concentration': 0.0,
                                   'state': 'Solid'}
                buff['chemical_dict'][name] = buffer_chemical

            for num_chem in range(num_liquids):
                chem_start = liquid_subsection_start + num_chem * 3
                labels = [('name', unicode.strip), ('concentration', float),
                          ('amount', float)]
                buffer_chemical = self._get_continuous_cells(
                    labels, chem_start, col, sheet
                )
                buffer_chemical['state'] = 'Liquid'
                name = buffer_chemical.pop("name")

                if name not in MISSING_VALUES:
                    buff['chemical_dict'][name] = buffer_chemical

            labels = [('volume', float), ('conductivity', float),
                      ('pH', float), ('temperature', float)]
            adl_data = self._get_continuous_cells(labels, section_start + 17,
                                                  col, sheet)
            buff.update(adl_data)

            buffer_prep_data[buff['name']] = buff

        return buffer_prep_data

    def _get_method_data(self, sheet, section_start, col):
        """Returns dictionary associated with the Method Information from
        column col.
        """
        method_data = self._get_continuous_cells(self.method_labels,
                                                 section_start+1, col, sheet)

        method_data.update({'steps': [], 'collection_criteria': {}})

        # Collect step data
        for i in range(1, method_data['num_steps'] + 1):
            logger.debug("Reading step {}...".format(i))
            method_data['steps'].append(self._get_next_step(sheet, i, col))

        # look for collection_criteria, raising error if none found
        try:
            collection_criteria_start = self._get_subsection_index(
                sheet, 'Start Collect Type', search_from=section_start
            )
            labels = ["start_collection_type",
                      ("start_collection_target", float),
                      "stop_collection_type",
                      ("stop_collection_target", float)]
            collection_data = self._get_continuous_cells(
                labels, collection_criteria_start, col, sheet
            )
            method_data['collection_criteria'] = collection_data

            step_data_start = section_start + 5
            step_num = (collection_criteria_start - 1 - step_data_start) // 5
            method_data['collection_step_number'] = step_num - 1
        except ValueError as e:
            msg = "Failed to collect collection criteria: error was {}. " \
                  "Continuing with the rest of the file.".format(e)
            logger.warning(msg)
            method_data['collection_step_number'] = -1

        return method_data

    def _get_performance_parameter_data(self, sheet, section_start, col):
        """Returns dictionary associated with the Performance Parameters
        from column col
        """
        product_component_assays = self.product.product_component_assays
        impurity_assays = self.product.impurity_assays

        offsets = self._get_perf_param_data_offsets(section_start)

        # Metadata subsection
        labels = [("pool_volume", float), ("step_yield", float),
                  ("pool_concentration", float)]
        perf_param_data = self._get_continuous_cells(
            labels, offsets['metadata'], col, sheet
        )

        # Product component assay subsection
        product_component_assay_dict = {}
        excel_product_component_assays = [
            sheet[offsets['product_component_assays'] + e, CONTENT_NAME_COL]
            for e in range(len(product_component_assays))
        ]
        for e, excel_assay in enumerate(excel_product_component_assays):
            if excel_assay not in product_component_assays:
                msg = "assay {} does not match assays in product: {}".format(
                        excel_assay, product_component_assays
                )
                logger.exception(msg)
                raise LookupError(msg)
            else:
                product_component_assay_dict[excel_assay] = \
                    float(sheet[offsets['product_component_assays'] + e, col])
        perf_param_data['product_component_assay_dict'] = \
            product_component_assay_dict

        # impurity assay subsection
        impurity_assay_dict = {}
        excel_impurity_assays = [
            sheet[offsets['impurity_names'] + e, 1]
            for e in range(len(impurity_assays))
        ]
        for e, excel_assay in enumerate(excel_impurity_assays):
            if excel_assay not in impurity_assays:
                msg = "assay {} does not match assays in product"
                msg = msg.format(excel_assay)
                logger.exception(msg)
                raise LookupError(msg)
            else:
                impurity_assay_dict[excel_assay] = \
                    float(sheet[offsets['impurity_names'] + e, col])
        perf_param_data['impurity_assay_dict'] = impurity_assay_dict

        # Read final params:
        labels = [("conductivity", float), ("pH", float)]
        adl_data = self._get_continuous_cells(
            labels, offsets['final_params'], col, sheet
        )
        perf_param_data.update(adl_data)

        return perf_param_data

    # Offset computation methods ----------------------------------------------

    def _get_load_data_offsets(self, section_start):
        """Returns dictionary of the primary offsets for the parts of the
        Load Information section.
        """
        product_component_assays = self.product.product_component_assays
        num_comp_assays = len(product_component_assays)

        impurity_assays = self.product.impurity_assays
        num_imp_assays = len(impurity_assays)

        component_start_offset = section_start + 5

        offsets = {
            'metadata': section_start + 1,
            'product_component_names': component_start_offset,
            'impurity_names': component_start_offset + num_comp_assays,
            'chemical_components': (component_start_offset +
                                    num_comp_assays + num_imp_assays)
        }
        return offsets

    def _get_perf_param_data_offsets(self, section_start):
        """Returns dictionary of the primary offsets for the parts of the
        Performance Parameter Information section.
        """
        product_component_assays = self.product.product_component_assays
        num_comp_assays = len(product_component_assays)

        impurity_assays = self.product.impurity_assays
        num_imp_assays = len(impurity_assays)

        assay_start = section_start + 4
        final_params_start = self._get_final_perf_param_offset(assay_start)

        offsets = {
            'metadata': section_start + 1,
            'product_component_assays': assay_start,
            'impurity_names': assay_start + num_comp_assays,
            'chemical_components': (assay_start + num_comp_assays +
                                    num_imp_assays),
            'final_params': final_params_start,
        }
        return offsets

    def _get_final_perf_param_offset(self, start):
        """ Look for the conductivity entry in the perf param section
        """
        sheet = self._get_sheet()
        i = start
        while sheet[i, 0].strip().lower() != "fraction data":
            if sheet[i, 1].strip().lower() == "conductivity":
                return i
            i += 1

        msg = ("Failed to find the conductivity in the performance parameter "
               "section. Please review the input file. Spreadsheet scanned "
               "from {} to {})".format(start, i))
        logger.exception(msg)
        raise IOError(msg)

    # HasTraits initialization methods ----------------------------------------

    def _general_section_labels_default(self):
        return [
            'product_name', 'study_name', 'study_id', 'study_type',
            'study_subtype', 'study_purpose', 'column_placement', 'site',
            'experimentalist'
        ]

    def _system_section_labels_default(self):
        return [
            'system_id', 'system_name', 'system_type',
            ('holdup_pump_to_loop', float), ('holdup_loop_to_col', float),
            ('holdup_col_to_detect', float),
            ('absorbance_detector_pathlength', float)
        ]

    def _column_section_labels_default(self):
        return [
            'packed_column_lot_id', 'resin_type', 'resin_lot_id',
            ('resin_avg_bead_diameter', float),
            ('resin_ligand_density', float), 'column_model',
            'column_description', ('column_packed_bed_height', float),
            ('compression_factor', float), ('HETP', float),
            ('asymmetry', float)
        ]

    def _method_labels_default(self):
        return ['experiment_name', ('experiment_number', int), 'run_type',
                ('num_steps', int)]
