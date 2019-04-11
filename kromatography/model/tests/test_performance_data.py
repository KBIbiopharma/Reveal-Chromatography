from unittest import TestCase

from scimath.units.api import UnitArray
from traits.testing.unittest_tools import UnittestTools

from kromatography.model.performance_data import PerformanceData
from kromatography.model.solution_with_product import SolutionWithProduct
from kromatography.utils.chromatography_units import gram_per_liter
from kromatography.model.tests.example_model_data import \
    SOLUTIONWITHPRODUCT_POOL


class TestPerformanceData(TestCase, UnittestTools):
    def setUp(self):
        self.pool = SolutionWithProduct(**SOLUTIONWITHPRODUCT_POOL)

    def test_create(self):
        PerformanceData(name="New Perf", pool=self.pool)

    def test_update_purity_string(self):
        perf_data = PerformanceData(name="New Perf", pool=self.pool)
        prod_comp_conc = UnitArray([0.1, 0.25, 0.05], units=gram_per_liter)
        with self.assertTraitChanges(perf_data, "pool_purities", 1):
            self.pool.product_component_concentrations = prod_comp_conc

        self.assertIsInstance(perf_data.pool_purities, str)
        purities = prod_comp_conc / self.pool.product_concentration * 100
        for purity in purities:
            self.assertIn(str(purity), perf_data.pool_purities)

        self.assertIn("%", perf_data.pool_purities)
