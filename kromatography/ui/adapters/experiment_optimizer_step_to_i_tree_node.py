
from traits.api import Instance

from app_common.traitsui.adapters.data_element_to_i_tree_node import \
    DataElementToITreeNode

from kromatography.compute.experiment_optimizer_step import \
    ExperimentOptimizerStep


class ExperimentOptimizerStepToITreeNode(DataElementToITreeNode):
    """ Adapts a ExperimentOptimizerStep to an ITreeNode.

    This class implements the ITreeNodeAdapter interface thus allowing the use
    of TreeEditor for viewing any ExperimentOptimizerStep.
    """

    adaptee = Instance(ExperimentOptimizerStep)

    # 'ITreeNodeAdapter' protocol ---------------------------------------------

    def _get_children(self):
        return []
