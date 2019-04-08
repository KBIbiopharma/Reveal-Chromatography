
from unittest import TestCase

from traitsui.api import Item, TreeEditor, View

from kromatography.ui.adapters.api import register_all_tree_node_adapters
from kromatography.model.data_manager import DataManager
from kromatography.model.tests.sample_data_factories import make_sample_study


class TestDataManagerTreeView(TestCase):

    def test_tree_node_adaptation(self):
        register_all_tree_node_adapters()
        study = make_sample_study()
        data_manager = DataManager(data_elements=[study])

        view = View(
            Item('data_elements', editor=TreeEditor())
        )
        ui = data_manager.edit_traits(view=view)
        ui.dispose()
