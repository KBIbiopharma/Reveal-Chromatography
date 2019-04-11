from unittest import TestCase

from kromatography.ui.tests.base_model_view_test_case import \
    BaseComponentArrayView, BaseModelViewTestCase
from kromatography.model.tests.sample_data_factories import \
    make_sample_binding_model


class TestStericMassActionModelView(BaseModelViewTestCase,
                                    BaseComponentArrayView, TestCase):
    """ Run all StericMassActionModelView tests for a SMA model view.
    """

    def setUp(self):
        # Register all views
        BaseModelViewTestCase.setUp(self)
        self.model = make_sample_binding_model()
        self.model_attr_to_test = "sma_ka"
