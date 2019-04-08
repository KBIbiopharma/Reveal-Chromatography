import logging

from traits.api import Any, Bool, Instance, List, Property, Str

from kromatography.model.api import ChromatographyData
from kromatography.model.data_source import DataSource, SimpleDataSource
from kromatography.model.experiment import Experiment

BASE_STUDY_TYPE = "UNDEFINED STUDY"

logger = logging.getLogger(__name__)


class BaseStudy(ChromatographyData):
    """ Study base class for both a modelling study or an experimental study.

    A study in general analyses a product and can contains simulations and
    experiments, as well as a datasource, that is a bank of standard
    chromatography components.
    """

    # -------------------------------------------------------------------------
    # Study traits
    # -------------------------------------------------------------------------

    #: Cross study datasource to assist in the experiment loading and parameter
    #: validation
    datasource = Instance(DataSource)

    #: Production studied
    product = Any

    #: Experiments
    experiments = List(Instance(Experiment))

    #: Is there a valid product set
    product_set = Property(Bool)

    # -------------------------------------------------------------------------
    # ChromatographyData traits
    # -------------------------------------------------------------------------

    type_id = Str(BASE_STUDY_TYPE)

    # -------------------------------------------------------------------------
    # ExperimentalStudy interface methods
    # -------------------------------------------------------------------------

    def add_experiments(self, experiment_list):
        """ Add multiple experiments to the study, checking that the target
        product is the same as the study and that they have different names.

        Parameters
        ----------
        experiment_list : iterable
            List (or other iterable) of experiments to add to the study.
        """
        # If only 1 experiment is passed, make it a list for consistency
        if isinstance(experiment_list, Experiment):
            experiment_list = [experiment_list]

        # Make sure all products are the same:
        experiment0 = experiment_list[0]
        for exp in experiment_list[1:]:
            if exp.product != experiment0.product:
                msg = ("All experiments to add to a study should be about the "
                       "same product, but experiment {} has product {} whereas"
                       "first experiment targets product {}.")
                msg = msg.format(exp.name, exp.product.name,
                                 experiment0.product.name)
                logger.exception(msg)
                raise ValueError(msg)

        # Check experiment product is consistent with Study's product
        study_product = self.product
        new_product = experiment0.product
        if self.product_set and new_product != study_product:
            msg = ("All experiments inside a study should be about the"
                   " same product, but the experiment to be added has"
                   " a different product than the first one in the "
                   "study ({} vs {})")
            msg = msg.format(new_product.unique_id, study_product.unique_id)
            logger.exception(msg)
            raise ValueError(msg)

        # Check that all experiments have a different names
        exp_names = [exp.name for exp in experiment_list]
        unique_names = set(exp_names)
        if len(unique_names) != len(exp_names):
            msg = ("Provided experiments have redundant names: "
                   "{}".format(unique_names))
            logger.exception(msg)
            raise ValueError(msg)

        for exp in experiment_list:
            self.experiments.append(exp)

    def search_experiment_by_name(self, name):
        """ Search and return experiment with a specific name.
        """
        exp_names = []
        for exp in self.experiments:
            exp_names.append(exp.name)
            if exp.name == name:
                return exp

        msg = "No experiment with name {}. Available experiments are {}"
        msg = msg.format(name, exp_names)
        logger.exception(msg)
        raise KeyError(msg)

    def _datasource_default(self):
        return SimpleDataSource()
