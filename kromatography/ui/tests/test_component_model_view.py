from unittest import TestCase

from kromatography.model.data_source import SimpleDataSource
from kromatography.ui.tests.base_model_view_test_case import \
    BaseModelViewTestCase


class TestComponentView(BaseModelViewTestCase, TestCase):
    """ Run all BaseModelViewTestCase for a Component model
    """

    def setUp(self):
        # Regist the views
        BaseModelViewTestCase.setUp(self)

        s = SimpleDataSource()
        self.model = s.get_object_of_type('components', 'Acetate')
