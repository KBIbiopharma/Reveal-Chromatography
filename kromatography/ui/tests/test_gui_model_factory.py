from unittest import TestCase

from pyface.ui.qt4.util.gui_test_assistant import GuiTestAssistant

from kromatography.model.study import Study
from kromatography.model.buffer import Buffer
from kromatography.model.tests.example_model_data import BUFFER_ELUTION
from kromatography.model.data_source import InStudyDataSource, \
    SimpleDataSource
from kromatography.ui.gui_model_factory import request_new_column,\
    DATASOURCE_OBJECT_FACTORIES, STUDY_DATASOURCE_OBJECT_FACTORIES
from kromatography.ui.api import register_all_data_views
from kromatography.ui.column_prep_view import ColumnPrepView
from kromatography.ui.factories.binding_model import BindingModelBuilder


class TestRequestModelGUIs(GuiTestAssistant, TestCase):

    def setUp(self):
        GuiTestAssistant.setUp(self)

        register_all_data_views()
        datasource = SimpleDataSource()
        product = datasource.get_object_of_type("products", 'Prod001')
        ds = InStudyDataSource()
        buf = Buffer(**BUFFER_ELUTION)
        ds.set_object_of_type("buffers", buf)
        self.study = Study(name="test", product=product, datasource=datasource,
                           study_datasource=ds)
        ds = InStudyDataSource()
        self.study2 = Study(name="test2", datasource=datasource,
                            study_datasource=ds)

    def test_study_ds_ui_creation(self):
        for factory in STUDY_DATASOURCE_OBJECT_FACTORIES.values():
            ui = factory(self.study, kind=None)
            ui.dispose()

    def test_study_ds_ui_creation_empty_study(self):
        for factory in STUDY_DATASOURCE_OBJECT_FACTORIES.values():
            ui = factory(self.study2, kind=None)
            ui.dispose()

    def test_user_ds_ui_creation(self):
        # Need a test here to test that the model is correct when the
        # kind='livemodal'.  Cannot test because ui.result is only
        # True when the gui window is closed manually.
        for factory in DATASOURCE_OBJECT_FACTORIES.values():
            ui = factory(self.study.datasource, kind=None)
            ui.dispose()

    def test_user_ds_ui_creation_with_overriding_defaults(self):
        default_name = "Foo"
        for key, factory in DATASOURCE_OBJECT_FACTORIES.items():
            ui = factory(self.study.datasource, kind=None,
                         name=default_name)
            # For these types, the UI is not a ModelView, just a HT View:
            special_factories = ["products", "system", "binding_models",
                                 "transport_models"]
            if key in special_factories:
                model_name = "object"
            else:
                model_name = "model"

            model = ui.context[model_name]
            if hasattr(model, "name"):
                self.assertEqual(model.name, default_name)
            ui.dispose()

    def test_user_ds_binding_creation_with_overriding_defaults(self):
        factory = DATASOURCE_OBJECT_FACTORIES["binding_models"]
        ui = factory(self.study.datasource, kind=None,
                     target_product=self.study.product)
        model = ui.context["object"]
        self.assertIsInstance(model, BindingModelBuilder)
        ui.dispose()

    def test_user_ds_transport_creation_with_overriding_defaults(self):
        factory = DATASOURCE_OBJECT_FACTORIES["transport_models"]
        ui = factory(self.study.datasource, kind=None,
                     target_product=self.study.product, name="Foo")
        model = ui.context["model"]
        self.assertEqual(model.name, "Foo")
        ui.dispose()

    def test_request_new_column_skip_column_prep(self):
        # Skip column prep step to test final UI of column
        column_prep = ColumnPrepView(datasource=self.study.datasource,
                                     column_type_name="Axichrom100",
                                     resin_name='Fractogel-SO3 (M)')
        ui = request_new_column(self.study, kind=None,
                                column_prep=column_prep)
        ui.dispose()
