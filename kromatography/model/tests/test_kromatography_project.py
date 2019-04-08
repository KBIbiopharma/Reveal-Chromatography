""" Tests for the KromatographyProject class. """

import unittest
from nose.tools import assert_equal, assert_is_instance

from traits.api import adapt
from traitsui.api import ITreeNode
from pyface.action.menu_manager import MenuManager

from kromatography.model.kromatography_project import KromatographyProject
from kromatography.model.data_source import SimpleDataSource, \
    STUDY_DS_OBJECT_TYPES
from kromatography.ui.adapters.api import register_all_tree_node_adapters
from kromatography.io.study import load_study_from_excel
from kromatography.utils.testing_utils import io_data_path
from kromatography.utils.app_utils import initialize_unit_parser

initialize_unit_parser()


class TestKromatographyProject(unittest.TestCase):

    def setUp(self):
        self.datasource = SimpleDataSource()
        self.project = KromatographyProject(datasource=self.datasource)
        register_all_tree_node_adapters()

    # -------------------------------------------------------------------------
    # Tests
    # -------------------------------------------------------------------------

    def test_study_creation(self):
        study = self.project.study
        self.assertTrue(study.is_blank)
        self.assertFalse(study.product_set)

    def test_study_datasource(self):
        study = self.project.study
        self.assertIs(study.datasource, self.project.datasource)

        expected_value_names = STUDY_DS_OBJECT_TYPES
        expected_value_names = set(expected_value_names)
        values = [val.name for val in
                  study.study_datasource.object_catalog.values()]
        self.assertEqual(set(values), set(expected_value_names))

    def test_study_tree_node_adaptation(self):
        study = self.project.study
        assert_valid_study_node_children(study)
        assert_valid_study_ds_nodes(study)

    def test_creation_with_complete_study(self):
        inp_file = io_data_path('ChromExampleDataV2.xlsx')
        study = load_study_from_excel(inp_file, datasource=self.datasource,
                                      allow_gui=False)
        project = KromatographyProject(datasource=self.datasource, study=study)

        study = project.study
        assert_valid_study_node_children(study)
        assert_valid_study_ds_nodes(study)


def assert_valid_study_node_children(study):
    tree_node = adapt(study, ITreeNode)
    expected_ds_entries = STUDY_DS_OBJECT_TYPES
    # 1 for the product, and 3 for the experiment list, simulation list and
    # analysis tools
    expected_num_children = 1 + len(expected_ds_entries) + 3
    assert_equal(len(tree_node.children), expected_num_children)


def assert_valid_study_ds_nodes(study):
    tree_node = adapt(study, ITreeNode)
    for ds_dict in tree_node.children:
        if not isinstance(ds_dict, dict):
            continue

        ds_node = adapt(ds_dict, ITreeNode)
        assert_is_instance(ds_node.get_menu(), MenuManager)
