from traits.api import Bool, Event, HasStrictTraits, Instance, Int, List, \
    Property, Str, Tuple
from traitsui.api import HGroup, Item, OKCancelButtons, TextEditor
from traitsui.tabular_adapter import TabularAdapter
from kromatography.ui.krom_view import KromView


class NoAutoTextEditor(TextEditor):
    auto_set = Bool(False)
    enter_set = Bool(True)
    multi_line = Bool(False)


class SimpleArrayAdapter(TabularAdapter):
    """ Adapter to display a 2D array or list of 1D arrays in a TabularEditor.
    """
    # Names of all columns including the index. Should be a list of tuples
    # mapping column number to its name. The index' "number" is "index"
    columns = List(Tuple)

    alignment = Str('right')

    format = Str('%.5g')

    row_names = List

    index_text = Property

    def _get_index_text(self):
        """ For row labels, use the number unless some names are specified
        """
        if not self.row_names:
            return str(self.row)
        else:
            return self.row_names[self.row]


class ArrayAdapterEvent(HasStrictTraits):
    """ Class to describe an event emitted by a Tabular View
    """
    row = Int
    column = Int
    old = Str
    new = Str


class SimpleNotifyingArrayAdapter(SimpleArrayAdapter):
    """ ArrayAdapter which emits an event when a value is modified.

    This is useful because we cannot listen to changes to an array, but might
    want to do things when that array is changed. A common use case would be
    when that array is proxy-ing other objects and these objects need to be
    updated when the proxy is updated.
    """

    value_changed = Event(Instance(ArrayAdapterEvent))

    def set_text(self, object, trait, row, column, text):
        old = self.get_text(object, trait, row, column)
        super(SimpleNotifyingArrayAdapter, self).set_text(object, trait, row,
                                                          column, text)
        event = ArrayAdapterEvent(old=old, new=text, row=row, column=column)
        self.value_changed = event


def build_array_adapter(index_name="Index", column_names=1, row_names=None):
    """ Build a SimpleNotifyingArrayAdapter from the row and column names.

    Parameters
    ----------
    column_names : int or list of str
        List of column names or number of column names to auto-generate.

    index_name : str (Optional)
        Name of the index column.

    """
    columns = [(index_name, 'index')]
    if isinstance(column_names, int):
        column_names = ["Col " + str(i) for i in range(column_names)]

    columns += [(name, i) for i, name in enumerate(column_names)]
    if row_names is None:
        row_names = []

    adapter = SimpleArrayAdapter(columns=columns, row_names=row_names)
    return adapter


def get_node_data_list_element(ui):
    """ Returns node information for the first element of a list displayed
    with a TreeEditor.
    """
    editor = get_tree_editor_in_ui(ui)
    root = editor._tree.itemAt(0, 0)
    first_element_node_id = root.child(0)
    expanded, node_adapter, obj = editor._get_node_data(first_element_node_id)
    return node_adapter, obj, first_element_node_id, expanded


def get_node_data_list(ui):
    """ Returns node information for a list displayed with a TreeEditor.
    """
    editor = get_tree_editor_in_ui(ui)
    root = editor._tree.itemAt(0, 0)
    expanded, node_adapter, obj = editor._get_node_data(root)
    return node_adapter, obj, root, expanded


def get_tree_editor_in_ui(ui):
    """ Returns the TreeEditor of a ui containing just that editor. """
    return ui._editors[0]


def get_group_items(node_adapter, obj):
    """ Collect the menu groups found in a node.
    """
    menu_manager = node_adapter.get_menu(obj)
    group_items = []
    for group in menu_manager.groups:
        group_items.extend(group.items)
    return group_items


class _NameEditor(HasStrictTraits):
    """ Utility editor to change the name of an object
    """
    msg = Str

    old_name = Str

    new_name = Str

    view = KromView(
        HGroup(
            Item("msg", style="readonly", visible_when="msg",
                 show_label=False),
        ),
        Item("old_name", style="readonly", width=300),
        Item("new_name", width=300),
        buttons=OKCancelButtons,
        title="Please provide a new name."
    )

    def _new_name_default(self):
        return self.old_name


def prompt_for_new_name(obj, msg="", kind="modal"):
    """ Utility to prompt a user to change a name.

    Parameters
    ----------
    obj : any
        Object to edit the name of.

    msg : str [OPTIONAL]
        Optional message to display in the UI to explain what to do, or why
        doing it for example.

    kind : None or str
        Kind of the dialog. Set to None to make it non-blocking. Useful for
        testing purposes.

    Returns
    -------
    str or None
        New name selected in the NameEditor if any, or None if the dialog was
        cancelled.
    """
    name_editor = _NameEditor(old_name=obj.name, msg=msg)
    ui = name_editor.edit_traits(kind=kind)
    if kind is None:
        return ui
    elif ui.result:
        return name_editor.new_name
