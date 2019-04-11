from traitsui.api import Menu, Action
from traits.api import Any, Instance

from kromatography.model.study import Study
from kromatography.model.data_source import STUDY_DS_OBJECT_TYPES

from .base_chromatography_data_to_i_tree_node import \
    BaseChromatographyDataToITreeNode


class StudyToITreeNode(BaseChromatographyDataToITreeNode):
    """ Adapts a Study to an ITreeNode.

    This class implements the ITreeNodeAdapter interface thus allowing the use
    of TreeEditor for viewing any Study.
    """

    adaptee = Instance(Study)

    children_changed_listener = Any

    # 'ITreeNodeAdapter' protocol ---------------------------------------------

    def get_menu(self):
        # See TreeEditor on_context_menu code to understand the context the
        # actions are evaluated in.
        return Menu(
            Action(name="New Simulation From Experiment...",
                   action="object.request_new_simulations_from_experiments"),
            #: FIXME - cant refer to datasource in the action statement?
            # Action(name="Create New Simulation...",
            #        action="object.request_new_simulation_from_datasource")
        )

    def _get_children(self):
        """ Collecting all traits that are ChromatographyData, None
        (uninitialized data) or lists/dictionaries of these things.
        """
        sim_elements = ["transport_models", "binding_models"]
        assert STUDY_DS_OBJECT_TYPES[-2:] == sim_elements
        sorted_ds_objects = [getattr(self.adaptee.study_datasource, key)
                             for key in STUDY_DS_OBJECT_TYPES[:-2]]
        sorted_sim_objects = [getattr(self.adaptee.study_datasource, key)
                              for key in sim_elements]
        children = ([self.adaptee.product] + sorted_ds_objects +
                    [self.adaptee.experiments] + sorted_sim_objects +
                    [self.adaptee.simulations, self.adaptee.analysis_tools])
        return children

    def when_children_changed(self, listener, remove):
        """ This takes care of propagating a change in the children of this
        list back to the tree editor by receiving the TreeEditor listener, and
        hot adding it as a listener on all children.

        Parameters
        ----------
        listener : Callable
            TreeEditor listener that must be called to force a repaint of the
            tree.

        remove : Bool
            Whether we should add a new listener to call the tree editor
            listener because the tree is being built, or removed because the
            tree editor is being cleaned up.
        """
        if remove:
            self.children_changed_listener = None
        else:
            self.children_changed_listener = listener

        non_list_children = ["product"]
        for name in non_list_children:
            self.adaptee.on_trait_change(self.children_changed, name=name,
                                         remove=remove, dispatch='ui')

    def children_changed(self, object, name, old, new):
        """ This calls the tree editor's listener with the appropriate
        arguments, which is the object that changed, the elements that were
        added as children and removed from children.

        FIXME: This is a horrible hack and we should figure out why the parent
        class is currently not doing it right.
        """
        from traits.trait_handlers import TraitListEvent

        event = TraitListEvent(added=[new], removed=[old])
        self.children_changed_listener(self.adaptee, '', event)

    def get_label(self):
        return "Study"
