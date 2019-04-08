from traits.api import Instance

from kromatography.model.study_analysis_tools import StudyAnalysisTools

from .base_chromatography_data_to_i_tree_node import \
    BaseChromatographyDataToITreeNode


class StudyAnalysisToolsToITreeNode(BaseChromatographyDataToITreeNode):
    """ Adapts a Study to an ITreeNode.

    This class implements the ITreeNodeAdapter interface thus allowing the use
    of TreeEditor for viewing any Study.
    """

    adaptee = Instance(StudyAnalysisTools)

    # 'ITreeNodeAdapter' protocol ---------------------------------------------

    def _get_children(self):
        children = [self.adaptee.simulation_grids,
                    self.adaptee.monte_carlo_explorations,
                    self.adaptee.optimizations]
        return children

    def get_label(self):
        return "Analysis Tools"
