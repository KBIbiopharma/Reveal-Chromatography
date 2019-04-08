import logging
from os.path import splitext

from .reader_writer import load_object, save_object

logger = logging.getLogger(__name__)


def load_project(filepath):
    """ Load a project (KromatographyTask to be precise) from a project file.

    Parameters
    ----------
    filepath : str
        Path to the file to load the object from.

    Examples
    --------
    >>> task = load_project(r"path\to\test.chrom")
    >>> study = task.project.study
    <WORK WITH THE STUDY...>
    """
    from kromatography.ui.tasks.kromatography_task import KromatographyTask

    task, legacy_file = load_object(filepath)
    if not isinstance(task, KromatographyTask):
        msg = "The path {} doesn't contain a KromatographyTask but a {}. You" \
              " should use load_object instead of load_project"
        msg = msg.format(filepath, type(task))
        logger.warning(msg)
    else:
        # Overwrite the project path in case the file was copied:
        task.project_filepath = filepath

    return task, legacy_file


def save_project(filepath, task):
    """ Store a project (KromatographyTask to be precise) into a project file.

    Examples
    --------
    >>> task = load_project(r"path\to\test.chrom")
    >>> study = task.project.study
    <MODIFY THE TASK OR STUDY...>
    >>> save_project("new_project.chrom", task)
    """
    from kromatography.ui.tasks.kromatography_task import KromatographyTask, \
        KROM_EXTENSION

    if not isinstance(task, KromatographyTask):
        msg = "This function is made to store a KromatographyTask, but a {} " \
              "was provided. Use save_object for any type of Chromatography " \
              "Data".format(type(task))
        logger.exception(msg)
        raise ValueError(msg)

    _, path_ext = splitext(filepath)
    if path_ext != KROM_EXTENSION:
        filepath = filepath + KROM_EXTENSION

    # In case this was a save-as, store the target filepath in the task:
    task.project_filepath = filepath
    return save_object(filepath, task)
