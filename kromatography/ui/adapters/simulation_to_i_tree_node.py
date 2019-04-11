from traitsui.api import Action, Separator
from traits.api import Instance
from kromatography.model.simulation import Simulation

from .base_chromatography_data_to_i_tree_node import \
    BaseChromatographyDataToITreeNode


RUN_ACTION = 'Run Simulation'
PLOT_ACTION = 'Plot Simulation'
DUPLIC_ACTION = 'Duplicate'


class SimulationToITreeNode(BaseChromatographyDataToITreeNode):
    """ Adapts a Simulation to an ITreeNode.

    This class implements the ITreeNodeAdapter interface thus allowing the use
    of TreeEditor for viewing any Simulation.
    """

    adaptee = Instance(Simulation)

    # 'ITreeNodeAdapter' protocol ---------------------------------------------

    def _non_standard_menu_actions(self):
        actions = [Separator(),
                   Action(name=RUN_ACTION,
                          action="object.fire_cadet_request"),
                   Action(name=PLOT_ACTION,
                          action="object.fire_plot_request"),
                   Action(name=DUPLIC_ACTION,
                          action="object.fire_duplicate_request"),
                   Separator()]
        return actions
