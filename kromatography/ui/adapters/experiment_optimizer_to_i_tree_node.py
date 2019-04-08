
from traits.api import Instance
from traitsui.qt4.tree_editor import DeleteAction

from kromatography.compute.experiment_optimizer import ExperimentOptimizer

from .base_chromatography_data_to_i_tree_node import \
    BaseChromatographyDataToITreeNode


class ExperimentOptimizerToITreeNode(BaseChromatographyDataToITreeNode):
    """ Adapts a ExperimentOptimizer to an ITreeNode.

    This class implements the ITreeNodeAdapter interface thus allowing the use
    of TreeEditor for viewing any ExperimentOptimizer.
    """

    adaptee = Instance(ExperimentOptimizer)

    # 'ITreeNodeAdapter' protocol ---------------------------------------------

    def _get_children(self):
        return [self.adaptee.steps, self.adaptee.optimal_simulations]

    def _standard_menu_actions(self):
        """ Returns the standard actions for the pop-up menu. """
        actions = [DeleteAction]
        return actions
