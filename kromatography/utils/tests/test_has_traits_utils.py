""" Tests for the utility functions in has_traits_utils module. """

from unittest import TestCase
import numpy as np

from scimath.units.api import UnitArray, UnitScalar
from traits.api import Float, Instance, List, Str

from app_common.traits.custom_trait_factories import ParameterArray, \
    ParameterFloat, ParameterInt, ParameterUnitArray, Parameter

from kromatography.utils.has_traits_utils import \
    search_parameters_in_chrom_data, search_parameters_in_sim
from kromatography.model.tests.sample_data_factories import \
    make_sample_simulation
from kromatography.model.chromatography_data import ChromatographyData

EQUAL = (True, "")

# Standard number of scannable parameters, excluding the source experiment:
NUM_PARAMETERS_STD = 68

# All scannable parameters, not excluding the source experiment:
NUM_PARAMETERS_ALL = 113


class B(ChromatographyData):
    """ Testing class"""
    b_int = ParameterInt()
    name = Str("new B")
    type_id = Str("B")


class A(ChromatographyData):
    """ Testing class"""
    name = Str("new A")
    type_id = Str("A")
    a_int = ParameterInt
    a_float = ParameterFloat
    a_list = List()
    a_array = ParameterArray
    a_uarray = ParameterUnitArray
    a_uscalar = Parameter
    a_chrom_obj = Instance(B)
    a_noparam = Float


class TestSearchParameters(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sim = make_sample_simulation()
        cls.num_comp = len(cls.sim.product.product_components)

    def setUp(self):
        uscal = UnitScalar(1, units="cm")
        uarr = UnitArray([1, 2, 3], units="cm")
        b = B(b_int=3)
        self.data = {"a_int": 1, "a_float": 1., "a_list": range(5),
                     "a_array": np.arange(4), "a_uarray": uarr,
                     "a_uscalar": uscal, "a_chrom_obj": b, "a_noparam": 2.}
        self.chrom_obj = A(**self.data)
        self.expected = ['a_array[0]', 'a_array[1]', 'a_array[2]',
                         'a_array[3]', 'a_uarray[0]', 'a_uarray[1]',
                         'a_uarray[2]', 'a_float', 'a_int', 'a_uscalar',
                         'a_chrom_obj.b_int']

    # -------------------------------------------------------------------------
    # Tests
    # -------------------------------------------------------------------------

    def test_search_parameters_in_simulation(self):
        params = search_parameters_in_chrom_data(self.sim)
        self.assert_all_sim_params_found(params, std_exlude=False)

    def test_search_parameters_in_simulation_specific_func(self):
        params = search_parameters_in_sim(self.sim)
        self.assert_all_sim_params_found(params, std_exlude=True)

    def test_search_parameters_in_simulation_with_filter(self):
        params = search_parameters_in_sim(self.sim,
                                          name_filter="binding_model")
        self.assert_all_sim_bind_params_found(params)
        params2 = search_parameters_in_sim(self.sim, name_filter="ing_mod")
        self.assert_all_sim_bind_params_found(params2)
        params3 = search_parameters_in_sim(self.sim, name_filter="nu")
        # +1 for the cation component:
        self.assertEqual(len(params3), self.num_comp+1)

    # Utilities ---------------------------------------------------------------

    def assert_all_sim_params_found(self, params, std_exlude=False):
        # Complete list
        if std_exlude:
            self.assertEqual(len(params), NUM_PARAMETERS_STD)
        else:
            self.assertEqual(len(params), NUM_PARAMETERS_ALL)

        # No duplicate
        self.assertEqual(len(params), len(set(params)))
        # All params are sub-objects from the sim
        sim_attrs = set(self.sim.trait_names())
        for param in params:
            param_head = param.split(".")[0]
            self.assertIn(param_head, sim_attrs)

    def assert_all_sim_bind_params_found(self, params):
        # Complete list
        self.assertEqual(len(params), 17)
        # No duplicate
        self.assertEqual(len(params), len(set(params)))
        # Complete set:
        expected = ['binding_model.sma_lambda']
        for bind_param in ["nu", "ka", "kd", "sigma"]:
            expected += ['binding_model.sma_{}[{}]'.format(bind_param, i)
                         for i in range(self.num_comp+1)]

        self.assertEqual(set(params), set(expected))
