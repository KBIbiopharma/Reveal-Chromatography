from unittest import TestCase
from traits.testing.unittest_tools import UnittestTools

from kromatography.ui.factories.binding_model import BindingModelBuilder
from kromatography.model.binding_model import BINDING_MODEL_TYPES, KLASS_MAP, \
    PhDependentStericMassAction, STERIC_BINDING_MODEL, StericMassAction


class TestBindingModelBuilder(TestCase, UnittestTools):
    def setUp(self):
        from kromatography.ui.api import register_all_data_views
        register_all_data_views()

    def test_create(self):
        builder = BindingModelBuilder(_target_component_names=["Cation", "a"])
        self.assertIsInstance(builder.model, StericMassAction)

    def create_failed_without_compoennts(self):
        builder = BindingModelBuilder()
        with self.assertRaises(ValueError):
            builder.model

    def test_bringup_with_sma(self):
        builder = BindingModelBuilder(_target_component_names=["Cation", "a"])
        ui = builder.edit_traits()
        ui.dispose()

    def test_bringup_all_types(self):
        for model_type in BINDING_MODEL_TYPES:
            builder = BindingModelBuilder(
                _target_component_names=["Cation", "a"],
                binding_model_type=model_type
            )
            ui = builder.edit_traits()
            ui.dispose()

    def test_change_model_type(self):
        # By default, an SMA model is built:
        builder = BindingModelBuilder(_target_component_names=["Cation", "a"])
        self.assertEqual(builder.model.model_type, STERIC_BINDING_MODEL)
        self.assertIsInstance(builder.model, StericMassAction)
        self.assertFalse(isinstance(builder.model,
                                    PhDependentStericMassAction))

        # The type can be changed live, and the model updates:
        for model_type, klass in KLASS_MAP.items():
            if model_type == STERIC_BINDING_MODEL:
                continue

            with self.assertTraitChanges(builder, "model"):
                with self.assertTraitChanges(builder, "active_model_view"):
                    builder.binding_model_type = model_type
                    self.assertIsInstance(builder.model, klass)
