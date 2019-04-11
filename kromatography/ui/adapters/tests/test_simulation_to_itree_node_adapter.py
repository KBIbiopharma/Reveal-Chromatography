from contextlib import contextmanager
from unittest import TestCase

from traits.api import adapt
from traitsui.api import Item, ITreeNode, TreeEditor, View

from kromatography.ui.adapters.api import register_all_tree_node_adapters
from kromatography.model.tests.sample_data_factories import \
    make_sample_simulation, make_sample_study
from kromatography.ui.adapters.simulation_to_i_tree_node import \
        SimulationToITreeNode, RUN_ACTION, PLOT_ACTION, DUPLIC_ACTION
from kromatography.utils.traitsui_utils import get_node_data_list_element, \
    get_group_items


class TestSimulationToITreeNode(TestCase):

    def setUp(self):
        register_all_tree_node_adapters()
        self.study = make_sample_study()
        self.model = make_sample_simulation()
        self.study.simulations.append(self.model)

    def test_tree_node_adaptation_bring_up(self):
        with self.create_temporary_view():
            pass

    def test_direct_adaptation(self):
        tree_node = adapt(self.model, ITreeNode)
        self.assertIsInstance(tree_node, SimulationToITreeNode)

    def test_menu(self):
        with self.create_temporary_view() as ui:
            node_adapter, obj, sim_node_id, _ = get_node_data_list_element(ui)
            group_items = get_group_items(node_adapter, obj)
            all_actions = [item.action.name for item in group_items]
            self.assertIn(RUN_ACTION, set(all_actions))
            self.assertIn(PLOT_ACTION, set(all_actions))
            self.assertIn(DUPLIC_ACTION, set(all_actions))

    def test_duplicate_menu_action(self):
        with self.create_temporary_view() as ui:
            editor = ui._editors[0]
            node_adapter, obj, sim_node_id, _ = get_node_data_list_element(ui)
            group_items = get_group_items(node_adapter, obj)
            duplicate_action = [item.action for item in group_items
                                if item.action.name == DUPLIC_ACTION][0]
            self.assertEqual(len(self.study.simulations), 1)
            # Set up the tree editor to fake a right click on a
            editor._data = node_adapter, obj, sim_node_id
            editor.perform(duplicate_action)
            self.assertEqual(len(self.study.simulations), 2)

    # Helper methods ----------------------------------------------------------

    @contextmanager
    def create_temporary_view(self):
        editor = TreeEditor(editable=False)
        view = View(Item('simulations', editor=editor))
        ui = self.study.edit_traits(view=view)
        try:
            yield ui
        finally:
            ui.dispose()
