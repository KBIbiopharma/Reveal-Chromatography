from traits.api import HasStrictTraits, Instance, Property, Str
from traitsui.api import EnumEditor, Item, OKCancelButtons, View

from kromatography.model.data_source import DataSource


class ColumnPrepView(HasStrictTraits):
    """ UI for selecting components to make a column object.
    """

    datasource = Instance(DataSource)

    column_type_name = Str

    column_type = Property(depends_on="column_type_name")

    resin_name = Str

    resin = Property(depends_on="resin_name")

    def traits_view(self):
        ds = self.datasource
        if ds:
            known_col_names = ds.get_object_names_by_type('column_models')
            known_resin_names = ds.get_object_names_by_type('resin_types')
        else:
            known_col_names = known_resin_names = []

        view = View(
            Item("column_type_name",
                 editor=EnumEditor(values=known_col_names)),
            Item("resin_name", editor=EnumEditor(values=known_resin_names)),
            resizable=True,
            buttons=OKCancelButtons,
            title="Select column components from DataSource"
        )

        return view

    def _get_column_type(self):
        col_type = self.datasource.get_object_of_type('column_models',
                                                      self.column_type_name)
        return col_type.clone_traits()

    def _get_resin(self):
        resin = self.datasource.get_object_of_type('resin_types',
                                                   self.resin_name)
        return resin.clone_traits()
