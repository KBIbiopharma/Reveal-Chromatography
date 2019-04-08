import logging

from kromatography.model.study import Study

logger = logging.getLogger(__name__)


def build_study_from_experimental_study(experimental_study, study_name="",
                                        study_purpose=""):
    """ Create a new Study from an experimental Study.
    """
    if not study_name:
        study_name = experimental_study.name

    if not study_purpose:
        study_purpose = experimental_study.study_purpose

    study = Study(name=study_name, study_purpose=study_purpose,
                  study_type=experimental_study.study_type,
                  datasource=experimental_study.datasource,
                  exp_study_filepath=experimental_study.filepath)
    # Adding experiments this way also leads to storing their components
    # (product, buffers, ...)
    study.add_experiments(experimental_study.experiments)

    return study
