from traitsui.api import ITreeNodeAdapter
from traits.api import Instance

from kromatography.model.data_source import SIMPLE_DS_OBJECT_TYPES, \
    SimpleDataSource


class SimpleDataSourceToITreeNode(ITreeNodeAdapter):
    """ Adapts a SimpleDataSource of objects to an ITreeNode.
    """

    adaptee = Instance(SimpleDataSource)

    # 'ITreeNodeAdapter' protocol ---------------------------------------------

    def allows_children(self):
        return True

    def has_children(self):
        return True

    def get_children(self):
        return [getattr(self.adaptee, self.adaptee._type_ids_map[type_id])
                for type_id in SIMPLE_DS_OBJECT_TYPES]

    def get_label(self):
        return self.adaptee.name
