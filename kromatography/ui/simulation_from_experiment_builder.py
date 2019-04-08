""" UI to select a set of experiments, transport and binding models and build
simulations from them.
"""
import logging

from pyface.api import warning
from traits.api import Bool, DelegatesTo, Instance, List, on_trait_change, \
    Property, Str
from traitsui.api import Action, CancelButton, Handler, HGroup, \
    InstanceEditor, Item, Label, ListStrEditor, VGroup, View

from app_common.std_lib.filepath_utils import add_suffix_if_exists

from kromatography.ui.experiment_selector import ExperimentSelector
from kromatography.ui.simulation_builder import SimulationBuilder
from kromatography.model.study import Study
from kromatography.model.factories.simulation import generate_sim_name
from kromatography.model.simulation import Simulation
from kromatography.model.factories.method import build_sim_method_from_method
from kromatography.model.method import StepLookupError
from kromatography.model.discretization import Discretization
from kromatography.model.solver import Solver
from kromatography.model.sensitivity import Sensitivity

logger = logging.getLogger(__name__)

# Add a create button to any traitsui view that triggers creation and can be
# disabled
CreateButton = Action(name='Create', action="_on_create",
                      enabled_when='can_create')


class SimulationGroupBuilderHandler(Handler):
    """ Have the create button just close the window, like the OK button. The
    actual create will happen in the calling code.
    """
    def _on_create(self, info):
        res = self.close(info, False)
        self._on_close(info)
        return res


class SimulationFromExperimentBuilder(SimulationBuilder):
    """ Build a list of simulations from experiments and models from datasource

    Unlike its parent class, this builder is capable of building 1 or more
    simulations, and builds them from experiments selected as well as common
    parameters: binding model, transport model, first and last simulated steps,
    initial buffer, solver, discretization model.

    The output simulation names are automatically generated from their source
    experiment, but avoiding collisions with existing simulations in the target
    study.
    """
    #: The list of target simulations to be created
    simulation_names = List(Str)

    #: UI to select a list of Experiments
    experiment_selector = Instance(ExperimentSelector, ())

    #: List of experiments to create simulations from
    experiment_selected = DelegatesTo("experiment_selector")

    #: Study and its datasource (with known sims, binding & transport models)
    target_study = Instance(Study)

    #: Can an optimizer be created from the current setup?
    can_create = Property(Bool, depends_on="experiment_selected, "
                                           "transport_model, "
                                           "binding_model")

    def __init__(self, **traits):
        if 'target_study' not in traits:
            msg = 'Cannot create a SimulationFromExperimentBuilder without a' \
                  ' target study.'
            logger.error(msg)
            raise ValueError(msg)

        initial_buffer_name = traits.pop('initial_buffer_name', None)
        super(SimulationFromExperimentBuilder, self).__init__(**traits)

        self.study_datasource = self.target_study.study_datasource
        if initial_buffer_name:
            self.initial_buffer_name = initial_buffer_name

    def traits_view(self):
        transp_model_name_editor = self._build_enum_editor_for_type(
            "transport_models"
        )
        bind_model_name_editor = self._build_enum_editor_for_type(
            "binding_models"
        )

        name_editor = ListStrEditor(
            title='Simulation names (double click to modify)',
            horizontal_lines=True, editable=True, multi_select=False,
        )
        view = View(
            Label("Select a set of experiments to build simulations from, as "
                  "well as the type of binding and transport models."),
            HGroup(
                Item("experiment_selector", editor=InstanceEditor(),
                     style="custom", show_label=False),
                Item("simulation_names", editor=name_editor, show_label=False),
            ),
            HGroup(
                Item("first_simulated_step_name"),
                Item("last_simulated_step_name"),
                Item("initial_buffer_name",
                     label="Override initial buffer with",
                     tooltip="Buffer the resin was in before the first "
                             "simulated step. Leave blank to infer from "
                             "experiment."),
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
            handler=SimulationGroupBuilderHandler(),
            buttons=[CancelButton, CreateButton],
            title="Configure Simulations"
        )
        return view

    # Public interface --------------------------------------------------------

    def to_simulations(self):
        """ Returns a list of simulations built from each experiment selected.
        """
        fstep, lstep = (self.first_simulated_step_name,
                        self.last_simulated_step_name)
        new_simulations = []
        for exp_name, sim_name in zip(self.experiment_selected,
                                      self.simulation_names):
            experiment = self.target_study.search_experiment_by_name(exp_name)
            try:
                sim_method = build_sim_method_from_method(
                    experiment.method, fstep, lstep,
                    initial_buffer=self.initial_buffer,
                )
            except StepLookupError as e:
                msg = "Failed to find the start/stop method steps for " \
                      "simulation {}. Its experiment doesn't seem to contain" \
                      " {} or {}. Please review these step names or treat " \
                      "this simulation separately from the others. Aborting..."
                msg = msg.format(sim_name, fstep, lstep)
                details = " Details: error was {}".format(e)
                logger.error(msg + details)
                warning(None, msg)
                return []

            simulation = Simulation(
                name=sim_name,
                column=experiment.column.clone_traits(copy="deep"),
                method=sim_method,
                first_simulated_step=self.first_simulated_step_name,
                last_simulated_step=self.last_simulated_step_name,
                transport_model=self.transport_model,
                binding_model=self.binding_model,
                source_experiment=experiment,
                solver=Solver(),
                discretization=Discretization(),
                sensitivity=Sensitivity(),
            )
            new_simulations.append(simulation)

        return new_simulations

    # Traits listener methods -------------------------------------------------

    @on_trait_change('experiment_selected')
    def update_simulation_names(self):
        """ Generate some default simulation names that don't conflict with
        existing simulations in target study.
        """
        self.simulation_names = generate_sim_names(self.experiment_selected,
                                                   self.target_study)

    # Property getters/setters ------------------------------------------------

    def _get_step_names(self):
        """ Collect the union of all step names for all experiment.
        """
        all_step_names = []
        for exp in self.target_study.experiments:
            exp_steps = [step.name for step in exp.method.method_steps]
            all_step_names.extend(exp_steps)

        return sorted(list(set(all_step_names)))

    def _get_can_create(self):
        can_create = self.experiment_selected and self.transport_model and \
            self.binding_model
        return can_create


def generate_sim_names(expt_names, study):
    """ Generate a list of simulation names for experiment names provided which
    are not already present in the study's existing simulations.
    """
    names = []
    existing_sim_names = [sim.name for sim in study.simulations]
    for expt in expt_names:
        candidate = generate_sim_name(expt)
        candidate = add_suffix_if_exists(candidate, existing_sim_names)
        names.append(candidate)
    return names


if __name__ == "__main__":
    from kromatography.model.tests.sample_data_factories import \
        make_sample_study

    study = make_sample_study(num_exp=5)
    sim_builder = SimulationFromExperimentBuilder(
        experiment_selector=ExperimentSelector(study=study),
        target_study=study,
    )
    sim_builder.configure_traits()
    print("selected: {}".format(sim_builder.experiment_selected))
