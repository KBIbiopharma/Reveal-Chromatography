
from traits.api import register_factory, TraitDictObject, TraitListObject
from traitsui.api import ITreeNode

from app_common.traitsui.adapters.trait_object_to_tree_node \
    import TraitDictObjectToTreeNode
from app_common.traitsui.adapters.data_element_to_i_tree_node import \
    DataElement, DataElementToITreeNode

from kromatography.ui.adapters.base_chromatography_data_to_i_tree_node import \
    BaseChromatographyDataToITreeNode, ChromatographyData
from kromatography.ui.adapters.data_manager_to_i_tree_node import \
    DataManager, DataManagerToITreeNode
from kromatography.ui.adapters.study_to_i_tree_node import Study, \
    StudyToITreeNode
from kromatography.ui.adapters.data_source_to_i_tree_node import \
    SimpleDataSource, SimpleDataSourceToITreeNode
from kromatography.ui.adapters.simulation_to_i_tree_node import \
    Simulation, SimulationToITreeNode
from kromatography.ui.adapters.simulation_group_to_i_tree_node import \
    SimulationGroup, SimulationGroupToITreeNode
from kromatography.ui.adapters.study_analysis_tools_to_i_tree_node import \
    StudyAnalysisTools, StudyAnalysisToolsToITreeNode
from kromatography.ui.adapters.brute_force_binding_model_optimizer_to_i_tree_node import BruteForce2StepBindingModelOptimizer, BruteForceBindingModelOptimizerToITreeNode  # noqa
from kromatography.ui.adapters.experiment_optimizer_step_to_i_tree_node \
    import ExperimentOptimizerStep, ExperimentOptimizerStepToITreeNode
from kromatography.ui.adapters.experiment_optimizer_to_i_tree_node import \
    ExperimentOptimizer, ExperimentOptimizerToITreeNode

from kromatography.utils.trait_object_to_tree_node import \
    TraitListObjectToTreeNode


def register_all_tree_node_adapters():
    """ Register in Traits all ITreeNode adapters so that a DataManager can be
    displayed automatically using a TreeEditor.
    """
    register_factory(BaseChromatographyDataToITreeNode, ChromatographyData,
                     ITreeNode)
    register_factory(DataManagerToITreeNode, DataManager, ITreeNode)
    register_factory(StudyToITreeNode, Study, ITreeNode)
    register_factory(SimpleDataSourceToITreeNode, SimpleDataSource, ITreeNode)
    register_factory(DataElementToITreeNode, DataElement, ITreeNode)

    register_factory(TraitListObjectToTreeNode, TraitListObject, ITreeNode)
    register_factory(TraitDictObjectToTreeNode, TraitDictObject, ITreeNode)
    register_factory(SimulationToITreeNode, Simulation, ITreeNode)
    register_factory(SimulationGroupToITreeNode, SimulationGroup, ITreeNode)
    register_factory(StudyAnalysisToolsToITreeNode, StudyAnalysisTools,
                     ITreeNode)
    register_factory(BruteForceBindingModelOptimizerToITreeNode,
                     BruteForce2StepBindingModelOptimizer, ITreeNode)
    register_factory(ExperimentOptimizerToITreeNode, ExperimentOptimizer,
                     ITreeNode)
    register_factory(ExperimentOptimizerStepToITreeNode,
                     ExperimentOptimizerStep, ITreeNode)
