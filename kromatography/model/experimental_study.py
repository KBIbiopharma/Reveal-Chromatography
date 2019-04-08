import logging

from traits.api import Property, Str, Unicode

from kromatography.model.base_study import BaseStudy

STUDY_TYPE = "EXPERIMENTAL_STUDY"

logger = logging.getLogger(__name__)


class ExperimentalStudy(BaseStudy):
    """ Experimental study, that is a set of experiments that can be loaded
    from an Excel file written by an experimentalist.
    """
    #: Excel file the study is loaded from
    filepath = Unicode

    #: Description of the scientific purpose for the experiments
    study_purpose = Str

    #: Study ID (lab notebook or ELN reference)
    study_id = Str

    #: Study type (e.g. Process Development, Process Characterization).
    # Potential for future enumeration
    study_type = Str

    #: Location where the experiments were conducted
    study_site = Str

    #: Experimentalist conducting the experiments
    experimentalist = Str

    #: Product studied.
    # Product or None if no experiments or no product in all experiments
    product = Property(depends_on="experiments")

    # -------------------------------------------------------------------------
    # ChromatographyData traits
    # -------------------------------------------------------------------------

    type_id = Str(STUDY_TYPE)

    # -------------------------------------------------------------------------
    # ExperimentalStudy private interface
    # -------------------------------------------------------------------------

    def _get_product(self):
        """ The product of the study is the product of any of its experiments
        or simulations.
        """
        for exp in self.experiments:
            if exp.product is not None:
                return exp.product

        return None

    def _get_product_set(self):
        return self.product is not None


if __name__ == "__main__":
    study = ExperimentalStudy(name="test study")
    study.configure_traits()
