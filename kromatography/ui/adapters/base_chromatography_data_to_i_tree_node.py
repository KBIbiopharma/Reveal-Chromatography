import logging
from traits.api import Instance, TraitDictObject, TraitListObject
from traitsui.menu import Menu, Separator
from traitsui.qt4.tree_editor import CopyAction, CutAction, DeleteAction, \
    RenameAction

from app_common.traitsui.adapters.data_element_to_i_tree_node import \
    DataElementToITreeNode
from app_common.traits.has_traits_utils import is_trait_event

from kromatography.model.api import ChromatographyData

TREE_TYPES = (ChromatographyData, TraitDictObject, TraitListObject)

logger = logging.getLogger(__name__)


class BaseChromatographyDataToITreeNode(DataElementToITreeNode):
    """ Adapts a general ChromatographyData to an ITreeNode.

    This class implements the ITreeNodeAdapter interface thus allowing the use
    of TreeEditor for viewing any ChromatographyData.
    """

    adaptee = Instance(ChromatographyData)

    def _get_children(self):
        """ Collecting all traits that are ChromatographyData, None
        (uninitialized data) or lists/dictionaries of these things.
        """
        children = []
        for trait_name in self.adaptee.trait_names():
            if is_trait_event(self.adaptee, trait_name):
                continue

            attr = getattr(self.adaptee, trait_name)

            if isinstance(attr, ChromatographyData):
                children.append(attr)
            elif isinstance(attr, TraitListObject):
                # Only pick up lists of ChromData
                if not attr:
                    children.append(attr)
                elif isinstance(attr[0], ChromatographyData):
                    children.append(attr)
            elif isinstance(attr, TraitDictObject):
                # Only pick up dict of ChromData
                if not attr:
                    children.append(attr)
                elif isinstance(attr.values()[0], ChromatographyData):
                    children.append(attr)

        return children

    def _standard_menu_actions(self):
        """ Returns the standard actions for the pop-up menu.
        """
        # An object can be copied, pasted, deleted and renamed, but not pasted
        # into.
        actions = [CutAction, CopyAction, Separator(), DeleteAction,
                   Separator(), RenameAction]

        return actions

    def _non_standard_menu_actions(self):
        """ Returns non standard menu actions for the pop-up menu.
        """
        actions = []
        return actions

    def get_menu(self):
        # See TreeEditor on_context_menu code to understand the context the
        # actions are evaluated in.

        # FIXME The order of actions in the drop down are not easily controlled
        # When the order can be controlled, it should be set per comments
        # on PR#586.
        actions = self._standard_menu_actions()
        actions.extend(self._non_standard_menu_actions())
        return Menu(*actions)

    def can_copy(self):
        """ Returns whether the object's children can be copied.
        """
        return True

    def can_rename_me(self):
        """ Returns whether the object can be renamed.
        """
        return True

    def can_delete(self):
        """ Returns whether the object's children can be deleted.
        """
        return True

    def can_delete_me(self):
        """ Returns whether the object can be deleted.
        """
        return True

    def confirm_delete(self):
        """ Checks whether a specified object can be deleted.

        Returns
        -------
        * **True** if the object should be deleted with no further prompting.
        * **False** if the object should not be deleted.
        * Anything else: Caller should take its default action (which might
          include prompting the user to confirm deletion).
        """
        return 'Confirm'
