"""
Chromatography run results contain continuous XY data, performance information,
collected into in a ChromatographyResults object.
"""
import logging

from traits.api import Constant, Dict, Instance

from kromatography.model.chromatography_data import ChromatographyData
from kromatography.model.performance_data import PerformanceData

logger = logging.getLogger(__name__)


class ChromatographyResults(ChromatographyData):
    """ Base class for the results from Chromatography experiment/simulation.

    Specifies the interface for the outputs/results that are of
    interest in a chromatography process as opposed to raw data from an
    experiment/simulation.

    This is a base class. Use either ExperimentResults or SimulationResults
    instead.
    """
    # ChromatographyResults interface -----------------------------------------

    #: Holds the continuous measurements of various quantities for the duration
    #: of the experiment/simulation.
    continuous_data = Dict

    #: Results from fractionation study of sample collected at various
    #: sampling times. For an experiment, these are typically a few time
    #: samples. For a simulation, it can be as large as the number of time
    #: steps in the simulation.
    # FIXME: We should actually also store the Fraction solution objects
    # (instances of a SolutionWithProduct)
    fraction_data = Dict

    #: Contains the results pertaining to the performance of the chromatography
    #: process. For an experiment, these results come from analysis of the
    #: collected pool solution. For a simulation, these parameters need to be
    #: computed from the `continuous_data` using the collection criteria.
    # FIXME: We should actually also store the Pool solution objects
    performance_data = Instance(PerformanceData)


class ExperimentResults(ChromatographyResults):
    """ Implementation of `ChromatographyResults` for experiment results.

    It contains continuous data in the :attr:`continuous_data` dictionary, and
    the fraction data found in Excel input file in the
    :attr:`fraction_data` dictionary.

    Compared to a simulation result object, this one contains an additional
    :attr:`import_settings` dict containing information about the mapping
    between AKTA header to dataset types, as well as the time shifts applied
    (hold up volume as well as a manual shift during AKTA file import).
    """
    # ExperimentResults interface ---------------------------------------------

    #: Settings with which the AKTA file and fractions were loaded.
    import_settings = Dict

    # ChromatographyData interface --------------------------------------------

    #: The type-id for this class.
    type_id = Constant('Experiment Results')


class SimulationResults(ChromatographyResults):
    """ Implementation of `ChromatographyResults` for simulation results.
    """
    # ChromatographyData interface --------------------------------------------

    #: The type-id for this class.
    type_id = Constant('Simulation Results')
