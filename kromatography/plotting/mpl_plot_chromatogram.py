import re
import numpy as np
import matplotlib.pyplot as plt

from kromatography.plotting.plot_utils import plot_data
from kromatography.utils.string_definitions import FRACTION_TOTAL_DATA_KEY


def plot_chromatogram(expt, sim):
    """ Build maplotlib plot to display experimental chromatogram and
    simulation chromatogram together following legacy code pattern.

    FIXME: This should take a study, experiment name/id and optionally a bunch
    of simulation id and create complete plot data.
    """
    data = build_data(expt, sim)
    plot_data(data)
    plt.show()


def build_data(expt, sim):
    """ Convert experiment and simulation into plot data.

    FIXME: This should ideally adapt ExperimentResult/SimulationResult
    objects to a `ChromatographyPlotData` that can then be plotted by the
    `ChromatogramPlot` (chaco plot)
    FIXME: check expt and sim are compatible
    """

    data = {}

    # NOTES:
    # set t0 = start of load step
    # time units -> minutes
    # concentrations/absorbance -> AU/cm

    # experiment results ------------------------------------------------------
    # total product conc (UV data)
    expt_results = expt.output
    uv_data = expt_results.continuous_data.get('uv')
    if uv_data is not None:
        # FIXME: we should just set simulation data timestamps to be
        # correct instead of truncation the plotted data
        # For now, just adjust experiment data to the simulation range

        # Get the start time for the Load step in the physical experiment.
        # To find this, look into the logs from the experiment and search
        # for the start of the Load section.
        log_book = expt_results.continuous_data['log_book']
        load_start_ind = -1
        for ii, log_entry in enumerate(log_book.y_data.tolist()):
            if re.search(".*[Ll]oad", log_entry):
                load_start_ind = ii
                break

        # FIXME: what to do if we can't find the start ?
        if load_start_ind == -1:
            raise RuntimeError(
                'Failed to find the start timestamp for the Load Step '
                'from the AKTA log_book data'
            )

        # create a mask for all data before the load step.
        t0 = log_book.x_data[load_start_ind]
        trunc_x = uv_data.x_data - t0
        mask = trunc_x > 0

        if np.sum(mask) == 0:
            raise RuntimeError((
                'No valid AKTA data found after the start of load step : {}'
            ).format(t0))

        # FIXME: The AKTA data seems to have the units (mAU). So convert
        # to AU/cm.
        y_data = uv_data.y_data / (1000. * expt.system.abs_path_length[()])

        # FIXME: need a mapping to plot labels.
        uv_name = "{}_Expt UV".format(expt.name)
        data[uv_name] = {
            'x': trunc_x[mask],
            'y': y_data[mask],
            'name': uv_name,
            'kind': 'experiment'
        }

    # product conc (fraction data). This has time with respect to the start of
    # the load already. No need to remove t0.

    total_fraction_data = expt_results.fraction_data.get(
        FRACTION_TOTAL_DATA_KEY
    )
    if total_fraction_data is not None:
        frac_x_data = total_fraction_data.x_data
        frac_y_data = total_fraction_data.y_data
        mask = frac_x_data > 0
        data['fraction'] = {
            'x': frac_x_data[mask],
            'y': frac_y_data[mask],
            'name': 'Fraction_Total',
            'kind': 'fraction'
        }

    # simulation results ------------------------------------------------------
    sim_results = sim.output
    cation_conc = sim_results.continuous_data['cation_Sim']

    # convert time to minutes
    # FIXME: use stored units instead of hardcoding units
    # FIXME: also, the `kind` attribute is currently being used by the plot
    # function to figure out layout/properties etc. figure out a better
    # classification/labels considering all the data that need to be plotted.
    sim_time = cation_conc.x_data / 60.0
    data['cation'] = {
        'x': sim_time,
        'y': cation_conc.y_data,
        'name': cation_conc.name,
        'kind': 'cation'
    }

    # Identify the data that goes into the chromatogram using metadata
    for name, xy_data in sim_results.continuous_data.iteritems():

        if xy_data.y_metadata['type'] == 'chromatogram':

            data[xy_data.name] = {
                'x': sim_time,
                'y': xy_data.y_data,
                'name': xy_data.name,
                'kind': 'sim'
            }

    return data
