""" Base ModelView class for binding and transport ModelView classes.
"""
from traits.api import Any, Instance, List
from traitsui.api import ModelView, TabularEditor

from kromatography.utils.traitsui_utils import build_array_adapter, \
    SimpleArrayAdapter


class BaseModelViewWithComponentArray(ModelView):
    """ Base ModelView for a model containing a list of arrays that should be
    displayed as 1 table (since all same length, 1 value per component).

    The setting of values in the arrays is done automatically by the
    TabularAdapter since component_array is just a list of the model's
    properties.

    Subclass to implement the initialization of :attr:`vector_attributes` and
    how the model is connected to the :attr:`component_array`.
    """
    model = Any

    #: list of attributes to display in the tabular editor
    vector_attributes = List

    #: Proxy array that allows to display all properties together in 1 table
    component_array = List

    #: UI tabular adapter to display the binding model arrays as 1 table
    _comp_array_adapter = Instance(SimpleArrayAdapter)

    #: Tabular editor to display component_array
    _tabular_editor = Instance(TabularEditor)

    # Traits initialization methods -------------------------------------------

    def _component_array_default(self):
        """ Collect all properties into 1 list to pass to TabularAdapter.
        """
        arr_list = [getattr(self.model, attr)
                    for attr in self.vector_attributes]
        return arr_list

    def __comp_array_adapter_default(self):
        index_name = 'Property name'
        column_names = self.model.component_names
        row_names = [attr.replace("_", " ") for attr in self.vector_attributes]
        adapter = build_array_adapter(index_name, column_names, row_names)
        return adapter

    def __tabular_editor_default(self):
        # FIXME: even though editable_labels=False, the editor seems to allow
        # to edit the row names (first column). Look into how to prevent the
        # editor from even giving the impression that it can be changed.

        return TabularEditor(adapter=self._comp_array_adapter,
                             auto_resize=True, editable_labels=False)
