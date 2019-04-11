from unittest import TestCase
import os
import shutil
from tables import open_file
import numpy as np
import zipfile
from numpy.testing.utils import assert_array_almost_equal

from app_common.std_lib.filepath_utils import string2filename
from app_common.apptools.io.serialization_utils import write_ndArray_to_hdf5, \
    read_ndArray_from_hdf5, zip_files, unzip_files
from app_common.apptools.io.reader_writer import LocalFileReader, \
    LocalFileWriter
from app_common.traits.assertion_utils import assert_has_traits_almost_equal, \
    assert_values_almost_equal

from kromatography.io.serializer import serialize
from kromatography.io.deserializer import deserialize
from kromatography.utils.cadet_simulation_builder import build_cadet_input
from kromatography.utils.io_utils import write_to_h5
from kromatography.model.factories.simulation import \
    build_simulation_from_experiment
from kromatography.solve.api import run_cadet_simulator
from kromatography.utils.testing_utils import io_data_path
from kromatography.io.study import load_study_from_excel
from kromatography.io.simulation_updater import update_simulation_results
from kromatography.io.serializer import Serializer
from kromatography.io.deserializer import deSerializer


class TestLowLevelSerializationHDF5(TestCase):
    """ Test of serialization components: HDF5 piece, json piece, ...
    """
    @classmethod
    def setUpClass(cls):
        input_file = io_data_path('ChromExampleDataV2.xlsx')
        cls.study = load_study_from_excel(input_file, allow_gui=False)

        # Building and running simulation for only 1 experiment
        expt = cls.study.experiments[0]
        output_file = "{}_{}_{}.h5".format(cls.study.name, expt.name,
                                           'cadet_simulation')
        output_file = string2filename(output_file)
        sim = build_simulation_from_experiment(expt)
        cls.study.simulations.append(sim)

        # create the CADET inputs
        cadet_input = build_cadet_input(sim)

        # write the CADET inputs
        write_to_h5(output_file, cadet_input, root='/input', overwrite=True)
        # run simulation to generate outputs
        run_cadet_simulator(output_file)
        update_simulation_results(sim, output_file)

    def setUp(self):
        # Reseting the array_collections
        Serializer.array_collection = {}
        deSerializer.array_collection = {}

        self.test_file = 'test_file.chrom'
        self.test_folder = 'test_dir'
        if os.path.exists(self.test_file):
            os.remove(self.test_file)
        if os.path.exists(self.test_folder):
            shutil.rmtree(self.test_folder)

    def tearDown(self):
        if os.path.exists(self.test_file):
            os.remove(self.test_file)
        if os.path.exists(self.test_folder):
            shutil.rmtree(self.test_folder)

    def test_write_read_simulation_to_hdf5(self):
        os.makedirs(self.test_folder)
        object_to_save = self.study.simulations[0]
        array_collection = serialize(object_to_save)[1]
        num_arrays = len(array_collection)
        hdf5_filenames = write_ndArray_to_hdf5(array_collection,
                                               self.test_folder)
        total_arrays_found = 0
        total_df_found = 0
        # File exist
        for filename in hdf5_filenames:
            self.assertTrue(os.path.isfile(filename))
            self.assertEqual(os.path.splitext(filename)[1], ".h5")

            # Files contain arrays
            with open_file(filename, "r") as f:
                for node in f.walk_nodes("/", "Array"):
                    total_arrays_found += 1
                    self.assertNotEqual(node.size_on_disk, 0)

                # Now listing groups because a dataframe or a series is stored
                # as a group directly inside the root node:
                df_names = f.root._g_list_group(f.root)[0]
                total_df_found += len(df_names)

        # Files contain all arrays and pandas objects
        self.assertEqual(total_arrays_found + total_df_found, num_arrays)

        new_data_collection = read_ndArray_from_hdf5(hdf5_filenames)
        assert_values_almost_equal(array_collection, new_data_collection)

    def test_zip_unzip(self):
        # Create fake files
        with open(self.test_file, "w") as f:
            f.write("FOOBAR")

        target_hdf5 = "test.h5"
        data = np.arange(10.)
        with open_file(target_hdf5, "w") as f:
            f.create_array("/",  "array0", data)

        # test zipping
        target_zip = "test.zip"
        zip_files(target_zip, [self.test_file, target_hdf5])
        with zipfile.ZipFile(target_zip, "r") as fzip:
            found = [fileobj.filename for fileobj in fzip.filelist]
            self.assertEqual(set(found), {self.test_file, target_hdf5})

        # Test unzipping
        found = unzip_files(target_zip, target_folder=self.test_folder)

        # Test content of unzipped files
        expected = [os.path.join(self.test_folder, fname)
                    for fname in [self.test_file, target_hdf5]]
        self.assertEqual(set(found), set(expected))
        with open(os.path.join(self.test_folder, self.test_file)) as f:
            self.assertEqual(f.read(), "FOOBAR")

        with open_file(target_hdf5, "r") as f:
            arr_content = f.get_node("/array0").read()
            assert_array_almost_equal(arr_content, data)

        # Clean up files other than self.test_file since tearDown takes care of
        # it
        for fname in [target_hdf5, target_zip]:
            if os.path.exists(fname):
                os.remove(fname)

    def test_write_read_roundtrip(self):
        object_to_save = self.study
        writer = LocalFileWriter(filepath=self.test_file, serialize=serialize)
        writer.save(object_to_save)

        reader = LocalFileReader(filepath=self.test_file,
                                 deserialize=deserialize)
        new_object, _ = reader.load()
        # Ignore the datasource and dirty flag since not stored when storing a
        # study:
        assert_has_traits_almost_equal(new_object, object_to_save,
                                       ignore=['datasource', 'dirty'])
