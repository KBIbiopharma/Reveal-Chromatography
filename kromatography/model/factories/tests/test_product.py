from unittest import TestCase

from scimath.units.api import UnitScalar

from kromatography.model.factories.product import add_strip_to_product
from kromatography.utils.assertion_utils import assert_unit_scalar_almost_equal
from kromatography.utils.chromatography_units import \
    extinction_coefficient_unit, gram_per_mol, kilogram_per_mol
from kromatography.utils.string_definitions import STRIP_COMP_NAME
from kromatography.utils.api import load_default_user_datasource


class TestAddStripToProduct(TestCase):
    def test_add_strip_to_product(self):
        ds = load_default_user_datasource()[0]
        prod0 = ds.get_object_of_type("products", "Prod000")
        new_prod, new_comp = add_strip_to_product(prod0, 18.8, 0.75)
        self.assert_new_prod_valid(prod0, new_prod, new_comp)

    def test_add_strip_to_product_pass_unitscalar(self):
        ds = load_default_user_datasource()[0]
        prod0 = ds.get_object_of_type("products", "Prod000")
        new_prod, new_comp = add_strip_to_product(
            prod0, UnitScalar(18.8e3, units=gram_per_mol),
            UnitScalar(0.75, units=extinction_coefficient_unit)
        )
        self.assert_new_prod_valid(prod0, new_prod, new_comp)

    # Helper methods ----------------------------------------------------------

    def assert_new_prod_valid(self, source_prod, new_prod, new_comp):
        self.assertEqual(new_comp.name, STRIP_COMP_NAME)
        assert_unit_scalar_almost_equal(
            new_comp.molecular_weight, UnitScalar(18.8, units=kilogram_per_mol)
        )
        assert_unit_scalar_almost_equal(
            new_comp.extinction_coefficient,
            UnitScalar(0.75, units=extinction_coefficient_unit)
        )

        self.assertIn(source_prod.name, new_prod.name)
        self.assertIn(new_comp, new_prod.product_components)
        for other_comp_name in source_prod.product_component_names:
            new_exps = new_prod.product_component_concentration_exps
            self.assertIn("(100 - {})".format(STRIP_COMP_NAME),
                          new_exps[other_comp_name])

        for comp in new_prod.product_components:
            self.assertEqual(comp.target_product, new_prod.name)
