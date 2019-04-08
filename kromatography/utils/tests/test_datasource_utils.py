from unittest import TestCase

from kromatography.utils.datasource_utils import (
    BaseEntryCreator, DATASOURCE_OBJECT_FACTORIES, prepare_datasource_catalog,
    prepare_study_datasource_catalog, STUDY_DATASOURCE_OBJECT_FACTORIES,
    StudyDataSourceEntryCreator, UserDataSourceEntryCreator
)
from kromatography.model.data_source import SimpleDataSource
from kromatography.model.tests.sample_data_factories import make_sample_study
import kromatography

MODEL_CLASS = {
    'components': kromatography.model.component.Component,
    'resin_types': kromatography.model.resin.Resin,
    'chemicals': kromatography.model.chemical.Chemical,
    'column_models': kromatography.model.column.ColumnType,
    'product_components': kromatography.model.product_component.ProductComponent,  # noqa
    'methods': kromatography.model.method.Method,
    'buffers': kromatography.model.buffer.Buffer,
    'system_types': kromatography.model.system.SystemType,
    # This cases lead to a preliminary UI before the actual object creation
    # UI:
    'products': kromatography.ui.factories.product.ProductBuilder,
    'columns': kromatography.ui.column_prep_view.ColumnPrepView,
    'systems': kromatography.ui.system_model_view.SystemTypeSelector,
    'loads': kromatography.ui.product_chooser_view.ProductChooser,
    'transport_models': kromatography.ui.product_chooser_view.ProductChooser,
    'binding_models': kromatography.ui.product_chooser_view.ProductChooser,
}


class TestDataSourcePreparationFunctions(TestCase):
    """ Test that datasource preparation functions add a creator on all DS
    object types.
    """
    def test_prepare_study_datasource_catalog(self):
        study = make_sample_study()
        prepare_study_datasource_catalog(study)
        ds = study.study_datasource
        self.assertCreatorOnAllEntries(ds)

    def test_prepare_datasource_catalog(self):
        datasource = SimpleDataSource()
        prepare_datasource_catalog(datasource)
        self.assertCreatorOnAllEntries(datasource)

    # helper methods ----------------------------------------------------------

    def assertCreatorOnAllEntries(self, datasource):
        keys_with_entry = (set(datasource.object_catalog.keys()) -
                           {'system_types', 'systems'})
        for key in keys_with_entry:
            val = getattr(datasource, key)
            self.assertIsInstance(val.add_new_entry, BaseEntryCreator)


class TestEntryCreator(TestCase):
    """ Make sure for all object type, the UI can be brought up, has the right
    type of model and the UI disposed of.
    """
    def test_UserDataSourceEntryCreator(self):
        datasource = SimpleDataSource()
        for key in DATASOURCE_OBJECT_FACTORIES:
            creator = UserDataSourceEntryCreator(
                datasource=datasource, datasource_key=key
            )
            self.assertCreatorValid(creator, key)

    def test_StudyDataSourceEntryCreator(self):
        study = make_sample_study()
        for key in STUDY_DATASOURCE_OBJECT_FACTORIES:
            creator = StudyDataSourceEntryCreator(study=study,
                                                  datasource_key=key)
            self.assertCreatorValid(creator, key)

    # helper methods ----------------------------------------------------------

    def assertCreatorValid(self, creator, key):
        ui = creator(kind=None)
        try:
            if 'model' in ui.context:
                self.assertIsInstance(ui.context['model'], MODEL_CLASS[key])
            else:
                self.assertIsInstance(ui.context['object'], MODEL_CLASS[key])
        finally:
            ui.dispose()
