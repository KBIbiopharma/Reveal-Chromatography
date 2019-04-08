from unittest import TestCase

from kromatography.model.tests.sample_data_factories import (
    make_sample_experiment, make_sample_simulation,
    make_sample_simulation_group, make_sample_simulation2, make_sample_study
)
from kromatography.model.study import Study
from kromatography.model.experiment import Experiment
from kromatography.model.simulation import Simulation
from kromatography.model.simulation_group import SimulationGroup
from kromatography.utils.testing_utils import io_data_path


class BaseTestDataMaker(object):
    def setUp(self):
        raise NotImplementedError("Base class")

    def test_instance(self):
        self.assertIsInstance(self.model, self.klass)


class TestStudyMaker(BaseTestDataMaker, TestCase):
    def setUp(self):
        self.model = make_sample_study()
        self.klass = Study


class TestSimulationMaker(BaseTestDataMaker, TestCase):
    def setUp(self):
        self.model = make_sample_simulation()
        self.klass = Simulation

    def test_simulation_with_results(self):
        res_file = io_data_path("Chrom_Example_Run_1_cadet_simulation.h5")
        model = make_sample_simulation(name='Run_1', result_file=res_file)
        self.assertIsInstance(model, Simulation)

    def test_simulation2(self):
        model = make_sample_simulation2()
        self.assertIsInstance(model, Simulation)


class TestExperimentMaker(BaseTestDataMaker, TestCase):
    def setUp(self):
        self.model = make_sample_experiment()
        self.klass = Experiment


class TestSimGroupMaker(BaseTestDataMaker, TestCase):
    def setUp(self):
        self.model = make_sample_simulation_group()
        self.klass = SimulationGroup
