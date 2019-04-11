import logging
import numpy as np
import pandas as pd
from functools import partial

from kromatography.model.chromatography_data import ChromatographyData
from app_common.traits.param_trait_search import search_parameters_in_data

logger = logging.getLogger(__name__)

POTENTIAL_PARAMETER_TYPES = (int, float, np.ndarray, pd.Series)


search_parameters_in_chrom_data = partial(search_parameters_in_data,
                                          data_klass=ChromatographyData)


def search_parameters_in_sim(sim, exclude=None, name_filter=None):
    """ Search for parameters that can be scanned in provided simulation.

    Parameters
    ----------
    sim : Simulation
        Simulation to search for Parameter type attributes in.

    exclude : list [OPTIONAL, default=("source_experiment", "output")]
        List of simulation attributes to ignore.

    name_filter : str [OPTIONAL, default=None]
        Text that all parameters returned should contain. Leave blank to see
        all parameters.

    Notes
    -----
    TODO: Add a caching for parameters so the same list doesn't get re-computed
    every time.
    """
    if exclude is None:
        exclude = ("source_experiment", "output")

    param_list = search_parameters_in_chrom_data(sim, exclude=exclude)
    if name_filter:
        param_list = [name for name in param_list if name_filter in name]
    return param_list
