from traits.api import Color, Int, Str
from traitsui.ui_editors.data_frame_editor import DataFrameAdapter


class DataFrameWithOutputsAdapter(DataFrameAdapter):
    """ Custom adapter to colorize the column outputs of a dataframe.
    """
    #: Color to use as background for the output columns/rows
    output_color = Color("lightgrey")

    #: Name of attribute of the object we are editing.
    # We can't pass the DF itself because it might get reallocated during the
    # life of the edited object
    df_attr_name = Str

    #: Number of columns/rows that contain outputs to be colorized
    num_outputs = Int


class DataFrameWithColumnOutputsAdapter(DataFrameWithOutputsAdapter):
    """ Custom adapter to colorize the column outputs of a dataframe.
    """
    def get_bg_color(self, obj, trait, row, column=0):
        """ Colorize the outputs in grey.
        """
        df = getattr(obj, self.df_attr_name)

        # Select background color
        # The tableEditor counts the index as column 0, whereas the user's
        # specifies behavior using DF columns
        total_cols = len(df.columns) + 1
        # Outputs are located on the last num_outputs columns:
        if column >= total_cols - self.num_outputs:
            return self.output_color

        return None
