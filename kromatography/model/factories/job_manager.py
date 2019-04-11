from app_common.encore.simple_async_job_manager import \
    SimpleAsyncJobManager


def create_start_job_manager(max_workers=0, executor="ProcessPoolExecutor"):
    """ Create and start an async job manager.

    NOTE: it is critical to avoid saturating the Operating System by calling
    this function many times. If too many process pools are created, segfaults
    can be seen in particular on OSX. The right approach is to create one job
    manager, and to make sure that no matter what happens during execution it
    gets shutdown before new ones are created.

    Parameters
    ----------
    max_workers : int
        Max number of processor workers used by the job manager. If left at 0,
        all available processors in the machine minus 1 will be used (leaving 1
        processor to handle the application's UI and other tasks).
    """
    job_manager = SimpleAsyncJobManager(max_workers=max_workers,
                                        _executor_klass=executor)
    job_manager.start()
    return job_manager
