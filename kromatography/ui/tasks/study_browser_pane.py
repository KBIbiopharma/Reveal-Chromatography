from traits.api import Any, Instance
from traitsui.api import Item, TreeEditor, View

from pyface.tasks.api import TraitsDockPane

from kromatography.model.study import Study
from kromatography.ui.adapters.api import register_all_tree_node_adapters


class StudyDataDockPane(TraitsDockPane):
    """ View on a Study object
    """

    # -------------------------------------------------------------------------
    # 'TaskPane' interface
    # -------------------------------------------------------------------------

    id = 'krom.study_data_pane'

    name = 'Study Data Browser'

    # -------------------------------------------------------------------------
    # DataExplorerDockPane
    # -------------------------------------------------------------------------

    #: Global container for all data to explore
    study = Instance(Study)

    #: Item last double-clicked on in the tree view
    requested_data_item = Any

    # -------------------------------------------------------------------------
    # HasTraits interface
    # -------------------------------------------------------------------------

    _tree_editor = Instance(TreeEditor)

    def traits_view(self):
        """ The view used to construct the dock pane's widget.
        """
        self._tree_editor = TreeEditor(editable=False, auto_open=1,
                                       dclick="requested_data_item",
                                       expands_on_dclick=False,
                                       hide_root=False
                                       )

        view = View(
            Item('study',
                 editor=self._tree_editor,
                 show_label=False),
            resizable=True
        )
        return view

    def __init__(self, **traits):
        super(StudyDataDockPane, self).__init__(**traits)

        # register the adapters for viewing the data tree using TreeEditor
        register_all_tree_node_adapters()

    # Traits listeners --------------------------------------------------------

    def _requested_data_item_changed(self):
        """ When a data item is double-clicked, open in central pane.

        FIXME: this doesn't get triggered if someone double clicks multiple
        times in a row on the same object, even if the tab has been closed in
        the meanwhile.
        """
        self.task.edit_object_in_central_pane(self.requested_data_item)
