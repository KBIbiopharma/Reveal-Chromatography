""" Tests that serialization generate the expect data.
"""

from unittest import TestCase
from nose.tools import assert_equal

from kromatography.io.serializer import serialize
from kromatography.utils.testing_utils import io_data_path
from kromatography.io.study import load_study_from_excel
from kromatography.model.tests.example_model_data import \
    ACIDIC_1_PRODUCT_COMPONENT_DATA, BUFFER_EQUIL_WASH1, COMPONENT_DATA

key_all_chrom_data = ['editable', 'name', 'class_metadata', 'uuid']


class TestSerializationContainerChromData(TestCase):
    def test_study(self):
        input_file = io_data_path('ChromExampleDataV2.xlsx')
        obj = load_study_from_excel(input_file, allow_gui=False)
        expected = ['product', 'is_blank', 'name', 'study_type', 'editable',
                    'class_metadata', 'study_purpose', 'experiments',
                    'simulations', 'study_datasource', 'exp_study_filepath',
                    'analysis_tools']
        assert_serial_data_contains(obj, expected)


class TestSerializationBasicChromData(TestCase):

    def test_component(self):
        from kromatography.model.component import Component
        obj = Component(**COMPONENT_DATA)
        expected = ['charge', 'pKa'] + key_all_chrom_data
        serial_data, array_data = assert_serial_data_contains(obj, expected)
        charge_data = serial_data["data"]['charge']
        pKa_data = serial_data["data"]['pKa']
        expected = ['data', 'units', 'class_metadata']
        self.assertEqual(set(charge_data.keys()), set(expected))
        self.assertEqual(set(pKa_data.keys()), set(expected))
        # Charge actual charge value
        self.assertEqual(charge_data['data'], 1.)
        self.assertEqual(charge_data['units']["class_metadata"]['type'],
                         'SmartUnit')

    def test_product_component(self):
        from kromatography.model.product_component import ProductComponent
        obj = ProductComponent(**ACIDIC_1_PRODUCT_COMPONENT_DATA)
        expected = ['target_product', 'molecular_weight',
                    'extinction_coefficient'] + key_all_chrom_data
        assert_serial_data_contains(obj, expected)

    def test_buffer(self):
        from kromatography.model.buffer import Buffer
        obj = Buffer(**BUFFER_EQUIL_WASH1)
        expected = ['temperature', 'density',
                    'chemical_component_concentrations', 'chemical_components',
                    'source', 'lot_id', 'description', 'pH', 'conductivity']
        expected += key_all_chrom_data
        serial_data, array_data = assert_serial_data_contains(obj, expected)
        temp_data = serial_data['data']['temperature']
        self.assertEqual(temp_data['data'], 20.0)
        density_data = serial_data['data']['density']
        self.assertEqual(density_data['data'], 1.0)


# Helper functions ------------------------------------------------------------


def assert_serial_data_contains(obj, expected):
    serial_data, array_collection = serialize(obj)
    stored_attrs = serial_data['data'].keys()
    assert_equal(set(stored_attrs), set(expected))
    return serial_data, array_collection
