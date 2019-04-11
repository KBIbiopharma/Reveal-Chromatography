import numpy as np

from scimath.units.api import UnitArray

from kromatography.utils.units_utils import vol_to_time


def calculate_step_start_times(sim):
    """ Calculate all step start times and stop time of the last step in min
    from the beginning of the method.

    Parameters
    ----------
    sim : _BaseExperiment (Experiment or Simulation)
        Experiment-like object containing the method to analyze.

    Returns
    -------
    UnitArray
        Start times for all steps and stop time of last step in minutes.
    """
    start_times = [0.]

    for step in sim.method.method_steps:
        step_time = vol_to_time(step.volume, step.flow_rate,
                                column=sim.column, to_unit="minute")
        start_times.append(step_time)

    start_times = np.cumsum(start_times)
    return UnitArray(start_times, units="minute")
