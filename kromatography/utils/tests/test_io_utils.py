# -*- coding: utf-8 -*-
""" Tests for the utility functions in io_utils module. """

from os.path import dirname, exists, join
from unittest import TestCase
from nose.tools import assert_equal
import h5py

from app_common.apptools.testing_utils import temp_fname

from kromatography.utils.cadet_simulation_builder import build_cadet_input
from kromatography.utils.io_utils import get_hdf5_content, read_from_h5, \
    write_to_h5
from kromatography.model.tests.sample_data_factories import make_sample_study2


ALL_INPUT_KEYS = {'CHROMATOGRAPHY_TYPE', 'discretization', 'model', 'solver',
                  'sensitivity'}

HERE = dirname(__file__)

F1NAME = join(HERE, "Sim__Run_1_cadet_simulation.h5")
F2NAME = join(HERE, "Sim__Run_2_cadet_simulation.h5")


def test_get_hdf5_content():
    with h5py.File(F1NAME, "r") as h5:
        content = get_hdf5_content(h5)
        assert_equal(content.keys(), ['input'])
        # extract the keys from the items tuples
        input_keys = zip(*content['input'])[0]
        assert_equal(set(input_keys), ALL_INPUT_KEYS)

    with h5py.File(F2NAME, "r") as h5:
        content = get_hdf5_content(h5)
        assert_equal(set(content.keys()), {'input', 'meta', 'output'})
        # extract the keys from the items tuples
        input_keys = zip(*content['output'])[0]
        assert_equal(set(input_keys), {'solution'})


class TestReadFromH5(TestCase):

    def setUp(self):
        self.f1name = F1NAME
        self.f2name = F2NAME

    def test_read_root_f1(self):
        # File with input only
        h5_content = read_from_h5(self.f1name)
        self.assertIsInstance(h5_content, dict)
        self.assertGreater(len(h5_content), 1)

        h5_content = read_from_h5(self.f1name, '/output')
        self.assertIsInstance(h5_content, dict)
        self.assertEqual(len(h5_content), 0)

    def test_read_root_f2(self):
        # File with input and output
        h5_content = read_from_h5(self.f2name)
        self.assertIsInstance(h5_content, dict)
        self.assertGreater(len(h5_content), 1)

        h5_content = read_from_h5(self.f2name, '/output/solution')
        self.assertIsInstance(h5_content, dict)
        self.assertNotEqual(len(h5_content), 0)


class TestWriteInputForSim(TestCase):
    def setUp(self):
        study1 = make_sample_study2(add_transp_bind_models=True, add_sims=1)
        self.sim1 = study1.simulations[0]

        study2 = make_sample_study2(add_transp_bind_models=True, add_sims=1,
                                    with_ph_bind=True)
        self.sim2 = study2.simulations[0]

    def test_write_basic_sim_for_cadet(self):
        data_found = self.write_sim_to_input_file_and_check(self.sim1)
        self.assertEqual(data_found[u"adsorption_type"], u'STERIC_MASS_ACTION')
        expected_binding_params = [u'sma_ka', u'sma_kd', u'sma_lambda',
                                   u'sma_nu', u'sma_sigma']
        found_data_names = set(data_found.keys())
        for cadet_item in expected_binding_params:
            self.assertIn(cadet_item, found_data_names)

    def test_write_ph_dependent_sim_for_cadet(self):

        data_found = self.write_sim_to_input_file_and_check(self.sim2)
        self.assertEqual(data_found[u"adsorption_type"],
                         u'EXTERNAL_STERIC_MASS_ACTION_PH')
        found_data_names = set(data_found.keys())
        expected_adsorption_params = [
            u'ext_prof_delta', u'ext_profile', u'ext_velocity', u'extsmaph_ka',
            u'extsmaph_ka_e', u'extsmaph_ka_ee', u'extsmaph_kd',
            u'extsmaph_kd_e', u'extsmaph_kd_ee', u'extsmaph_lambda',
            u'extsmaph_nu', u'extsmaph_nu_p', u'extsmaph_nu_pp',
            u'extsmaph_sigma', u'extsmaph_sigma_p', u'extsmaph_sigma_pp'
        ]
        for cadet_item in expected_adsorption_params:
            self.assertIn(cadet_item, found_data_names)

    # utilities ---------------------------------------------------------------

    def write_sim_to_input_file_and_check(self, sim):
        cadet_input = build_cadet_input(sim)
        output_file = "test.h5"
        with temp_fname(output_file):
            write_to_h5(output_file, cadet_input, root='/input',
                        overwrite=True)
            self.assertTrue(exists(output_file))
            with h5py.File(F1NAME, "r") as h5:
                self.assertEqual(h5.keys(), [u"input"])
                expected = [u'CHROMATOGRAPHY_TYPE', u'discretization',
                            u'model', u'sensitivity', u'solver']
                self.assertEqual(set(h5[u"input"].keys()), set(expected))

            data_found = read_from_h5(output_file)
            return data_found
