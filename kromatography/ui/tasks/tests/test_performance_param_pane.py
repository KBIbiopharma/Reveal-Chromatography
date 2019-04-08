from unittest import TestCase

from kromatography.utils.testing_utils import load_study_with_exps_and_ran_sims
from kromatography.model.kromatography_project import KromatographyProject
from kromatography.ui.tasks.performance_param_pane import PerformanceParamPane
from kromatography.model.study import add_sims_from_exp_to_study

from app_common.apptools.testing_utils import temp_bringup_ui_for


class TestPerformanceParamPane(TestCase):

    def setUp(self):
        study = load_study_with_exps_and_ran_sims()
        self.project = KromatographyProject(study=study)
        self.perf_param_pane = PerformanceParamPane(study=self.project.study)

    def test_updated_when_sim_added(self):
        # test current perf_param data model
        self.assertEqual(len(self.perf_param_pane.performance_data), 2)
        exp_name = self.project.study.experiments[0].name
        add_sims_from_exp_to_study(self.project.study, [exp_name],
                                   first_simulated_step_name="Load",
                                   last_simulated_step_name="Strip")
        self.assertEqual(len(self.perf_param_pane.performance_data), 3)

    def test_bring_up(self):
        with temp_bringup_ui_for(self.perf_param_pane):
            pass
