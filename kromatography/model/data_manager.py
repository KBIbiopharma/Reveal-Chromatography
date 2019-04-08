from traits.api import Any, HasStrictTraits, List


class DataManager(HasStrictTraits):
    """ Data container for all data objects to edit and visualize.

    That will include ChromatographyData objects as well as job, analysis, and
    anything that the GUI will edit.
    """

    data_elements = List(Any)
