""" Tests for the BindingModel classes. """

from unittest import TestCase
import numpy as np
from numpy.testing import assert_array_almost_equal

from kromatography.model.binding_model import ExternalLangmuir, Langmuir, \
    LANGMUIR_BINDING_MODEL, PH_LANGMUIR_BINDING_MODEL, \
    PH_STERIC_BINDING_MODEL, PhDependentStericMassAction, \
    STERIC_BINDING_MODEL, StericMassAction

from kromatography.utils.assertion_utils import assert_has_traits_almost_equal


class TestStericMassAction(TestCase):

    def setUp(self):
        self.num_comps = 4
        self.model = StericMassAction(self.num_comps, name="test")
        self.attrs = ['sma_kd', 'sma_nu', 'sma_sigma']
        self.model_type = STERIC_BINDING_MODEL
        self.model_klass = StericMassAction

    # -------------------------------------------------------------------------
    # Tests
    # -------------------------------------------------------------------------
    def test_vector_lengths(self):
        for attr_name in self.attrs:
            self.assertEqual(len(getattr(self.model, attr_name)),
                             self.num_comps)

    def test_default_values(self):
        self.assertEqual(self.model.model_type, self.model_type)
        self.assertEqual(self.model.is_kinetic, 0)
        assert_array_almost_equal(self.model.sma_ka, np.ones(self.num_comps))
        assert_array_almost_equal(self.model.sma_kd, np.ones(self.num_comps))
        assert_array_almost_equal(self.model.sma_nu,
                                  np.ones(self.num_comps) * 5)
        assert_array_almost_equal(self.model.sma_sigma,
                                  np.ones(self.num_comps) * 100)

    def test_create_with_num_prod_comp(self):
        mod2 = self.model_klass(num_prod_comp=self.num_comps-1, name="test")
        assert_has_traits_almost_equal(self.model, mod2)


class TestPhDependentStericMassAction(TestStericMassAction):

    def setUp(self):
        super(TestPhDependentStericMassAction, self).setUp()
        self.model = PhDependentStericMassAction(self.num_comps, name="test")
        self.vector_attr_list = ['sma_kd', 'sma_nu', 'sma_sigma', 'sma_ka_ph',
                                 'sma_ka_ph2', 'sma_kd_ph', 'sma_kd_ph2',
                                 'sma_nu_ph', 'sma_sigma_ph']
        self.model_type = PH_STERIC_BINDING_MODEL
        self.model_klass = PhDependentStericMassAction

    # -------------------------------------------------------------------------
    # Tests
    # -------------------------------------------------------------------------

    def test_default_values(self):
        super(TestPhDependentStericMassAction, self).test_default_values()
        ph_dep_attrs = ['sma_ka_ph', 'sma_ka_ph2', 'sma_kd_ph', 'sma_kd_ph2',
                        'sma_nu_ph', 'sma_sigma_ph']
        for attr in ph_dep_attrs:
            assert_array_almost_equal(getattr(self.model, attr),
                                      np.zeros(self.num_comps))


class TestLangmuir(TestStericMassAction):

    def setUp(self):
        self.num_comps = 4
        self.model = Langmuir(self.num_comps, name="test")
        self.model_type = LANGMUIR_BINDING_MODEL
        self.model_klass = Langmuir
        self.attrs = ['mcl_ka', 'mcl_kd', 'mcl_qmax']

    # -------------------------------------------------------------------------
    # Tests
    # -------------------------------------------------------------------------

    def test_default_values(self):
        self.assertEqual(self.model.model_type, self.model_type)
        self.assertEqual(self.model.is_kinetic, 0)
        for attr in self.attrs:
            if attr.endswith("kd"):
                self.assertEqual(getattr(self.model, attr).sum(),
                                 self.num_comps)
            else:
                self.assertEqual(getattr(self.model, attr).sum(), 0)


class TestExternalLangmuir(TestLangmuir):

    def setUp(self):
        self.num_comps = 4
        self.model = ExternalLangmuir(self.num_comps, name="test")

        self.attrs = ['mcl_ka', 'extl_ka_t', 'extl_ka_tt',
                      'extl_ka_ttt', 'mcl_kd', 'extl_kd_t', 'extl_kd_tt',
                      'extl_kd_ttt', 'mcl_qmax', 'extl_qmax_t',
                      'extl_qmax_tt', 'extl_qmax_ttt']
        self.model_type = PH_LANGMUIR_BINDING_MODEL
        self.model_klass = ExternalLangmuir
