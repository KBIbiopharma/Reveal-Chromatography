import logging
from collections import OrderedDict

from traits.api import Array, Dict, Either, Enum, Instance, Str

from app_common.model_tools.data_element import DataElement

from kromatography.utils.io_utils import get_sanitized_state

NoneOrStr = Either(None, Str)
NoneOrDict = Either(None, Dict)
NoneOr1DArray = Either(None, Array(shape=(None,)))

logger = logging.getLogger(__name__)


def _check_traits_not_none(trait_obj):
    """ Throw error if any trait in `trait_obj` is `None`.
    """
    sanitized_state = get_sanitized_state(trait_obj)
    invalid_attribs = ["{!r}: {!r}".format(k, v)
                       for k, v in sanitized_state.items() if v is None]
    if any(invalid_attribs):
        msg = 'Uninitialized traits : {}\n{}'
        msg = msg.format(trait_obj.__class__, '\t\n'.join(invalid_attribs))
        logger.exception(msg)
        raise ValueError(msg)


class ChromeFamily(DataElement):
    """ Class describing a family of related chrome data curves.

    Typically, curves with same units (e.g. UV, temperature, conductivity etc)
    would be considered a family.

    NOTE: It might be worth considering if we need a separate ChromeFamily
    class or if we should just collapse the traits into ChromLog.
    One advantage of keeping the data and the family/plot attributes separate
    would be to allow saving/loading/editing these attributes.
    """
    #: A short description of the family.
    description = NoneOrStr

    #: The label for displaying to user
    data_label = NoneOrStr

    #: The label for displaying to user
    time_label = NoneOrStr

    #: The units for the data curves
    data_unit_label = NoneOrStr

    #: The units for the time axis
    time_unit_label = NoneOrStr

    #: The properties to use for the top level container for the logs in this
    #: family
    plot_container_properties = NoneOrDict

    def __init__(self, **traits):
        super(ChromeFamily, self).__init__(**traits)
        # check all attributes are initialized.
        _check_traits_not_none(self)


class ChromeLog(DataElement):
    """ Contains all relevant data for a curve in the Chromatogram.

    NOTE: The main difference from XYData is that this class has attributes
    specific to creating a plot (e.g. `family`, unit converted etc) whereas
    the XYData contains the raw data from the experiment/simulation.
    """
    #: The x and y data for the log.
    x_data = NoneOr1DArray

    y_data = NoneOr1DArray

    #: The family (e.g. UV/ Temperature / pH) that this  belongs to.
    family = Instance(ChromeFamily)

    #: The properties to use for rendering the logs corr. to this family.
    renderer_properties = Dict

    #: The source for the Chrome data. Again prob. belongs in ChromeLog.
    source_type = Either(None, Enum(['experiment', 'simulation', 'fraction']))

    def __init__(self, **traits):
        super(ChromeLog, self).__init__(**traits)
        # check all attributes are initialized.
        _check_traits_not_none(self)


class ChromeLogCollection(DataElement):
    """ Holds a collection of ChromeLogs and any context specific information
    for that collection.

    This class should provide access to the logs/data from a *single*
    experiment/simulation and any specific context information needed for
    unit converters etc. (e.g. t0, info for CV to time conversion etc).

    NOTES
    -----
    :

    * It might make sense for these classes to have a map of unit converters
      that can be used by `Chromatogram(Model/Plot)` to convert the data to
      appropriate units. (can we use the unit_manager from scimath here ?)

    * Also, it would be nice to make this sit on top of a `BaseExperiment`
      and provide lazy access to data. That way, we don't have to explicitly
      construct the `ChromeLog` for all available data
    """
    #: The collection of ChromeLog instances managed by this object.
    logs = Instance(OrderedDict, ())

    #: Type of origin: collection built from an experiment or a sim?
    source_type = Enum(["experiment", "simulation"])

    #: Name of the source experiment this collection will inherit styling from
    source = NoneOrStr


class ChromatogramModel(DataElement):
    """ Class that contains the data required for a chromatogram editor.

    NOTES
    -----

      * The model contains a collection of `ChromeLogCollection`.
      * A `ChromeLogCollection` is a collection of time series data from either
        an experiment or a simulation.
      * Each model has a reference 'ChromeLogCollection`.
      * It should be possible add/remove instances of `ChromLogCollection`.

    """

    #: The collection of all chrome data (multiple ChromeLogCollections).
    #: This object should contain all the data, for a study, that should be
    #: displayed in the chaco plot.
    log_collections = Dict(Str, Instance(ChromeLogCollection))

    def _name_default(self):
        return "Chromatogram"
