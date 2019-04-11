from traitsui.api import ITreeNodeAdapter
from traits.api import Instance

from kromatography.model.data_manager import DataManager


class DataManagerToITreeNode(ITreeNodeAdapter):
    """ Adapts a DataManager of objects to an ITreeNode.

    Note: Not much is done here
    because the data manager itself shouldn't show in the tree editor. It will
    just serve as the root object since it is tricky to have the root be a
    list.
    """

    adaptee = Instance(DataManager)

    # 'ITreeNodeAdapter' protocol ---------------------------------------------

    def allows_children(self):
        return True

    def has_children(self):
        return True

    def get_children(self):
        return [self.adaptee.data_elements]
