
from traitsui.table_column import ObjectColumn
from traits.api import Instance, List, on_trait_change
from traitsui.api import HGroup, Item, ModelView, Spring, TableEditor, \
    TabularEditor, TextEditor, VGroup, View

from app_common.traitsui.adapters.series_tabular_adapter import \
    PandasSeriesAdapter
from app_common.traitsui.unit_scalar_editor import \
    UnitScalarEditor
from app_common.traitsui.unit_scalar_column import \
    UnitScalarColumn
from kromatography.model.product import Product
from kromatography.model.product_component import ProductComponent
from kromatography.model.product_component_assay import ProductComponentAssay
from kromatography.model.factories.product_component_assay import \
    assay_instances_from_names, assay_names_from_instances
from kromatography.utils.traitsui_utils import NoAutoTextEditor
from .product_component_model_view import COMPONENT_NAME_TOOLTIP, \
    VALID_COMP_NAME

COMPONENT_TABLE_EDITOR = TableEditor(
    columns=[
        ObjectColumn(name='name', _label="Component name",
                     editor=NoAutoTextEditor(), cell_color="lightgrey"),
        UnitScalarColumn(name='molecular_weight'),
        UnitScalarColumn(name='extinction_coefficient'),
    ],
    auto_size=True,
    sortable=False,
    row_factory=ProductComponent,
)

COMPONENT_CONC_EXPRESSION_EDITOR = TabularEditor(
    adapter=PandasSeriesAdapter(
        values_label="Concentration expression",
        values_tooltip=("Component concentration expression. Should be valid "
                        "python expressions only using the assays names below"
                        " and the total product concentration as "
                        "`product_concentration`."),
        index_label="Component name",
        index_tooltip="Component name"
    )
)


ASSAY_NAME_TOOLTIP = "Must be different from corresponding component. " + \
                     COMPONENT_NAME_TOOLTIP

ASSAY_TABLE_EDITOR = TableEditor(
    # Non-trivial validation because assays names are involved in sympy
    # expressions to compute the component's concentrations:
    columns=[
        ObjectColumn(name='name', tooltip=ASSAY_NAME_TOOLTIP,
                     editor=TextEditor(evaluate=VALID_COMP_NAME)),
    ],
    editable=True,
    sortable=False,
    deletable=True,
    row_factory=ProductComponentAssay,
    row_factory_kw={'name': 'Type_Assay_Name'}
)


class ProductView(ModelView):
    """ View for a Product
    """

    # -------------------------------------------------------------------------
    # ProductView interface
    # -------------------------------------------------------------------------

    #: Proxy for product's assays data since TableEditor works with Lists of
    #: objects.
    product_component_assays = List(ProductComponentAssay)

    # -------------------------------------------------------------------------
    # ModelView interface
    # -------------------------------------------------------------------------

    model = Instance(Product)

    # -------------------------------------------------------------------------
    # HasTraits interface
    # -------------------------------------------------------------------------

    def default_traits_view(self):
        view = View(
            VGroup(
                HGroup(
                    Item('model.name', width=300),
                    Spring(),
                    Item('model.product_type', style="readonly", label="Type"),
                ),
                Item("model.description", style="custom"),
                Item('model.pI', editor=UnitScalarEditor(), label="pI"),
                VGroup(
                    Item('model.product_components', show_label=False,
                         editor=COMPONENT_TABLE_EDITOR),
                    show_border=True, label="Product components"
                ),
                VGroup(
                    Item('model.product_component_concentration_exps',
                         editor=COMPONENT_CONC_EXPRESSION_EDITOR,
                         show_label=False),
                    show_border=True,
                    label="Product component concentration expressions"
                ),
                VGroup(
                    Item('product_component_assays', editor=ASSAY_TABLE_EDITOR,
                         show_label=False),
                    show_border=True, label="Assays"
                ),
            ),
            resizable=True,
        )
        return view

    # -------------------------------------------------------------------------
    # Traits listeners
    # -------------------------------------------------------------------------

    @on_trait_change("model.product_component_assays[]")
    def get_product_component_assays(self):
        assay_names = self.model.product_component_assays
        self.product_component_assays = assay_instances_from_names(assay_names)

    @on_trait_change("product_component_assays, product_component_assays.name,"
                     "product_component_assays[]")
    def update_model_product_component_assays(self):
        self.model.product_component_assays = assay_names_from_instances(
            self.product_component_assays
        )


if __name__ == '__main__':
    from kromatography.model.data_source import SimpleDataSource
    from kromatography.utils.app_utils import initialize_unit_parser
    initialize_unit_parser()

    s = SimpleDataSource()

    product = s.get_object_of_type('products', 'Prod001')
    product_view = ProductView(model=product)
    product_view.configure_traits()
    product.print_traits()
