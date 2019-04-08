""" Export all plot data from active plot tab.

Created on: Oct 24th 2016
Updated on: Oct 25th 2016
Script version: 3
Reveal Chromatography versions: 0.5.3, 0.6.0
"""
# Script inputs ---------------------------------------------------------------

# List of experiment or simulation names to export (case ignored). Leave empty
# to export everything
COLLECTIONS_TO_INCLUDE = []
# Example: exporting just 1 experiment and the corresponding simulation:
# COLLECTIONS_TO_INCLUDE = ['Run_1', 'Sim: run_1']

# Script ----------------------------------------------------------------------
import logging
from os.path import abspath, exists, isfile, splitext
import pandas as pd

from pyface.api import error, confirm, NO

from kromatography.utils.extra_file_dialogs import to_csv_file_requester
from kromatography.utils.app_utils import IS_WINDOWS
from kromatography.plotting.data_models import ChromatogramModel

logger = logging.getLogger(__name__)

logger.warning("Exporting data from a plot tab...")


def export_chrom_model_to_csv(chrom_model, target_file, force=False,
                              collections=()):
    """ Export to a CSV file all the curves found in a ChromatogramModel.

    If the file already exists, the export will be aborted unless force is set
    to True.

    Parameters
    ----------
    chrom_model : ChromatogramModel
        Plot model to store.

    target_file : str
        Path to the file to create.

    force : bool
        Ignore if the target file already exists?

    collections : iterable of strings
        List/tuple of collection names to include (that is experiment or
        simulation names). Leave empty to export every collection.
    """
    if collections:
        if not isinstance(collections, (list, tuple, set)):
            msg = "The list of collections to export must be a list, but a {}"\
                  " was provided.".format(type(collections))
            logger.error(msg)
            raise ValueError(msg)

        collections = list(collections)
        for element in collections:
            if not isinstance(collections, (list, tuple, set)):
                msg = "The list of collections to export must only contain " \
                      "strings with collection names but a {} was found."
                msg = msg.format(type(element))
                logger.error(msg)
                raise ValueError(msg)

        collections = set([col.lower() for col in collections])

    if not isinstance(chrom_model, ChromatogramModel):
        msg = "Active tab is not a plot. Please select the plot you want to " \
              "export and run again."
        logger.exception(msg)
        raise ValueError(msg)

    target_file = abspath(target_file)

    if isfile(target_file) and not force:
        msg = "Can't export Chromatogram model to {} because it already " \
              "exists. Set force to True to ignore.".format(target_file)
        logger.exception(msg)
        raise IOError(msg)

    log_dfs = []
    for collection_name, collection in chrom_model.log_collections.items():
        if collections and collection_name.lower() not in collections:
            continue

        for name, log in collection.logs.items():
            data = {collection_name + ": " + name + " (x)": log.x_data}
            log_dfs.append(pd.DataFrame(data))
            data = {collection_name + ": " + name + " (y)": log.y_data}
            log_dfs.append(pd.DataFrame(data))

    if not log_dfs:
        msg = "No data found with current selection. Collections requested " \
              "are {}. Typos?".format(collections)
        logger.error(msg)
        return

    logger.debug("Exporting {} datasets exported to {}.".format(len(log_dfs),
                                                                target_file))
    df = pd.concat(log_dfs, axis=1)
    df.to_csv(target_file)
    logger.debug("Data exported to {}.".format(target_file))


central_pane = task.central_pane
active_chrom_plot = central_pane.active_editor.obj
if not isinstance(active_chrom_plot, ChromatogramModel):
    msg = "Active tab is not a plot. Please select the plot you want to " \
          "export and run again."
    logger.exception(msg)
    error(None, msg)
else:
    export_path = to_csv_file_requester()
    if export_path is not None:
        export_ext = splitext(export_path)[1]
        if not export_ext:
            export_path += ".csv"

    abort = False
    # Only confirm on windows, since on Mac, the FileDialog has this builtin.
    if exists(export_path) and IS_WINDOWS:
        result = confirm(None, "The file already exists: overwrite?")
        if result == NO:
            abort = True

    if export_path and not abort:
        export_chrom_model_to_csv(active_chrom_plot, export_path, force=True,
                                  collections=COLLECTIONS_TO_INCLUDE)

# End of script ---------------------------------------------------------------
