""" Low level classes and functions to launch CADET binary on HDF5 input file.
"""

import logging
import os
import time
from os.path import abspath, isfile, isabs, join
from subprocess import PIPE, Popen
from multiprocessing import current_process

from traits.api import Instance, Int, Str

from kromatography.utils.app_utils import get_cadet_version, IS_OSX
from kromatography.utils.preferences import SolverPreferenceGroup
from kromatography.solve.work_executor import InvalidExecutorError, \
    WorkExecutor

START_CADET_LOG = "=============== CADET LOG START ==============="

STOP_CADET_LOG = "=============== CADET LOG STOP ==============="

# List of strings to search for in the CADET output to detect a failed run
CADET_ERROR_TERMS = ["exception"]

logger = logging.getLogger(__name__)


class BaseCADETExecutor(WorkExecutor):
    """ A WorkExecutor to manage the execution of a CADET run on an input file.

    This executor can be given a custom cadet solver binary command. Otherwise,
    it will search for it. Call execute once created, to launch CADET in a
    different process, and wait for that process to finish.

    Since this object and methods are expected to be called from sub-processes,
    all relevant data is collected, and exceptions and logging are avoided.
    """

    #: The full path or the name of the CADET binary command to use.
    cadet_binary = Str

    #: Number of CPUs per simulation run
    num_cpu_per_task = Int

    #: Current Solver preferences
    solver_prefs = Instance(SolverPreferenceGroup)

    def __init__(self, **traits):
        super(BaseCADETExecutor, self).__init__(**traits)

        if not self.cadet_binary:
            msg = "No cadet_binary provided!"
            logger.exception(msg)
            raise InvalidExecutorError(msg)

        if not check_valid_command(self.cadet_binary):
            msg = 'Command not found : {!r}'.format(self.cadet_binary)
            logger.exception(msg)
            raise InvalidExecutorError(msg)

    def execute(self, input_file):
        """ Execute the CADET run on the provided input file.

        Parameters
        ----------
        input_file : str
            Path to the HDF5 CADET input file.

        Returns
        -------
        Dict with description of the parameters of the run.
        """
        t1 = time.time()
        # check the input file exists.
        input_file = abspath(input_file)
        if not isfile(input_file):
            exception = 'Input file not found : {!r}'.format(input_file)
            out = ""
            ret_val = 1000
            output_errors = 0
        else:
            try:
                version, build = get_cadet_version(self.cadet_binary)
                msg = "Executing {} (version {}, build {})"
                msg = msg.format(self.cadet_binary, version, build)
                logger.debug(msg)
                ret_val, out = self.call_executable(input_file)
            except Exception as e:
                out = ""
                exception = "Failed to execute the CADET run with error {}"
                exception = exception.format(e)
                ret_val = 2000
                output_errors = 0
            else:
                output_errors = check_cadet_output(out)
                if output_errors > 0:
                    exception = "CADET solver failed to complete with {} " \
                                "errors.".format(output_errors)
                else:
                    exception = ""

        run_time = time.time() - t1
        proc_name = current_process().name
        msg = "Ran CADET on input file {} on proc. {} in {}s."
        msg = msg.format(input_file, proc_name, run_time)
        logger.debug(msg)

        return {'output_file': input_file, "cadet_output": out,
                "return_code": ret_val, "cadet_errors": output_errors,
                "run time": run_time, "process name": proc_name,
                "exception": exception}

    def call_executable(self, input_file):
        msg = "Base class: use one of the implementations"
        logger.exception(msg)
        raise NotImplementedError(msg)

    # HasTraits initialization methods ----------------------------------------

    def _cadet_binary_default(self):
        return self.solver_prefs.solver_binary_path

    def _num_cpu_per_task_default(self):
        return self.solver_prefs.cadet_num_threads

    def _solver_prefs_default(self):
        from kromatography.utils.app_utils import get_preferences
        prefs = get_preferences()
        return prefs.solver_preferences


class CADETExecutor(BaseCADETExecutor):
    """ A WorkExecutor to manage the execution of a CADET run on an input file.

    This executor can be given a custom cadet solver binary command. Otherwise,
    it will search for it. Call execute once created, to launch CADET in a
    different process, and wait for that process to finish.

    Since this object and methods are expected to be called from sub-processes,
    all relevant data is collected, and exceptions and logging are avoided.
    """

    def call_executable(self, input_file):
        cmd = [self.cadet_binary, input_file]
        # Note that shell=True fails on OSX, unable to load DLLs. But
        # on windows, it suppresses the console when running cadet if
        # launched with pythonw.exe. Very annoying to run a SimGroup
        # otherwise. More details at
        # http://stackoverflow.com/questions/7006238/
        if IS_OSX:
            shell = False
        else:
            shell = True
            cmd = " ".join(cmd)

        kwargs = dict(stdout=PIPE, stderr=PIPE, shell=shell)
        logger.debug(cmd)
        process = Popen(cmd, **kwargs)
        out, err = process.communicate()
        ret_val = process.returncode
        return ret_val, out + err


# Utilities -------------------------------------------------------------------


def check_cadet_output(stdout):
    """ Try and guess when CADET failed to run properly by detecting exception
    raised and other major issues preventing from computing simulation output.
    """
    output_val = 0
    stdout = stdout.lower()
    for error_term in CADET_ERROR_TERMS:
        if error_term in stdout:
            output_val += 1

    return output_val


def check_valid_command(command):
    """ Return `True` if `command` is an executable command.
    """

    def _is_executable(path):
        """ Return True if `path` is an executable file.
        """
        return os.access(path, os.X_OK)

    # If the full-path is specified then just check directly.
    if isabs(command):
        return _is_executable(command)

    # If just the command is specified, check for the binary in $PATH
    paths = os.environ['PATH'].split(os.pathsep)
    for path in paths:
        if _is_executable(join(path, command)):
            return True

    # If not found in $PATH, then the command is not valid.
    return False
