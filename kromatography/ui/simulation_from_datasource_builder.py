import logging

from traits.api import Bool, Instance, Property, Str
from traitsui.api import HGroup, Item, OKCancelButtons, VGroup, View
from pyface.api import warning

from app_common.traits.has_traits_utils import is_has_traits_almost_equal

from kromatography.model.data_source import DataSource
from kromatography.model.discretization import Discretization
from kromatography.model.solver import Solver
from kromatography.model.sensitivity import Sensitivity
from kromatography.model.simulation import Simulation
from kromatography.ui.simulation_builder import SimulationBuilder

SIMULATION_STEP_TYPES = ['Equilibration', 'Load', 'Wash', 'Elution', 'Strip']

logger = logging.getLogger(__name__)


class SimulationFromDatasourceBuilder(SimulationBuilder):
    """ Build a simulation from datasource components.

    Class to support selecting all attributes to build a Simulation purely
    from both study and user datasource elements, as well as binding and
    transport models.
    """
    #: User Datasource to pull standard data from
    datasource = Instance(DataSource)

    #: Product this simulation is for. Must be valid product name in dataSource
    product_name = Str

    #: Instance of the product the output simulation should get
    product = Property(depends_on="product_name")

    #: Can the product be changed?
    product_change_allowed = Bool(True)

    #: Name of the column to use in the simulation
    column_name = Str

    #: Instance of the column the output simulation should get
    column = Property(depends_on="column_name")

    #: Name of the source method to build the simulation's method from
    method_name = Str

    #: Datasource method the output simulation's method is built from
    method = Property(depends_on="method_name")

    def __init__(self, **traits):
        super(SimulationFromDatasourceBuilder, self).__init__(**traits)
        if "product_name" in traits:
            self.product_change_allowed = False

    def traits_view(self):
        """ Build the valid values for each parameters, and build the view.
        """
        product_name_editor = self._build_enum_editor_for_type("products")
        column_name_editor = self._build_enum_editor_for_type("columns")
        method_name_editor = self._build_enum_editor_for_type("methods")
        bind_model_name_editor = self._build_enum_editor_for_type(
            "binding_models"
        )
        transp_model_name_editor = self._build_enum_editor_for_type(
            "transport_models"
        )

        view = View(
            VGroup(
                Item("simulation_name"),
                HGroup(
                    Item("product_name", editor=product_name_editor,
                         enabled_when="product_change_allowed"),
                    Item("column_name", editor=column_name_editor),
                ),
                HGroup(
                    Item("method_name", editor=method_name_editor),
                    Item("first_simulated_step_name"),
                    Item("last_simulated_step_name"),
                    Item("initial_buffer_name",
                         label="Override initial buffer with",
                         tooltip="Buffer the resin was in before the first "
                                 "simulated step. Leave blank to infer from "
                                 "method."),
                    show_border=True, label="Simulation method",
                ),
                VGroup(
                    Item("binding_model_name", editor=bind_model_name_editor),
                    Item("transport_model_name",
                         editor=transp_model_name_editor),
                    Item("solver_type"),
                    Item("discretization_type"),
                    show_border=True, label="CADET models",
                ),
            ),
            buttons=OKCancelButtons,
            title="Configure Simulations",
            width=400, height=400,
            resizable=True
        )

        return view

    def to_simulation(self):
        """ Returns a new Simulation object from current builder.
        """
        from kromatography.model.factories.method import \
            build_sim_method_from_method

        sim_method = build_sim_method_from_method(
            self.method, self.first_simulated_step_name,
            self.last_simulated_step_name, initial_buffer=self.initial_buffer,
        )

        simulation = Simulation(
            name=self.simulation_name,
            column=self.column,
            method=sim_method,
            first_simulated_step=self.first_simulated_step_name,
            last_simulated_step=self.last_simulated_step_name,
            transport_model=self.transport_model,
            binding_model=self.binding_model,
            solver=Solver(),
            discretization=Discretization(),
            sensitivity=Sensitivity(),
        )

        # Product is a property of a simulation, which isn't set until we set
        # the method.
        if not is_has_traits_almost_equal(simulation.product, self.product):
            msg = ("The simulation's product (read in the method) doesn't "
                   "match the selected product. Please review the product and"
                   " method selected.")
            logger.info(msg)
            warning(None, msg, "Review simulation data")

        return simulation

    # Traits listener methods -------------------------------------------------

    def _method_name_changed(self):
        if self.step_names:
            self.first_simulated_step_name = self.step_names[0]
            self.last_simulated_step_name = self.step_names[-1]

    # Property getters/setters ------------------------------------------------

    def _get_column(self):
        return self._get_object_clone_from_name("columns", self.column_name)

    def _get_product(self):
        return self._get_object_clone_from_name("products", self.product_name)

    def _get_method(self):
        if self.method_name:
            method = self._get_object_clone_from_name("methods",
                                                      self.method_name)
            method.initial_buffer = self.initial_buffer
            return method

    def _get_step_names(self):
        if self.method_name:
            return [step.name for step in self.method.method_steps]
        else:
            return []


if __name__ == "__main__":
    from kromatography.model.data_source import SimpleDataSource
    from kromatography.model.tests.sample_data_factories import \
        make_sample_study

    study = make_sample_study()
    sim_builder = SimulationFromDatasourceBuilder(
        datasource=SimpleDataSource(), study_datasource=study.study_datasource
    )
    sim_builder.configure_traits()
