""" Utility for easy exploration of content of AKTA files.
"""
import pandas as pd


def plot_akta_data(akta_content):
    """ Display 1 timeseries read from an AKTA file.

    Parameters
    ----------
    akta_content : dict
        Dictionary containing numpy arrays with a set of x values and y values.
        These arrays are assumed to be mapped to keys of the form 'time_NAME'
        and NAME where NAME describes the type of data stored.

        This expects a dictionary as returned by
        `kromatography.io.akta_reader.read_akta`.
    """
    import matplotlib.pyplot as plt

    all_series = []
    for key in akta_content:
        if key.startswith("time_"):
            x_key = key
            y_key = key[len("time_"):]
            assert(key in akta_content)
            data = pd.Series(akta_content[y_key], index=akta_content[x_key])
            all_series.append(data)

    num_series = len(all_series)
    for i, series in enumerate(all_series):
        series = series.dropna()
        plt.subplot(num_series, 1, i+1)
        series.plot()
        plt.title("Timeseries for {}".format(y_key.upper()))
    plt.show()
