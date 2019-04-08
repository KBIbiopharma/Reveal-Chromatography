from unittest import TestCase

from kromatography.model.factories.binding_model import \
    create_binding_model
from kromatography.model.binding_model import StericMassAction, Langmuir, \
    ExternalLangmuir, PhDependentStericMassAction, LANGMUIR_BINDING_MODEL, \
    PH_LANGMUIR_BINDING_MODEL, PH_STERIC_BINDING_MODEL, STERIC_BINDING_MODEL


class TestBuildBindingModel(TestCase):

    def test_fail_creation_no_num_comp(self):
        with self.assertRaises(ValueError):
            create_binding_model(0)
        with self.assertRaises(ValueError):
            create_binding_model(1)

    def test_build_default_binding_model(self):
        # Default is SMA:
        for i in range(2, 10):
            model = create_binding_model(i)
            self.assertIsInstance(model, StericMassAction)

    def test_fail_build_sma_binding_model(self):
        # Can't create an SMA model with 1 component: no prod comp:
        with self.assertRaises(ValueError):
            create_binding_model(1, model_type=STERIC_BINDING_MODEL)

    def test_build_langmuir_binding_model(self):
        for i in range(1, 10):
            model = create_binding_model(i, model_type=LANGMUIR_BINDING_MODEL)
            self.assertIsInstance(model, Langmuir)

    def test_fail_build_langmuir_binding_model(self):
        # Can't create an SMA model with 1 component: no prod comp:
        with self.assertRaises(ValueError):
            create_binding_model(0, model_type=LANGMUIR_BINDING_MODEL)

    def test_build_ph_sma_binding_model(self):
        for i in range(2, 10):
            model = create_binding_model(i, model_type=PH_STERIC_BINDING_MODEL)
            self.assertIsInstance(model, PhDependentStericMassAction)

    def test_build_ph_langmuir_binding_model(self):
        for i in range(1, 10):
            model = create_binding_model(i,
                                         model_type=PH_LANGMUIR_BINDING_MODEL)
            self.assertIsInstance(model, ExternalLangmuir)
