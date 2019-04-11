""" Tests for the CADETSimulationExecutor class. """

from os.path import join
import shutil
import tempfile
import unittest

from kromatography.utils.testing_utils import model_data_path
from kromatography.solve.cadet_executor import (
    CADETExecutor, InvalidExecutorError
)


class BaseCadetExecutorTests(object):
    """ Base class test test any cadet executor.
    """
    def setUp(self):
        source_file = model_data_path('cadet_inputs.h5')

        # copy the example dataset into temp dir for testing to avoid
        # modifying the example dataset.
        self.tmpdir = tempfile.mkdtemp()
        self.input_file = join(self.tmpdir, 'cadet_inputs.h5')
        shutil.copyfile(source_file, self.input_file)

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    # -------------------------------------------------------------------------
    # Tests
    # -------------------------------------------------------------------------
    def test_simulation_execution(self):
        runner = self.executor
        results = runner.execute(self.input_file)
        self.assertEqual(results['output_file'], self.input_file)
        self.assertNotEqual(results["cadet_output"], "")
        self.assertEqual(results["exception"], "")
        self.assertEqual(results["return_code"], 0)
        self.assertEqual(results["cadet_errors"], 0)

    def test_failed_simulation_execution(self):
        runner = self.executor
        results = runner.execute('BAD FILE NAME')
        exception = results["exception"]
        self.assertTrue(exception.startswith('Input file not found'))
        self.assertEqual(results["cadet_output"], "")

    def test_invalid_binary(self):
        with self.assertRaises(InvalidExecutorError):
            self.executor_class(cadet_binary='blah')


class TestCadetExecutor(unittest.TestCase):
    def setUp(self):
        super(TestCadetExecutor, self).setUp()
        self.executor_class = CADETExecutor
        self.executor = CADETExecutor()
