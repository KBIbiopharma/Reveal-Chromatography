from abc import abstractmethod

from traits.api import ABCHasStrictTraits


# FIXME: Fill this out
class ExecutionFailedError(Exception):
    """ Thrown if a `WorkExecutor` encountered an error during execution.
    """
    pass


# FIXME: Fill this out
class InvalidExecutorError(RuntimeError):
    """ Thrown if a `WorkExecutor` could not be initialized.
    """
    pass


class WorkExecutor(ABCHasStrictTraits):
    """ Interface for a work item executor.
    """

    @abstractmethod
    def execute(self, work_id, *args, **kwargs):
        """ Execute the work item corresponding to `work_id`.

        This method can be called multiple times with different arguments.
        """
