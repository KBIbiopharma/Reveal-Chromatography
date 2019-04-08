from traitsui.table_column import ObjectColumn

from traits.api import Instance, List, on_trait_change
from traitsui.api import EnumEditor, Item, ModelView, OKCancelButtons, View, \
    TableEditor, VGroup
from scimath.units.api import UnitScalar, UnitArray

from app_common.traitsui.unit_scalar_editor import UnitScalarEditor  # noqa
from app_common.traitsui.unit_scalar_column import \
    UnitScalarColumn
from kromatography.model.buffer import Buffer
from kromatography.model.component import Component
from kromatography.model.data_source import DataSource


class BufferComponent(Component):
    """ Proxy class to adapt a list of Components and a concentrations array
    to a table editor.

    FIXME: Display the component's pka and charge too, for completion?
    """
    # concentration of the component in the buffer
    concentration = Instance(UnitScalar)


class BufferView(ModelView):
    """ View for a Buffer.
    """

    #: Buffer to edit
    model = Instance(Buffer)

    #: Proxy for the list of components in the buffer. Needed to display them
    #: in a TableEditor.
    buffer_components = List(Instance(BufferComponent))

    #: (multi-study) Datasource to access known data
    datasource = Instance(DataSource)

    #: List of known components to create a buffer from. Populated from the
    #: datasource or specified directly.
    known_components = List

    def default_traits_view(self):
        known_component_names = [comp.name for comp in self.known_components]
        buff_comp_editor = build_buffer_component_table_editor(
            known_component_names
        )

        view = View(
            Item('model.name'),
            Item('model.pH', label='pH', editor=UnitScalarEditor()),
            Item('model.conductivity', label='Conductivity',
                 editor=UnitScalarEditor()),
            VGroup(
                Item('buffer_components', editor=buff_comp_editor,
                     label='Buffer Components')
            ),
            # Relevant when used as standalone view:
            resizable=True, buttons=OKCancelButtons,
            title="Configure buffer"
        )
        return view

    def __init__(self, model, **traits):
        super(BufferView, self).__init__(model, **traits)

        # If a model contains components that are not in the datasource,
        # populate it
        if not self.known_components and self.model.chemical_components:
            self.known_components += self.model.chemical_components

        self.update_buffer_components()

    # -------------------------------------------------------------------------
    # Traits listeners
    # -------------------------------------------------------------------------

    def update_buffer_components(self):
        """ Returns a list of BufferComponents, constructed from the
        model's chemical_component data
        """
        num_comps = len(self.model.chemical_components)
        buff = self.model
        buffer_components = []
        for ii in range(num_comps):
            concentration_units = \
                buff.chemical_component_concentrations.units
            buff_comp_data = {
                'name': buff.chemical_components[ii].name,
                'concentration': UnitScalar(
                    buff.chemical_component_concentrations[ii],
                    units=concentration_units
                )
            }
            buffer_components.append(BufferComponent(**buff_comp_data))

        self.buffer_components = buffer_components

    @on_trait_change("buffer_components, buffer_components.[name,"  # noqa
                     "concentration]", post_init=True)
    def update_model(self):
        """ Updates the model when traits in the ProductComponents change
        """
        values = self.buffer_components

        components = []
        concentrations = []
        for e, comp in enumerate(values):
            concentrations.append(comp.concentration[()])
            ds_comp = [component for component in self.known_components
                       if component.name == comp.name][0]
            components.append(ds_comp)

        # Update the model in 1 step
        traits = {"chemical_components": components,
                  "chemical_component_concentrations": UnitArray(
                      concentrations, units=comp.concentration.units)}
        self.model.trait_set(**traits)

    def _known_components_default(self):
        if self.datasource:
            return self.datasource.get_objects_by_type("components")
        else:
            return []


def build_buffer_component_table_editor(known_component_names):
    """ Build an editor for a list of BufferComponent instances.
    """
    default_conc = UnitScalar(0, units="mmol/L")

    component_editor = TableEditor(
        columns=[
            ObjectColumn(name='name',
                         editor=EnumEditor(values=known_component_names)),
            UnitScalarColumn(name='concentration')
        ],
        editable=True,
        sortable=False,
        deletable=True,
        row_factory=BufferComponent,
        row_factory_kw={"name": known_component_names[0],
                        "concentration": default_conc},
    )
    return component_editor


if __name__ == '__main__':
    # setting up model
    from kromatography.model.tests.example_model_data import BUFFER_ELUTION
    from kromatography.model.data_source import SimpleDataSource

    ds = SimpleDataSource()
    buff = Buffer(**BUFFER_ELUTION)
    buff.print_traits()
    buff_view = BufferView(model=buff, datasource=ds)
    buff_view.configure_traits()
