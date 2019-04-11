"""ExcelReader for current version to load data into dictionaries of strings
and floats.

Assumptions on Excel file for this version:

Rule1: Major Sections (which are contained in the first column):

    * General Experiment Information
    * Chromatography System Information
    * Chromatography Column Information
    * Load Information
    * Buffer Information
    * Method Information
    * Performance Parameters
    * Fraction Data
    * Continuous Data

Rule2: 2nd column contains data names for given section, which are all assumed
to be fixed (later will want to change this for flexibility for user).

Rule3: 4th-xth columns contain data values.

Rule4: Units are not attempted to be read in.

Rule5: If a cell expects a number, then reader fails if it doesn't find one,
but for  all other cells, any input is accepted (including no input).

TODO: add unit support.
"""

import logging

from traits.api import Constant

from .base_excel_reader import BaseExcelReader, CONTENT_NAME_COL, \
    ExcelReadError, FIRST_CONTENT_COL, StepNotFoundError
from kromatography.utils.string_definitions import STRIP_COMP_NAME
from kromatography.model.method import UNSET

logger = logging.getLogger(__name__)

MISSING_VALUES = ['', 'NA', 'N/A']


class ExcelReader(BaseExcelReader):
    """ Reader for the current version of the Excel input file format.

    This is the most recent and recommended version of the Reveal input files.

    Examples
    --------
    >>> reader = ExcelReader(file_path="path/to/excel/file.xlsx")
    >>> all_data = reader.get_all_data()
    """

    _excel_version = Constant(2)

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

        num_prod_assay = (offsets["impurity_names"] -
                          offsets["component_assay_names"])

        load_data = {}

        # read loads in one by one and store in dict by name
        for col in range(3, num_columns):
            # Metadata subsection
            load = self._get_continuous_cells(
                self.load_labels, offsets['metadata'], col, sheet
            )
            load['solution_type'] = 'Load'

            # Product component assay subsection
            product_component_assay_dict = {}
            first_assay_row = offsets['component_assay_names']
            # Assay names expected to be in the load section of the Excel file
            # The strip component by definition cannot be present in the load!
            excel_product_component_assays = [
                sheet[first_assay_row + e, CONTENT_NAME_COL]
                for e in range(num_prod_assay)
            ]
            for e, excel_assay in enumerate(excel_product_component_assays):
                if excel_assay not in product_component_assays:
                    msg = ("Assay {} not found in product definition. Known "
                           "assays are {}.")
                    msg = msg.format(excel_assay, product_component_assays)
                    logger.exception(msg)
                    raise LookupError(msg)

                product_component_assay_dict[excel_assay] = \
                    float(sheet[offsets['component_assay_names'] + e, col])

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

            load_data[load['name']] = load

        return load_data

    def get_buffer_prep_data(self):
        """Returns dictionary of buffers with key as their name from the excel.
        """
        sheet = self._get_sheet()

        # find buff[section
        section_start = self._get_section_index(sheet,
                                                self.buffer_section_name)

        # determine number of columns in section
        last_column = self._get_section_last_col(sheet, section_start)

        # read buffers in one by one and store in dict by name
        buffer_prep_data = {}

        for col in range(FIRST_CONTENT_COL, last_column):
            logger.debug("Reading buffer in column {}...".format(col))

            buff = self._get_continuous_cells(
                self.buffer_labels, section_start + 1, col, sheet
            )
            # Offset information
            offsets = self._get_buffer_offsets(sheet, section_start)
            num_solids = (offsets["liquid_start"]-offsets["solid_start"]) // 2
            num_liquids = (offsets["liquid_end"]-offsets["liquid_start"]) // 3

            buff['chemical_dict'] = {}
            for num_chem in range(num_solids):
                chem_start = offsets["solid_start"] + num_chem * 2
                labels = [('name', unicode.strip), ('amount', float)]
                buffer_chemical = self._get_continuous_cells(
                    labels, chem_start, col, sheet
                )
                buffer_chemical['concentration'] = 0.0
                buffer_chemical['state'] = 'Solid'

                name = buffer_chemical.pop("name")
                if name not in MISSING_VALUES:
                    buff['chemical_dict'][name] = buffer_chemical

            for num_chem in range(num_liquids):
                chem_start = offsets["liquid_start"] + num_chem * 3
                labels = [('name', unicode.strip), ('concentration', float),
                          ('amount', float)]
                buffer_chemical = self._get_continuous_cells(
                    labels, chem_start, col, sheet
                )
                buffer_chemical['state'] = 'Liquid'

                name = buffer_chemical.pop("name")
                if name not in MISSING_VALUES:
                    buff['chemical_dict'][name] = buffer_chemical

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
        i = 0
        while True:
            i += 1
            logger.debug("Reading step {}...".format(i))
            try:
                step_data = self._get_next_step(sheet, i, col)
                method_data['steps'].append(step_data)
            except StepNotFoundError:
                break

        self._get_collection_criteria(sheet, col, method_data)
        return method_data

    def _get_collection_criteria(self, sheet, col, method_data):
        """ Read collection criteria information and update method_data dict.
        """
        coll_crit_start = self._get_section_index(sheet,
                                                  self.coll_crit_section_name)
        do_collect = sheet[coll_crit_start + 1, col]
        if do_collect.lower() == "no":
            exp_num = col - FIRST_CONTENT_COL
            msg = "No collect collection criteria for experiment"
            msg = msg.format(exp_num)
            logger.debug(msg)
            collection_data = {}
            coll_step_num = UNSET
        else:
            labels = ["Collection step",
                      "start_collection_type",
                      ("start_collection_target", float),
                      "start_collection_while",
                      "stop_collection_type",
                      ("stop_collection_target", float),
                      "stop_collection_while"]
            collection_data = self._get_continuous_cells(
                labels, coll_crit_start+2, col, sheet
            )
            coll_step_name = collection_data.pop("Collection step")
            coll_step_num = self._get_step_num(coll_step_name, method_data)

        method_data['collection_criteria'] = collection_data
        method_data['collection_step_number'] = coll_step_num

    def _get_performance_parameter_data(self, sheet, section_start, col):
        """ Returns dictionary associated with the Performance Parameters
        from column col.
        """
        perf_param_start = self._get_section_index(
            sheet, self.performance_section_name
        )
        do_collect = sheet[perf_param_start + 1, col]

        if do_collect.lower() == "no":
            exp_num = col-FIRST_CONTENT_COL
            msg = "No collect collection criteria for experiment"
            msg = msg.format(exp_num)
            logger.debug(msg)
            return {}

        product_component_assays = self.product.product_component_assays
        impurity_assays = self.product.impurity_assays

        offsets = self._get_perf_param_data_offsets(section_start)
        # Number of product assays to expect computed in the offsets
        num_product_assays = (offsets["impurity_names"] -
                              offsets["product_component_assays"])

        # Metadata subsection
        labels = [("pool_volume", float), ("step_yield", float),
                  ("pool_concentration", float), ("conductivity", float),
                  ("pH", float)]
        perf_param_data = self._get_continuous_cells(
            labels, offsets['metadata'], col, sheet
        )

        # Product component assay subsection
        component_assay_dict = {}
        excel_product_component_assays = [
            sheet[offsets['product_component_assays'] + e, CONTENT_NAME_COL]
            for e in range(num_product_assays)
        ]
        for e, excel_assay in enumerate(excel_product_component_assays):
            if excel_assay not in product_component_assays:
                msg = "assay {} does not match assays in product: {}".format(
                        excel_assay, product_component_assays
                )
                logger.exception(msg)
                raise LookupError(msg)
            else:
                component_assay_dict[excel_assay] = \
                    float(sheet[offsets['product_component_assays'] + e, col])

        perf_param_data['product_component_assay_dict'] = component_assay_dict

        # impurity assay subsection
        impurity_assay_dict = {}
        excel_impurity_assays = [
            sheet[offsets['impurity_names'] + e, 1]
            for e in range(len(impurity_assays))
        ]
        for e, excel_assay in enumerate(excel_impurity_assays):
            if excel_assay not in impurity_assays:
                msg = "assay {} does not match impurity assays in product"
                msg = msg.format(excel_assay)
                logger.exception(msg)
                raise LookupError(msg)
            else:
                impurity_assay_dict[excel_assay] = \
                    float(sheet[offsets['impurity_names'] + e, col])

        perf_param_data['impurity_assay_dict'] = impurity_assay_dict
        return perf_param_data

    def _get_step_num(self, step_name, method_data):
        """ Return the step index for provided step name.

        Raises
        ------
        ValueError:
            If there is no step with the name provided or more than 1 step with
            the name provided.
        """
        candidates = []
        for i, step_data in enumerate(method_data["steps"]):
            if step_data["name"].lower() == step_name.lower():
                candidates.append(i)

        if len(candidates) != 1:
            msg = "Collection indicated to be done at step {} but found more" \
                  " or less than 1 step with that name.".format(step_name)
            logger.exception(msg)
            raise ExcelReadError(msg)

        return candidates[0]

    # Offset calculation methods ----------------------------------------------

    def _get_buffer_offsets(self, sheet, section_start):
        """ Compute the location of the solid and liquid additions in buffer
        section.
        """
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

        liquid_subsection_end = self._get_subsection_index(
            sheet, "", search_from=liquid_subsection_start
        )

        return {"solid_start": solid_subsection_start,
                "liquid_start": liquid_subsection_start,
                "liquid_end": liquid_subsection_end}

    def _get_load_data_offsets(self, section_start):
        """Returns dictionary of the primary offsets for the parts of the
        Load Information section.
        """
        product_component_assays = self.product.product_component_assays
        num_comp_assays = len(product_component_assays)
        # If strip is present in assay, it won't be in the load, by definition
        # of the strip component
        if STRIP_COMP_NAME in product_component_assays:
            num_comp_assays -= 1

        impurity_assays = self.product.impurity_assays
        num_imp_assays = len(impurity_assays)

        metadata_len = len(self.load_labels) + 1
        component_assay_start_offset = section_start + metadata_len + 1

        offsets = {
            'metadata': section_start + 1,
            'component_assay_names': component_assay_start_offset,
            'impurity_names': component_assay_start_offset + num_comp_assays,
            'chemical_components': (component_assay_start_offset +
                                    num_comp_assays + num_imp_assays + 1)
        }
        return offsets

    def _get_perf_param_data_offsets(self, section_start):
        """Returns dictionary of the primary offsets for the parts of the
        Performance Parameter Information section.
        """
        product_component_assays = self.product.product_component_assays
        num_comp_assays = len(product_component_assays)
        # If strip is present in assay, it won't be in the load, by definition
        # of the strip component
        if STRIP_COMP_NAME in product_component_assays:
            num_comp_assays -= 1

        impurity_assays = self.product.impurity_assays
        num_imp_assays = len(impurity_assays)

        assay_start = section_start + 8

        offsets = {
            'metadata': section_start + 2,
            'product_component_assays': assay_start,
            'impurity_names': assay_start + num_comp_assays,
            'chemical_components': (assay_start + num_comp_assays +
                                    num_imp_assays + 1),
        }
        return offsets

    # HasTraits initialization methods ----------------------------------------

    def _general_section_labels_default(self):
        return [
            'product_name', 'study_name', 'study_id', 'study_type',
            'study_purpose', 'site', 'column_placement', 'experimentalist'
        ]

    def _system_section_labels_default(self):
        return [
            'system_type', 'system_name', 'system_id',
            ('holdup_pump_to_loop', float), ('holdup_loop_to_col', float),
            ('holdup_col_to_detect', float),
            ('absorbance_detector_pathlength', float)
        ]

    def _column_section_labels_default(self):
        return [
            'packed_column_lot_id', 'resin_type', 'resin_lot_id',
            'column_model', 'column_description',
            ('column_packed_bed_height', float), ('compression_factor', float),
            ('HETP', float), ('asymmetry', float)
        ]

    def _buffer_labels_default(self):
        return ['name', 'source', 'description', 'lot_id', ('volume', float),
                ('density', float), ('conductivity', float), ('pH', float),
                ('temperature', float)]

    def _load_labels_default(self):
        return ['name', 'source', 'description', 'lot_id',
                ('product_concentration', float), ('density', float),
                ('conductivity', float), ('pH', float), ('temperature', float)]

    def _method_labels_default(self):
        return ['experiment_name', 'run_type']
