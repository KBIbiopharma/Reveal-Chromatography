import logging

from traits.api import Bool, Instance, List, on_trait_change, Property, Str, \
    Unicode
from pyface.api import confirm, warning, YES

from kromatography.model.base_study import BaseStudy
from kromatography.model.api import Experiment, Product, Simulation
from kromatography.model.simulation_group import SIM_GROUP_GRID_TYPE, \
    SIM_GROUP_MC_TYPE
from kromatography.model.data_source import DataSource
from kromatography.model.product import BLANK_PRODUCT_NAME, \
    make_blank_product
from kromatography.model.study_analysis_tools import StudyAnalysisTools
from kromatography.utils.datasource_utils import \
    prepare_study_datasource_catalog
from kromatography.solve.sim_runner_manager import SimulationRunnerManager

STUDY_TYPE = "STUDY"

BLANK_SIMULATION = Simulation(name="New simulation")
BLANK_STUDY_NAME = "New study"

logger = logging.getLogger(__name__)


class SimulationNameCollisionError(ValueError):
    pass


class Study(BaseStudy):
    """ Model for a complete analysis study.

    This contains a list of simulations, a list of experiments, a set of core
    parameters used as center point for the study, and a study_datasource to
    store custom objects to be reused in the various simulations: solutions,
    custom binding models, custom transport models, ...
    """

    # -------------------------------------------------------------------------
    # Study traits
    # -------------------------------------------------------------------------

    #: Modeling Study Type
    #: (e.g. Parameter Estimation, Model Qualification, Monte Carlo)
    study_type = Str

    #: Modeling Study Purpose
    study_purpose = Str

    #: Source file for the experimental study
    exp_study_filepath = Unicode

    #: Product studied.
    product = Instance(Product)

    #: Experiments
    experiments = List(Instance(Experiment))

    #: List of simulations exploring this setup
    simulations = List(Instance(Simulation))

    #: Local source of custom configured data: binding models, solutions, ...
    study_datasource = Instance(DataSource)

    #: Container to analysis tools (simulation grids, optimizers, ...)
    analysis_tools = Instance(StudyAnalysisTools, ())

    #: Has the study been modified by anyone?
    is_blank = Bool(True)

    #: Object to collect all simulation runners, making sure they update sims
    sim_runner_manager = Instance(SimulationRunnerManager, ())

    #: Is there a Strip component in the product set?
    product_contains_strip = Property(Bool)

    # -------------------------------------------------------------------------
    # ChromatographyData traits
    # -------------------------------------------------------------------------

    type_id = Str(STUDY_TYPE)

    def __init__(self, **traits):
        super(Study, self).__init__(**traits)

        # Add attributes to contribute new entries to the object_catalog
        prepare_study_datasource_catalog(self)

    # -------------------------------------------------------------------------
    # Study interface methods
    # -------------------------------------------------------------------------

    def create_new_experiment(self):
        new_experiment = Experiment(name="New experiment")
        self.experiments.append(new_experiment)

    def add_experiments(self, experiment_list):
        """ Add multiple experiments to the study, and update its product if

        Parameters
        ----------
        experiment_list : iterable
            List (or other iterable) of experiments to add to the study.
        """
        if isinstance(experiment_list, Experiment):
            experiment_list = [experiment_list]

        super(Study, self).add_experiments(experiment_list)

        if not self.product_set:
            self.product = experiment_list[0].product

        self.update_datasource_from_experiment(experiment_list)

    def add_simulations(self, simulation_list):
        """ Add sims provided if their names don't collide with existing sims.

        Parameters
        ----------
        simulation_list : iterable
            List (or other iterable) of simulations to add to the study.

        Raises
        ------
        SimulationNameCollisionError
            If one of the simulations to be added has a name which collides
            with existing simulations.
        """
        if isinstance(simulation_list, Simulation):
            simulation_list = [simulation_list]

        existing_sim_names = {s.name for s in self.simulations}

        for sim in simulation_list:
            sim_name = sim.name
            if sim_name in existing_sim_names:
                msg = "Unable to add simulation {} to study {} because there" \
                      " is already a simulation with that name."
                msg = msg.format(sim_name, self.name)
                raise SimulationNameCollisionError(msg)

            self.simulations.append(sim)
            existing_sim_names.add(sim_name)

    def update_datasource_from_experiment(self, experiment_list):
        """ Store in the study datasource all complex objects defined in the
        experiments.
        """
        ds = self.study_datasource

        attrs_to_collect = ["column", "system", "method"]
        for exp in experiment_list:
            for attr in attrs_to_collect:
                obj = getattr(exp, attr)
                ds.set_object_of_type(attr+"s", obj)

    def update_from_experimental_study(self, experimental_study):
        """ Load experimental study data into current study.
        """
        bad_product = (self.product is not None and
                       self.product.name != BLANK_PRODUCT_NAME and
                       self.product != experimental_study.product)
        if bad_product:
            msg = (
                "Failed to load experiments because they study a different"
                " product ({} vs {})".format(self.product.name,
                                             experimental_study.product.name)
            )
            raise ValueError(msg)

        self.experiments.extend(experimental_study.experiments)

        self.product = experimental_study.product

        if not self.name.strip() or self.name == BLANK_STUDY_NAME:
            self.name = "Experimental name: {}".format(
                experimental_study.name
            )

        if not self.study_purpose.strip():
            self.study_purpose = ("Experimental purpose:\n" +
                                  experimental_study.study_purpose)

        self.update_datasource_from_experiment(experimental_study.experiments)

    def request_new_simulations_from_experiments(self):
        """ Add new simulations mirroring experiment(s) in the current study.
        """
        from kromatography.ui.simulation_from_experiment_builder import \
            SimulationFromExperimentBuilder
        from kromatography.ui.experiment_selector import ExperimentSelector

        sim_builder = SimulationFromExperimentBuilder(
            experiment_selector=ExperimentSelector(study=self),
            target_study=self,
        )
        ui = sim_builder.edit_traits(kind="livemodal")
        if ui.result:
            new_sims = sim_builder.to_simulations()
            self.simulations.extend(new_sims)

    def request_new_simulation_group(self, sim=None):
        """ Create a new SimulationGroup around a center point simulation that
        already exists.
        """
        from kromatography.ui.simulation_group_builder import \
            SimulationGroupBuilder

        builder = SimulationGroupBuilder(center_point_simulation=sim,
                                         target_study=self)
        ui = builder.edit_traits(kind='livemodal')
        if not ui.result:
            return

        group = builder.build_group()
        if group.size == 0:
            msg = "No parameter was chosen. No grid created."
            logger.warning(msg)
            warning(None, msg)
            return

        if group.type == SIM_GROUP_GRID_TYPE:
            self.analysis_tools.simulation_grids.append(group)
        elif group.type == SIM_GROUP_MC_TYPE:
            self.analysis_tools.monte_carlo_explorations.append(group)
        else:
            msg = "Group type {} not supported"
            logger.exception(msg)
            raise NotImplementedError(msg)

        return group

    def request_new_simulation_from_datasource(self, datasource):
        """ Add a new simulation selected from a standard object in datasource.
        """
        from kromatography.ui.simulation_from_datasource_builder import \
            SimulationFromDatasourceBuilder

        sim_builder = SimulationFromDatasourceBuilder(
            datasource=datasource, study_datasource=self.study_datasource
        )
        if self.product_set:
            product_name = self.product.name
            sim_builder.product_name = product_name
            sim_builder.product_change_allowed = False

        ui = sim_builder.edit_traits(kind="livemodal")
        if ui.result:
            simulation = sim_builder.to_simulation()
            if simulation is not None:
                self.add_simulations(simulation)

    def request_strip_fraction_tool(self):
        self.analysis_tools.request_strip_fraction_tool(self.experiments)

    def create_new_optimizer(self):
        """ Returns new optimizer to find optimized sim to fit a set of exps.
        """
        from kromatography.ui.brute_force_optimizer_builder import \
            BruteForceOptimizerBuilder
        from kromatography.compute.factories.experiment_optimizer import \
            optimizer_builder_to_optimizer
        from kromatography.ui.experiment_selector import ExperimentSelector

        optimizer_builder = BruteForceOptimizerBuilder(target_study=self)
        optimizer_builder.experiment_selector = ExperimentSelector(study=self)
        ui = optimizer_builder.edit_traits(kind="livemodal")
        if not ui.result:
            return

        optimizer = optimizer_builder_to_optimizer(optimizer_builder)

        # Need to use UV continuous data for cost computation?
        first_target_exp = optimizer.target_experiments[0]
        all_comps = self.product.product_component_names
        use_uv_needed = (len(all_comps) == 1 and all_comps[0] not in
                         first_target_exp.output.fraction_data)
        if use_uv_needed:
            msg = "Requesting to run an optimizer for a pure protein " \
                  "chromatogram but there is no fraction measured for the" \
                  " pure protein. Please confirm if continuous UV data can " \
                  "be used in place of fractions, to compute the quality of " \
                  "matching between a simulation and the target experiment."
            res = confirm(None, msg, title="Use UV?", default=YES)
            if res == YES:
                # This will trigger setting the flag all the way to all
                # cost_functions
                optimizer.use_uv_for_cost = True

        self.analysis_tools.optimizations.append(optimizer)
        return optimizer

    def add_duplicate_simulation(self, simulation):
        """ Add duplicate of provided simulation to the current study.
        """
        new_simulation = simulation.copy()
        new_simulation.name = '{}_duplicate'.format(new_simulation.name)
        self.add_simulations(new_simulation)

    def run_simulations(self, job_manager, sims=None, wait=False):
        """ Runs simulations in Cadet and update them with results on success.
        """
        from kromatography.ui.simulation_selector import SimulationSelector
        from kromatography.solve.simulation_runner import run_simulations

        # have user select simulations if none passed
        if sims is None:
            sim_selector = SimulationSelector(
                study=self, title="Select Simulation(s) to run"
            )
            ui = sim_selector.edit_traits(kind='livemodal')

            if ui.result:
                selected_sim_names = sim_selector.simulations_selected

                sims = [self.search_simulation_by_name(sim_name)
                        for sim_name in selected_sim_names]
            else:
                return

        runner = run_simulations(sims, job_manager=job_manager, wait=wait)
        self.sim_runner_manager.add_runner(runner)

    def run_simulation_group(self, job_manager, sim_group=None, wait=False):
        """ Runs all sims of a SimulationGroup in Cadet, update with results
        """
        from kromatography.ui.simulation_selector import \
            SingleSimulationGroupSelector

        # have user select simulations if none passed
        if sim_group is None:
            group_selector = SingleSimulationGroupSelector(study=self)
            ui = group_selector.edit_traits(kind='livemodal')
            if ui.result:
                sim_group_name = group_selector.simulation_group_selected
                sim_group = self.search_simulation_group_by_name(
                    sim_group_name
                )
            else:
                return

        runner = sim_group.run(job_manager=job_manager, study=self, wait=wait)
        self.sim_runner_manager.add_runner(runner)

    def run_optimizer(self, job_manager, optimizer, wait=False):
        """ Launch the run of the provided optimizer, keeping track of created
        runners.
        """
        optimizer.run(job_manager, wait=wait)

    def search_simulation_by_name(self, name, how="deep"):
        """ Returns the Simulation matching the specified name, if any.

        Regular simulations are searched first, then simulations inside all
        simulation grids, then simulations inside optimizers are searched if
        how is set to "deep".

        Parameters
        ----------
        name : str
            Name of the Simulation to look for.

        how : str
            Search strategy. Supported values are "deep" (default) and
            "shallow". If `how="shallow"`, only search inside the study's
            `simulations` list. If `how="deep"`, search first there,
            and, if not found, search within the study's SimulationGroup and
            Optimizer objects.

        Raises
        ------
        KeyError
            Raised if no simulation is found with the provided name.
        """
        for sim in self.simulations:
            if sim.name == name:
                return sim

        if how == "deep":
            # Simulation not found. Looking inside simulation groups if any...
            for simulation_group in self.analysis_tools.simulation_grids:
                for sim in simulation_group.simulations:
                    if sim.name == name:
                        return sim

            # Still not found: looking into optimizations
            for optimizer in self.analysis_tools.optimizations:
                for sim in optimizer.optimal_simulations:
                    if sim.name == name:
                        return sim

        sim_names = [sim.name for sim in self.simulations]
        msg = "No simulation with name {}. Available sims are {}"
        msg = msg.format(name, sim_names)
        logger.exception(msg)
        raise KeyError(msg)

    def search_simulation_group_by_name(self, name, how="deep"):
        """ Returns the SimulationGroup matching the specified name, if any.

        Simulation grids are searched first, then simulation grids built by
        optimizers are searched.

        Parameters
        ----------
        name : str
            Name of the SimulationGroup to look for.

        how : str
            Search strategy. Supported values are "deep" (default) and
            "shallow". If "shallow", only search inside the analysis_tools
            dedicated list of SimulationGroups. If "deep", search first there,
            and, if not found, search within the Optimizer objects.

        Raises
        ------
        KeyError
            Raised if no simulation grid is found with the provided name.
        """
        all_groups = self.analysis_tools.simulation_grids
        for simulation_group in all_groups:
            if simulation_group.name == name:
                return simulation_group

        if how == "deep":
            # Not found: looking into optimizations
            for optimizer in self.analysis_tools.optimizations:
                for step in optimizer.steps:
                    for group in step.simulation_groups:
                        if group.name == name:
                            return group

        group_names = [group.name for group in all_groups]
        msg = "No simulation group with name {}. Available groups are {}"
        msg = msg.format(name, group_names)
        logger.exception(msg)
        raise KeyError(msg)

    # HasTraits listeners -----------------------------------------------------

    # We are not listening to the datasource attribute, because that is an
    # attribute exterior to the study:
    @on_trait_change("name, study_purpose, study_type, product, experiments,"
                     " simulations, exp_study_filepath, "
                     "study_datasource.[object_catalog, buffers, loads, "
                     "columns, methods, binding_models, transport_models]",
                     post_init=True)
    def update_blank(self):
        self.is_blank = False

    @on_trait_change('simulations:duplicate_request')
    def duplicate_simulation(self, obj, name, new):
        self.add_duplicate_simulation(obj)

    # HasTraits property getters/setters --------------------------------------

    def _get_product_set(self):
        return (self.product is not None and
                self.product.name != BLANK_PRODUCT_NAME)

    def _get_product_contains_strip(self):
        from kromatography.utils.string_definitions import STRIP_COMP_NAME

        if not self.product_set:
            return False

        product = self.product
        return STRIP_COMP_NAME in product.product_component_names

    # HasTraits initialization methods ----------------------------------------

    def _study_datasource_default(self):
        """ Build a default study datastore with a set of objects that are
        specific to this study.
        """
        from kromatography.model.data_source import InStudyDataSource
        return InStudyDataSource(name="Study DataSource")

    def _product_default(self):
        return make_blank_product()


def make_blank_study(**traits):
    """ Make a new blank study.

    Any trait can be passed, except is_blank that has to be True.
    """

    traits.pop("is_blank", None)

    if "name" not in traits:
        traits["name"] = BLANK_STUDY_NAME

    study = Study(is_blank=True, **traits)
    return study


def add_sims_from_exp_to_study(study, experiment_names,
                               first_simulated_step_name,
                               last_simulated_step_name,
                               initial_buffer_name=None):
    """ Create simulations from experiments and add them to study.

    Parameters
    ----------
    study : Study
        Study to which to add new simulations.

    experiment_names : list(str)
        List of experiment names to create the simulations from.

    first_simulated_step_name : str
        Name of the method step to start the simulation's method.

    last_simulated_step_name : str
        Name of the method step to end the simulation's method.

    initial_buffer_name : str [OPTIONAL]
        Name of the buffer to use for initial condition. If not set, it will be
        derived from first_simulated_step_name.
    """
    from kromatography.ui.simulation_from_experiment_builder import \
        SimulationFromExperimentBuilder

    sim_builder = SimulationFromExperimentBuilder(
        target_study=study,
        first_simulated_step_name=first_simulated_step_name,
        last_simulated_step_name=last_simulated_step_name,
        initial_buffer_name=initial_buffer_name
    )
    sim_builder.experiment_selector.experiment_selected = experiment_names
    study.simulations.extend(sim_builder.to_simulations())
