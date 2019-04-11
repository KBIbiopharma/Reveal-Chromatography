from traits.api import Bool, Button, HasStrictTraits, Instance
from traitsui.api import HGroup, Item, ModelView, Spring, UItem, VGroup, View


class ChromatographyDataCRUDEditor(HasStrictTraits):
    """ Editor that handles Creating/Read/Update/Delete operations for a model.
    """
    model_view = Instance(ModelView)

    # Supported actions -------------------------------------------------------

    enable_edit_button = Button('Enable Edits')

    disable_edit_button = Button('Disable Edits')

    # Private traits ----------------------------------------------------------

    _editable = Bool(True)

    def default_traits_view(self):
        view = View(
            VGroup(
                VGroup(
                    Item('model_view', style='custom', show_label=False),
                    show_border=True,
                    enabled_when='_editable',
                ),
                Spring(),
                HGroup(
                    UItem('enable_edit_button', enabled_when="not _editable"),
                    UItem('disable_edit_button', enabled_when="_editable")
                ),
            ),
        )
        return view

    # Trait Listeners ---------------------------------------------------------

    def _enable_edit_button_fired(self):
        self._editable = True

    def _disable_edit_button_fired(self):
        self._editable = False
