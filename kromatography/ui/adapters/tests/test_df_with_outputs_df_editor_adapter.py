import pandas as pd
import unittest
from contextlib import contextmanager
import PySide

from traits.api import HasTraits, Instance
from traitsui.ui_editors.data_frame_editor import DataFrameEditor
from traitsui.api import Item, View

from kromatography.ui.adapters.df_with_outputs_df_editor_adapter import \
    DataFrameWithColumnOutputsAdapter

# Colors is RGBA tuples
YELLOW = PySide.QtGui.QColor.fromRgbF(1., 1., 0., 1.)
WHITE = PySide.QtGui.QColor.fromRgbF(1., 1., 1., 1.)
LIGHT_GREY = PySide.QtGui.QColor.fromRgbF(0.827451, 0.827451, 0.827451, 1.)


class Model(HasTraits):
    cost_data = Instance(pd.DataFrame)


class BaseDataFrameWithOutputsAdapter(object):
    def test_bring_up_no_output(self):
        with self.bring_ui_up(self.model_1_ouput, num_outputs=0) as ui:
            self.assert_output_header_white(ui, self.model_1_ouput)
            self.assert_input_white(ui, self.model_1_ouput)
            self.assert_all_output_color(ui, self.model_1_ouput, WHITE)

    def test_bring_up(self):
        with self.bring_ui_up(self.model_1_ouput, num_outputs=1) as ui:
            self.assert_output_header_white(ui, self.model_1_ouput)
            self.assert_input_white(ui, self.model_1_ouput)
            self.assert_all_output_color(ui, self.model_1_ouput, LIGHT_GREY)

    def test_multiple_outputs(self):
        with self.bring_ui_up(self.model_2_ouputs, num_outputs=2) as ui:
            self.assert_output_header_white(ui, self.model_2_ouputs)
            self.assert_input_white(ui, self.model_2_ouputs)
            self.assert_all_column_color(ui, self.model_2_ouputs, 2,
                                         LIGHT_GREY)
            self.assert_all_column_color(ui, self.model_2_ouputs, 3,
                                         LIGHT_GREY)

    # Helpers -----------------------------------------------------------------

    @contextmanager
    def bring_ui_up(self, model, num_outputs=1):
        adapter = self.adapter_class(
                df_attr_name="cost_data",
                num_outputs=num_outputs
            )
        cost_data_editor = DataFrameEditor(adapter=adapter)
        view = View(Item('cost_data', editor=cost_data_editor))
        ui = model.edit_traits(view=view)
        try:
            yield ui
        finally:
            ui.dispose()

    def get_background_color(self, editor, model, row, col):
        # The adapter returns None when the default (white) is to be used:
        bg_col = editor.adapter.get_bg_color(model, "cost_data", row, col)
        if bg_col is None:
            bg_col = WHITE
        return bg_col


class TestDataFrameWithColumnOutputsAdapter(BaseDataFrameWithOutputsAdapter,
                                            unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super(TestDataFrameWithColumnOutputsAdapter, self).__init__(*args,
                                                                    **kwargs)
        self.adapter_class = DataFrameWithColumnOutputsAdapter

    def setUp(self):
        self.size = 3
        self.index = ["sim_{}".format(i) for i in range(self.size)]
        data = pd.DataFrame({"ka": [1, 2, 3], "cost": [0.5, 0.1, 0.75]},
                            index=self.index)
        # order the columns
        self.data_1_output = data[["ka", "cost"]]
        self.model_1_ouput = Model(cost_data=self.data_1_output)

        data = {"ka": [1, 2, 3], "cost1": [0.5, 0.1, 0.75],
                "cost2": [0., 0.1, 0.75]}
        data = pd.DataFrame(data, index=self.index)
        self.data_2_outputs = data[["ka", "cost1", "cost2"]]
        self.model_2_ouputs = Model(cost_data=self.data_2_outputs)

    # Helpers -----------------------------------------------------------------

    def assert_output_header_white(self, ui, model):
        index_col = 0
        self.assert_all_column_color(ui, model, index_col, WHITE)

    def assert_input_white(self, ui, model):
        input_col = 1
        self.assert_all_column_color(ui, model, input_col, WHITE)

    def assert_all_output_color(self, ui, model, color):
        output_col = 2
        self.assert_all_column_color(ui, model, output_col, color)

    def assert_all_column_color(self, ui, model, column, color):
        editor = ui._editors[0]
        for i in range(self.size):
            self.assertEqual(
                self.get_background_color(editor, model, i, column), color
            )
