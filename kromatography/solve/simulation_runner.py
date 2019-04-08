""" Runner capable of preparing a list of simulations for CADET runs and
executing these runs asynchronously using an SimpleAsyncJobManager.

This is designed to work well in multi-processing environments since it submits
thinly wrapped pure CADET jobs on CADET input files to avoid pickling large
python objects (simulations).
"""
import logging
from uuid import uuid4
from time import sleep, time

from traits.api import HasStrictTraits, Instance, Int, List, Property, Str
from pyface.timer.api import Timer

from app_common.encore.simple_async_job_manager import JobManager, TimeOutError

from kromatography.solve.simulation_job_utils import \
    prepare_simulation_for_run
from kromatography.utils.string_definitions import SIM_FINISHED_FAIL, \
    SIM_FINISHED_SUCCESS
from kromatography.io.simulation_updater import update_simulation_results

logger = logging.getLogger(__name__)

# Amount of time (in sec) between 2 checks that all simulations have run during
# Runner.wait method.
POLLING_PERIOD = .5

# Amount of time between 2 checks of job items have finished working
TIMER_PERIOD = 500

FINISHED_STATUSES = [SIM_FINISHED_FAIL, SIM_FINISHED_SUCCESS]


def run_simulations(simulation_list, job_manager=None, wait=True,
                    timeout=None):
    """ Function to submit a list of simulations.

    Can block the process and wait for all simulations to finish running.

    Parameters
    ----------
    simulation_list : list
        List of simulation instances to run.

    job_manager : JobManager [OPTIONAL]
        JobManager instance to use to manage the CADET runs. If not provided, a
        new manager will be created.

    wait : bool
        Should the process wait for all simulation to finish running?

    timeout : int or None
        Number of seconds for the wait to timeout. Ignored if wait=False.

    Returns
    -------
    SimulationRunner
        Simulation runner created to run the provided simulations.
    """
    runner = SimulationRunner(simulation_list=simulation_list,
                              job_manager=job_manager)
    runner.submit_jobs()

    if wait:
        runner.wait(timeout=timeout)
    return runner


class SimulationRunner(HasStrictTraits):
    """ Submit a list of simulation for run to a job manager, and update them
    once CADET has run.

    If no job manager is provided, a multi-processing one with be created, with
    cpu_count-1 max workers.
    """
    #: JobManager responsible for submitting CADET jobs asynchronously
    job_manager = Instance(JobManager)

    #: list of simulations to run
    simulation_list = List

    #: ID of the job that contains running all simulations
    job_id = Str

    #: List of work items submitted, one for each simulation
    work_item_ids = List(Str)

    #: Number of workers a job manager should be created with if not provided.
    max_workers = Int

    #: A unique ID for the object
    uuid = Str

    result_timer = Instance(Timer)

    #: Have all self.simulations run?
    has_run = Property

    def __init__(self, **traits):
        if "job_manager" in traits and traits["job_manager"] is None:
            traits.pop("job_manager")

        super(SimulationRunner, self).__init__(**traits)
        self.start()

    def start(self):
        if not self.job_manager.started:
            self.job_manager.start()

    def submit_jobs(self):
        """ Submit all simulations for CADET run.
        """
        job_id, wk_ids = self.job_manager.submit(_submit_simulations_as_job,
                                                 self.simulation_list)
        self.job_id = job_id
        self.work_item_ids = wk_ids
        self.result_timer.start()
        logger.debug("Submitted {}".format(self.job_id))

    def wait(self, timeout=None):
        """ Wait until all simulations have been updated.
        """
        if not self.job_id:
            msg = "Can't wait on a SimulationRunner that hasn't " \
                  "submitted any job."
            logger.error(msg)
            return

        t0 = time()
        while True:
            if timeout and time() - t0 > timeout:
                msg = "The wait() call timed out after {} secs."
                msg = msg.format(timeout)
                raise TimeOutError(msg)

            # Since this call is a never ending loop, we have to call the
            # simulation updater explicitely:
            self._check_update_sims()
            if self.has_run:
                return

            sleep(POLLING_PERIOD)

    # Call-backs and listeners ------------------------------------------------

    def update_simulation_from_results(self, work_id):
        """ Trigger simulation update when a job manager work item has finished
        """
        msg = "Work {} completed, requesting to update corresponding " \
              "simulation...".format(work_id)
        logger.debug(msg)

        sim_idx = self.work_item_ids.index(work_id)
        sim = self.simulation_list[sim_idx]

        results = self.job_manager.get_results(self.job_id, work_id=work_id)
        self._update_simulation(sim, results)

    def _check_update_sims(self):
        """ Check on running simulations and update if they finished.
        """
        assert self.job_id in self.job_manager._job_results

        finished_items = self.job_manager._job_results[self.job_id].keys()
        if finished_items:
            msg = "Found finished items: {}. Updating simulations."
            msg = msg.format(finished_items)
            logger.debug(msg)

        for work_id in finished_items:
            self.update_simulation_from_results(work_id)

        if self.has_run:
            logger.debug("All simulations have run: stopping timer.")
            self.result_timer.stop()

    def _update_simulation(self, sim, results):
        """ Analyze the results from the CADET executor and update simulation.
        """
        output_file = results["output_file"]
        expected_output_file = sim._get_cadet_filepath()
        if expected_output_file != output_file:
            msg = "Logic is bad: attempting to update simulation {} with " \
                  "wrong CADET output file {}."
            msg = msg.format(expected_output_file, output_file)
            logger.critical(msg)
            raise RuntimeError(msg)

        if results["exception"]:
            msg = "CADET failed to run on simulation {} ({}) with error {}. " \
                  "Full output was\n{}"
            msg = msg.format(sim.name, sim.uuid, results["exception"],
                             results["cadet_output"])
            logger.error(msg)
            sim.run_status = SIM_FINISHED_FAIL
        elif results["cadet_errors"]:
            msg = "CADET failed to solve simulation {} ({}) with error {}." \
                  "Full output was\n{}"
            msg = msg.format(sim.name, sim.uuid, results["cadet_errors"],
                             results["cadet_output"])
            logger.warning(msg)
            sim.run_status = SIM_FINISHED_FAIL
        else:
            msg = "CADET ran successfully on simulation {} ({}). Full output" \
                  " was\n{}."
            msg = msg.format(sim.name, sim.uuid, results["cadet_output"])
            logger.debug(msg)
            update_simulation_results(sim, output_file)
            sim.run_status = SIM_FINISHED_SUCCESS

        # Trigger a final update of the simulation object
        sim.cadet_run_finished = True

    # HasTraits initialization methods ----------------------------------------

    def _job_manager_default(self):
        from kromatography.model.factories.job_manager import \
            create_start_job_manager
        return create_start_job_manager(max_workers=self.max_workers)

    def _max_workers_default(self):
        from multiprocessing import cpu_count
        return max(cpu_count() - 1, 1)

    def _uuid_default(self):
        return str(uuid4())

    def _result_timer_default(self):
        return Timer(TIMER_PERIOD, self._check_update_sims)

    # Property getters/setters ------------------------------------------------

    def _get_has_run(self):
        return all([sim.has_run for sim in self.simulation_list])


def _submit_simulations_as_job(sims):
    """ New Generator function for creating sim_workitems but avoiding passing
    a complicated HasTraits instance since they are painful to pickle/unpickle.

    Parameters
    ----------
    sims : list
        List of simulations to submit as a job work item.
    """
    from kromatography.solve.api import run_cadet_simulator
    from kromatography.utils.app_utils import get_preferences

    prefs = get_preferences()
    use_slurm = prefs.solver_preferences.use_slurm_scheduler

    for sim in sims:
        output_file = prepare_simulation_for_run(sim)
        yield run_cadet_simulator, (output_file,), {"use_slurm": use_slurm}


if __name__ == "__main__":
    from traits.api import Any, Button
    from traitsui.api import View, Item

    from kromatography.model.tests.sample_data_factories import \
        make_sample_simulation, make_sample_simulation_group2
    from kromatography.utils.app_utils import initialize_logging
    from kromatography.model.factories.job_manager import \
        create_start_job_manager

    initialize_logging(verbose=True)

    sim = make_sample_simulation(name='Run_1')
    NUM_JOBS = 1
    NUM_WORK_ITEMS_PER_JOB = 2
    NUM_SIM = NUM_JOBS * NUM_WORK_ITEMS_PER_JOB

    t0 = time()
    # runner1 = sim.run()
    # group = make_sample_simulation_group2(size=2)
    # runner2 = group.run(wait=True)

    class SimpleGroupUI(HasStrictTraits):
        group = Any
        job_manager = Any
        button = Button("Run sims")
        view = View(
            Item("object.group.run_status"),
            Item("button"),
        )

        def _button_fired(self):
            self.group.run(self.job_manager)

        def _job_manager_default(self):
            job_manager = create_start_job_manager()
            return job_manager

        def _group_default(self):
            return make_sample_simulation_group2(size=2)

    ui = SimpleGroupUI()
    ui.configure_traits()
