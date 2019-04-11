import logging

from kromatography.model.lazy_simulation import LazyLoadingSimulation, \
    Simulation
from kromatography.model.factories.transport_model import \
    create_transport_model
from kromatography.model.factories.binding_model import create_binding_model
from kromatography.model.factories.method import build_sim_method_from_method

SIM_NAME_PATTERN = "Sim: {}"

logger = logging.getLogger(__name__)


def generate_sim_name(expt_name):
    """ Generate a simulation name from an experiment name.
    """
    return SIM_NAME_PATTERN.format(expt_name)


def build_simulation_from_experiment(experiment, binding_model=None,
                                     transport_model=None, name="",
                                     fstep='Load', lstep='Strip',
                                     initial_buffer=None, lazy_loading=False,
                                     **traits):
    """ Build a Simulation object given an experiment and some models.

    Now only used for testing purposes.

    Parameters
    ----------
    experiment : Experiment
        Source experiment to build the simulation from.

    binding_model : BindingModel [OPTIONAL]
        Binding model to build the simulation from. If not provided, a default
        model with default value will be generated.

    transport_model : TransportModel [OPTIONAL]
        Transport model to build the simulation from. If not provided, a
        default model with default value will be generated.

    name : str [OPTIONAL]
        Name of the future simulation

    fstep : str [OPTIONAL, default='Load']
        Name of the first step to simulate. Defaults to 'Load'.

    lstep : str [OPTIONAL, default='Strip']
        Name of the last step to simulate. Defaults to 'Strip'.

    initial_buffer : Buffer [OPTIONAL]
        Buffer instance to use as initial buffer for the simulation method. If
        not provided, the buffer in the experimental step before the first
        simulated step will be used.

    lazy_loading : bool [OPTIONAL, default=False)
        Should the resulting simulation be of LazyLoadingSimulation type?
    """

    if not name:
        name = generate_sim_name(experiment.name)

    # NOTE: The number of components is : product components + cation
    # The first component is always the cation, followed by the product
    # components.
    num_components = len(experiment.product.product_component_names) + 1

    if binding_model is None:
        binding_model = create_binding_model(num_components)

    if transport_model is None:
        transport_model = create_transport_model(num_components)

    # The solver, discretization and other simulation params are set to
    # defaults (configured by CADET simulation builder)
    sim_method = build_sim_method_from_method(
        experiment.method, first_simulated_step=fstep,
        last_simulated_step=lstep, initial_buffer=initial_buffer,
    )

    simulation = Simulation(
        name=name,
        column=experiment.column.clone_traits(copy="deep"),
        transport_model=transport_model,
        binding_model=binding_model,
        source_experiment=experiment,
        method=sim_method,
        **traits
    )
    if lazy_loading:
        simulation = LazyLoadingSimulation.from_simulation(simulation)

    return simulation
