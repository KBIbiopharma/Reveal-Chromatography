from unittest import TestCase

from kromatography.model.factories.transport_model import \
    create_transport_model
from kromatography.model.transport_model import GeneralRateModel


class TestBuildTransportModel(TestCase):

    def test_fail_creation_no_num_comp(self):
        with self.assertRaises(ValueError):
            create_transport_model(0)
        with self.assertRaises(ValueError):
            create_transport_model(1)

    def test_build_transport_model(self):
        for i in range(2, 10):
            model = create_transport_model(i)
            self.assertIsInstance(model, GeneralRateModel)
