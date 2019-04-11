"""
Chromatography run results contain continuous XY data, performance information,
collected into in a ChromatographyResults object.
"""
import logging

from traits.api import Array, Constant, Dict

from kromatography.model.chromatography_data import ChromatographyData

logger = logging.getLogger(__name__)


class XYData(ChromatographyData):
    """ Holds a collection of (x, y) data and their metadata.

    An instance of this class typically represents a time series data, where
    `x_data`, `y_data`  correspond to the time and value axes respectively.

    FIXME: it is not clear if all the arrays should be unit arrays ?
        a. sometime we may not have units (log_book etc.)

    perhaps just provide properties/methods that return UnitArrays while
    leaving the underlying data just be arrays ?
    """

    #: The data samples for the independant axis (typically time).
    #: This is always a float array.
    x_data = Array(dtype=float)

    #: The data samples for the dependant axis (e.g. uv280, temperature).
    #: This is often a float array but can be string array. For instance, the
    #: `log_book` data for an experiment contains comments from the
    #: user/instrument over the duration of the experiment.
    y_data = Array()

    #: Contains any metadata corresponding to `x_data`.
    x_metadata = Dict

    #: Contains any metadata corresponding to `y_data`.
    y_metadata = Dict

    # -------------------------------------------------------------------------
    # ChromatographyData traits
    # -------------------------------------------------------------------------

    #: The type-id for this class.
    type_id = Constant('X-Y Data')

    def mpl_show(self, filepath="", **kwargs):
        """ Quick Matplotlib plot of the current data and show/save to file.

        Parameters
        ----------
        filepath : str
            Path to the file to export the plot to. Leave empty to show the
            plot live instead.

        kwargs : dict
            Extra arguments for the savefig function. See documentation for
            :func:`matplotlib.pyplot.savefig`.
        """
        from matplotlib.pyplot import plot, show, savefig, title, xlabel, \
            ylabel

        plot(self.x_data, self.y_data)
        title(self.name)
        x_axis_label = "X ({})".format(self.x_metadata.get("units", ""))
        xlabel(x_axis_label)
        y_axis_label = "Y ({})".format(self.y_metadata.get("units", ""))
        ylabel(y_axis_label)
        if filepath:
            savefig(filepath, **kwargs)
        else:
            show()
