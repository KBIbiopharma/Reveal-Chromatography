"""Plotting Functionality for Experiment and Simulation Results
"""

import itertools
import matplotlib.pyplot as plt

plt.rcParams['xtick.labelsize'] = 20
plt.rcParams['ytick.labelsize'] = 20

LINESTYLES = ["-", "--", "-.", ":"]
LINECYCLER = itertools.cycle(LINESTYLES)

PLOT_PROPERTIES = {
    'sim': {
        'ax': 0,
        'label': None,
        'legend': 'upper left',
        'plotkw': {
            'color': 'green'
        }
    },
    'cation': {
        'ax': 1,
        'label': None,
        'legend': None,
        'plotkw': {
            'color': 'blue'
        }
    },
    'experiment': {
        'ax': 0,
        'legend': 'upper left',
        'label': None,
        'plotkw': {
            'color': 'red',
            'linestyle': 'solid'
        }
    },
    'fraction': {
        'ax': 0,
        'legend': 'upper left',
        'label': 'Fractions Total',
        'plotkw': {
            'color': 'red',
            'linestyle': 'none',
            'marker': 'o',
        }
    }
}


def _get_xlim(data):
    """Returns the largest `x` value for all datasets in data
    """
    return max([dataset['x'][-1] for dataset in data.values()])


def _init_plot_axes(data):
    """
    """
    fig, ax = plt.subplots(figsize=[12, 8])
    axes = [ax, ax.twinx()]
    axes[0].set_xlabel('Time (min)', fontsize=26, fontweight='bold')
    # FIXME set plot axis limits (with Total_sim data?)
    x_lim = _get_xlim(data)
    axes[0].set_xlim([0, x_lim])
    axes[0].set_ylabel("Absorbance at 280 nm (AU/cm)",
                       fontsize=26,
                       fontweight='bold')
    axes[0].tick_params(axis='y', colors='green')

    axes[1].set_ylabel('Cation Concentration (mM)',
                       fontsize=26,
                       fontweight='bold')
    axes[1].tick_params(axis='y', colors='blue')

    return axes


def _plot_axes(data, axes):
    """data is dict specifying 'x', 'y', 'name', 'kind'
    returns new axes if no axes given
    """
    properties = PLOT_PROPERTIES[data['kind']]
    ax = axes[properties['ax']]

    if properties['label'] is None:
        label = data['name']
    else:
        label = properties['label']

    if data['kind'] == 'sim':
        properties['plotkw']['linestyle'] = next(LINECYCLER)

    ax.plot(data['x'], data['y'], label=label, **properties['plotkw'])

    if properties['legend'] is not None:
        ax.legend(loc=properties['legend'])
    return axes


def plot_data(data):
    """Creates and returns a matplotlib axes with data plotted.

    Parameters
    ----------
    data : dict
        "name" : "dataset" pairs, where dataset is a dictionary of
        'x' data, 'y' data, 'name' of the dataset, and 'kind'
        of the dataset (see PLOT_PROPERTIES for valid 'kind's)
    """
    # initialize axes if none given
    axes = _init_plot_axes(data)

    # iterate through each dataset plotting
    for name in data:
        _plot_axes(data[name], axes)
    return axes


if __name__ == '__main__':
    from kromatography.utils.testing_utils import plot_data_path
    import pickle

    # Read in raw_data and transform into expected input format
    DATAFILE = 'plotdata.pkl'
    path = plot_data_path(DATAFILE)
    with open(path, 'r') as f:
        raw_data = pickle.load(f)

    data = {
        'Cation': raw_data[0]['Cation'],
        'uv280': raw_data[1],
        'fraction': raw_data[2]
    }
    raw_data[0].pop('Cation')
    for sim in raw_data[0]:
        data[sim] = raw_data[0][sim]
        data[sim]['kind'] = 'sim'
    data['Cation']['kind'] = 'cation'
    data['uv280']['kind'] = 'experiment'
    data['fraction']['kind'] = 'fraction'

    # Plot the data from expected input format
    axes = plot_data(data)

    plt.show()
