
from traits.api import adapt
from traitsui.api import ModelView
from pyface.ui.qt4.util.gui_test_assistant import GuiTestAssistant

from app_common.apptools.testing_utils import temp_bringup_ui_for

from kromatography.model.data_source import SimpleDataSource
from kromatography.ui.api import register_all_data_views
from kromatography.ui.chrom_data_crud_editor import \
    ChromatographyDataCRUDEditor


class BaseModelViewTestCase(GuiTestAssistant):

    @classmethod
    def setUpClass(cls):
        # This will add the all ModelView classes as a factory to convert a
        # ChromData to a traitsUI ModelView.
        register_all_data_views()

        cls.ds = SimpleDataSource()

    def setUp(self):
        GuiTestAssistant.setUp(self)

    def tearDown(self):
        GuiTestAssistant.tearDown(self)

    def test_view_adaptation(self):
        model_view = self._get_model_view()
        self.assertIsInstance(model_view, ModelView)

    def test_view_building(self):
        model_view = self._get_model_view()
        with temp_bringup_ui_for(model_view):
            pass

    def test_view_inside_CRUD_editor(self):
        model_view = self._get_model_view()
        crud_editor = ChromatographyDataCRUDEditor(model_view=model_view)
        with temp_bringup_ui_for(crud_editor):
            pass

    # Utility methods ---------------------------------------------------------

    def _get_model_view(self):
        return adapt(self.model, ModelView)


class BaseComponentArrayView(object):
    def test_build_component_array_from_components(self):
        model_view = self._get_model_view()
        self.assertIsInstance(model_view.component_array, list)
        self.assertEqual(len(model_view.component_array),
                         len(model_view.vector_attributes))
        # Make sure there is no proxy: the model arrays are contained in the
        # component_array attr:
        vectors = [getattr(self.model, attr)
                   for attr in model_view.vector_attributes]
        for i, arr in enumerate(vectors):
            self.assertIs(model_view.component_array[i], arr)

    def test_change_editor_changes_model(self):
        """ Make sure changing the editor/adapter changes the model. """
        model_view = self._get_model_view()
        adapter = model_view._comp_array_adapter
        row = 0
        column = 2
        text = "0.5"
        adapter.set_text(model_view, "component_array", row, column, text)
        model_attr = getattr(self.model, self.model_attr_to_test)
        # column - 1 since in the editor treats the index of the table as a
        # column too:
        self.assertEqual(model_attr[column-1], 0.5)
