""" Module containing the deserializer api function and supporting classes.

The deserializers are versioned and the ones in this module correspond to the
latest protocol. Because the software's goal is to be able to run any past file
created by users, old versions of deserializers that were updated are stored in
the legacy_deserializers.py module.
"""
import logging

from traits.api import Any

from app_common.apptools.io.deserializer import deSerializer

logger = logging.getLogger(__name__)


def deserialize(serial_data, array_collection=None):
    """ Functional entry point to deserialize any serial data.

    See app_common implementation for details.
    """
    from app_common.apptools.io.deserializer import deserialize
    from .legacy_deserializers import LEGACY_DESERIALIZER_MAP

    local_deserializers = {key: val for key, val in globals().items()
                           if key.endswith("DeSerializer")}
    deSerializer.legacy_deserializers.update(LEGACY_DESERIALIZER_MAP)
    return deserialize(serial_data, array_collection=array_collection,
                       additional_deserializers=local_deserializers)


class chromatographyDataDeSerializer(deSerializer):
    """ Base class for deserializing all chromatographyData objects.
    """
    def get_instance(self, constructor_data):
        import kromatography.model.chromatography_data
        instance = getattr(kromatography.model.chromatography_data,
                           constructor_data['metadata']['type'])(
                           **constructor_data['kwargs'])
        return instance


class kromatographyTaskDeSerializer(deSerializer):
    def get_instance(self, constructor_data):
        from kromatography.ui.tasks.kromatography_task import KromatographyTask
        instance = KromatographyTask(**constructor_data['kwargs'])
        return instance


class kromatographyProjectDeSerializer(deSerializer):
    def get_instance(self, constructor_data):
        from kromatography.model.kromatography_project import \
            KromatographyProject
        instance = KromatographyProject(**constructor_data['kwargs'])
        self.post_creation_instance_updates(instance)
        return instance

    def post_creation_instance_updates(self, instance):
        # Ensure that the study inherits the datasource from its project
        instance.study.datasource = instance.datasource


class bindingModelDeSerializer(chromatographyDataDeSerializer):
    def get_instance(self, constructor_data):
        import kromatography.model.binding_model
        instance = getattr(kromatography.model.binding_model,
                           constructor_data['metadata']['type'])(
                           **constructor_data['kwargs'])
        return instance


class stericMassActionDeSerializer(bindingModelDeSerializer):
    pass


class phDependentStericMassActionDeSerializer(bindingModelDeSerializer):
    pass


class langmuirDeSerializer(bindingModelDeSerializer):
    pass


class externalLangmuirDeSerializer(bindingModelDeSerializer):
    pass


class bufferDeSerializer(chromatographyDataDeSerializer):
    def get_instance(self, constructor_data):
        import kromatography.model.buffer
        instance = getattr(kromatography.model.buffer,
                           constructor_data['metadata']['type'])(
                           **constructor_data['kwargs'])
        return instance


class chemicalDeSerializer(chromatographyDataDeSerializer):
    def get_instance(self, constructor_data):
        import kromatography.model.chemical
        instance = getattr(kromatography.model.chemical,
                           constructor_data['metadata']['type'])(
                           **constructor_data['kwargs'])
        return instance


class collectionCriteriaDeSerializer(chromatographyDataDeSerializer):
    def get_instance(self, constructor_data):
        import kromatography.model.collection_criteria
        instance = getattr(kromatography.model.collection_criteria,
                           constructor_data['metadata']['type'])(
                           **constructor_data['kwargs'])
        return instance


class columnDeSerializer(chromatographyDataDeSerializer):
    protocol_version = 2

    def get_instance(self, constructor_data):
        import kromatography.model.column
        instance = getattr(kromatography.model.column,
                           constructor_data['metadata']['type'])(
                           **constructor_data['kwargs'])
        return instance


class columnTypeDeSerializer(columnDeSerializer):
    protocol_version = 0


class componentDeSerializer(chromatographyDataDeSerializer):
    def get_instance(self, constructor_data):
        import kromatography.model.component
        instance = getattr(kromatography.model.component,
                           constructor_data['metadata']['type'])(
                           **constructor_data['kwargs'])
        return instance


class dataSourceDeSerializer(chromatographyDataDeSerializer):
    def get_instance(self, constructor_data):
        import kromatography.model.data_source
        instance = getattr(kromatography.model.data_source,
                           constructor_data['metadata']['type'])(
                           **constructor_data['kwargs'])
        return instance


class inMemoryDataSourceDeSerializer(dataSourceDeSerializer):
    protocol_version = 1


class simpleDataSourceDeSerializer(inMemoryDataSourceDeSerializer):
    pass


class inStudyDataSourceDeSerializer(inMemoryDataSourceDeSerializer):
    pass


class discretizationDeSerializer(chromatographyDataDeSerializer):
    def get_instance(self, constructor_data):
        import kromatography.model.discretization
        # FIXME This check should be incorporated for all applicable classes
        if 'kwargs' in constructor_data:
            instance = getattr(kromatography.model.discretization,
                               constructor_data['metadata']['type'])(
                               **constructor_data['kwargs'])
        else:
            instance = getattr(kromatography.model.discretization,
                               constructor_data['metadata']['type'])(
                               )
        return instance


class experimentDeSerializer(chromatographyDataDeSerializer):
    def get_instance(self, constructor_data):
        import kromatography.model.experiment
        instance = getattr(kromatography.model.experiment,
                           constructor_data['metadata']['type'])(
                           **constructor_data['kwargs'])
        return instance


class methodDeSerializer(chromatographyDataDeSerializer):
    def get_instance(self, constructor_data):
        import kromatography.model.method
        instance = getattr(kromatography.model.method,
                           constructor_data['metadata']['type'])(
                           **constructor_data['kwargs'])
        return instance


class methodStepDeSerializer(methodDeSerializer):
    protocol_version = 1

    def get_instance(self, constructor_data):
        import kromatography.model.method_step
        instance = getattr(kromatography.model.method_step,
                           constructor_data['metadata']['type'])(
                           **constructor_data['kwargs'])
        return instance


class performanceDataDeSerializer(chromatographyDataDeSerializer):
    def get_instance(self, constructor_data):
        import kromatography.model.chromatography_results
        instance = getattr(kromatography.model.chromatography_results,
                           constructor_data['metadata']['type'])(
                           **constructor_data['kwargs'])
        return instance


class productDeSerializer(chromatographyDataDeSerializer):
    def get_instance(self, constructor_data):
        import kromatography.model.product
        instance = getattr(kromatography.model.product,
                           constructor_data['metadata']['type'])(
                           **constructor_data['kwargs'])
        return instance


class productComponentDeSerializer(chromatographyDataDeSerializer):
    def get_instance(self, constructor_data):
        import kromatography.model.product_component
        instance = getattr(kromatography.model.product_component,
                           constructor_data['metadata']['type'])(
                           **constructor_data['kwargs'])
        return instance


class resinDeSerializer(chromatographyDataDeSerializer):
    def get_instance(self, constructor_data):
        import kromatography.model.resin
        instance = getattr(kromatography.model.resin,
                           constructor_data['metadata']['type'])(
                           **constructor_data['kwargs'])
        return instance


class resultsDeSerializer(chromatographyDataDeSerializer):
    def get_instance(self, constructor_data):
        import kromatography.model.chromatography_results
        instance = getattr(kromatography.model.chromatography_results,
                           constructor_data['metadata']['type'])(
                           **constructor_data['kwargs'])
        return instance


class experimentResultsDeSerializer(resultsDeSerializer):
    protocol_version = 2


class simulationResultsDeSerializer(resultsDeSerializer):
    pass


class schurSolverDeSerializer(chromatographyDataDeSerializer):
    instance_collection = {}

    def get_instance(self, constructor_data):
        import kromatography.model.schur_solver
        instance = getattr(kromatography.model.schur_solver,
                           constructor_data['metadata']['type'])(
                           **constructor_data['kwargs'])
        return instance


class sensitivityDeSerializer(chromatographyDataDeSerializer):
    def get_instance(self, constructor_data):
        import kromatography.model.sensitivity
        if 'kwargs' in constructor_data:
            instance = getattr(kromatography.model.sensitivity,
                               constructor_data['metadata']['type'])(
                               **constructor_data['kwargs'])
        else:
            instance = getattr(kromatography.model.sensitivity,
                               constructor_data['metadata']['type'])(
                               )

        return instance


class simulationDeSerializer(chromatographyDataDeSerializer):
    protocol_version = 2

    def get_instance(self, constructor_data):
        # Load the simulation type from the api module to support in-memory and
        # lazy loading:
        import kromatography.model.api
        klass = getattr(kromatography.model.api,
                        constructor_data['metadata']['type'])
        instance = klass(**constructor_data['kwargs'])
        return instance


class lazyLoadingSimulationDeSerializer(simulationDeSerializer):
    protocol_version = 1


class simulationGroupDeSerializer(chromatographyDataDeSerializer):
    protocol_version = 1

    def get_instance(self, constructor_data):
        from kromatography.model.simulation_group import SimulationGroup

        instance = SimulationGroup(**constructor_data['kwargs'])
        return instance


class solutionDeSerializer(chromatographyDataDeSerializer):
    def get_instance(self, constructor_data):
        import kromatography.model.solution
        instance = getattr(kromatography.model.solution,
                           constructor_data['metadata']['type'])(
                           **constructor_data['kwargs'])
        return instance


class solutionWithProductDeSerializer(chromatographyDataDeSerializer):
    def get_instance(self, constructor_data):
        import kromatography.model.solution_with_product
        instance = getattr(kromatography.model.solution_with_product,
                           constructor_data['metadata']['type'])(
                           **constructor_data['kwargs'])
        return instance


class solverDeSerializer(chromatographyDataDeSerializer):
    protocol_version = 1

    def get_instance(self, constructor_data):
        import kromatography.model.solver
        instance = getattr(kromatography.model.solver,
                           constructor_data['metadata']['type'])(
                           **constructor_data['kwargs'])
        return instance


class studyDeSerializer(chromatographyDataDeSerializer):
    protocol_version = 2

    def get_instance(self, constructor_data):
        import kromatography.model.study
        instance = getattr(kromatography.model.study,
                           constructor_data['metadata']['type'])(
                           **constructor_data['kwargs'])
        return instance


class studyAnalysisToolsDeSerializer(deSerializer):
    def get_instance(self, constructor_data):
        from kromatography.model.study_analysis_tools import StudyAnalysisTools
        instance = StudyAnalysisTools(**constructor_data['kwargs'])
        return instance


class bruteForceOptimizerDeSerializer(deSerializer):
    protocol_version = 2

    def get_instance(self, constructor_data):
        from kromatography.compute.brute_force_optimizer import \
            BruteForceOptimizer

        instance = BruteForceOptimizer(
            **constructor_data['kwargs']
        )
        self.post_creation_instance_updates(instance)
        return instance

    def post_creation_instance_updates(self, instance):
        """ Once the optimizer is made, update its cost function and steps.
        """
        # Update steps
        attr_list = ['target_experiments']
        for step in instance.steps:
            for attr in attr_list:
                setattr(step, attr, getattr(instance, attr))

        # Update the starting point sim only for the first step since the other
        # ones will be set by the run of the first step.
        first_step = instance.steps[0]
        first_step.starting_point_simulations = \
            instance.starting_point_simulations


class bruteForce2StepBindingModelOptimizerDeSerializer(bruteForceOptimizerDeSerializer):  # noqa
    protocol_version = 3

    def get_instance(self, constructor_data):
        from kromatography.compute.brute_force_binding_model_optimizer import \
            BruteForce2StepBindingModelOptimizer

        instance = BruteForce2StepBindingModelOptimizer(
            **constructor_data['kwargs']
        )
        self.post_creation_instance_updates(instance)
        return instance


class costFunction0DeSerializer(deSerializer):
    def get_instance(self, constructor_data):
        from kromatography.compute.cost_functions import CostFunction0
        instance = CostFunction0(**constructor_data['kwargs'])
        return instance


class bruteForceOptimizerStepDeSerializer(deSerializer):
    protocol_version = 2

    def get_instance(self, constructor_data):
        from kromatography.compute.brute_force_optimizer_step import \
            BruteForceOptimizerStep

        instance = BruteForceOptimizerStep(**constructor_data['kwargs'])
        return instance


class bindingModelOptimizerStepDeSerializer(deSerializer):
    protocol_version = 1

    klass = Any

    def prepare_constructor_data(self, constructor_data):
        # Experiments will be passed by the containing optimizer...
        constructor_data["target_experiments"] = []

    def get_instance(self, constructor_data):
        self.prepare_constructor_data(constructor_data['kwargs'])
        instance = self.klass(**constructor_data['kwargs'])
        return instance


class bruteForceBindingModelOptimizerStepDeSerializer(bindingModelOptimizerStepDeSerializer):  # noqa
    protocol_version = 2

    def _klass_default(self):
        from kromatography.compute.brute_force_binding_model_optimizer_step \
            import BruteForceBindingModelOptimizerStep
        return BruteForceBindingModelOptimizerStep


class constantBruteForceBindingModelOptimizerStepDeSerializer(bindingModelOptimizerStepDeSerializer):  # noqa
    protocol_version = 1

    def _klass_default(self):
        from kromatography.compute.constant_binding_model_optimizer_step \
            import ConstantBruteForceBindingModelOptimizerStep
        return ConstantBruteForceBindingModelOptimizerStep


class parameterScanDescriptionDeSerializer(deSerializer):
    def get_instance(self, constructor_data):
        from kromatography.model.parameter_scan_description import \
            ParameterScanDescription
        instance = ParameterScanDescription(**constructor_data['kwargs'])
        return instance


class systemDeSerializer(chromatographyDataDeSerializer):
    def get_instance(self, constructor_data):
        import kromatography.model.system
        instance = getattr(kromatography.model.system,
                           constructor_data['metadata']['type'])(
                           **constructor_data['kwargs'])
        return instance


class systemTypeDeSerializer(chromatographyDataDeSerializer):
    def get_instance(self, constructor_data):
        import kromatography.model.system
        instance = getattr(kromatography.model.system,
                           constructor_data['metadata']['type'])(
                           **constructor_data['kwargs'])
        return instance


class timeIntegratorDeSerializer(chromatographyDataDeSerializer):
    def get_instance(self, constructor_data):
        import kromatography.model.time_integrator
        instance = getattr(kromatography.model.time_integrator,
                           constructor_data['metadata']['type'])(
                           **constructor_data['kwargs'])
        return instance


class transportModelDeSerializer(chromatographyDataDeSerializer):
    protocol_version = 1

    def get_instance(self, constructor_data):
        import kromatography.model.transport_model
        instance = getattr(kromatography.model.transport_model,
                           constructor_data['metadata']['type'])(
                           **constructor_data['kwargs'])
        return instance


class generalRateModelDeSerializer(transportModelDeSerializer):
    pass


class singleParamSimulationDiffDeSerializer(deSerializer):
    def build_object(self, serial_data):
        from kromatography.model.simulation_group import \
            SingleParamSimulationDiff
        data = serial_data['data']
        val = serial_data['data']['val']
        deserializer = self.select_deserializer(val)
        data["val"] = deserializer.build_object(val)
        return SingleParamSimulationDiff(**data)


class wenoDeSerializer(chromatographyDataDeSerializer):
    def get_instance(self, constructor_data):
        import kromatography.model.weno
        instance = getattr(kromatography.model.weno,
                           constructor_data['metadata']['type'])(
                           **constructor_data['kwargs'])
        return instance


class xYDataDeSerializer(chromatographyDataDeSerializer):
    def get_instance(self, constructor_data):
        import kromatography.model.x_y_data
        instance = getattr(kromatography.model.x_y_data,
                           constructor_data['metadata']['type'])(
                           **constructor_data['kwargs'])
        return instance
