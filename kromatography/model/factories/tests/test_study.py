from unittest import TestCase

from kromatography.model.factories.study import \
    build_study_from_experimental_study
from kromatography.model.study import Study
from kromatography.model.experimental_study import ExperimentalStudy
from kromatography.io.study import load_exp_study_from_excel
from kromatography.utils.testing_utils import io_data_path
from kromatography.utils.app_utils import initialize_unit_parser

initialize_unit_parser()


class TestBuildStudyFromExperimentalStudy(TestCase):

    def test_build_study(self):
        filepath = io_data_path('ChromExampleDataV2.xlsx')

        exp_study = load_exp_study_from_excel(filepath, allow_gui=False)
        self.assertIsInstance(exp_study, ExperimentalStudy)

        study = build_study_from_experimental_study(
            experimental_study=exp_study
        )
        self.assertIsInstance(study, Study)
        attr_list = ["datasource", "product"]
        for attr in attr_list:
            self.assertIs(getattr(study, attr), getattr(exp_study, attr))

        attr_list = ["experiments", "study_purpose", "study_type"]
        for attr in attr_list:
            self.assertEqual(getattr(study, attr), getattr(exp_study, attr))

        self.assertEqual(study.simulations, [])
        self.assertEqual(len(study.experiments), 3)

        ds = study.study_datasource
        self.assertEqual(len(ds.methods), 3)
        self.assertEqual(len(ds.loads), 2)
        self.assertEqual(len(ds.buffers), 3)
        self.assertEqual(len(ds.columns), 1)
