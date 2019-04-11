import logging

from scimath.units.api import UnitScalar, UnitArray

from kromatography.model.api import Buffer, Chemical, Column, ColumnType, \
    Component, Method, ProductComponent, Resin, System, SystemType
from kromatography.model.factories.transport_model import \
    create_transport_model
from kromatography.model.solution_with_product import SolutionWithProduct
from kromatography.ui.factories.product import ProductBuilder
from kromatography.ui.buffer_model_view import BufferView
from kromatography.ui.chemical_model_view import ChemicalView
from kromatography.ui.column_model_view import ColumnView
from kromatography.ui.column_prep_view import ColumnPrepView
from kromatography.ui.column_type_model_view import ColumnTypeView
from kromatography.ui.component_model_view import ComponentView
from kromatography.ui.product_component_model_view import ProductComponentView
from kromatography.ui.general_rate_model_view import GeneralRateModelView
from kromatography.ui.method_model_view import MethodModelView
from kromatography.ui.product_chooser_view import ProductChooser
from kromatography.ui.resin_model_view import ResinView
from kromatography.ui.system_model_view import SystemView
from kromatography.ui.system_type_model_view import SystemTypeView
from kromatography.ui.solution_with_product_view import \
    SolutionWithProductView
import kromatography.utils.chromatography_units as chr_units
from kromatography.ui.factories.binding_model import BindingModelBuilder

logger = logging.getLogger(__name__)


def request_new_method(study, kind="livemodal", **traits):
    """ Build a new instance of a data model invoking its UI editor.

    The provided study may contain data necessary to create the model.

    Parameters
    ----------
    study : Study
        Study that this load solution configuration tool will be contributed
        to.

    kind : None or str
        Kind of the dialog. Set to None to make it non-blocking. Useful for
        testing purposes.

    traits : dict
        Attributes of the created object. Used to override the defaults.
    """
    model = Method(name="New method")
    view = MethodModelView(model=model, datasource=study.study_datasource)
    return _show_view_and_return_model(view, kind)


def request_new_load_solution(study, kind="livemodal", **traits):
    """ Build a new instance of a data model invoking its UI editor.

    The provided study may contain data necessary to create the model.

    Parameters
    ----------
    study : Study
        Study that this load solution configuration tool will be contributed
        to.

    kind : None or str
        Kind of the dialog. Set to None to make it non-blocking. Useful for
        testing purposes.

    traits : dict
        Attributes of the created object. Used to override the defaults.
    """
    if not study.product_set:
        prod_chooser = ProductChooser(datasource=study.datasource)
        ui = prod_chooser.edit_traits(kind=kind)
        if kind is None:
            return ui
        elif ui.result:
            study.product = prod_chooser.selected_product
        else:
            return

    model = SolutionWithProduct(name="New load", solution_type="Load",
                                product=study.product, **traits)
    view = SolutionWithProductView(model=model, datasource=study.datasource)
    return _show_view_and_return_model(view, kind)


def request_new_buffer(study, kind="livemodal", **traits):
    """ Build a new instance of a buffer invoking its UI editor.

    The provided study may contain data necessary to create the model.

    Parameters
    ----------
    study : Study
        Study that this load solution configuration tool will be contributed
        to.

    kind : None or str
        Kind of the dialog. Set to None to make it non-blocking. Useful for
        testing purposes.

    traits : dict
        Attributes of the created object. Used to override the defaults.
    """
    model = Buffer(name="New buffer", **traits)
    view = BufferView(model=model, datasource=study.datasource)
    return _show_view_and_return_model(view, kind)


def request_new_system(study, kind="livemodal", **traits):
    """ Build a new instance of a System invoking its UI editor.

    The provided study may contain data necessary to create the model.

    Parameters
    ----------
    study : Study
        Study that this load solution configuration tool will be contributed
        to.

    kind : None or str
        Kind of the dialog. Set to None to make it non-blocking. Useful for
        testing purposes.

    traits : dict
        Attributes of the created object. Used to override the defaults.
    """
    from kromatography.ui.system_model_view import SystemTypeSelector

    selector = SystemTypeSelector(datasource=study.datasource)
    ui = selector.edit_traits(kind=kind)
    if kind is None:
        return ui
    elif ui.result:
        type = selector.selected_system_type
    else:
        return

    model = System(name="New System", system_type=type,
                   abs_path_length=UnitScalar(0, units="cm"), **traits)
    view = SystemView(model=model, datasource=study.datasource,
                      _allow_type_editing=False)
    return _show_view_and_return_model(view, kind)


def request_new_column(study, kind="livemodal", **traits):
    """ Build a new instance of a column invoking its UI editor.

    The provided study may contain data necessary to create the model.

    Parameters
    ----------
    study : Study
        Study that this load solution configuration tool will be contributed
        to.

    kind : None or str
        Kind of the dialog. Set to None to make it non-blocking. Useful for
        testing purposes.

    traits : dict
        Attributes of the created object, as well as the column_prep to build
        the column from. Other traits used to override the defaults.
    """
    column_prep = traits.pop("column_prep", None)
    if column_prep is None:
        column_prep = ColumnPrepView(datasource=study.datasource)
        ui = column_prep.edit_traits(kind=kind)

        if kind is None:
            return ui
        elif not ui.result:
            return

    model = Column(name="New column",
                   column_type=column_prep.column_type,
                   resin=column_prep.resin, **traits)
    view = ColumnView(model=model)
    return _show_view_and_return_model(view, kind)


def request_transport_model(study, kind="livemodal", **traits):
    """ Build a new instance of a transport_model invoking its UI editor.

    The provided study may contain data necessary to create the model.

    Parameters
    ----------
    study : Study
        Study that this transport_model configuration tool will be contributed
        to.

    kind : None or str
        Kind of the dialog. Set to None to make it non-blocking. Useful for
        testing purposes.

    traits : dict
        Attributes of the created object. Used to override the defaults.
    """
    if not study.product_set:
        prod_chooser = ProductChooser(datasource=study.datasource)
        ui = prod_chooser.edit_traits(kind=kind)
        if kind is None:
            return ui
        elif ui.result:
            study.product = prod_chooser.selected_product
        else:
            return

    traits.setdefault("name", "New GR model")
    traits["target_product"] = study.product.name

    # Reminder: binding model describes Cation component as its first component
    component_names = ["Cation"] + study.product.product_component_names
    model = create_transport_model(study.product.num_components+1,
                                   component_names=component_names, **traits)
    view = GeneralRateModelView(model=model)
    return _show_view_and_return_model(view, kind)


def request_binding_model(study, kind="livemodal", **traits):
    """ Build a new instance of a binding_model invoking its UI editor.

    The provided study may contain data necessary to create the model.

    Parameters
    ----------
    study : Study
        Study that this binding_model configuration tool will be contributed
        to.

    kind : None or str
        Kind of the dialog. Set to None to make it non-blocking. Useful for
        testing purposes.

    traits : dict
        Attributes of the created object. Used to override the defaults.
    """
    if not study.product_set:
        prod_chooser = ProductChooser(datasource=study.datasource)
        ui = prod_chooser.edit_traits(kind=kind)
        if kind is None:
            return ui
        elif ui.result:
            study.product = prod_chooser.selected_product
        else:
            return

    traits["target_product"] = study.product.name
    # Reminder: binding model describes Cation component as its first component
    component_names = study.product.product_component_names
    view = BindingModelBuilder(_target_component_names=component_names,
                               **traits)
    return _show_view_and_return_model(view, kind)


# SimpleDataSource factories ##################################################


def request_new_chemical(datasource, kind="livemodal", **traits):
    """ Build a new instance of a component invoking its UI editor.

    Parameters
    -----------
    datasource : Instance(SimpleDataSource)
        User datasource targeted to be contributed to.

    kind : str
        Should be set to None to make it non-blocking (only useful for testing
        purposes).

    traits : dict
        Attributes of the created object. Used to override the defaults.

    Returns
    -------
    Tuple with the object created and the data to create it since it is to be
    contributed to the SimpleDataSource.
    """
    mol_weight_units = chr_units.gram_per_mol
    defaults = dict(name="New Chemical",
                    molecular_weight=UnitScalar(0.0, units=mol_weight_units),
                    state="Solid")
    defaults.update(traits)

    model = Chemical(**defaults)
    view = ChemicalView(model=model, datasource=datasource)
    return _show_view_and_return_model(view, kind)


def request_new_resin(datasource, kind="livemodal", **traits):
    """ Build a new instance of a component invoking its UI editor.

    Parameters
    -----------
    datasource : Instance(SimpleDataSource)
        User datasource targeted to be contributed to.

    kind : str
        Should be set to None to make it non-blocking (only useful for testing
        purposes).

    traits : dict
        Attributes of the created object. Used to override the defaults.

    Returns
    -------
    Tuple with the object created and the data to create it since it is to be
    contributed to the SimpleDataSource.
    """
    defaults = dict(
        name="New Resin", resin_type='CEX', ligand='SO3',
        average_bead_diameter=UnitScalar(0.0, units='um'),
        ligand_density=UnitScalar(0.0, units=chr_units.milli_molar),
        settled_porosity=UnitScalar(0.0, units=chr_units.fraction)
    )
    defaults.update(traits)

    model = Resin(**defaults)
    view = ResinView(model=model)
    return _show_view_and_return_model(view, kind)


def request_new_column_type(datasource, kind="livemodal", **traits):
    """ Build a new instance of a ColumnType invoking its UI editor.

    Parameters
    -----------
    datasource : Instance(SimpleDataSource)
        User datasource targeted to be contributed to.

    kind : str
        Should be set to None to make it non-blocking (only useful for testing
        purposes).

    traits : dict
        Attributes of the created object. Used to override the defaults.

    Returns
    -------
    Tuple with the object created and the data to create it since it is to be
    contributed to the SimpleDataSource.
    """
    defaults = dict(name='New Column Type', manufacturer='manufacturer',
                    manufacturer_name='New Column Type',
                    diameter=UnitScalar(0.0, units='cm'),
                    bed_height_range=UnitArray([0., 0.], units='cm'),
                    bed_height_adjust_method='None')
    defaults.update(traits)
    model = ColumnType(**defaults)
    view = ColumnTypeView(model=model)
    return _show_view_and_return_model(view, kind)


def request_new_system_type(datasource, kind="livemodal", **traits):
    """ Build a new instance of a SystemType invoking its UI editor.

    Parameters
    -----------
    datasource : Instance(SimpleDataSource)
        User datasource targeted to be contributed to.

    kind : str
        Should be set to None to make it non-blocking (only useful for testing
        purposes).

    traits : dict
        Attributes of the created object. Used to override the defaults.

    Returns
    -------
    Tuple with the object created and the data to create it since it is to be
    contributed to the SimpleDataSource.
    """
    defaults = dict(
        name='New System Type', manufacturer='manufacturer',
        manufacturer_name='New System Type',
        flow_range=UnitArray([0., 0.], units=chr_units.ml_per_min)
    )
    defaults.update(traits)
    model = SystemType(**defaults)
    view = SystemTypeView(model=model)
    return _show_view_and_return_model(view, kind)


def request_new_component(datasource, kind="livemodal", **traits):
    """ Build a new instance of a chemical component invoking its UI editor.

    Parameters
    -----------
    datasource : Instance(SimpleDataSource)
        User datasource targeted to be contributed to.

    kind : str
        Should be set to None to make it non-blocking (only useful for testing
        purposes).

    traits : dict
        Attributes of the created object. Used to override the defaults.

    Returns
    -------
    Tuple with the object created and the data to create it since it is to be
    contributed to the SimpleDataSource.
    """
    defaults = dict(name="New Component", charge=UnitScalar(0.0, units='1'),
                    pKa=UnitScalar(0.0, units='1'))
    defaults.update(traits)
    model = Component(**defaults)
    view = ComponentView(model=model)
    return _show_view_and_return_model(view, kind)


def request_new_product(datasource, kind="livemodal", **traits):
    """ Build a new instance of a Product invoking its UI editor.
    This method returns both the object created and the data to create it since
    it is to be contributed to the SimpleDataSource which contains both a data
    and an object catalog.

    Parameters
    -----------
    datasource : Instance(SimpleDataSource)
        User datasource targeted to be contributed to.

    kind : str
        Should be set to None to make it non-blocking (only useful for testing
        purposes).

    traits : dict
        Attributes of the created object. Used to override the defaults.

    Returns
    -------
    Tuple with the object created and the data to create it since it is to be
    contributed to the SimpleDataSource.
    """
    defaults = dict(name="New Product", product_type="Unknown",
                    pI=UnitScalar(0, units="1"), datasource=datasource)
    defaults.update(traits)
    builder = ProductBuilder(**defaults)
    ui = builder.edit_traits(kind=kind)
    if kind is None:
        return ui
    elif ui.result:
        model = builder.build_product()
        return model
    else:
        logger.debug("Product builder view was cancelled.")


def request_new_product_component(datasource, kind="livemodal", **traits):
    """ Build a new instance of a ProdutComponent invoking its UI editor.

    Parameters
    -----------
    datasource : Instance(SimpleDataSource)
        User datasource targeted to be contributed to.

    kind : str
        Should be set to None to make it non-blocking (only useful for testing
        purposes).

    traits : dict
        Attributes of the created object. Used to override the defaults.

    Returns
    -------
    Tuple with the object created and the data to create it since it is to be
    contributed to the SimpleDataSource.
    """
    ext_coef_units = chr_units.extinction_coefficient_unit
    defaults = dict(
        name="New_Component", target_product="Unknown",
        molecular_weight=UnitScalar(0.0, units=chr_units.kilo_dalton),
        extinction_coefficient=UnitScalar(0.0, units=ext_coef_units)
    )
    defaults.update(traits)

    model = ProductComponent(**defaults)
    view = ProductComponentView(model=model)
    return _show_view_and_return_model(view, kind)


def request_transport_model_ds(datasource, kind="livemodal", **traits):
    """ Build a new instance of a transport_model invoking its UI editor.

    The provided study may contain data necessary to create the model.

    Parameters
    ----------
    datasource : Instance(SimpleDataSource)
        User datasource targeted to be contributed to.

    kind : None or str
        Kind of the dialog. Set to None to make it non-blocking. Useful for
        testing purposes.

    traits : dict
        Attributes of the created object. Used to override the defaults.
    """
    target_product = traits.pop("target_product", None)
    if target_product is None:
        prod_chooser = ProductChooser(datasource=datasource)
        ui = prod_chooser.edit_traits(kind=kind)
        if kind is None:
            return ui
        elif ui.result:
            target_product = prod_chooser.selected_product
        else:
            return

    traits.setdefault("name", "New GR model")
    traits["target_product"] = target_product.name
    # Reminder: binding model describes Cation component as its first component
    component_names = ["Cation"] + target_product.product_component_names
    model = create_transport_model(target_product.num_components + 1,
                                   component_names=component_names, **traits)
    view = GeneralRateModelView(model=model)
    return _show_view_and_return_model(view, kind)


def request_binding_model_ds(datasource, kind="livemodal", **traits):
    """ Build a new instance of a binding_model invoking its UI editor.

    The provided study may contain data necessary to create the model.

    Parameters
    ----------
    datasource : Instance(SimpleDataSource)
        User datasource targeted to be contributed to.

    kind : None or str
        Kind of the dialog. Set to None to make it non-blocking. Useful for
        testing purposes.

    traits : dict
        Attributes of the created object. Used to override the defaults.
    """
    target_product = traits.pop("target_product", None)
    if target_product is None:
        prod_chooser = ProductChooser(datasource=datasource)
        ui = prod_chooser.edit_traits(kind=kind)
        if kind is None:
            return ui
        elif ui.result:
            target_product = prod_chooser.selected_product
        else:
            return

    traits["target_product"] = target_product.name
    # Reminder: binding model describes Cation component as its first component
    component_names = ["Cation"] + target_product.product_component_names
    view = BindingModelBuilder(_target_component_names=component_names,
                               **traits)
    return _show_view_and_return_model(view, kind)


# Utilities ###################################################################


def _show_view_and_return_model(view, kind):
    """ Show view in specified kind and return its model when positive result
    and if not in test mode. Return ui object otherwise.
    """
    ui = view.edit_traits(kind=kind)

    if kind is None:
        return ui
    elif ui.result:
        return view.model


# Mapping between InMemoryDataSource entries and the factory to request a new
# entry:
STUDY_DATASOURCE_OBJECT_FACTORIES = {
    "loads": request_new_load_solution,
    "buffers": request_new_buffer,
    "columns": request_new_column,
    "systems": request_new_system,
    "methods": request_new_method,
    "binding_models": request_binding_model,
    "transport_models": request_transport_model
}

DATASOURCE_OBJECT_FACTORIES = {
    'products': request_new_product,
    'product_components': request_new_product_component,
    'resin_types': request_new_resin,
    'column_models': request_new_column_type,
    'system_types': request_new_system_type,
    'components': request_new_component,
    'chemicals': request_new_chemical,
    "binding_models": request_binding_model_ds,
    "transport_models": request_transport_model_ds
}
