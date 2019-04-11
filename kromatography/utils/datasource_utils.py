import logging

from traits.api import Any, Callable, HasStrictTraits, Property, Str

from app_common.pyface.monitored_actions import action_monitoring

from kromatography.model.simulation import Simulation
from kromatography.ui.gui_model_factory import DATASOURCE_OBJECT_FACTORIES, \
    STUDY_DATASOURCE_OBJECT_FACTORIES
from kromatography.model.chromatography_data import ChromatographyData

BLANK_SIMULATION = Simulation(name="New simulation")

logger = logging.getLogger(__name__)


class BaseEntryCreator(HasStrictTraits):
    """ Generic object to request, create and add a new datasource entry to the
    datasource object_catalog dict. This might require to have access to the
    study to pull data like the chosen product or the user datasource.
    It might also request to select a product if not already set.
    """
    #: Datsource being contributed to
    datasource = Any

    #: Type of object being contributed
    datasource_key = Str

    #: List of objects being contributed to
    data = Property

    #: Function that should be invoked to display a GUI model builder.
    factory = Callable

    #: What the model factories need as their main input.
    factory_input = Any

    def _get_data(self):
        raise NotImplementedError()

    def __call__(self, kind="livemodal", **traits):
        """ Invoke the UI for the model factory and add to datasource attribute

        Parameters
        ----------
        kind : None or str
            Kind of the dialog. Set to None to make it non-blocking. Useful for
            testing purposes.

        traits : dict
            Attributes of the created object. Used to override the defaults.
        """
        action_name = "Adding new {} to {}"
        action_name = action_name.format(self.datasource_key,
                                         self.datasource.name)
        with action_monitoring(action_name):
            new_obj = self.factory(self.factory_input, kind=kind, **traits)

            if isinstance(new_obj, ChromatographyData):
                self.datasource.set_object_of_type(self.datasource_key,
                                                   new_obj)
            else:
                msg = "Object creation process aborted."
                logger.info(msg)

        return new_obj


class StudyDataSourceEntryCreator(BaseEntryCreator):
    """ Object to request, create and add a new datasource entry to a study
    datasource object_catalog dict.
    """
    #: Study containing the datasource being contributed to.
    study = Any

    #: Datasource being contributed to
    datasource = Property(depends_on="study")

    def _get_data(self):
        return getattr(self.datasource, self.datasource_key)

    def _factory_default(self):
        return STUDY_DATASOURCE_OBJECT_FACTORIES.get(self.datasource_key)

    def _get_datasource(self):
        return self.study.study_datasource

    def _factory_input_default(self):
        return self.study


class UserDataSourceEntryCreator(BaseEntryCreator):
    """ Object to request, create and add a new datasource entry to a
    SimpleDatasource object_catalog dict.
    """
    def _get_data(self):
        return getattr(self.datasource, self.datasource_key)

    def _factory_default(self):
        return DATASOURCE_OBJECT_FACTORIES.get(self.datasource_key)

    def _factory_input_default(self):
        return self.datasource


def prepare_study_datasource_catalog(study):
    """ Adds a factory object to add to each entry of a study datasource.
    """
    ds = study.study_datasource
    for key in ds.object_catalog:
        # Build a factory that can be called to add a new object to each of
        # these lists. Done that way so that it can be invoked from a
        # right-click action
        val = getattr(ds, key)
        if key in STUDY_DATASOURCE_OBJECT_FACTORIES:
            creator = StudyDataSourceEntryCreator(study=study,
                                                  datasource_key=key)
            val.add_new_entry = creator


def prepare_datasource_catalog(datasource):
    """ Adds a factory object to add to each entry of a user datasource.
    """
    for key in datasource.object_catalog:
        val = getattr(datasource, key)
        if key in DATASOURCE_OBJECT_FACTORIES:
            creator = UserDataSourceEntryCreator(datasource=datasource,
                                                 datasource_key=key)
            val.add_new_entry = creator
