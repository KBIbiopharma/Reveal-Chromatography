""" Tests for the SolutionWithProduct Class. """

from unittest import TestCase
import numpy as np

from scimath.units.api import UnitArray, UnitScalar
from scimath.units.dimensionless import percent
from traits.api import TraitError
from traits.testing.unittest_tools import UnittestTools

from app_common.scimath.assertion_utils import assert_unit_array_almost_equal,\
    assert_unit_array_not_almost_equal, assert_unit_scalar_almost_equal
from app_common.apptools.assertion_utils import flexible_assert_equal

from kromatography.model.solution_with_product import SolutionWithProduct
from kromatography.utils.chromatography_units import gram_per_liter
from kromatography.model.tests.example_model_data import \
    SOLUTIONWITHPRODUCT_LOAD, SOLUTIONWITHPRODUCT_LOAD_WITH_STRIP, \
    SOLUTIONWITHPRODUCT_POOL


class TestSolutionWithProductLoad(TestCase):

    def setUp(self):
        self.load = SolutionWithProduct(**SOLUTIONWITHPRODUCT_LOAD)

    # -------------------------------------------------------------------------
    # Tests
    # -------------------------------------------------------------------------
    def test_invalid_construction(self):
        with self.assertRaises(ValueError):
            self.load = SolutionWithProduct()

    def test_construction_load(self):
        load = self.load
        for key, value in SOLUTIONWITHPRODUCT_LOAD.items():
            flexible_assert_equal(getattr(load, key), value, msg=key)

        self.assertEqual(load.unique_id, {'name': load.name})

    def test_no_set_prod_comp_conc(self):
        load = self.load
        new_prod_comp_conc = UnitArray([1.20, 0.50, 1.304],
                                       units=gram_per_liter)
        assert_unit_array_not_almost_equal(
            load.product_component_concentrations,
            new_prod_comp_conc
        )

    def test_product_component_conc_calc(self):
        load = self.load
        load_conc_units = load.product_concentration.units
        expt_concentrations = UnitArray(
            [0.07896, 0.82908, 0.03195718], units=load_conc_units
        )
        assert_unit_array_almost_equal(
            load.product_component_concentrations,
            expt_concentrations,
            atol=1e-5
        )

    def test_product_concentration(self):
        load = self.load
        comp_conc_sum = load.product_component_concentrations.sum()
        self.assertAlmostEqual(comp_conc_sum.tolist(),
                               load.product_concentration.tolist(), places=4)
        self.assertEqual(load.product_component_concentrations.units,
                         load.product_concentration.units)

    def test_product_component_purity_calc(self):
        load = self.load
        load_conc_units = load.product_concentration.units
        expt_concentrations = UnitArray(
            [0.07896, 0.82908, 0.03195718], units=load_conc_units
        )
        expt_purities = expt_concentrations / load.product_concentration * 100
        expt_purities = UnitArray(expt_purities, units=percent)
        assert_unit_array_almost_equal(
            load.product_component_purities, expt_purities, atol=1e-5
        )

    def test_impurity_conc_calc(self):
        load = self.load
        expt_concentrations = UnitArray(
            [0.00319, 0.00319], units=load.product_concentration.units
        )
        assert_unit_array_almost_equal(
            load.impurity_concentrations,
            expt_concentrations,
            atol=1e-5
        )

    def test_anion_concentration(self):
        load = self.load
        concentration_unit = load.chemical_component_concentrations.units
        expt_concentration = UnitScalar(37, units=concentration_unit)
        assert_unit_array_almost_equal(load.anion_concentration,
                                       expt_concentration, atol=1e-5)

    def test_cation_concentration(self):
        load = self.load
        concentration_unit = load.chemical_component_concentrations.units
        expt_concentration = UnitScalar(30, units=concentration_unit)
        assert_unit_array_almost_equal(load.cation_concentration,
                                       expt_concentration, atol=1e-5)


class TestSolutionWithProductStripHandling(TestCase, UnittestTools):

    def setUp(self):
        self.load_no_strip = SolutionWithProduct(**SOLUTIONWITHPRODUCT_LOAD)
        self.load = SolutionWithProduct(**SOLUTIONWITHPRODUCT_LOAD_WITH_STRIP)

    def test_get_strip_fraction(self):
        assert_unit_scalar_almost_equal(self.load.strip_mass_fraction,
                                        UnitScalar(0.0, units='%'))

    def test_get_strip_fraction_no_strip_comp(self):
        self.assertTrue(np.isnan(self.load_no_strip.strip_mass_fraction[()]))

    def test_set_strip_fraction(self):
        self.load.strip_mass_fraction = UnitScalar(10.0, units='%')
        assert_unit_scalar_almost_equal(self.load.strip_mass_fraction,
                                        UnitScalar(10.0, units='%'))

    def test_set_strip_fraction_triggers_event(self):
        # THis is important to make sure the UI updates itself:
        with self.assertTraitChanges(self.load, "_strip_fraction_updated"):
            self.load.strip_mass_fraction = UnitScalar(10.0, units='%')

    def test_set_strip_fraction_no_strip_comp(self):
        self.load_no_strip.strip_mass_fraction = UnitScalar(10.0, units='%')
        # Doesn't change the fact that we can't ask for it:
        self.assertTrue(np.isnan(self.load_no_strip.strip_mass_fraction[()]))


class TestSolutionWithProductPool(TestCase):

    def setUp(self):
        self.pool = SolutionWithProduct(**SOLUTIONWITHPRODUCT_POOL)

    # -------------------------------------------------------------------------
    # Tests
    # -------------------------------------------------------------------------

    def test_construction_pool(self):
        pool = self.pool
        for key, value in SOLUTIONWITHPRODUCT_POOL.items():
            flexible_assert_equal(getattr(pool, key), value, msg=key)

        self.assertEqual(pool.unique_id, {'name': pool.name})

    def test_set_prod_comp_conc(self):
        pool = self.pool
        new_prod_comp_conc = UnitArray([1.20, 0.50, 1.304],
                                       units=gram_per_liter)
        pool.product_component_concentrations = new_prod_comp_conc
        assert_unit_array_almost_equal(pool.product_component_concentrations,
                                       new_prod_comp_conc)

    def test_product_component_purity_calc(self):
        pool = self.pool
        pool_conc_units = pool.product_concentration.units
        sim_concentrations = UnitArray([0.1, 0.25, 0.05],
                                       units=pool_conc_units)
        pool.product_component_concentrations = sim_concentrations
        sim_purities = sim_concentrations / pool.product_concentration * 100
        sim_purities = UnitArray(sim_purities, units=percent)
        assert_unit_array_almost_equal(
            pool.product_component_purities, sim_purities, atol=1e-5
        )

    def test_validate_prod_comp_conc(self):
        pool = self.pool
        new_prod_comp_conc = UnitArray([1.20, 0.50], units=gram_per_liter)
        with self.assertRaises(TraitError):
            pool.product_component_concentrations = new_prod_comp_conc

    def test_product_component_assays_exps1(self):
        self.pool.product_concentration = UnitScalar(1.0, units=gram_per_liter)
        self.pool.product_component_concentrations = \
            UnitArray([0.2, 0.3, 0.5], units=gram_per_liter)
        assay_percentages = self.pool.compute_assays('product_component',
                                                     self.pool.product)
        self.assertEqual(sum(assay_percentages), 100.0,
                         msg="Assay results sum !=100")
