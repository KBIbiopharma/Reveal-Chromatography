from unittest import TestCase

from kromatography.ui.tests.base_model_view_test_case import \
    BaseComponentArrayView, BaseModelViewTestCase
from kromatography.model.tests.sample_data_factories import \
    make_sample_binding_model


class TestPhDepenentStericMassActionModelView(BaseModelViewTestCase,
                                              BaseComponentArrayView,
                                              TestCase):
    """ Run all BaseModelViewTestCase tests for a ph-dependent SMA model view.
    """

    def setUp(self):
        # Register all views
        BaseModelViewTestCase.setUp(self)
        self.model = make_sample_binding_model(ph_dependence=True)
        self.model_attr_to_test = "sma_ka"
