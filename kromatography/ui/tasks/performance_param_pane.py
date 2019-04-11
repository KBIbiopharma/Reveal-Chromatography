from pyface.tasks.api import TraitsDockPane
from traits.api import Instance, List, Property
from traitsui.api import Item, View, TableEditor, HGroup
from traitsui.table_column import ObjectColumn

from kromatography.model.product import Product
from kromatography.model.study import Study
from kromatography.model.chromatography_results import PerformanceData
from kromatography.utils.traitsui_utils import NoAutoTextEditor
from app_common.traitsui.unit_scalar_editor import \
    UnitScalarEditor
from app_common.traitsui.unit_scalar_column import \
    UnitScalarColumn


def build_performance_data_table_editor():
    """ Build a table editor to display a list of PerformanceParameters of
    Simulations modeling the provided product.
    """
    pool_conc_tooltip = 'Sum of concentration of all product components'
    purity_tooltip = 'Purities (c_comp/c_all_comps * 100) of all product ' \
                     'components.'

    columns = [
        ObjectColumn(name='name', label='Simulation Name',
                     editor=NoAutoTextEditor()),
        UnitScalarColumn(name='start_collect_time',
                         label='Start Collect Time',
                         editor=UnitScalarEditor()),
        UnitScalarColumn(name='stop_collect_time',
                         label='Stop Collect Time',
                         editor=UnitScalarEditor()),
        UnitScalarColumn(name='pool_volume', label='Pool Volume',
                         editor=UnitScalarEditor()),
        UnitScalarColumn(name='step_yield', label='Yield',
                         editor=UnitScalarEditor()),
        UnitScalarColumn(name='pool_concentration',
                         label='Pool Concentration',
                         tooltip=pool_conc_tooltip,
                         editor=UnitScalarEditor()),
        ObjectColumn(name='pool_purities',
                     label='Pool Product Component Purities',
                     tooltip=purity_tooltip),
    ]

    editor = TableEditor(columns=columns, deletable=False, auto_size=True,
                         sortable=True, editable=False)
    return editor


class PerformanceParamPane(TraitsDockPane):
    """ View on a Performance Parameter Data and JobManager object
    """

    # -------------------------------------------------------------------------
    # 'TaskPane' interface
    # -------------------------------------------------------------------------

    id = 'krom.performance_param_pane'

    name = 'Simulation Performance Parameters'

    # -------------------------------------------------------------------------
    # PerformanceParamPane
    # -------------------------------------------------------------------------

    #: Study monitored
    study = Instance(Study)

    #: Target product
    product = Property(Instance(Product), depends_on='study.product')

    performance_data = Property(
        List(PerformanceData),
        depends_on='study:simulations.perf_param_data_event'
    )

    # -------------------------------------------------------------------------
    # HasTraits interface
    # -------------------------------------------------------------------------

    def traits_view(self):
        """ The view used to construct the dock pane's widget.
        """
        perf_data_editor = build_performance_data_table_editor()

        view = View(
            HGroup(
                Item('performance_data', show_label=False,
                     editor=perf_data_editor),
            ),
            resizable=True
        )
        return view

    # Traits listeners --------------------------------------------------------

    def _get_performance_data(self):
        perf_data = []
        for sim in self.study.simulations:
            if sim.output is not None:
                perf_data.append(sim.output.performance_data)
            else:
                # if sim hasn't been run yet, at least append name to table
                perf_data.append(PerformanceData(name=sim.name))

        return perf_data

    def _get_product(self):
        return self.study.product
