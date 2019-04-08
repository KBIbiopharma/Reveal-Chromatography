from traits.api import Any, Constant, Instance, List, Str

from app_common.model_tools.data_element import DataElement
from kromatography.ui.multi_experim_strip_fraction_calculator_view import \
    MultiExpStripFractionCalculatorView


class StudyAnalysisTools(DataElement):
    """ Small container object to store simulation grids and optimizers done in
    a study.
    """
    # DataElement interface ---------------------------------------------------

    name = Str("Analysis tools")

    type_id = Constant("Analysis Tools")

    # StudyAnalysisTools interface --------------------------------------------

    #: List of regular simulation grids created to analyze the study
    simulation_grids = List()

    #: List of randomly sampled simulation groups created to analyze the study
    monte_carlo_explorations = List()

    #: List of optimizations created to analyze the study
    optimizations = List()

    # StudyAnalysisTools private interface ------------------------------------

    #: Handle on currently active Strip calculator to avoid gc collection
    _strip_calculator_view = Instance(MultiExpStripFractionCalculatorView)

    #: Handle on UI object for the strip_calculator view to avoid gc collection
    _strip_calculator_ui = Any

    def request_strip_fraction_tool(self, experiments):
        self._strip_calculator_view = MultiExpStripFractionCalculatorView(
                target_experiments=experiments
            )
        self._strip_calculator_ui = self._strip_calculator_view.edit_traits(
            kind="live"
        )
