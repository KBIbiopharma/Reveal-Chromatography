""" API functions and classes for the Reveal Chromatography SOLVE sub-package.
"""
from os.path import basename

from kromatography.model.simulation import FILENAME_SUFFIX
from .simulation_runner import run_simulations
from .simulation_job_utils import create_cadet_file_for_sim
from .cadet_executor import CADETExecutor
from .slurm_cadet_executor import SlurmCADETExecutor

SLURM_SCRIPT_FNAME = "run_solver_{uuid}.slurm"


def run_cadet_simulator(input_file, use_slurm=False):
    """ API function to run CADET simulator for the given input file.

    This is useful for people less comfortable with OOP, as well as for
    submitting cadet runs to other processes, since we can't pickle
    CADETSimulationExecutor instances.

    Parameters
    ----------
    input_file : file_path
        The HDF5 input file for the CADET simulator.

    use_slurm : bool
        Override the preferences and for to use SLURM or not? Leave blank to
        follow preferences.

    Returns
    -------
    dict
        Returns the dictionary of information about the CADET run that the
        executor's `execute` method returns.
    """
    if use_slurm:
        # Make a difference SLURM script file for each job:
        uuid = basename(input_file).replace(FILENAME_SUFFIX, "")
        cadet_executor = SlurmCADETExecutor(
            slurm_script_fname=SLURM_SCRIPT_FNAME.format(uuid=uuid))
    else:
        cadet_executor = CADETExecutor()

    return cadet_executor.execute(input_file)


__all__ = ["run_simulations", "create_cadet_file_for_sim",
           "run_cadet_simulator"]
