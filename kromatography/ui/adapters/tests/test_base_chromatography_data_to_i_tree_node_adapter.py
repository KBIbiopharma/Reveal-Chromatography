from contextlib import contextmanager
from unittest import TestCase
from nose.tools import assert_equal, assert_greater, assert_greater_equal

from traits.api import adapt
from traitsui.api import Item, ITreeNode, TreeEditor, View
from traitsui.qt4.tree_editor import CopyAction, CutAction, DeleteAction, \
    PasteAction, RenameAction
from traitsui.qt4.clipboard import clipboard

from app_common.traits.assertion_utils import assert_has_traits_almost_equal

from kromatography.ui.adapters.api import register_all_tree_node_adapters
from kromatography.model.lazy_simulation import LazyLoadingSimulation
from kromatography.model.tests.sample_data_factories import \
    make_sample_binding_model, make_sample_simulation, make_sample_study, \
    make_sample_user_ds, make_sample_binding_model_optimizer, \
    make_sample_brute_force_optimizer, make_sample_simulation_group
from kromatography.ui.adapters.base_chromatography_data_to_i_tree_node import \
    BaseChromatographyDataToITreeNode
from kromatography.ui.adapters.experiment_optimizer_to_i_tree_node import \
    ExperimentOptimizerToITreeNode
from kromatography.ui.adapters.brute_force_binding_model_optimizer_to_i_tree_node import BruteForceBindingModelOptimizerToITreeNode  # noqa
from kromatography.ui.adapters.simulation_group_to_i_tree_node import \
    SimulationGroupToITreeNode
from kromatography.utils.traitsui_utils import get_node_data_list, \
    get_node_data_list_element, get_group_items, get_tree_editor_in_ui

MODELS_TO_TEST = ['binding_model', 'transport_model']


class TestBaseChromatographyToITreeNode(TestCase):

    def setUp(self):
        self.standard_actions = [DeleteAction, RenameAction, CopyAction,
                                 CutAction]
        register_all_tree_node_adapters()
        # Make a study and add all possible chromatography objects to the study
        # Make a study with 1 experiment
        self.study = make_sample_study(1)
        simulation = make_sample_simulation()
        self.study.simulations.append(simulation)
        self.user_ds = make_sample_user_ds(with_bind_trans=True)
        self.user_ds_entries = self.user_ds.object_catalog.keys()
        self.user_ds_objects = [getattr(self.user_ds, key)
                                for key in self.user_ds_entries]
        self.study.study_datasource.binding_models.\
            append(self.study.simulations[0].binding_model)
        self.study.study_datasource.transport_models.\
            append(self.study.simulations[0].transport_model)
        in_study_ds = self.study.study_datasource
        self.in_study_ds_entries = in_study_ds.object_catalog.keys()
        self.in_study_objects = [getattr(in_study_ds, key)
                                 for key in self.in_study_ds_entries]

    def test_in_study_direct_adaptation(self):
        objects_checked = 0
        for object_list in self.in_study_objects:
            if len(object_list) > 0:
                objects_checked += 1
                model = object_list[0]
                tree_node = adapt(model, ITreeNode)
                self.assertIsInstance(tree_node,
                                      BaseChromatographyDataToITreeNode)
        self.assertEqual(objects_checked, len(self.in_study_objects))

    def test_user_ds_direct_adaptation(self):
        objects_checked = 0
        for object_list in self.user_ds_objects:
            objects_checked += 1
            model = object_list[0]
            tree_node = adapt(model, ITreeNode)
            self.assertIsInstance(tree_node,
                                  BaseChromatographyDataToITreeNode)
        self.assertEqual(objects_checked, len(self.user_ds_objects))

    def test_datasource_data_menu(self):
        # loop over the name of all lists in both datasources, build a UI and
        # collect the first node inside each list to analyze the node's menu
        # entries:
        entries = self.user_ds_entries + self.in_study_ds_entries
        num_study_entries = len(self.in_study_ds_entries)
        datasources = [self.user_ds] * len(self.user_ds_entries) + \
                      [self.study.study_datasource] * num_study_entries

        for entry, ds in zip(entries, datasources):
            with create_temporary_view(entry, ds) as ui:
                node_adapter, obj, sim_node_id, _ = get_node_data_list_element(
                    ui
                )
                group_items = get_group_items(node_adapter, obj)
                actions = [item.action for item in group_items]
                self.assertEqual(set(actions), set(self.standard_actions))
                for action in actions:
                    if action.name in ["Cut", "Copy"]:
                        self.assertTrue(action.enabled)
                        self.assertTrue(action.visible)

    def test_datasource_list_menu(self):
        # loop over all datasource lists, build a UI and check that the node's
        # menu entries contain the PastAction:
        entries = self.user_ds_entries + self.in_study_ds_entries
        num_study_entries = len(self.in_study_ds_entries)
        datasources = [self.user_ds] * len(self.user_ds_entries) + \
                      [self.study.study_datasource] * num_study_entries

        for entry, ds in zip(entries, datasources):
            assert_list_menu_content_greater(ds, entry, {PasteAction},
                                             or_equal=True)

    def test_copy_action(self):
        ds = self.user_ds
        bind0 = ds.binding_models[0]
        self.right_click_on_list_data_and_action(ds, "binding_models", "Copy")
        self.assertIs(clipboard.instance, bind0)

    def test_paste_into_ds_list(self):
        ds = self.user_ds
        existing = len(ds.binding_models)
        bind0 = make_sample_binding_model()
        # Avoid collision with existing model:
        bind0.name = "New name"
        clipboard.instance = bind0
        self.right_click_on_list_and_action(ds, "binding_models", "Paste")
        self.assertEqual(len(ds.binding_models), existing + 1)
        self.assertIs(ds.binding_models[-1], bind0)

    def test_paste_into_simulation_list(self):
        sim_list = self.study.simulations
        existing = len(sim_list)
        sim = self.study.simulations[0].copy()
        sim.name = "NEW NAME TO AVOID COLLISION"
        clipboard.instance = sim
        self.right_click_on_list_and_action(self.study, "simulations", "Paste")
        self.assertEqual(len(sim_list), existing + 1)
        self.assertIs(sim_list[-1], sim)

    def test_paste_lazy_sim_into_simulation_list(self):
        sim_list = self.study.simulations
        existing = len(sim_list)
        sim = self.study.simulations[0].copy()
        sim.name = "NEW NAME TO AVOID COLLISION"
        sim = LazyLoadingSimulation.from_simulation(sim)
        clipboard.instance = sim
        self.right_click_on_list_and_action(self.study, "simulations", "Paste")
        self.assertEqual(len(sim_list), existing + 1)
        # Not the same object because the sim was converted to regular sim so
        # that it doesn't cause issues when pasting
        self.assertIsNot(sim_list[-1], sim)
        assert_has_traits_almost_equal(sim_list[-1], sim, check_type=False)

    def test_paste_into_wrong_ds_list(self):
        """ Trying to paste binding model into transport_models list = no-op.
        """
        ds = self.user_ds
        existing = len(ds.binding_models)
        bind0 = make_sample_binding_model()
        clipboard.instance = bind0
        self.right_click_on_list_and_action(ds, "transport_models", "Paste")
        self.assertEqual(len(ds.binding_models), existing)

    # Helper methods ----------------------------------------------------------

    def right_click_on_list_and_action(self, ds, list_name, action_name):
        """ Programmatically create a tree view for the provided datasource,
        right click on one of its lists and select an action.
        """
        with create_temporary_view(list_name, ds) as ui:
            node_adapter, obj, node_id, _ = get_node_data_list(ui)
            group_items = get_group_items(node_adapter, obj)
            action = [item.action for item in group_items
                      if item.action.name == action_name][0]
            tree_editor = get_tree_editor_in_ui(ui)
            tree_editor._data = (node_adapter, obj, node_id)
            tree_editor._perform(action)

    def right_click_on_list_data_and_action(self, ds, list_name, action_name):
        """ Programmatically create a tree view for the provided datasource,
        right click on the first element of one its lists and select an action.
        """
        with create_temporary_view(list_name, ds) as ui:
            node_adapter, obj, node_id, _ = get_node_data_list_element(ui)
            group_items = get_group_items(node_adapter, obj)
            action = [item.action for item in group_items
                      if item.action.name == action_name][0]
            tree_editor = get_tree_editor_in_ui(ui)
            tree_editor._data = (node_adapter, obj, node_id)
            tree_editor._perform(action)


class TestAnalysisToolsToITreeNode(TestCase):

    def setUp(self):
        register_all_tree_node_adapters()
        # Make a study and add all possible chromatography objects to the study
        # Make a study with 1 experiment
        self.study = make_sample_study(1)
        simulation = make_sample_simulation()
        self.study.simulations.append(simulation)

    def test_optimizer_list_to_itree_node_menu(self):
        analysis_tools = self.study.analysis_tools
        assert_list_menu_content_equal(analysis_tools, "optimizations",
                                       {PasteAction})
        assert_list_menu_content_equal(analysis_tools, "simulation_grids",
                                       {PasteAction})

    def test_optimizer_to_itree_node(self):
        model = make_sample_brute_force_optimizer()
        analysis_tools = self.study.analysis_tools
        analysis_tools.optimizations.append(model)
        tree_node = adapt(model, ITreeNode)
        self.assertIsInstance(tree_node, ExperimentOptimizerToITreeNode)
        assert_list_element_menu_content_equal(analysis_tools, "optimizations",
                                               {DeleteAction})

    def test_binding_optimizer_to_itree_node(self):
        model = make_sample_binding_model_optimizer()
        analysis_tools = self.study.analysis_tools
        analysis_tools.optimizations.append(model)
        tree_node = adapt(model, ITreeNode)
        self.assertIsInstance(tree_node,
                              BruteForceBindingModelOptimizerToITreeNode)
        assert_list_element_menu_content_equal(analysis_tools, "optimizations",
                                               {DeleteAction})

    def test_sim_group_to_itree_node_menu(self):
        model = make_sample_simulation_group()
        analysis_tools = self.study.analysis_tools
        analysis_tools.simulation_grids.append(model)
        tree_node = adapt(model, ITreeNode)
        self.assertIsInstance(tree_node, SimulationGroupToITreeNode)
        expected = {DeleteAction}
        assert_list_element_menu_content_greater(analysis_tools,
                                                 "simulation_grids", expected)


def assert_list_menu_content_equal(container_obj, list_name, actions):
    """ Build a UI for the container object displaying the list, and assert the
    menu content on the list.
    """
    assert_menu_content(container_obj, list_name, actions,
                        get_node_data_list, assert_equal)


def assert_list_element_menu_content_equal(container_obj, list_name, actions):
    """ Build a UI for the container object displaying the list, and assert the
    menu content on the list.
    """
    assert_menu_content(container_obj, list_name, actions,
                        get_node_data_list_element, assert_equal)


def assert_list_element_menu_content_greater(obj, list_name, actions,
                                             or_equal=False):
    """ Build a UI for the container object displaying the list, and assert the
    menu content on the list.
    """
    if or_equal:
        assert_func = assert_greater_equal
    else:
        assert_func = assert_greater

    assert_menu_content(obj, list_name, actions,
                        get_node_data_list_element, assert_func)


def assert_list_menu_content_greater(obj, list_name, actions, or_equal=False):
    """ Build a UI for the container object displaying the list, and assert the
    menu content on the list.
    """
    if or_equal:
        assert_func = assert_greater_equal
    else:
        assert_func = assert_greater

    assert_menu_content(obj, list_name, actions, get_node_data_list,
                        assert_func)


def assert_menu_content(container_obj, list_name, expected_actions,
                        node_data_getter, assert_func=None):
    """ Build a UI for the container object displaying a list of object, and
    assert the menu content on an tree element.
    """
    if assert_func is None:
        assert_func = assert_equal

    with create_temporary_view(list_name, container_obj) as ui:
        node_adapter, obj, sim_node_id, _ = node_data_getter(ui)
        group_items = get_group_items(node_adapter, obj)
        actions = [item.action for item in group_items]
        assert_func(set(actions), expected_actions)


@contextmanager
def create_temporary_view(attribute_name, obj):
    """ Build tree view for 1 entry in datasource and dispose of it after use.
    """
    editor = TreeEditor(editable=False)
    view = View(Item(attribute_name, editor=editor))
    ui = obj.edit_traits(view=view)
    try:
        yield ui
    finally:
        ui.dispose()
