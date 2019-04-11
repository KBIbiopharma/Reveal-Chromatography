""" IO interfaces to load datasets and objects.
"""
from ..model.factories.study import build_study_from_experimental_study
from ..utils.app_utils import initialize_unit_parser, \
    load_default_user_datasource
from .experimental_study_builder import ExperimentalStudyBuilder
from .reader_writer import load_object, save_object

initialize_unit_parser()


def load_exp_study_from_excel(filepath, datasource=None, allow_gui=True):
    """ Returns an ExperimentalStudy from an Excel file.

    Parameters
    -----------
    filepath : str
        Path to the Excel file where the study data is stored.

    datasource : Instance(DataSource) [OPTIONAL]
        Database-like object to pull standard values for all parameters based
        on selection from Excel file. If not provided, the default datasource
        will be loaded.

    allow_gui : bool
        Whether AKTA reader can prompt user for settings. Set to False when
        running tests.
    """
    if datasource is None:
        datasource, _ = load_default_user_datasource()

    builder = ExperimentalStudyBuilder(
        input_file=filepath, data_source=datasource, allow_akta_gui=allow_gui
    )
    study = builder.build_study()
    return study


def load_study_from_excel(filepath, datasource=None, allow_gui=True):
    """ Returns an Study from an Excel file.

    Parameters
    -----------
    filepath : str
        Path to the Excel file where the study data is stored.

    datasource : Instance(DataSource) [OPTIONAL]
        Database-like object to pull standard values for all parameters based
        on selection from Excel file. If not provided, the default datasource
        will be loaded.

    allow_gui : bool
        Whether AKTA reader can prompt user for settings. Set to False when
        running tests.
    """
    experimental_study = load_exp_study_from_excel(filepath, datasource,
                                                   allow_gui=allow_gui)
    study = build_study_from_experimental_study(experimental_study)
    return study


def load_sim_from_study(study_filepath, sim_name):
    """ Load a simulation from a project file.

    Parameters
    ----------
    study_filepath : str
        Path to the study file (containing a KromatographyTask).

    sim_name : str
        Name of the simulation to extract.
    """
    task, _ = load_object(study_filepath)
    study = task.project.study
    return study.search_simulation_by_name(sim_name)


def load_study_from_project_file(filepath, with_user_data=True):
    """ Returns the study contained in a project file (.chrom).

    Parameters
    ----------
    filepath : str
        Absolute or relative path to the file to load.

    with_user_data : bool [OPTIONAL]
        Set the loaded study's user data from default user data? Defaults to
        True.
    """
    from ..utils.api import load_default_user_datasource

    task, _ = load_object(filepath)
    study = task.project.study
    if with_user_data:
        study.datasource = load_default_user_datasource()[0]
    return study


def save_study_to_project_file(filepath, study):
    """ Returns the study contained in a project file (.chrom).

    Parameters
    ----------
    filepath : str
        Absolute or relative path to the file to save the project to.

    study : Study
        Study to save.
    """
    from ..model.kromatography_project import KromatographyProject
    from ..ui.tasks.kromatography_task import KromatographyTask

    project = KromatographyProject(study=study, datasource=study.datasource)
    task = KromatographyTask(project=project, project_filepath=filepath)
    save_object(filepath, task)
