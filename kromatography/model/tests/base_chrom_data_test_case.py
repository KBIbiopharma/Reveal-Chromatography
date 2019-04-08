

class BaseChromDataTestCase(object):
    """ Base class to define general tests for all ChromData models.
    """

    def setUp(self):
        """ Define the model attribute
        """
        raise NotImplementedError()

    def test_unique_id(self):
        """ Force the creation of the unique_id
        """
        self.assertIsInstance(self.model.unique_id, dict)
        for key, val in self.model.unique_id.items():
            self.assertIsInstance(key, basestring)
            self.assertIsInstance(val, (basestring, dict))
