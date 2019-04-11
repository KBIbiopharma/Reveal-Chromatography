import logging

from traits.api import Button, HasStrictTraits, Instance, Property
from traitsui.api import HGroup, InstanceEditor, Item, ModelView,\
        OKCancelButtons, Spring, Tabbed, TextEditor, VGroup, View

from kromatography.model.simulation import Simulation
from kromatography.model.solver import Solver
from kromatography.model.discretization import Discretization
from kromatography.ui.solver_model_view import SolverView
from kromatography.ui.discretization_model_view import DiscretizationView
from kromatography.ui.general_rate_model_view import GeneralRateModelView
from kromatography.ui.steric_mass_action_model_view import \
    StericMassActionModelView
from kromatography.ui.ph_dependent_steric_mass_action_model_view import \
    PhDependentStericMassActionModelView
from kromatography.model.binding_model import STERIC_BINDING_MODEL, \
    PH_STERIC_BINDING_MODEL

logger = logging.getLogger(__name__)


class SimulationView(ModelView):
    """ View for a Simulation object.
    """
    #: Simulation model to display
    model = Instance(Simulation)

    #: ModelView for the model's transport model
    transport_model_view = Property(depends_on="model")

    #: ModelView for the model's binding model
    binding_model_view = Property(depends_on="model")

    #: Button to expose all remaining parameters of a simulation
    show_advanced_parameters = Button("Show Advanced Parameters")

    #: Container of the additional advanced simulation parameters
    simulation_details = Property(depends_on="model")

    def default_traits_view(self):
        view = View(
            VGroup(
                Item('model.name'),
                Item('model.description',
                     editor=TextEditor(auto_set=True, enter_set=True),
                     style="custom"),
                Tabbed(
                    VGroup(
                        Item('transport_model_view', editor=InstanceEditor(),
                             style="custom", show_label=False),
                        label="Transport Model"
                    ),
                    VGroup(
                        Item('binding_model_view', editor=InstanceEditor(),
                             style="custom", show_label=False),
                        label="Binding Model"
                    ),
                    springy=True
                ),
                HGroup(
                    Item('model.run_status', style="readonly"),
                    Spring(),
                    Item('show_advanced_parameters', show_label=False),
                ),
            ),
            resizable=True,
        )
        return view

    # -------------------------------------------------------------------------
    # Traits listeners
    # -------------------------------------------------------------------------

    def _show_advanced_parameters_fired(self):
        self.simulation_details.edit_traits(kind="livemodal")

    def _get_simulation_details(self):
        return _SimulationDetails(discretization=self.model.discretization,
                                  solver=self.model.solver)

    def _get_transport_model_view(self):
        return GeneralRateModelView(model=self.model.transport_model)

    def _get_binding_model_view(self):
        if self.model.binding_model.model_type == STERIC_BINDING_MODEL:
            return StericMassActionModelView(model=self.model.binding_model)
        elif self.model.binding_model.model_type == PH_STERIC_BINDING_MODEL:
            return PhDependentStericMassActionModelView(
                model=self.model.binding_model
            )
        else:
            msg = "Trying to display a binding model of type {}".format(
                self.model.binding_model.model_type
            )
            logger.exception(msg)
            raise NotImplementedError(msg)


class _SimulationDetails(HasStrictTraits):
    """ Utility class to contain all advanced parameters of a simulation.

    FIXME: should we add the sensitivity parameters?
    """

    solver = Instance(Solver)

    solver_view = Property(depends_on="solver")

    discretization = Instance(Discretization)

    discretization_view = Property(depends_on="solver")

    view = View(
        VGroup(
            Item("solver_view", editor=InstanceEditor(), style="custom",
                 show_label=False),
            show_border=True, label="CADET Solver Parameters"
        ),
        VGroup(
            Item("discretization_view", editor=InstanceEditor(),
                 style="custom", show_label=False),
            show_border=True, label="Discretization Parameters"
        ),
        resizable=True,
        buttons=OKCancelButtons,
    )

    def _get_solver_view(self):
        return SolverView(model=self.solver)

    def _get_discretization_view(self):
        return DiscretizationView(model=self.discretization)


if __name__ == '__main__':
    # setting up model
    from kromatography.model.tests.sample_data_factories import \
        make_sample_simulation

    sim = make_sample_simulation()
    solution_view = SimulationView(model=sim)
    solution_view.configure_traits()
