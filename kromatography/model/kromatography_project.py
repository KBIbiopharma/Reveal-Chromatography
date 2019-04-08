"""
"""
import logging

from traits.api import Bool, HasStrictTraits, Instance, List, Property, Str

from app_common.encore.job_manager import JobManager
from .data_manager import DataManager
from .data_source import DataSource, SIMPLE_DS_OBJECT_TYPES, \
    STUDY_DS_OBJECT_TYPES
from .study import make_blank_study, Study

logger = logging.getLogger(__name__)


class KromatographyProject(HasStrictTraits):
    """ Global model to support the Kromatography GUI application.

    Responsible for holding data, and notifying when data gets deleted.
    """
    # -------------------------------------------------------------------------
    # 'KromatographyProject' interface
    # -------------------------------------------------------------------------

    #: Project's name
    name = Str

    #: Accessor for all data to edit
    data_manager = Instance(DataManager)

    #: Source of default data objects for creating new data elements. Set to
    #: parent KromatographyApp.
    datasource = Instance(DataSource)

    #: Manager for running CADET jobs
    job_manager = Instance(JobManager)

    #: Study this project will make
    study = Instance(Study)

    #: List of UUIDs of deleted object so that containing Task can close
    #: related tab
    deleted_objects = List

    #: List of chromatogram plots created
    chrom_plots = List

    #: Check if the project's components have been modified
    is_blank = Property(Bool,
                        depends_on="name, study, datasource, chrom_plots")

    # Traits initializers -----------------------------------------------------

    def _data_manager_default(self):
        return DataManager(data_elements=[self.datasource, self.study])

    def _study_default(self):
        study = make_blank_study(datasource=self.datasource)
        return study

    def _chrom_plots_default(self):
        return []

    def _get_is_blank(self):
        """ Returns whether any part of the project hasn't been modified.

        Modifications to the user datasource are ignored.
        """
        if self.name:
            return False

        if self.chrom_plots:
            return False

        if self.study:
            study = self.study
            if not study.is_blank:
                return False

            if study.product_set:
                return False

        return True

    def add_object_deletion_listeners(self):
        """ Add a listener to each and every list where object may be deleted.

        This is used by the KromTask to trigger the closure of corresponding
        central pane editor(s) if any.
        """
        # list of paths to lists that might be open in the central pane:
        lists_to_listen = {
            "study": ["simulations", "experiments"],
            "study.study_datasource": STUDY_DS_OBJECT_TYPES,
            "datasource": SIMPLE_DS_OBJECT_TYPES,
            "study.analysis_tools": ["optimizations", "simulation_grids",
                                     "monte_carlo_explorations",
                                     "optimizations.optimal_simulations",
                                     "simulation_grids.simulations",
                                     "monte_carlo_explorations.simulations"]
        }
        for obj_path, list_names in lists_to_listen.items():
            obj = eval("self.{}".format(obj_path))
            for name in list_names:
                obj.on_trait_change(self._notify_list_change, name+"[]")

    def _notify_list_change(self, obj, name, objects_deleted, obj_added):
        """ Store information about objects being deleted from the project.
        """
        for obj_deleted in objects_deleted:
            obj_info = {"uuid": obj_deleted.uuid, "name": obj_deleted.name,
                        "type": obj_deleted.__class__.__name__}
            self.deleted_objects.append(obj_info)
