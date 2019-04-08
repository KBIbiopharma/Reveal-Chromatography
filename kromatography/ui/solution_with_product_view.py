
from traits.api import Bool, Instance, List, on_trait_change, Property, Str
from traitsui.api import Item, ModelView, OKCancelButtons, VGroup, View
from scimath.units.api import UnitScalar, UnitArray
from scimath.units.dimensionless import percent

from app_common.traitsui.label_with_html import \
    LabelWithHyperlinks
from kromatography.model.data_source import DataSource
from app_common.traitsui.unit_scalar_editor import UnitScalarEditor  # noqa
from kromatography.model.solution_with_product import SolutionWithProduct
from kromatography.utils.solution_with_product_utils import (
    build_assay_list_editor, build_chemical_component_editor,
    ChemicalComponent, ProductAssay
)
from kromatography.utils.string_definitions import STRIP_COMP_NAME
from kromatography.ui.menu_entry_names import STRIP_TOOL_NAME


class SolutionWithProductView(ModelView):
    """ ModelView for a SolutionWithProduct.

    This view proxies the model's chemical component array, with a list of
    ChemicalComponent instances so that they can all be displayed in a table.
    Changes to the view automatically triggers an update to the model, but not
    the other way around, since nothing should be modifying the model, other
    than the view. The view can be updated by calling
    :meth:`update_chemical_components` explicitly. The same holds for the
    the model's product_assays, proxied by a list of ProductAssays.

    Note that the strip fraction is displayed separately from the other assays
    values though these quantities are very similar, and stored together in the
    same UnitArray. That's because the other components assay sum up to 100%,
    whereas the strip fraction is designed to be applying a global factor
    reducing the total amount of all other components.
    """
    # FIXME: we should expose the impurity assay values as an extra table.

    #: Model to display the data of:
    model = Instance(SolutionWithProduct)

    datasource = Instance(DataSource)

    #: All regular component product assay, that is excluding the Strip if any:
    product_assays = List(Instance(ProductAssay))

    _has_strip = Property(Bool, depends_on="model")

    _strip_desc = Str

    chemical_components = List(Instance(ChemicalComponent))

    def default_traits_view(self):
        prod = self.model.product
        all_assays = prod.product_component_assays
        assay_names = [assay for assay in all_assays
                       if assay != STRIP_COMP_NAME]
        if self.datasource:
            component_names = self.datasource.get_object_names_by_type(
                "components"
            )
        else:
            component_names = []

        view = View(
            Item('model.name', label='Name'),
            Item('model.product_concentration', label='Product Concentration',
                 editor=UnitScalarEditor()),
            Item('model.conductivity', label='Conductivity',
                 editor=UnitScalarEditor()),
            Item('model.pH', label='pH', editor=UnitScalarEditor()),
            VGroup(
                Item('product_assays', show_label=False,
                     editor=build_assay_list_editor(assay_names)),
                VGroup(
                    VGroup(
                        Item("_strip_desc", editor=LabelWithHyperlinks(),
                             style="readonly", show_label=False,
                             resizable=True)
                    ),
                    Item('model.strip_mass_fraction',
                         editor=UnitScalarEditor(), style="readonly"),
                    visible_when="_has_strip"),
                label='Product assay fractions', show_border=True,
            ),
            VGroup(
                Item('chemical_components', show_label=False,
                     editor=build_chemical_component_editor(component_names)),
                label='Chemical Components', show_border=True,
            ),
            # Relevant when used as standalone view only:
            resizable=True, buttons=OKCancelButtons, width=400,
            title="Configure the solution"
        )
        return view

    # -------------------------------------------------------------------------
    # HasTraits interface
    # -------------------------------------------------------------------------

    def __init__(self, model, **traits):

        super(SolutionWithProductView, self).__init__(model, **traits)

        self.update_chemical_components()
        self.update_product_assays()

    # Traits listeners --------------------------------------------------------

    def update_product_assays(self):
        """ Returns a list of ProductAssays for all comps but strip

        It is constructed from the model's assay data.
        """
        solution = self.model
        assay_values = solution.product_component_assay_values
        if assay_values is None:
            vals = [0.] * len(solution.product.product_component_assays)
            assay_values = UnitArray(vals, units=percent)

        num_comps = len(assay_values)
        product_assays = []
        for i in range(num_comps):
            assay_name = solution.product.product_component_assays[i]
            # Exclude the strip, since it is handled separately:
            if assay_name == STRIP_COMP_NAME:
                continue

            prod_assay_data = {
                'name': assay_name,
                'proportion': UnitScalar(assay_values[i],
                                         units=assay_values.units)
            }
            product_assays.append(ProductAssay(**prod_assay_data))

        self.product_assays = product_assays

    @on_trait_change("product_assays, product_assays.[name, proportion]")
    def update_model_product_assays(self):
        """ Updates the model when traits in the ProductAssays change
        """
        prod_assays = self.product_assays
        solution = self.model
        value_names = [val.name for val in prod_assays]
        proportions = [comp.proportion for comp in prod_assays]

        # Add back the the strip assay if exists
        if self._has_strip:
            value_names.append(STRIP_COMP_NAME)
            proportions.append(self.model.strip_mass_fraction)

        # Modify the model:
        solution.product.product_component_assays = value_names
        if prod_assays:
            from kromatography.utils.units_utils import unitted_list_to_array
            solution.product_component_assay_values = unitted_list_to_array(
                proportions
            )
        else:
            solution.product_component_assay_values = UnitArray([],
                                                                units=percent)

    def update_chemical_components(self):
        """ Returns a list of ChemicalComponents, constructed from the
        model's chemical_component data
        """
        num_comps = len(self.model.chemical_components)
        solution = self.model
        chemical_components = []
        for ii in range(num_comps):
            concentration_units = \
                solution.chemical_component_concentrations.units
            chem_comp_data = {
                'name': solution.chemical_components[ii].name,
                'concentration': UnitScalar(
                    solution.chemical_component_concentrations[ii],
                    units=concentration_units
                )
            }
            chemical_components.append(ChemicalComponent(**chem_comp_data))

        self.chemical_components = chemical_components

    @on_trait_change("chemical_components, chemical_components.[name,"
                     "concentration]")
    def update_model_chemical_components(self):
        """ Updates the model when traits in the ChemicalComponents change
        """
        if self.datasource is None:
            return

        chem_comps = self.chemical_components
        solution = self.model
        comp_list = []
        for e, comp in enumerate(chem_comps):
            chem_comp = self.datasource.get_object_of_type("components",
                                                           comp.name)
            comp_list.append(chem_comp)

        solution.chemical_components = comp_list

        if chem_comps:
            solution.chemical_component_concentrations = UnitArray(
                [comp.concentration[()] for comp in chem_comps],
                units=comp.concentration.units
            )
        else:
            solution.chemical_component_concentrations = UnitArray([])

    # Traits property getters/setters -----------------------------------------

    def _get__has_strip(self):
        return STRIP_COMP_NAME in self.model.product.product_component_assays

    def __strip_desc_default(self):
        strip_desc = r"The strip fraction describes the percentage of total " \
                     r"absorbance to assign to the strip component. (Use " \
                     r"the dedicated tool to modify: <i>Tools > {}</i>.)"
        strip_desc = strip_desc.format(STRIP_TOOL_NAME)
        return strip_desc


if __name__ == '__main__':
    # setting up model
    from kromatography.model.tests.example_model_data import SOLUTIONWITHPRODUCT_LOAD  # noqa
    from kromatography.model.data_source import SimpleDataSource

    ds = SimpleDataSource()
    solution = SolutionWithProduct(**SOLUTIONWITHPRODUCT_LOAD)
    solution.print_traits()
    solution_view = SolutionWithProductView(model=solution, datasource=ds)
    solution_view.configure_traits()
