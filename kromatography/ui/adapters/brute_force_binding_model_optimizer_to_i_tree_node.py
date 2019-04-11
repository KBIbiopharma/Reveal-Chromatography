
from traits.api import Instance
from traitsui.qt4.tree_editor import DeleteAction

from kromatography.compute.brute_force_binding_model_optimizer import \
    BruteForce2StepBindingModelOptimizer

from .base_chromatography_data_to_i_tree_node import \
    BaseChromatographyDataToITreeNode


class BruteForceBindingModelOptimizerToITreeNode(BaseChromatographyDataToITreeNode):  # noqa
    """ Adapts a BruteForce2StepBindingModelOptimizer to an ITreeNode.

    This class implements the ITreeNodeAdapter interface thus allowing the use
    of TreeEditor for viewing any BindingModelOptimizer.
    """

    adaptee = Instance(BruteForce2StepBindingModelOptimizer)

    # 'ITreeNodeAdapter' protocol ---------------------------------------------

    def _get_children(self):
        return [self.adaptee.steps, self.adaptee.optimal_simulations,
                self.adaptee.optimal_models]

    def _standard_menu_actions(self):
        """ Returns the standard actions for the pop-up menu. """
        actions = [DeleteAction]
        return actions
