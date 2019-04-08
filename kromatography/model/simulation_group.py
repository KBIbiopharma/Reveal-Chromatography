""" SimulationGroup class implementation and supporting classes and functions.

This defines an unordered collection of simulations that are specified as their
difference to some reference simulation called "center point".

That requires the introduction of a SimulationDiff concept wich needs to
encapsulate all the information to generate the Simulation if added to the
center point. That is currently implemented as a sequence (tuple) of
SingleParamSimulationDiff, with attributes 'extended_attr' and 'val'.
"""
from __future__ import division, print_function

from os.path import isfile
import logging
from collections import namedtuple
import pandas as pd
import numpy as np
from uuid import UUID

from scimath.units.api import UnitScalar
from traits.api import Any, Bool, cached_property, Constant, Dict, Enum, \
    Event, Instance, Int, List, on_trait_change, Property, Set, Str

from app_common.std_lib.filepath_utils import attempt_remove_file

from kromatography.model.chromatography_data import ChromatographyData
from kromatography.model.lazy_simulation import LazyLoadingSimulation
from kromatography.model.simulation import FILENAME_SUFFIX, Simulation
from kromatography.utils.string_definitions import MULTI_SIM_RUNNER_CREATED, \
    MULTI_SIM_RUNNER_FINISHED, MULTI_SIM_RUNNER_RUNNING
from kromatography.io.simulation_updater import update_simulation_results

#: The string constant for the SimulationGroup type-id
SIMULATIONGROUP_TYPE = 'SimulationGroup'

logger = logging.getLogger(__name__)

# Class/structure describing one of the differences between 2 simulations. A
# difference between 2 simulations is a sequence (tuple)
SingleParamSimulationDiff = namedtuple("SingleParamSimulationDiff",
                                       ['extended_attr', 'val'])

YIELD_PERF = "step_yield (%)"

# Paths to general performance parameters we want in the Group's data table
PERF_PARAMS = {"pool_volume (CV)": "output.performance_data.pool_volume",
               YIELD_PERF: "output.performance_data.step_yield",
               "pool_concentration (g/L)":
                   "output.performance_data.pool.product_concentration"}

PURITY_PERF_PREFIX = "purity:"

SIM_COL_NAME = "Simulation name"

SIM_GROUP_GRID_TYPE = "Multi-Param Grid"

SIM_GROUP_MC_TYPE = "Monte-Carlo Exploration"

GROUP_TYPES = [SIM_GROUP_GRID_TYPE, SIM_GROUP_MC_TYPE]


class SimulationGroup(ChromatographyData):
    """ Represents a group of simulations around a "center point" simulation.

    These groups of simulations describes and manages an unordered collection
    of Simulations that are specified as their difference to some reference
    simulation called "center point" (CP). That center point isn't necessarily
    part of the group, though it can and is then mapped to "None".
    Alternatively, a simulation in the group may have all it parameters
    (almost) equal to the values in the CP.

    In addition to the CP simulation, the group is characterized by the list of
    simulation differences describing how the simulations in the group differ
    from the CP. A "simulation diff" is just a tuple of
    SingleParamSimulationDiff instances, which contain the path to the
    parameter to change, and the value.

    Note: to save memory, simulation groups may be built with a
    LazyLoadingSimulation as its center point. Then, all simulations in the
    group will be LazyLoading.
    """
    # -------------------------------------------------------------------------
    # SimulationGroup traits
    # -------------------------------------------------------------------------

    #: Type of simulation group: regular grid, randomly generated, ...
    type = Enum(GROUP_TYPES)

    #: Central simulation around which to build the group
    center_point_simulation = Instance(Simulation)

    #: Whether the group contains LazyLoading or in-memory simulations.
    is_lazy_loading = Property(Bool, depends_on="center_point_simulation")

    #: Delete CADET files along the way to conserve disk space?
    auto_delete_run_sims = Bool(False)

    #: Name of central sim from which all simulations are a deviation
    center_point_simulation_name = Str

    #: List of simulation diffs to create the simulations in the group
    simulation_diffs = List

    #: List of simulations in the group. Same order as simulation_diffs
    simulations = List

    #: List of simulation outputs/output files so that simulations can be
    #: reconstructed from their diff and these files
    _simulation_output_cache = List

    #: Number of simulations in the group.
    size = Property(depends_on="simulation_diffs")

    #: Fires when user executes context menu action 'Run All Simulations...'
    #: Listened to by KromatographyTask
    cadet_request = Event

    #: Fires when user executes context menu action 'Plot All Simulations...'
    #: Listened to by KromatographyTask
    plot_request = Event

    #: Collated results from all simulations
    group_data = Instance(pd.DataFrame)

    #: Dict mapping performance parameter name and attribute paths
    perf_params = Dict

    #: Event triggered when the group_data dataframe is updated
    group_data_updated_event = Event

    #: Has the group's simulation been run?
    has_run = Property(Bool, depends_on="simulations:cadet_run_finished")

    #: Status of the optimizer as a string
    run_status = Enum([MULTI_SIM_RUNNER_CREATED, MULTI_SIM_RUNNER_RUNNING,
                       MULTI_SIM_RUNNER_FINISHED])

    #: Set of simulation UUIDs already run
    sims_run = Set

    #: Number of simulations already run
    size_run = Property(Int, depends_on="sims_run")

    #: Percentage of the group run
    percent_run = Property(Str, depends_on="size_run")

    #: Simulation runner
    sim_runner = Any

    # -------------------------------------------------------------------------
    # ChromatographyData traits
    # -------------------------------------------------------------------------

    #: The user visible type-id for the class.
    type_id = Constant(SIMULATIONGROUP_TYPE)

    def __init__(self, **traits):
        super(SimulationGroup, self).__init__(**traits)
        if 'group_data' not in traits:
            self.initialize_group_data()

    def __str__(self):
        s = "SimulationGroup: {} ({} simulations)".format(self.name, self.size)
        return s

    def __add__(self, second_group):
        if not isinstance(second_group, SimulationGroup):
            msg = "Unable to add a SimulationGroup to a {}".format(
                type(second_group))
            logger.exception(msg)
            raise ValueError(msg)

        if self.center_point_simulation:
            prod = self.center_point_simulation.product
            comp_names = prod.product_component_names
            second_product = second_group.center_point_simulation.product
            second_comp_names = second_product.product_component_names
            if comp_names != second_comp_names:
                msg = "Unable to add 2 SimulationGroups that do not target " \
                      "the same components."
                logger.exception(msg)
                raise ValueError(msg)

        all_group_data = pd.concat([self.group_data, second_group.group_data])
        all_diffs = self.simulation_diffs + second_group.simulation_diffs
        all_sims = self.simulations + second_group.simulations
        new = SimulationGroup(
            group_data=all_group_data.reset_index(drop=True),
            simulation_diffs=all_diffs, simulations=all_sims,
            name=self.name + "+" + second_group.name,
            center_point_simulation=self.center_point_simulation,
            auto_delete_run_sims=self.auto_delete_run_sims
        )
        return new

    def fire_cadet_request(self):
        """ Trigger event that a CADET run was requested. The Study containing
        the group listens to this.
        """
        self.cadet_request = True

    def fire_plot_request(self):
        """ Trigger event that a plot of all simulations was requested. The
        Study containing the group listens to this.
        """
        self.plot_request = True

    @on_trait_change("simulation_diffs", post_init=True)
    def initialize_group_data(self):
        """ Initialize the group_data DataFrame from the simulation_diffs.
        """
        if not self.simulation_diffs:
            return

        series = {}
        for i, diff in enumerate(self.simulation_diffs):
            short_sim_name = short_sim_name_from_sim_number(i)
            sim_data = {attr_name: val for attr_name, val in diff}
            init_perfs = {perf_name: np.nan for perf_name in self.perf_params}
            sim_data.update(init_perfs)
            series[short_sim_name] = pd.Series(sim_data)

        group_data = pd.DataFrame(series, dtype="float64").transpose()
        group_data.index.name = SIM_COL_NAME
        group_data = group_data.reset_index()
        # Make sure the order of columns is sim_name, inputs, outputs:
        input_params = list(set(group_data.columns) - set(self.perf_params) -
                            {SIM_COL_NAME})
        ordered_cols = ([SIM_COL_NAME] + sorted(input_params) +
                        sorted(list(self.perf_params.keys())))
        self.group_data = group_data[ordered_cols]

    def run(self, job_manager, study=None, wait=False):
        """ Rebuild and run CADET on all simulations of the group.

        Parameters
        ----------
        job_manager : JobManager
            Manager to send simulation runs to.

        study : Study [OPTIONAL]
            Study containing the simulation that serves as center point for the
            group. Needed only if the simulation_group doesn't have its
            center_point_simulation set.

        wait : bool [OPTIONAL]
            Make this call blocking, by forcing to wait until the job manager
            has run all simulations. False by default. In that case, listen to
            has_run to know that all simulation have finished running.

        Returns
        -------
        list
            List of Job ids submitted for run.
        """
        from kromatography.solve.simulation_runner import run_simulations

        self.run_status = MULTI_SIM_RUNNER_RUNNING
        self.sims_run = set([])

        if self.center_point_simulation is None:
            self.center_point_simulation = study.search_simulation_by_name(
                self.center_point_simulation_name
            )

        msg = "Rebuilding and running {} simulations for group {}."
        msg = msg.format(self.size, self.name)
        logger.debug(msg)

        self.initialize_simulations()
        self.sim_runner = run_simulations(self.simulations, job_manager,
                                          wait=wait)
        return self.sim_runner

    def wait(self):
        """ Wait for all simulations in the group to be run and has_run to
        update to True.
        """
        if self.has_run:
            return
        elif self.run_status == MULTI_SIM_RUNNER_CREATED:
            self.run(self._job_manager, wait=True)

        self.sim_runner.wait()

    def initialize_simulations(self, use_output_cache=False):
        """ Initialize the list of simulation from the diffs and center point.

        Parameters
        ----------
        use_output_cache : bool [OPTIONAL, default=False]
            Whether to initialize the simulations reusing the cached cadet
            file names. This is used when a group's simulations have been
            cleared to conserve memory, and needs to be rebuilt.
        """
        if self.center_point_simulation is None:
            return

        msg = "Rebuilding {} simulations for group {}."
        msg = msg.format(self.size, self.name)
        logger.debug(msg)

        self.clear_simulations()
        if not use_output_cache:
            self._simulation_output_cache = []

        for i, diff in enumerate(self.simulation_diffs):
            self.create_and_append_sim_from_sim_diff(
                i, diff, use_output_cache=use_output_cache
            )

    def clear_simulations(self):
        """ Empty simulation list without creating a new one

        Needed to be done that way so that the data browser doesn't loose
        track of it.
        """
        while self.simulations:
            self.simulations.pop(0)

    def release_simulation_list(self):
        """ Free up memory by emptying the list of simulations and releasing
        handle on the simulation runner.

        The simulations can be rebuilt from the list of simulation diffs and
        the list of output file names.

        Note that the corresponding memory will only be freed up once the
        python garbage collector runs, at a time hard to predict.
        """
        msg = "Deleting all simulations from group {}".format(self.name)
        logger.debug(msg)
        self.clear_simulations()
        self.sim_runner = None

    def get_simulation(self, sim_idx):
        """ Retrieve or rebuild a simulation from the group.

        Parameters
        ----------
        sim_idx : int
            Index of the simulation in the simulations list.
        """
        if self.simulations:
            return self.simulations[sim_idx]

        diff = self.simulation_diffs[sim_idx]
        sim = add_sim_to_diff(self.center_point_simulation, diff)
        output_filename = self._simulation_output_cache[sim_idx]
        sim.uuid = UUID(output_filename[:-len(FILENAME_SUFFIX)])
        sim.name = self._sim_name_from_idx(sim_idx)
        if isfile(sim.cadet_filepath):
            update_simulation_results(sim)
            sim.set_as_run()
        else:
            sim.set_as_not_run()
        return sim

    def create_and_append_sim_from_sim_diff(self, diff_idx, diff,
                                            use_output_cache=False):
        """ Create new simulation from center point + diff and append to
        simulation list.
        """
        sim = add_sim_to_diff(self.center_point_simulation, diff)
        sim.name = self._sim_name_from_idx(diff_idx)
        sim.on_trait_change(self.listen_to_sim_has_run, "has_run")
        self.simulations.append(sim)
        if use_output_cache:
            sim.cadet_filename = self._simulation_output_cache[diff_idx]
            if not self.is_lazy_loading:
                sim.load_results()

            sim.set_as_run()
        else:
            self._simulation_output_cache.append(sim.cadet_filename)
        return sim

    # Private interface -------------------------------------------------------

    def _update_run_attrs(self, sim):
        """ Update run related parameters when a simulation has run.
        """
        self.sims_run.add(sim.uuid)

        if self.has_run:
            self.run_status = MULTI_SIM_RUNNER_FINISHED
        else:
            msg = "Group {} {} run".format(self.name, self.percent_run)
            logger.debug(msg=msg)

    def _update_group_data_perf_param(self, sim, sim_index=None):
        """ Update the dataframe with results of the simulation that ran.
        """
        if sim_index is None:
            sim_index = self._search_for_sim_index(sim)

        # Update all performance parameters in output DF for that column
        if sim.output is None or sim.method.collection_criteria is None:
            # Simulation failed, don't try to eval the output:
            for perf_param_name, perf_param in self.perf_params.items():
                self.group_data.loc[sim_index, perf_param_name] = np.nan
        else:
            eval_context = {"output": sim.output}
            for perf_param_name, perf_param in self.perf_params.items():
                val = eval(perf_param, eval_context)
                self.group_data.loc[sim_index, perf_param_name] = float(val)

        # Free up disk space and memory if requested:
        if self.auto_delete_run_sims:
            attempt_remove_file(sim.cadet_filepath)
            self.simulations.remove(sim)

        # Manually trigger the event, because the modification happens below
        # the Traits layer.
        self.group_data_updated_event = True

    def _search_for_sim_index(self, sim):
        """ Returns the DF index value containing data for provided simulation.

        Note that the index of the DF isn't the same as the row number, since
        the DF may be sorted before this method is called.

        Parameters
        ----------
        sim : Simulation
            Simulation searched.

        Returns
        -------
        int
            Index of the simulation's row.
        """
        short_name = short_sim_name_from_fullname(sim.name)
        df = self.group_data
        try:
            index = df.index[(df[SIM_COL_NAME] == short_name)][0]
        except IndexError as e:
            known_names = self.group_data[SIM_COL_NAME]
            msg = "Failed to find simulation {} from group_data of SimGroup " \
                  "{}. Known short sim names are {}. Error was {}."
            msg = msg.format(sim.name, self.name, known_names, e)
            logger.exception(msg)
            raise

        return index

    def _sim_name_from_idx(self, sim_idx):
        """ Build simulation name from simulation index in group.
        """
        short_name = short_sim_name_from_sim_number(sim_idx)
        return "{}_{}".format(short_name, self.name)

    # Traits listeners --------------------------------------------------------

    def _group_data_changed(self):
        self.group_data_updated_event = True

    def _center_point_simulation_changed(self):
        self.center_point_simulation_name = self.center_point_simulation.name

    def listen_to_sim_has_run(self, sim, attr, new):
        """ A simulation has finished running: update group data and run
        status/progress.
        """
        logger.debug("Simulation {} has run: update group...".format(sim.uuid))
        if not sim.has_run:
            return

        self._update_group_data_perf_param(sim)
        self._update_run_attrs(sim)

    # Traits property getters -------------------------------------------------

    def _get_has_run(self):
        if not self.simulation_diffs:
            return False

        return self.size_run == self.size

    def _get_size_run(self):
        return len(self.sims_run)

    def _get_percent_run(self):
        if self.size:
            percent_run = self.size_run / self.size * 100.
        else:
            percent_run = np.nan

        return "{:.2f} %".format(percent_run)

    @cached_property
    def _get_size(self):
        return len(self.simulation_diffs)

    @cached_property
    def _get_is_lazy_loading(self):
        return isinstance(self.center_point_simulation, LazyLoadingSimulation)

    @staticmethod
    def col_is_output(col_name):
        is_fixed_name_perf = col_name in PERF_PARAMS.keys()
        is_purity = col_name.startswith(PURITY_PERF_PREFIX)
        return is_fixed_name_perf or is_purity

    # Traits initialization methods -------------------------------------------

    def _perf_params_default(self):
        perf_params = {}
        perf_params.update(PERF_PARAMS)
        if self.center_point_simulation:
            prod = self.center_point_simulation.product
            comp_names = prod.product_component_names
        else:
            msg = "Unable to derive the component names from simulation " \
                  "group {}. Will assume no purities in performances."
            msg = msg.format(self.name)
            logger.warning(msg)
            comp_names = []

        for i, comp in enumerate(comp_names):
            perf_name = "{} {} (%)".format(PURITY_PERF_PREFIX, comp)
            attr_path = "output.performance_data.pool." \
                        "product_component_purities[{}]".format(i)
            perf_params[perf_name] = attr_path

        return perf_params


def short_sim_name_from_fullname(sim_name):
    """ Shorter version of the simulation name for the simulation in a group.
    """
    return sim_name.split("_")[0]


def short_sim_name_from_sim_number(sim_num):
    return "Sim {}".format(sim_num)


def get_val_for_sim(sim, attr):
    """ Look up extended attribute for the provided simulation (using eval).

    Parameters
    ----------
    sim : Simulation
        Simulation to extract the value from.

    attr : str
        Extended attribute path to lookup.

    Returns
    -------
    Value for the attribute or np.nan if not found.
    """
    try:
        return eval("sim." + attr, {"sim": sim})
    except AttributeError:
        return np.nan


def add_sim_to_diff(orig_sim, diff):
    """ Create a new simulation that differs from orig_sim only by diff.

    Note: since this operation typically modifies the inputs, the new
    simulation's outputs are cleared and the simulation is reset to having not
    been run.

    FIXME: could define a SimDiff object and have this code below be the
    definition of the + between a simulation and a Diff.

    Parameters
    ----------
    orig_sim : Simulation or LazyLoadingSimulation
        Simulation to build the result from.

    diff : tuple of SingleParamSimDiff
        Difference between orig_sim and the Simulation to generate.

    Returns
    -------
    Simulation or LazyLoadingSimulation
        Result of the "operation" orig_sim + diff, with the output cleared. The
        type of the resulting simulation is the same as the input simulation.
    """
    invalid_input = (not isinstance(orig_sim, Simulation) or
                     not isinstance(diff, (tuple, list)))
    if invalid_input:
        msg = ("add_sim_and_diff can only take a Simulation and a "
               "SimulationDiff (tuple of SingleParamSimulationDiff) but got {}"
               " and {}".format(type(orig_sim), type(diff)))
        logger.exception(msg)
        raise ValueError(msg)

    sim = orig_sim.clone()
    sim.set_as_not_run()
    for single_param_diff in diff:
        if not isinstance(single_param_diff, SingleParamSimulationDiff):
            msg = ("Cannot add diff to simulation {} because {} isn't an "
                   "instance of a SingleParamSimulationDiff but a {}")
            msg = msg.format(orig_sim.name, single_param_diff,
                             type(single_param_diff))
            raise ValueError(msg)
        extended_attr, val = single_param_diff
        if extended_attr is not None:
            # FIXME: exec isn't the most robust approach. Replace with getattr
            if isinstance(val, UnitScalar):
                if val.units.label is None:
                    units = str(val.units)
                else:
                    units = val.units.label
                val = "UnitScalar({}, units='{}')".format(val.item(), units)

            expr = "sim.{} = {}".format(extended_attr, val)
            exec(expr)
    return sim


def append_run_sim_to_group(group, sim, diff=None):
    """ Utility to append an already run simulation to a SimulationGroup.
    """
    group.simulations.append(sim)
    if diff is not None:
        group.simulation_diffs.append(diff)

    empty_perfs = [np.nan for _ in group.group_data.columns]
    sim_index = len(group.group_data)
    group_data = group.group_data
    group_data.loc[sim_index, :] = empty_perfs
    group._update_group_data_perf_param(sim, sim_index=sim_index)
    for col in group_data.columns:
        if col == SIM_COL_NAME:
            group_data.loc[sim_index, col] = sim.name
        elif col not in group.perf_params:
            val = eval("sim.{}".format(col), {"sim": sim})
            group_data.loc[sim_index, col] = float(val)
