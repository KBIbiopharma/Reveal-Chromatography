from traitsui.table_column import ObjectColumn

from traits.api import Instance, HasStrictTraits, Str
from traitsui.api import EnumEditor, TableEditor
from scimath.units.api import UnitScalar
from scimath.units.dimensionless import percent

from app_common.traitsui.unit_scalar_editor import UnitScalarEditor  # noqa
from app_common.traitsui.unit_scalar_column import \
    UnitScalarColumn
from kromatography.model.component import Component


class ProductAssay(HasStrictTraits):
    """ Proxy class to adapt a list of product assays and their proportions
    to a table editor
    """
    #: Name of assay
    name = Str

    #: Proportion of the assay in the product in %
    proportion = Instance(UnitScalar)

    def _proportion_default(self):
        return UnitScalar(0.0, units=percent)


def build_assay_list_editor(known_assays_names):
    """ Build a table editor to display a list of product assays.

    Parameters
    ----------
    known_assays_names : list(str)
        List of assay names available, if wanting to allow users to add assays.
    """
    if known_assays_names:
        row_factory = ProductAssay
        default_name = known_assays_names[0]
    else:
        row_factory = False
        default_name = ""

    editor = TableEditor(
        columns=[
            ObjectColumn(name='name',
                         editor=EnumEditor(values=known_assays_names)),
            UnitScalarColumn(name='proportion', editor=UnitScalarEditor())
        ],
        editable=True,
        sortable=False,
        deletable=True,
        row_factory=row_factory,
        row_factory_kw={"name": default_name},
    )
    return editor


class ChemicalComponent(Component):
    """ Proxy class to adapt a list of chemical components and their
    concentrations to a table editor
    """
    concentration = Instance(UnitScalar)

    def _concentration_default(self):
        return UnitScalar(0.0, units="mmol/L")


def build_chemical_component_editor(known_component_names):
    """ Build a table editor to display a list of chemical components.
    """
    if known_component_names:
        row_factory = ChemicalComponent
        default_name = known_component_names[0]
    else:
        row_factory = False
        default_name = ""

    editor = TableEditor(
        columns=[
            ObjectColumn(name='name',
                         editor=EnumEditor(values=known_component_names)),
            UnitScalarColumn(name='concentration', editor=UnitScalarEditor())
        ],
        editable=True,
        sortable=False,
        deletable=True,
        row_factory=row_factory,
        row_factory_kw={"name": default_name},
    )
    return editor
