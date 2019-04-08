from traits.api import Instance
from traitsui.api import Action
from traitsui.qt4.tree_editor import DeleteAction
from traitsui.menu import Separator

from kromatography.model.simulation_group import SimulationGroup
from .base_chromatography_data_to_i_tree_node import \
    BaseChromatographyDataToITreeNode


class SimulationGroupToITreeNode(BaseChromatographyDataToITreeNode):
    """ Adapts a SimulationGroup to an ITreeNode.

    This class implements the ITreeNodeAdapter interface thus allowing the use
    of TreeEditor for viewing any SimulationGroup.
    """

    adaptee = Instance(SimulationGroup)

    # 'ITreeNodeAdapter' protocol ---------------------------------------------

    def _get_children(self):
        return [self.adaptee.simulations]

    def get_label(self):
        return "{name} ({num_sim} simulations)".format(
            num_sim=self.adaptee.size, name=self.adaptee.name
        )

    def _standard_menu_actions(self):
        """ Returns the standard actions for the pop-up menu. """
        actions = [DeleteAction, Separator()]
        return actions

    def _non_standard_menu_actions(self):
        """ Returns non standard menu actions for the pop-up menu.
        """
        actions = [
            Action(name="Run All Simulations...",
                   action="object.fire_cadet_request"),
            Action(name="Plot All Simulations...",
                   action="object.fire_plot_request"),
        ]
        return actions
