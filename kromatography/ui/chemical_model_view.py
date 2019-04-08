from traitsui.table_column import ObjectColumn

from traits.api import Instance, List, on_trait_change, Int
from traitsui.api import EnumEditor, Item, ModelView, OKCancelButtons, \
    TableEditor, View, VGroup

from app_common.traitsui.unit_scalar_editor import UnitScalarEditor  # noqa
from kromatography.model.chemical import Chemical
from kromatography.model.component import Component
from kromatography.model.data_source import DataSource


class ChemicalComponent(Component):
    """ Proxy class to adapt a list of Components and a concentrations array
    to a table editor.

    FIXME: Display the component's pka and charge too, for completion?
    """
    component_atom_count = Int


class ChemicalView(ModelView):
    """ View for Chemical model.

    FIXME: In the current state, this view is built with the proper datasource
    when a new Chemical is created from data explorer context menu, but not
    when a model is edited in the central pane. Therefore, temporary code is
    contained in the __init__ to populate self.known_components from the
    model's components.
    """

    #: Chemical to edit
    model = Instance(Chemical)

    #: Proxy for the list of components in the chemical. Needed to display them
    #: in a TableEditor.
    chemical_components = List(Instance(ChemicalComponent))

    #: (multi-study) Datasource to access known data
    datasource = Instance(DataSource)

    #: List of known components to create a buffer from. Populated from the
    #: datasource or specified directly.
    known_components = List

    def default_traits_view(self):
        known_component_names = [comp.name for comp in self.known_components]
        chem_comp_editor = build_chemical_component_table_editor(
            known_component_names
        )

        # FIXME: How do we want to 'create' this object in the UI?
        # i.e. what traits should be editable and what should be read only

        # Note: Current traits not in view of Chemical are 'component_list',
        # and 'component_atom_counts' which will be picked up by Tree
        view = View(
            Item('model.name'),
            Item('model.state'),
            Item('model.formula', style='readonly'),
            Item('model.molecular_weight', label='Molecular Weight',
                 editor=UnitScalarEditor()),
            VGroup(
                Item('chemical_components', editor=chem_comp_editor,
                     label='Chemical Components')
            ),
            resizable=True, buttons=OKCancelButtons,
            title="Configure Chemical"
        )
        return view

    def __init__(self, model, **traits):
        super(ChemicalView, self).__init__(model, **traits)

        # If a model contains components that are not in the datasource,
        # populate it. This is necessary since for now this view isn't given a
        # the project's datasource
        if not self.known_components and self.model.component_list:
            self.known_components += self.model.component_list

        self.update_chemical_components()

    # -------------------------------------------------------------------------
    # Traits listeners
    # -------------------------------------------------------------------------

    def update_chemical_components(self):
        """ Returns a list of BufferComponents, constructed from the
        model's chemical_component data
        """
        num_comps = len(self.model.component_list)
        chem = self.model
        chemical_components = []
        for ii in range(num_comps):
            chem_comp_data = {
                'name': chem.component_list[ii].name,
                'component_atom_count': chem.component_atom_counts[ii]
            }
            chemical_components.append(ChemicalComponent(**chem_comp_data))

        self.chemical_components = chemical_components

    @on_trait_change("chemical_components, chemical_components.[name,"  # noqa
                     "component_atom_count]", post_init=True)
    def update_model(self):
        """ Updates the model when traits in the Components change
        """
        values = self.chemical_components

        components = []
        atom_count = []
        for e, comp in enumerate(values):
            atom_count.append(comp.component_atom_count)
            ds_comp = [component for component in self.known_components
                       if component.name == comp.name][0]
            components.append(ds_comp)

        # Update the model in 1 step to avoid model being inconsistent
        traits = {"component_list": components,
                  "component_atom_counts": atom_count}
        self.model.trait_set(**traits)

    def _known_components_default(self):
        if self.datasource:
            return self.datasource.get_objects_by_type("components")
        else:
            return []


def build_chemical_component_table_editor(known_component_names):
    """ Build an editor for a list of chemical components.
    """
    default_count = 1

    component_editor = TableEditor(
        columns=[
            ObjectColumn(name='name',
                         editor=EnumEditor(values=known_component_names)),
            ObjectColumn(name='component_atom_count')
        ],
        editable=True,
        sortable=False,
        deletable=True,
        row_factory=ChemicalComponent,
        row_factory_kw={"name": known_component_names[0],
                        "component_atom_count": default_count},
    )
    return component_editor


if __name__ == '__main__':
    # setting up model
    from kromatography.model.data_source import SimpleDataSource
    s = SimpleDataSource()
    model = s.build_chemical_from_data("Sodium_Chloride")
    model_view = ChemicalView(model=model)
    model_view.configure_traits()
