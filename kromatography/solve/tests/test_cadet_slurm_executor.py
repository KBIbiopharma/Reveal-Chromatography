""" Tests for the SLURM based CADETExecutor class.
"""

from unittest import skipUnless, TestCase
from app_common.std_lib.sys_utils import IS_LINUX

from kromatography.solve.slurm_cadet_executor import check_slurm_installed, \
    SlurmCADETExecutor
from kromatography.solve.tests.test_cadet_simulation_executor import \
    BaseCadetExecutorTests

slurm_installed = check_slurm_installed(executable="sbatch")


@skipUnless(IS_LINUX, "Not linux environment: SLURM can't be available.")
class TestCadetExecutor(TestCase, BaseCadetExecutorTests):
    def setUp(self):
        super(TestCadetExecutor, self).setUp()
        self.executor_class = SlurmCADETExecutor
        self.executor = self.executor_class()
