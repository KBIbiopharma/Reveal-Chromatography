from unittest import TestCase

from app_common.apptools.testing_utils import temp_bringup_ui_for

from kromatography.ui.simulation_selector import BaseSimulationSelector, \
    SingleSimulationSelector, SingleSimulationGroupSelector
from kromatography.utils.testing_utils import io_data_path
from kromatography.io.api import load_study_from_project_file

STUDY_FNAME = io_data_path("demo_final_statev0.7.2.chrom")

STUDY = load_study_from_project_file(STUDY_FNAME)


class TestBaseSimulationSelector(TestCase):
    def test_creation_base_selector(self):
        selector = BaseSimulationSelector(study=STUDY)
        self.assertEqual(selector.simulation_names_available, ["Sim: Run_1"])
        self.assertEqual(selector.simulation_group_names_available,
                         ["New SimulationGroup"])

    def test_bringup(self):
        selector = BaseSimulationSelector(study=STUDY)
        with temp_bringup_ui_for(selector):
            pass


class TestSimulationSelector(TestCase):
    def test_bringup(self):
        selector = SingleSimulationSelector(study=STUDY)
        with temp_bringup_ui_for(selector):
            pass


class TestSimulationGroupSelector(TestCase):
    def test_bringup(self):
        selector = SingleSimulationGroupSelector(study=STUDY)
        with temp_bringup_ui_for(selector):
            pass
