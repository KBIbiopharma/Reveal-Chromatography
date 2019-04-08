from unittest import TestCase
from pandas import Series
from pandas.util.testing import assert_series_equal

from scimath.units.api import UnitScalar

from app_common.apptools.testing_utils import temp_bringup_ui_for
from app_common.traits.assertion_utils import assert_has_traits_almost_equal

from kromatography.ui.factories.product import ComponentDescription, Product,\
    ProductBuilder, ProductComponentAssay
from kromatography.model.data_source import SimpleDataSource
from kromatography.utils.string_definitions import STRIP_COMP_NAME
import kromatography.utils.chromatography_units as chr_units
from kromatography.model.factories.product import add_strip_to_product

ext_coef_units = chr_units.extinction_coefficient_unit


class TestProductBuilder(TestCase):
    def setUp(self):
        self.ds = SimpleDataSource()
        self.builder = ProductBuilder(datasource=self.ds)

    def test_bring_up(self):
        self.builder.expert_mode = False
        with temp_bringup_ui_for(self.builder):
            pass

        self.builder.expert_mode = True
        with temp_bringup_ui_for(self.builder):
            pass

    def test_default_attributes(self):
        self.assertFalse(self.builder.expert_mode)
        # Default target product not known in default datasource
        known_products = {comp.target_product for comp in
                          self.ds.get_objects_by_type("product_components")}
        self.assertNotIn(self.builder.name, known_products)
        # Therefore, there are no candidate components:
        self.assertEqual(self.builder._component_candidates_names, [])

    def test_build_product_fail_no_type(self):
        prod = self.builder.build_product(allow_ui=False)
        self.assertIsNone(prod)

    def test_build_product_empty_default(self):
        self.builder.product_type = "Globular"
        prod = self.builder.build_product(allow_ui=False)
        self.assertIsInstance(prod, Product)
        self.assertEqual(len(prod.product_components), 1)
        comp = prod.product_components[0]
        self.assertEqual(comp.name, STRIP_COMP_NAME)
        self.assertEqual(comp.target_product, prod.name)

    def test_build_product_empty_no_strip(self):
        self.builder.product_type = "Globular"
        self.builder.add_strip = False
        prod = self.builder.build_product(allow_ui=False)
        self.assertIsInstance(prod, Product)
        self.assertEqual(prod.product_components, [])

    def test_build_product_empty_expert_mode(self):
        self.builder.product_type = "Globular"
        self.builder.expert_mode = True
        prod = self.builder.build_product(allow_ui=False)
        self.assertIsInstance(prod, Product)
        self.assertEqual(prod.product_components, [])

    def test_build_product_with_comp_expert_mode(self):
        """ Test that builder in expert mode can rebuild PROD000.
        """
        original_prod0 = self.ds.get_objects_by_type("products",
                                                     {"name": "Prod000"})[0]
        comp_names = [c.name for c in original_prod0.product_components]

        self.builder.name = "Prod000"
        self.builder.product_type = "Globular"
        self.builder.pI = UnitScalar(7.52, units='1')
        self.builder.expert_mode = True

        # In expert mode, we set the list of assay names and component names
        # and expressions:
        for name in comp_names:
            assay_name = "CEX_{}".format(name)
            exp = "product_concentration * {} / 100".format(assay_name)
            comp_desc = ComponentDescription(name=name,
                                             concentration_exps=exp)
            self.builder.component_descs.append(comp_desc)
            assay = ProductComponentAssay(name=assay_name)
            self.builder.component_assay_names.append(assay)

        prod = self.builder.build_product(allow_ui=False)
        ignore = ["amino_acids", "amino_acid_numbers"]
        assert_has_traits_almost_equal(prod, original_prod0,
                                       ignore=ignore)

        # In expert mode, add_strip is ignored:
        self.builder.add_strip = True
        prod = self.builder.build_product(allow_ui=False)
        ignore = ["amino_acids", "amino_acid_numbers"]
        assert_has_traits_almost_equal(prod, original_prod0,
                                       ignore=ignore)

    def test_build_product_with_comp_simplified_mode(self):
        """ Modify PROD000 and make sure builder can rebuild it (no strip).

        Simplify its component and assay names, and make sure the simplified
        builder with add_strip=False can rebuild it.
        """
        orig_prod0 = self.ds.get_objects_by_type("products",
                                                 {"name": "Prod000"})[0]
        comp_names = [c.name for c in orig_prod0.product_components]
        # Change the assays to be named like the components since the
        # simplified mode only supports that:
        orig_assays = ['CEX_Acidic_2', 'CEX_Acidic_1', 'CEX_Native']
        self.assertEqual(orig_prod0.product_component_assays, orig_assays)
        orig_prod0.product_component_assays = comp_names
        exps = ["product_concentration * CEX_{} / 100".format(name)
                for name in comp_names]
        orig_conc_exps = Series(exps, index=comp_names)
        assert_series_equal(orig_prod0.product_component_concentration_exps,
                            orig_conc_exps)
        new_exps = ["product_concentration * {} / 100".format(name)
                    for name in comp_names]
        orig_prod0.product_component_concentration_exps = \
            Series(new_exps, index=comp_names)

        self.builder.name = "Prod000"
        self.builder.product_type = "Globular"
        self.builder.pI = UnitScalar(7.52, units='1')
        self.builder.expert_mode = False
        self.builder.add_strip = False

        # In simplified mode, we just set a list of component names:
        for name in comp_names:
            comp_desc = ComponentDescription(name=name)
            self.builder.component_descs.append(comp_desc)

        prod = self.builder.build_product(allow_ui=False)
        ignore = ["amino_acids", "amino_acid_numbers"]
        assert_has_traits_almost_equal(prod, orig_prod0,
                                       ignore=ignore)

    def test_build_product_with_comp_simplified_mode_with_strip(self):
        """ Modify PROD000 and make sure builder can rebuild it (with strip).

        Add a strip to it, and change its component and assay names, and make
        sure the simplified building with the add_strip=True.
        """
        orig_prod0 = self.ds.get_objects_by_type("products",
                                                 {"name": "Prod000"})[0]
        comp_names = [c.name for c in orig_prod0.product_components]
        # Change the assays to be named like the components since the
        # simplified mode only supports that:
        orig_prod0.product_component_assays = comp_names
        new_exps = ["product_concentration * {} / 100".format(name)
                    for name in comp_names]
        orig_prod0.product_component_concentration_exps = \
            Series(new_exps, index=comp_names)

        # Modify the prod to add a strip
        new_prod, strip_comp = add_strip_to_product(orig_prod0)

        # Rebuild prod0 with the builder:
        self.builder.name = new_prod.name
        self.builder.product_type = "Globular"
        self.builder.pI = UnitScalar(7.52, units='1')
        self.builder.expert_mode = False
        self.builder.add_strip = True

        for comp in new_prod.product_components:
            name = comp.name
            if name != STRIP_COMP_NAME:
                self.ds.set_object_of_type("product_components", comp)
                comp_desc = ComponentDescription(name=name)
                self.builder.component_descs.append(comp_desc)

        prod = self.builder.build_product(allow_ui=False)
        ignore = ["amino_acids", "amino_acid_numbers", "name"]
        assert_has_traits_almost_equal(prod, new_prod, ignore=ignore)
