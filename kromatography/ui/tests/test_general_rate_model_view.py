from unittest import TestCase

from kromatography.model.tests.sample_data_factories import \
    make_sample_transport_model
from kromatography.ui.tests.base_model_view_test_case import \
    BaseComponentArrayView, BaseModelViewTestCase


class TestGeneralRateModelView(BaseModelViewTestCase, BaseComponentArrayView,
                               TestCase):
    """ Run all BaseModelViewTestCase tests for a GRM view.
    """

    def setUp(self):
        # Register all views
        BaseModelViewTestCase.setUp(self)
        self.model = make_sample_transport_model()
        self.model_attr_to_test = "film_mass_transfer"
