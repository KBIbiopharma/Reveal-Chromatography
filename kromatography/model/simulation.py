""" Simulation class implementation
"""
import logging
from numpy import cumsum, linspace
from os.path import isfile, join
from uuid import UUID, uuid4

from traits.api import Bool, Constant, Enum, Event, Instance, on_trait_change,\
    Property, Str
from scimath.units import SI
from scimath.units.unit_scalar import UnitArray

from kromatography.model.transport_model import TransportModel
from kromatography.model.binding_model import BindingModel
from kromatography.model.discretization import Discretization
from kromatography.model.solver import Solver
from kromatography.model.sensitivity import Sensitivity
from kromatography.model.experiment import _BaseExperiment, Experiment
from kromatography.utils.app_utils import get_cadet_input_folder
from kromatography.utils.string_definitions import SIM_NOT_RUN, SIM_SUBMITTED,\
    SIM_RUNNING, SIM_FINISHED_SUCCESS, SIM_FINISHED_FAIL
from kromatography.solve.simulation_runner import run_simulations
from kromatography.utils.units_utils import vol_to_time
from kromatography.solve.simulation_job_utils import walk_dataelement_editable
from kromatography.io.simulation_updater import build_simulation_results

#: The string constant for the Simulation type-id
SIMULATION_TYPE = 'Simulation'

ALL_SIM_RUN_STATUSES = [SIM_NOT_RUN, SIM_SUBMITTED, SIM_RUNNING,
                        SIM_FINISHED_SUCCESS, SIM_FINISHED_FAIL]

FILENAME_SUFFIX = "_cadet.h5"

logger = logging.getLogger(__name__)


class Simulation(_BaseExperiment):
    """ Class containing data necessary to run Cadet Simulation.

    The description of the steps involved in the simulation are to be found in
    its method, attribute declared in the BaseExperiment. Information about the
    steps of the experiment that corresponds to the simulation are accessible
    via the source_experiment attribute.
    """
    #: User notes about the simulation's origin, purpose, ...
    description = Str()

    # -------------------------------------------------------------------------
    # Simulation traits
    # -------------------------------------------------------------------------

    #: Binding model (binding of the protein to the resins)
    binding_model = Instance(BindingModel)

    #: Transport model (transport of the protein across the column)
    transport_model = Instance(TransportModel)

    #: CADET solver discretization parameters (for solving differential eq.)
    discretization = Instance(Discretization, args=())

    #: Sensitivity parameters
    sensitivity = Instance(Sensitivity, args=())

    #: Wrapper around the CADET diff equ solver
    solver = Instance(Solver, args=())

    #: Experiment this simulation was built from.
    # FIXME: we could consider making this a weakref or store just the name of
    # the experiment as long as we enforce the unicity of these names
    source_experiment = Instance(Experiment)

    # -------------------------------------------------------------------------
    # Traits only relevant when a simulation is built from an experiment.
    # -------------------------------------------------------------------------

    #: Timestamps at the beginning/end of each simulated steps
    section_times = Instance(UnitArray)

    #: Name of the first step simulated by CADET, among source experiment steps
    first_simulated_step = Str

    #: Name of the last step simulated by CADET, among source experiment steps
    last_simulated_step = Str

    # -------------------------------------------------------------------------
    # Run related attributes
    # -------------------------------------------------------------------------

    #: Set to false at the creation/before a run, and set to True after running
    has_run = Bool

    #: CADET run status in more details
    run_status = Enum(ALL_SIM_RUN_STATUSES)

    #: Name of the HDF5 CADET input file generated to run this simulation
    cadet_filename = Property(Str, depends_on="uuid")

    #: Full absolute path to the HDF5 CADET input/output file.
    cadet_filepath = Property(Str, depends_on="uuid")

    # -------------------------------------------------------------------------
    # Event related traits
    # -------------------------------------------------------------------------

    #: Fires when user executes right-click menu action 'Plot Simulation',
    #: is listened to by KromatographyTask
    plot_request = Event

    #: Fires when user executes right-click menu action 'Run Simulation...',
    #: is listened to by KromatographyTask
    cadet_request = Event

    #: Fires when cadet has finished running, whether successfully or not
    cadet_run_finished = Event

    #: Fires when Simulation perf param results get updated (i.e. after
    #: Cadet get's called)
    perf_param_data_event = Event

    #: Fires when user executes right-click menu action 'Duplicate',
    #: is listened to by Study
    duplicate_request = Event

    # -------------------------------------------------------------------------
    # ChromatographyData traits
    # -------------------------------------------------------------------------

    #: The user visible type-id for the class.
    type_id = Constant(SIMULATION_TYPE)

    def __init__(self, **traits):
        super(Simulation, self).__init__(**traits)
        # Make sure that the simulation and its output parameter names are
        # sync-ed up no matter the order of traits during object creation:
        self._name_changed()
        # Make sure that the simulation's solver and method are in sync once it
        # is all initialized (critical to avoid CADET crashes):
        self.reset_solver_user_times()

    # Copy related methods ----------------------------------------------------

    def copy(self):
        """ Returns new sim equal to this one except uuid and set as not-run.

        Note: It is important that a new simulation copies only the inputs and
        not the outputs and that it supports modifications. It is also critical
        that the new simulation respects all objects linking. For example, a
        simulation using a buffer multiple times should be using the same
        instance of that buffer, such that changes to it affects all its uses.
        """
        new_sim = self.clone()
        new_sim.set_as_not_run()  # erases output
        return new_sim

    def clone(self):
        """ Returns a new & independent simulation but equal to this one,
        except for its uuid.
        """
        # clone_traits with deep copy respects object linking:
        new_sim = self.clone_traits(copy="deep")
        # New uuid since new sim:
        new_sim.uuid = uuid4()
        return new_sim

    # Run related methods -----------------------------------------------------

    def run(self, job_manager, wait=False):
        """ Run the current simulation submitting the job to the provided
        job_manager.
        """
        self.set_as_not_run()
        runner = run_simulations([self], job_manager=job_manager, wait=wait)
        return runner

    def set_as_not_run(self):
        """ Reset to not be run: updates flags and deletes output.
        """
        self.output = None
        walk_dataelement_editable(self, True,
                                  skip_traits=['source_experiment'])
        self.has_run = False
        self.run_status = SIM_NOT_RUN

    def set_as_run(self):
        """ Reset the run flags to be run.

        Note: run_status not set because it depends how the run went.
        """
        walk_dataelement_editable(self, False,
                                  skip_traits=['source_experiment'])
        self.has_run = True

    def create_cadet_input_file(self):
        """ Create CADET input file if doesn't already exist and return path.
        """
        from kromatography.solve.simulation_job_utils import \
            create_cadet_file_for_sim

        if isfile(self.cadet_filepath):
            return self.cadet_filepath
        else:
            return create_cadet_file_for_sim(self)

    def load_results(self):
        output = build_simulation_results(self, self.cadet_filepath)
        self.output = output
        return output

    # Listeners ---------------------------------------------------------------

    def _cadet_run_finished_fired(self):
        self.set_as_run()

    @on_trait_change("method.method_steps, method.method_steps.volume,"
                     "method.method_steps.flow_rate, column.bed_height_actual,"
                     "column.column_type.diameter,"
                     "solver.number_user_solution_points", post_init=True)
    def reset_solver_user_times(self):
        """ Set simulation output properties, including solver solution times.
        """
        if self.method is None or len(self.method.method_steps) == 0:
            return

        self.section_times = get_section_times(
            self.method.method_steps, self.column, tgt_units="second"
        )

        num_times = self.solver.number_user_solution_points
        solution_times = linspace(0., self.section_times[-1], num_times)
        self.solver.trait_set(write_at_user_times=1,
                              user_solution_times=solution_times)

    def _name_changed(self):
        # Keep performance_data's name in sync
        if self.output and self.output.performance_data:
            self.output.performance_data.name = self.name

    # Initialization methods --------------------------------------------------

    def _first_simulated_step_default(self):
        if self.source_experiment:
            return self.source_experiment.method.load.name
        else:
            return ""

    def _last_simulated_step_default(self):
        if self.source_experiment:
            return self.source_experiment.method.method_steps[-1].name
        else:
            return ""

    def _run_status_default(self):
        if self.has_run and self.output is not None:
            return SIM_FINISHED_SUCCESS
        elif self.has_run and self.output is None:
            return SIM_FINISHED_FAIL
        else:
            return SIM_NOT_RUN

    # Event related methods ---------------------------------------------------

    # Method to fire updates. Needed in the form of a method to expose these
    # updates to the data explorer's context menus.

    def fire_plot_request(self):
        self.plot_request = True

    def fire_cadet_request(self):
        self.cadet_request = True

    def fire_perf_param_data_event(self):
        self.perf_param_data_event = True

    def fire_duplicate_request(self):
        self.duplicate_request = True

    # Property getters/setters ------------------------------------------------

    def _get_cadet_filename(self):
        return str(self.uuid) + FILENAME_SUFFIX

    def _set_cadet_filename(self, fname):
        if not fname:
            return

        logger.debug("Setting the cadet_filename of a sim overwrites its uuid")
        self.uuid = UUID(fname[:-len(FILENAME_SUFFIX)])

    def _get_cadet_filepath(self):
        cadet_file_path = join(get_cadet_input_folder(), self.cadet_filename)
        return cadet_file_path


# Utilities ###################################################################


def get_section_times(section_steps, column, tgt_units=None):
    """ Return timestamps start/stop of all method steps. First start is 0.

    Parameters
    ----------
    section_steps : list(MethodStep)
        The list of method steps in the simulation.

    column : Column
        The column the steps are flowing through.

    tgt_units : scimath.Unit (OPTIONAL)
        The units for the returned data. Defaults to "seconds".

    Returns
    -------
    section_times : UnitArray
        The step timestamps for the section in the units given in `tgt_units`.
        These are the boundary times for all steps. Therefore
        len(section_times) == len(section_steps) + 1
    """
    if tgt_units is None:
        tgt_units = SI.second

    section_durations = []
    for step in section_steps:
        step_duration = vol_to_time(step.volume, step.flow_rate, column,
                                    tgt_units)
        section_durations.append(step_duration)

    section_times = UnitArray(cumsum([0.0] + section_durations),
                              units=tgt_units)
    return section_times
