from traits.api import Either, HasStrictTraits, List, Str
from traitsui.api import Item, ListStrEditor, OKCancelButtons

from kromatography.utils.traitsui_utils import KromView


class ProjectFileSelector(HasStrictTraits):
    path_list = List(Str)

    selected = Either(Str, List(Str))

    view = KromView(
        Item("path_list", show_label=False,
             editor=ListStrEditor(title='Project(s) to load',
                                  selected="selected",
                                  editable=False, multi_select=True)),
        title="Select the project(s) to load",
        buttons=OKCancelButtons,
        width=500
    )

    def _selected_default(self):
        return []
