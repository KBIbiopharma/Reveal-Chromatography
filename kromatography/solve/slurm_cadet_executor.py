""" Low level classes and functions to launch CADET binary on HDF5 input file.
"""

import logging
from subprocess import CalledProcessError, check_output
import sys
from textwrap import dedent
from os.path import join
from time import sleep

from traits.api import HasStrictTraits, Instance, Int, Str

from app_common.traits.has_traits_utils import trait_dict

from kromatography.utils.preferences import SolverPreferenceGroup
from .cadet_executor import BaseCADETExecutor

logger = logging.getLogger(__name__)

SLURM_LOG_PATTERN = "slurm_solver_%j.log"

#: Number of seconds before polling on a job again to see if it has finished
SLURM_JOB_POLLING_PERIOD = 3


class SlurmCADETExecutor(BaseCADETExecutor):
    """ WorkExecutor to manage executing CADET using a SLURM scheduler.
    """
    #: SLURM executable to use to submit jobs
    slurm_binary = Str

    #: SLURM executable to use to inquire about jobs
    slurm_squeue_binary = Str("squeue")

    #: Name of the slurm script to (over)write to submit jobs
    slurm_script_fname = Str

    #: Folder to create SLURM files
    slurm_scratch_dir = Str

    def call_executable(self, input_file):
        if not sys.platform.startswith("linux"):
            msg = "Slurm execution not supported on platforms other than Linux"
            logger.exception(msg)
            raise NotImplementedError(msg)

        job_params = SlurmBatchJobParams(cpus_per_task=self.num_cpu_per_task,
                                         solver_prefs=self.solver_prefs)
        slurm_file = join(self.slurm_scratch_dir, self.slurm_script_fname)
        generate_slurm_script(slurm_file, input_file,
                              solver_executable=self.cadet_binary,
                              scratch_dir=self.slurm_scratch_dir,
                              job_params=job_params)
        cmd = [self.slurm_binary, slurm_file]

        # Submit the job to SLURM:
        submission_out = check_output(cmd)
        job_id = extract_slurm_run_id(submission_out)
        msg = "Submitted job {} with command {}. Output was {}".format(
            job_id, cmd, submission_out)
        logger.debug(msg)

        # Starting a blocking call to poll the job_id and wait for it to finish
        wait_on_slurm_job(job_id, squeue_executable=self.slurm_squeue_binary)
        out_file = join(self.slurm_scratch_dir,
                        SLURM_LOG_PATTERN.replace("%j", job_id))
        msg = "Slurm log stored in {}".format(out_file)
        logger.debug(msg)
        solver_output = open(out_file).read()
        ret_code = 0
        return ret_code, solver_output

    def _slurm_binary_default(self):
        from kromatography.utils.app_utils import get_preferences
        prefs = get_preferences()
        return prefs.solver_preferences.slurm_binary

    def _slurm_scratch_dir_default(self):
        from kromatography.utils.app_utils import get_executor_folder
        return get_executor_folder()


class SlurmBatchJobParams(HasStrictTraits):
    """ Batch SLURM job execution parameters.
    """
    #: Name of the SLURM partition to submit the job to
    partition = Str

    #: Number of cluster nodes to allocate for the job
    nodes = Int(1)

    #: Max number of tasks
    ntasks = Int(1)

    #: Number of CPUs to allocate for the task
    cpus_per_task = Int

    #: Max amount of time for a single job
    time = Str("00:30:00")

    #: Name of the CADET run job
    job_name = Str

    #: Max amount of memory the task can use, in GB
    mem = Int(1)

    #: Pattern of the output file SLURM will write STDOUT to
    output_pattern = Str(SLURM_LOG_PATTERN)

    #: Solver related preferences
    solver_prefs = Instance(SolverPreferenceGroup)

    def _partition_default(self):
        return self.solver_prefs.slurm_partition

    def _job_name_default(self):
        return self.solver_prefs.slurm_job_name

    def _cpus_per_task_default(self):
        return self.solver_prefs.cadet_num_threads

    def __prefs_default(self):
        from kromatography.utils.app_utils import get_preferences
        prefs = get_preferences()
        return prefs.solver_preferences


def extract_slurm_run_id(launch_output):
    """ Parse the run id out of the sbatch output.
    """
    return launch_output.split()[-1]


def wait_on_slurm_job(job_id, squeue_executable="squeue"):
    """ Wait until a SLURM job has finished.

    This is done by checking the output of squeue for the specified job. As
    long as the job is running, it is in the queue. Once it has finished, the
    output from the squeue command is only the headers of the table.
    """
    cmd = [squeue_executable, "-j", job_id]
    while True:
        try:
            out = check_output(cmd)
        except CalledProcessError as e:
            msg = "Failed to inquire about job {}. Error was {}. Wrong job " \
                  "number?".format(job_id, e)
            logger.exception(msg)
            raise

        if len(out.splitlines()) == 1:
            break

        sleep(SLURM_JOB_POLLING_PERIOD)


def generate_slurm_script(slurm_file, input_file, solver_executable="cadet-cs",
                          scratch_dir=".", job_params=None):
    """ Generate slurm script to execute the cadet executable on a CADET file.

    Parameters
    ----------
    slurm_file : str
        Path to the SLURM script to generate.

    input_file : str
        Path to the solver input file.

    solver_executable : str
        Path to the executable to launch the solver.

    scratch_dir : str
        Path to the scratch directory to store SLURM script files and output
        files.

    job_params : SlurmBatchJobParams
        SLURM job parameters.
    """
    # Note that the call to cadet re-exports the OMP_NUM_THREADS because the
    # value set inside the HDF5 input file is (sometimes) ignored:
    content_template = dedent("""
    #!/bin/bash -l
    #SBATCH --partition={partition}
    #SBATCH --nodes={nodes}
    #SBATCH --ntasks={ntasks}
    #SBATCH --cpus-per-task={cpus_per_task}
    #SBATCH --time={time}
    #SBATCH --job-name={job_name}
    #SBATCH --mem={mem}G
    #SBATCH -o {scratch_dir}/{output_pattern}
    {solver_executable} {input_file}
    """).lstrip()
    if job_params is None:
        job_params = SlurmBatchJobParams()

    params = trait_dict(job_params)
    content = content_template.format(input_file=input_file,
                                      solver_executable=solver_executable,
                                      scratch_dir=scratch_dir, **params)
    with open(slurm_file, "w") as f:
        f.write(content)
        logger.debug("Slurm file content:\n{}\n".format(content))


def check_slurm_installed(executable=None):
    """ Check that slurm is installed and that batch jobs can be submitted.
    """
    # --wrap to avoid having to create a script file:
    cmd = [executable, "--wrap", '"sleep .1"']
    try:
        out = check_output(cmd)
        msg = "Command {} ran with output {}.".format(cmd, out)
        logger.debug(msg)
        return True
    except OSError as e:
        msg = "Failed to run the command {} with error {}.".format(cmd, e)
        logger.info(msg)
        return False
