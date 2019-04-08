"""
"""
import logging

from scimath.units.api import UnitScalar

from kromatography.io.akta_reader import AKTAReader
from kromatography.model.x_y_data import XYData
from kromatography.utils.units_utils import vol_to_time
from kromatography.utils.string_definitions import UV_DATA_KEY

logger = logging.getLogger(__name__)

# Map the run_type to the type of the method step which is eluting the product.
# Used by the holdup volume computation to convert the holdup volume into a
# holdup time
PRODUCT_FLOW_STEP = {"Pulse Injection": "Step Elution",
                     "Pulse Gradient": "Gradient Elution",
                     "Gradient Elution": "Gradient Elution",
                     "Step Elution": "Step Elution",
                     "Flow Through": "Load",
                     "Frontal Elution": "Load"}


def continuous_data_from_akta(import_settings, target_experiment):
    """ Utility to load/transform AKTA data from settings dict, and target exp.

    Parameters
    ----------
    import_settings : dict
        AKTA file import settings.

    target_experiment : Experiment
        Target experiment for which AKTA file contains data. Used to shift the
        data by the hold up volume.

    Returns
    -------
    dict
        Dict mapping data type to XYData storing traces.
    """
    continuous_data = {}
    # AKTA reader applies the truncation of the data for every point before the
    # time of origin:
    akta_reader = AKTAReader(
        file_path=import_settings["akta_fname"],
        time_of_origin=float(import_settings["time_of_origin"]),
        col_name_patterns=import_settings["col_name_patterns"]
    )

    header_info = akta_reader.header_info
    for key in akta_reader.available_dataset_types:
        time_key = 'time_' + key
        cont_data = XYData(
            name=key,
            x_data=akta_reader.get_data([time_key])[time_key],
            x_metadata=header_info[time_key],
            y_data=akta_reader.get_data([key])[key],
            y_metadata=header_info[key],
        )
        continuous_data[key] = cont_data

    # Modify results to shift output data by the holdup volume
    offset = shift_continuous_data_by_holdup_vol(continuous_data,
                                                 target_experiment)
    # Record volume used:
    import_settings["holdup_volume"] = offset
    return continuous_data


def shift_continuous_data_by_holdup_vol(cont_data, target_experiment):
    """ Shift all continuous and fraction data to remove holdup_volume.
    This is necessary when trying to compare experiments and simulations,
    because simulations don't assume any piping before and after the
    chromatography column.
    """
    # Shift time axis for continuous data:
    if UV_DATA_KEY in cont_data:
        xydata = cont_data[UV_DATA_KEY]
        x_units = xydata.x_metadata['units']
        time_offset = compute_time_offset_from_holdup_volume(target_experiment,
                                                             x_units)

        # Shift time axis for continuous data (AKTA files x axis datasets
        # are always in same unit so it can just be computed once)
        for xydata in cont_data.values():
            xydata.x_data -= time_offset

        return UnitScalar(time_offset, units=x_units)


def shift_fraction_data_by_holdup_vol(fraction_data, target_experiment):
    """ Shift all continuous and fraction data to remove holdup_volume.
    This is necessary when trying to compare experiments and simulations,
    because simulations don't assume any piping before and after the
    chromatography column.
    """
    # Shift time axis for fraction data. Note: all fraction datasets share
    # the same x_data array, so grab it from one of the XYData objects
    xydata = fraction_data.values()[0]
    x_units = xydata.x_metadata.get('units', 'minute')
    time_offset = compute_time_offset_from_holdup_volume(target_experiment,
                                                         x_units)
    xydata.x_data -= time_offset


def compute_time_offset_from_holdup_volume(target_experiment, tgt_units="min"):
    """ Compute the time offset to apply to result data from system and column
    info.

    Returns
    -------
    UnitScalar
        Time offset in tgt_units.
    """
    method = target_experiment.method
    step_type = PRODUCT_FLOW_STEP[method.run_type]
    product_flow_step = method.get_step_of_type(step_type)
    flow_rate = product_flow_step.flow_rate
    holdup_volume = target_experiment.system.holdup_volume
    column = target_experiment.column
    time_offset = vol_to_time(holdup_volume, flow_rate, column=column,
                              to_unit=tgt_units)
    return time_offset
