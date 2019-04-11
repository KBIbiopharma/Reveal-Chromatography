from unittest import TestCase

from kromatography.model.tests.example_model_data import BUFFER_ELUTION
from kromatography.ui.tests.base_model_view_test_case import \
    BaseModelViewTestCase
from kromatography.model.buffer import Buffer


class TestBufferView(BaseModelViewTestCase, TestCase):
    """ Run all BaseModelViewTestCase + special tests for a Buffer view.
    """

    def setUp(self):
        # This registers all views defined in kromatography/ui/adapters/api.py
        BaseModelViewTestCase.setUp(self)
        self.model = Buffer(**BUFFER_ELUTION)
