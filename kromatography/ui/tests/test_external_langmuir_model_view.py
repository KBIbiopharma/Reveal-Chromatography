from unittest import TestCase

from kromatography.ui.tests.base_model_view_test_case import \
    BaseComponentArrayView, BaseModelViewTestCase
from kromatography.model.tests.sample_data_factories import \
    make_sample_langmuir_binding_model


class TestLangmuirModelView(BaseModelViewTestCase, BaseComponentArrayView,
                            TestCase):
    """ LangmuirModelView tests.
    """

    def setUp(self):
        # Register all views
        BaseModelViewTestCase.setUp(self)
        self.model = make_sample_langmuir_binding_model()
        self.model_attr_to_test = "mcl_ka"


class TestExternalLangmuirModelView(BaseModelViewTestCase,
                                    BaseComponentArrayView, TestCase):
    """ ExternalLangmuirModelView tests.
    """
    def setUp(self):
        # Register all views
        BaseModelViewTestCase.setUp(self)
        self.model = make_sample_langmuir_binding_model(ph_dependence=True)
        self.model_attr_to_test = "mcl_ka"
