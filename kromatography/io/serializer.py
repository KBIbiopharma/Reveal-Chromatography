""" Module with the serialization api function and supporting classes. The goal
is to store a REVEAL project. The implementation relies on a recursive class
which selects the serializer needed based on the type of the object and splits
the object content into a dictionary of data and a dictionary of numpy arrays.
The first data can be dumped into a json file. The dictionary of data can be
dumped into an HDF5 file.

These serializers are versioned: as soon as the content of either dictionary
gets modified for an object type, the serializer's protocol gets bumped up 1
unit and that defines the new standard. The software will (try to) guaranty
that any file can be loaded, but a project can only be written into the latest
protocol.

FIXME: Move all specific implementations of the Serializer class to other
modules.
"""
import logging

from app_common.apptools.io.serializer import Serializer

logger = logging.getLogger(__name__)


def serialize(obj, array_collection=None):
    """ Serialization functional entry point.

    Parameters
    ----------
    obj : any
        Object to serialize

    array_collection : dict
        Dictionary mapping all numpy arrays stored to an id in the serial data.
    """
    from app_common.apptools.io.serializer import serialize
    from kromatography.ui.branding import APP_FAMILY, APP_TITLE, APP_UUID
    from kromatography import __build__, __version__
    software_version = [__version__, __build__]

    return serialize(obj, array_collection=array_collection,
                     software_name="{} {}".format(APP_FAMILY, APP_TITLE),
                     software_uuid=APP_UUID,
                     software_version=software_version,
                     additional_serializers=globals())


class ChromatographyData_Serializer(Serializer):
    def get_serial_data(self, obj):
        # Skip data part: most every class gets created without positional args
        serial_data = self.get_serial_data_base(obj)
        serial_data.update(self.get_instance_data(obj))
        return serial_data


class KromatographyTask_Serializer(Serializer):
    def get_serial_data(self, obj):
        serial_data = self.get_serial_data_base(obj)
        serial_data.update(self.get_instance_data(obj))
        return serial_data

    def attr_names_to_serialize(self, obj):
        return ['name', 'project', 'project_filepath']


class KromatographyProject_Serializer(Serializer):
    def get_serial_data(self, obj):
        serial_data = self.get_serial_data_base(obj)
        serial_data.update(self.get_instance_data(obj))
        return serial_data

    def attr_names_to_serialize(self, obj):
        return ['name', 'study']


class BindingModel_Serializer(ChromatographyData_Serializer):
    pass


class StericMassAction_Serializer(BindingModel_Serializer):
    pass


class PhDependentStericMassAction_Serializer(BindingModel_Serializer):
    pass


class Langmuir_Serializer(BindingModel_Serializer):
    pass


class ExternalLangmuir_Serializer(BindingModel_Serializer):
    pass


class Buffer_Serializer(ChromatographyData_Serializer):
    pass


class Chemical_Serializer(ChromatographyData_Serializer):
    pass


class CollectionCriteria_Serializer(ChromatographyData_Serializer):
    pass


class Column_Serializer(ChromatographyData_Serializer):
    protocol_version = 2


class ColumnType_Serializer(ChromatographyData_Serializer):
    pass


class Component_Serializer(ChromatographyData_Serializer):
    pass


class DataSource_Serializer(ChromatographyData_Serializer):
    pass


class InMemoryDatasource_Serializer(DataSource_Serializer):
    protocol_version = 1

    def attr_names_to_serialize(self, obj):
        return ['name', 'object_catalog']


class InStudyDataSource_Serializer(InMemoryDatasource_Serializer):
    pass


class SimpleDataSource_Serializer(InMemoryDatasource_Serializer):
    pass


class Discretization_Serializer(ChromatographyData_Serializer):
    pass


class Experiment_Serializer(ChromatographyData_Serializer):
    pass


class Method_Serializer(ChromatographyData_Serializer):
    pass


class MethodStep_Serializer(Method_Serializer):
    protocol_version = 1


class PerformanceData_Serializer(ChromatographyData_Serializer):
    pass


class Product_Serializer(ChromatographyData_Serializer):
    pass


class ProductComponent_Serializer(ChromatographyData_Serializer):
    pass


class Resin_Serializer(ChromatographyData_Serializer):
    pass


class Results_Serializer(ChromatographyData_Serializer):
    pass


class ExperimentResults_Serializer(Results_Serializer):
    protocol_version = 2


class SimulationResults_Serializer(Results_Serializer):
    pass


class SchurSolver_Serializer(ChromatographyData_Serializer):
    pass


class Sensitivity_Serializer(ChromatographyData_Serializer):
    pass


class Simulation_Serializer(ChromatographyData_Serializer):
    protocol_version = 2


class LazyLoadingSimulation_Serializer(Simulation_Serializer):
    """ Lazy sims don't store their outputs.
    """
    protocol_version = 1

    def attr_names_to_serialize(self, obj):
        super_klass = super(LazyLoadingSimulation_Serializer, self)
        std_attrs = super_klass.attr_names_to_serialize(obj)
        std_attrs.remove("output")
        return std_attrs


class SimulationGroup_Serializer(ChromatographyData_Serializer):
    protocol_version = 1

    def attr_names_to_serialize(self, obj):
        return ['name', 'center_point_simulation_name', 'group_data',
                'simulation_diffs', 'perf_params', 'run_status', 'type']


class Solution_Serializer(ChromatographyData_Serializer):
    pass


class SolutionWithProduct_Serializer(ChromatographyData_Serializer):
    pass


class Solver_Serializer(ChromatographyData_Serializer):
    protocol_version = 1


class Study_Serializer(ChromatographyData_Serializer):
    protocol_version = 2

    def attr_names_to_serialize(self, obj):
        return ['product', 'is_blank', 'name', 'study_purpose', 'study_type',
                'editable', 'experiments', 'simulations', 'study_datasource',
                'exp_study_filepath', 'analysis_tools']


class StudyAnalysisTools_Serializer(ChromatographyData_Serializer):
    def attr_names_to_serialize(self, obj):
        return ['simulation_grids', 'monte_carlo_explorations',
                'optimizations']


class BruteForceOptimizer_Serializer(Serializer):
    protocol_version = 2

    def attr_names_to_serialize(self, obj):
        return ['name', 'target_experiments', 'target_components', 'steps',
                'starting_point_simulations', 'optimal_simulations',
                'cost_function_type', 'has_run', 'status']


class BruteForce2StepBindingModelOptimizer_Serializer(BruteForceOptimizer_Serializer):  # noqa
    protocol_version = 3

    def attr_names_to_serialize(self, obj):
        parent = super(BruteForce2StepBindingModelOptimizer_Serializer, self)
        general_attrs = parent.attr_names_to_serialize(obj)
        specific_attrs = ['optimal_models', 'do_refine', 'refining_factor',
                          'refining_step_spacing', 'refining_step_num_values']
        return general_attrs + specific_attrs


class BruteForceOptimizerStep_Serializer(Serializer):
    protocol_version = 2

    def attr_names_to_serialize(self, obj):
        """ Attributes to store.

        Skipping properties that can be reconstructed, simulations and
        attributes that are common to all steps and that are stored on the
        optimizer (cost_function_type, transport_model, target_experiments).
        """
        return ['name', 'cost_data', 'cost_agg_func', 'target_components',
                'cost_function_type', 'has_run', 'parameter_list', 'status']


class ParameterScanDescription_Serializer(Serializer):
    def attr_names_to_serialize(self, obj):
        return ['name', 'low', 'high', 'spacing', 'num_values',
                "parallel_parameters"]


class ConstantBruteForceBindingModelOptimizerStep_Serializer(BruteForceOptimizerStep_Serializer):  # noqa
    protocol_version = 1


class BruteForceBindingModelOptimizerStep_Serializer(BruteForceOptimizerStep_Serializer):  # noqa
    protocol_version = 2


class CostFunction0_Serializer(Serializer):
    def attr_names_to_serialize(self, obj):
        return ['weights', 'cost_data', 'target_components',
                'peak_height_max_cost', 'peak_slope_high_trigger_fraction',
                'peak_slope_low_trigger_fraction', 'peak_slope_max_cost']


class System_Serializer(ChromatographyData_Serializer):
    pass


class SystemType_Serializer(ChromatographyData_Serializer):
    pass


class TimeIntegrator_Serializer(ChromatographyData_Serializer):
    pass


class TransportModel_Serializer(Serializer):
    protocol_version = 1

    def get_serial_data(self, obj):
        serial_data = self.get_serial_data_base(obj)
        serial_data.update(self.get_instance_data(obj))
        return serial_data


class GeneralRateModel_Serializer(TransportModel_Serializer):
    pass


class SingleParamSimulationDiff_Serializer(Serializer):
    def get_serial_data(self, obj):
        serial_data = self.get_serial_data_base(obj)
        serial_data.update({'data': self.get_data(obj)})
        return serial_data

    def get_data(self, obj):
        # Storing values in json as a list since its a native json type.
        data = {'extended_attr': obj.extended_attr,
                'val': self.serialize(obj.val)}
        return data


class Weno_Serializer(ChromatographyData_Serializer):
    pass


class XYData_Serializer(ChromatographyData_Serializer):
    pass
