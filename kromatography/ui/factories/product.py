""" GUIs, classes and utilities to build a new product.
"""
import logging

from scimath.units.api import UnitScalar
from traits.api import Bool, Button, HasStrictTraits, Instance, List, \
    Property, Str
from traitsui.api import HGroup, Item, Label, ListStrEditor, OKCancelButtons, \
    Spring, TableEditor, VGroup
from traitsui.table_column import ObjectColumn
from pyface.api import error

from app_common.traitsui.unit_scalar_editor import UnitScalarEditor  # noqa
from kromatography.model.product import Product
from kromatography.model.data_source import SimpleDataSource
from kromatography.model.product_component_assay import ProductComponentAssay
from kromatography.ui.product_model_view import assay_names_from_instances, \
    ASSAY_TABLE_EDITOR
from app_common.traitsui.text_with_validation_editors import \
    TextWithExcludedValuesEditor
import kromatography.utils.chromatography_units as chr_units
from kromatography.model.api import ProductComponent
from kromatography.utils.string_definitions import STRIP_COMP_NAME
from kromatography.utils.traitsui_utils import KromView

logger = logging.getLogger(__name__)


class ComponentDescription(HasStrictTraits):
    """ Grouping of product component name and concentration expression, to
    display together in a table editor.
    """
    name = Str

    target_product = Str

    concentration_exps = Str("product_concentration")


class ProductBuilder(HasStrictTraits):
    """ New Product builder, from available components of a datasource.
    """
    #: Name of the future product being created
    name = Str("New product")

    #: User notes about the products's origin, purpose, ...
    description = Str

    #: Type of the future product
    product_type = Str

    #: pI of the future product
    pI = Instance(UnitScalar)

    #: Simplified UI of full one?
    expert_mode = Bool

    #: List of component descriptions: names and concentration expressions
    component_descs = List(Instance(ComponentDescription))

    #: Whether to automatically add a strip component to the new Product.
    # Only used in the non-expert mode
    add_strip = Bool(True)

    #: List of additional component description. Only 1 comp allowed: Strip
    strip_component_descs = List(Instance(ComponentDescription))

    #: Actual strip compoment that the future product will include
    strip_component = Instance(ProductComponent)

    #: List of assay values (only displayed in the expert mode)
    component_assay_names = List(ProductComponentAssay)

    #: List of existing product component names targeting the desired product
    _component_candidates_names = Property(List(Str))

    #: Datasource to pull product components from
    datasource = Instance(SimpleDataSource)

    _add_comp_button = Button("Add Product Component(s)")

    _edit_strip_comp_button = Button("Edit Strip Properties")

    _add_assay_button = Button("Add Assay Values")

    def traits_view(self):
        component_descr_simple_editor = build_component_descr_editor(False)
        component_descr_expert_editor = build_component_descr_editor(True)
        known_products = self.datasource.get_object_names_by_type('products')
        name_editor = TextWithExcludedValuesEditor(
            forbidden_values=set(known_products)
        )
        expert_mode_tooltip = "Expert mode: customize assay names, and " \
                              "control concentration expressions."

        strip_label = 'Strip component, automatically added to account for' \
                      ' load mass eluting during the Strip step, if any.'
        view = KromView(
            VGroup(
                HGroup(
                    Item('name', editor=name_editor, width=300),
                    Item('product_type'),
                ),
                Item("description", style="custom"),
                Item('pI', editor=UnitScalarEditor(), label="pI"),
                HGroup(
                    Spring(),
                    Item('expert_mode', tooltip=expert_mode_tooltip),
                ),
                VGroup(
                    Item('component_descs', show_label=False,
                         editor=component_descr_simple_editor),
                    Item('_add_comp_button', show_label=False),
                    HGroup(
                        Spring(),
                        Item('add_strip', tooltip=expert_mode_tooltip),
                    ),
                    VGroup(
                        Label(strip_label),
                        HGroup(
                            Item('strip_component_descs', style='readonly',
                                 editor=component_descr_simple_editor,
                                 show_label=False, height=40),
                            Item('_edit_strip_comp_button', show_label=False),
                        ),
                        visible_when="add_strip"
                    ),
                    label="Product component names",
                    show_border=True, visible_when="not expert_mode"
                ),
                VGroup(
                    Item('component_descs', show_label=False,
                         editor=component_descr_expert_editor,
                         visible_when="expert_mode"),
                    Item('_add_comp_button', show_label=False),
                    label="Product components and concentration expressions",
                    show_border=True, visible_when="expert_mode"
                ),
                VGroup(
                    Item('component_assay_names', editor=ASSAY_TABLE_EDITOR,
                         show_label=False),
                    Item("_add_assay_button", show_label=False),
                    label="Component assay values",
                    show_border=True, visible_when="expert_mode"
                ),
            ),
            width=600, height=600, title="Specify New Product Characteristics",
            buttons=OKCancelButtons
        )
        return view

    def build_product(self, allow_ui=True):
        """ Create an instance of a Product from the characteristics and
        component descriptions of the builder.
        """
        try:
            if not self.expert_mode:
                self.expand_product_attributes()

            # Collect components
            components = self.lookup_components()

            # Collect component concentration expressions
            concentration_exps = [comp.concentration_exps
                                  for comp in self.component_descs]
            if self.add_strip and not self.expert_mode:
                strip_desc = self.strip_component_descs[0]
                strip_expression = strip_desc.concentration_exps
                concentration_exps.append(strip_expression)

            # Collect assays:
            assay_names = assay_names_from_instances(
                self.component_assay_names
            )
            if self.add_strip and not self.expert_mode:
                assay_names.append(STRIP_COMP_NAME)

            # Build product instance
            prod = Product(
                name=self.name, product_type=self.product_type,
                description=self.description,
                pI=self.pI, product_components=components,
                product_component_concentration_exps=concentration_exps,
                product_component_assays=assay_names
            )

            if self.add_strip and not self.expert_mode:
                self.datasource.set_object_of_type("product_components",
                                                   self.strip_component)
        except Exception as e:
            msg = ("Failed to create new product. Please try again or report "
                   "this issue to the software provider if the problem "
                   "persists, providing the log file of this session.")
            details = "\nError was {}.".format(e)
            logger.exception(msg + details)
            if allow_ui:
                error(None, msg)
            prod = None

        return prod

    def expand_product_attributes(self):
        """ The product was setup in simplified mode: expand product assays and
        component concentration expressions.
        """
        for comp_desc in self.component_descs:
            comp_name = comp_desc.name
            assay = ProductComponentAssay(name=comp_name)
            self.component_assay_names.append(assay)
            comp_expr = "product_concentration * {} / 100".format(comp_name)
            if self.add_strip:
                comp_expr += " * (100 - Strip) / 100"

            comp_desc.concentration_exps = comp_expr

    def lookup_components(self):
        """ Look up product components in the builder's DS to match the comp
        descriptions.
        """
        ds = self.datasource
        components = []

        for comp in self.component_descs:
            filters = {'name': comp.name, 'target_product': self.name}
            candidates = ds.get_objects_by_type("product_components",
                                                filter_by=filters)
            if len(candidates) == 1:
                components.append(candidates[0])
            else:
                msg = ("Expected to find 1 candidate component with name {} "
                       "and target product {} but found {}.")
                msg = msg.format(comp.name, self.name, len(candidates))
                logger.exception(msg)
                raise ValueError(msg)

        if self.add_strip and not self.expert_mode:
            components.append(self.strip_component)
        return components

    # Trait listeners ---------------------------------------------------------

    def __add_comp_button_fired(self):
        selector = ProductComponentSelector(
            component_names=self._component_candidates_names,
            datasource=self.datasource, target_product=self.name,
        )
        ui = selector.edit_traits(kind='livemodal')
        if ui.result:
            # Reset in case the UI has been called multiple times
            self.component_descs = []
            for comp_name in selector.selected_component_names:
                comp_desc = ComponentDescription(name=comp_name,
                                                 target_product=self.name)
                self.component_descs.append(comp_desc)

    def __edit_strip_comp_button_fired(self):
        from kromatography.ui.product_component_model_view import \
            ProductComponentView

        editor = ProductComponentView(model=self.strip_component,
                                      target_product_editable=False,
                                      name_editable=False,
                                      title="Configure Strip Component")
        editor.edit_traits(kind="livemodal")

    def __add_assay_button_fired(self):
        new_assay = ProductComponentAssay(name="Type Assay Name")
        self.component_assay_names.append(new_assay)

    def _name_changed(self):
        self.strip_component.target_product = self.name

    # Trait property getters/setters ------------------------------------------

    def _get__component_candidates_names(self):
        return collect_component_candidates_names(self.name, self.datasource)

    # Trait initialization methods --------------------------------------------

    def _pI_default(self):
        return UnitScalar(0., units='1')

    def _strip_component_descs_default(self):
        strip_conc_exps = "product_concentration * {} / 100".format(
            STRIP_COMP_NAME
        )
        comp_desc = ComponentDescription(
            name=STRIP_COMP_NAME, target_product=self.name,
            concentration_exps=strip_conc_exps,
        )
        return [comp_desc]

    def _strip_component_default(self):
        ext_coef_units = chr_units.extinction_coefficient_unit
        strip_comp = ProductComponent(
            name=STRIP_COMP_NAME, target_product=self.name,
            molecular_weight=UnitScalar(0.0, units=chr_units.kilogram_per_mol),
            extinction_coefficient=UnitScalar(0.0, units=ext_coef_units),
        )
        return strip_comp


class ProductComponentSelector(HasStrictTraits):
    """ Utility UI class to select a list of product component names targeting
    a specific product, or create new ones.
    """
    target_product = Str

    component_names = List(Str)

    selected_component_names = List(Str)

    datasource = Instance(SimpleDataSource)

    create_comp_button = Button("Create New Component")

    def traits_view(self):
        no_comp_msg = ('No components were found targeting the requested '
                       'product ({}). Please create the needed components '
                       'first.'.format(self.target_product))
        view = KromView(
            # Embedding the label in a Group to give it space and work around a
            # traitsui bug with Label and visible_when (traitsui issues #298)
            HGroup(
                Label(no_comp_msg),
                visible_when='component_names == []'
            ),
            Item('component_names',
                 editor=ListStrEditor(selected='selected_component_names',
                                      multi_select=True),
                 label="Select component(s)"),
            Item('create_comp_button', show_label=False),
            title="Select components to build the product.",
            resizable=True,
            buttons=OKCancelButtons,
        )
        return view

    def _create_comp_button_fired(self):
        from kromatography.utils.datasource_utils import \
            UserDataSourceEntryCreator

        creator = UserDataSourceEntryCreator(
            datasource=self.datasource,
            datasource_key='product_components'
        )
        creator(target_product=self.target_product)
        self.update_candidates()

    def update_candidates(self):
        self.component_names = collect_component_candidates_names(
            self.target_product, self.datasource
        )
        self.selected_component_names = self.component_names

    def _selected_component_names_default(self):
        return self.component_names


def collect_component_candidates_names(target_product, datasource):
    """ Collect the name of all product components in the datasource targeting
    the specified product.
    """
    filters = {'target_product': target_product}
    candidates = datasource.get_objects_by_type("product_components",
                                                filter_by=filters)
    candidates_names = [comp.name for comp in candidates]
    return candidates_names


def build_component_descr_editor(expert_mode):
    """ Build a table editor to edit a list of ComponentDescription.
    """
    columns = [ObjectColumn(name='name', style="readonly",
                            label="Component name",
                            tooltip="Name of component to build product with. "
                                    "Must exist in user data.")]
    if expert_mode:
        tooltip = ("Enter the expression to compute the component's "
                   "concentration, as a function of the total product "
                   "concentration ('product_concentration') and the component "
                   "assay names.")

        columns += [ObjectColumn(name='concentration_exps',
                                 label="Component concentration expression",
                                 tooltip=tooltip)]

    editor = TableEditor(
        columns=columns,
        editable=True,
        sortable=False,
        deletable=True,
    )

    return editor


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    builder = ProductBuilder(datasource=SimpleDataSource())
    builder.configure_traits()
    builder.build_product()
