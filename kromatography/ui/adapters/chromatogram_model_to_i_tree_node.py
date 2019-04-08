from traitsui.api import ITreeNodeAdapter
from traits.api import Instance

from kromatography.plotting.data_models import ChromatogramModel


class ChromatogramModelToITreeNode(ITreeNodeAdapter):
    """ Adapts a ChromatogramModel (supporting plots) to an ITreeNode.
    """

    adaptee = Instance(ChromatogramModel)

    # 'ITreeNodeAdapter' protocol ---------------------------------------------

    def allows_children(self):
        return False

    def has_children(self):
        return False

    def get_children(self):
        return []

    def get_label(self):
        return "Plots: {}".format(self.adaptee.name.capitalize())
