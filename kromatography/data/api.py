""" API functions related to the tutorial data.
"""


def load_tutorial_project():
    """ Load the tutorial data into a study and return it.
    """
    from os.path import join, dirname
    from kromatography.io.api import load_study_from_excel

    path = join(dirname(__file__), "tutorial_data",
                "Example_Gradient_Elution_Study.xlsx")
    study = load_study_from_excel(path)
    return study
