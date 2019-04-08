""" Storage of the legacy deserializers to guaranty that any old project
created in the wild can be read in the future.
"""
import logging

from scimath.units.api import UnitScalar
from traits.api import Any

from app_common.apptools.io.deserializer import unitScalarDeSerializer

from kromatography.io.deserializer import \
    bruteForce2StepBindingModelOptimizerDeSerializer, \
    bruteForceOptimizerDeSerializer, chromatographyDataDeSerializer, \
    costFunction0DeSerializer, columnDeSerializer, deSerializer, \
    experimentResultsDeSerializer, methodDeSerializer, \
    simpleDataSourceDeSerializer, simulationDeSerializer, studyDeSerializer, \
    bruteForceOptimizerStepDeSerializer, solverDeSerializer, \
    constantBruteForceBindingModelOptimizerStepDeSerializer, \
    bruteForceBindingModelOptimizerStepDeSerializer

logger = logging.getLogger(__name__)

LEGACY_AKTA_COL_SEARCH_PATTERNS = {
    'uv': r'(UV.*\d{3}((nm$)|($)))',
    'conductivity': r'(COND$)',
    'concentration': r'(CONC$)',
    'pH': r'(pH$)',
    'flow': r'(FLOW$)',
    'fraction': r'(FRACTIONS?$)',
    'log_book': r'(Log(book)?$)',
    'temperature': r'(TEMP$)',
}

# Utilities -------------------------------------------------------------------


def rename_cost_data_df(kwargs):
    """ Rename the ALL_COST cost_data column to the new name for optimizer
    steps created before version 0.10.2
    """
    from kromatography.compute.experiment_optimizer_step import \
        ALL_COST_COL_NAME

    cost_data = kwargs["cost_data"]
    old_cost_col_name = "Cost (All components)"
    cols = cost_data.columns.tolist()
    idx = cols.index(old_cost_col_name)
    cols[idx] = ALL_COST_COL_NAME
    cost_data.columns = cols


# Deserializers for old objects -----------------------------------------------


class unitArrayDeSerializer0(unitScalarDeSerializer):
    protocol_version = 0


class ndarrayDeSerializer0(deSerializer):
    """ Deserializer for arrays when their id was stored with id_ and the
    result of the id operation instead of a unique uuid with no prefix.
    """
    protocol_version = 0

    def build_object(self, serial_data):
        from numpy import array
        filename = serial_data['class_metadata']['filename']
        arr_uuid = "id_" + str(serial_data['class_metadata']['id'])
        return array(self.array_collection[(filename, arr_uuid)])


class dataFrameDeSerializer0(deSerializer):
    protocol_version = 0

    def build_object(self, serial_data):
        filename = serial_data['class_metadata']['filename']
        obj_id = 'id_' + str(serial_data['class_metadata']['id'])
        return self.array_collection[(filename, obj_id)]


class simulationDeSerializer1(simulationDeSerializer):
    protocol_version = 1

    def get_instance(self, constructor_data):
        constructor_data['kwargs'].pop("solver_name", None)
        return super(simulationDeSerializer1, self).get_instance(
            constructor_data
        )


class lazyLoadingSimulationDeSerializer0(simulationDeSerializer1):
    protocol_version = 0


class simulationDeSerializer0(chromatographyDataDeSerializer):
    protocol_version = 0

    def get_instance(self, constructor_data):
        from kromatography.model.simulation import Simulation
        kwargs = constructor_data['kwargs']
        kwargs.pop("step_indices")
        instance = Simulation(**kwargs)
        # Back then, methods didn't store an initial buffer. Try to retrieve it
        if instance.method.initial_buffer is None:
            try:
                method = self.rebuild_method(instance)
            except Exception as e:
                msg = "Deserialized an old version of a Simulation and failed"\
                      " to rebuild the method: error was {}".format(e)
                logger.debug(msg)
                method = None

            if method:
                instance.method = method

        return instance

    def rebuild_method(self, sim):
        """ Return a fully formed method from source experiment.
        """
        from kromatography.model.factories.method import \
            build_sim_method_from_method
        # Rebuild the method from source_experiment if possible"
        if sim.source_experiment is not None:
            source_method = sim.source_experiment.method
            fstep = sim.method.method_steps[0].name
            lstep = sim.method.method_steps[-1].name
            sim_method = build_sim_method_from_method(source_method, fstep,
                                                      lstep)
            return sim_method


class methodStepDeSerializer0(methodDeSerializer):
    """ Method serializer before solutions defaulted to an empty list when not
    specified.
    """
    protocol_version = 0

    def get_instance(self, constructor_data):
        from kromatography.model.method_step import MethodStep

        traits = constructor_data['kwargs']
        if traits['solutions'] is None:
            traits['solutions'] = []

        instance = MethodStep(**traits)
        return instance


class simulationGroupDeSerializer0(chromatographyDataDeSerializer):
    """ Deserializer at or before release 0.5.3, when simulation groups didn't
    store the simulation diffs and stored its data with each simulation along a
    column.
    """
    protocol_version = 0

    def get_instance(self, constructor_data):
        from kromatography.model.simulation_group import SimulationGroup

        self.transpose_group_data(constructor_data['kwargs'])
        instance = SimulationGroup(**constructor_data['kwargs'])
        return instance

    def transpose_group_data(self, constructor_data):
        from kromatography.model.simulation_group import SIM_COL_NAME

        group_data = constructor_data["group_data"]
        group_data = group_data.transpose()
        group_data.index.name = SIM_COL_NAME
        constructor_data["group_data"] = group_data.reset_index()


class bindingModelCostFunction0DeSerializer0(costFunction0DeSerializer):
    """ Deserializer needed for projects saved before Oct 1st 2016, when the
    cost function was called `bindingModelCostFunction0`. Therefore, this class
    has nothing to do other than exist with the correct name.
    """
    protocol_version = 0


class constantBruteForceBindingModelOptimizerStepDeSerializer0(constantBruteForceBindingModelOptimizerStepDeSerializer):  # noqa
    protocol_version = 0

    def get_instance(self, constructor_data):
        # Remove the cost function, since now only its name is stored (and
        # currently, there is support for only 1 of them):
        kwargs = constructor_data['kwargs']
        kwargs.pop('cost_function', None)
        rename_cost_data_df(kwargs)
        return super(constantBruteForceBindingModelOptimizerStepDeSerializer0, self).get_instance(constructor_data)  # noqa


class constantBindingModelOptimizerStepDeSerializer0(deSerializer):
    """ This is for binding model optimizer steps where the transport and
    binding models are stored instead of the full starting point simulation.
    """
    protocol_version = 0

    klass = Any

    def prepare_constructor_data(self, constructor_data):
        # Experiments will be passed by the containing optimizer...
        constructor_data["target_experiments"] = []
        constructor_data.pop('center_binding_model')

    def get_instance(self, constructor_data):
        kwargs = constructor_data['kwargs']
        self.prepare_constructor_data(kwargs)
        rename_cost_data_df(kwargs)
        instance = self.klass(**kwargs)
        return instance

    def _klass_default(self):
        from kromatography.compute.constant_binding_model_optimizer_step import ConstantBruteForceBindingModelOptimizerStep  # noqa
        return ConstantBruteForceBindingModelOptimizerStep


class bruteForceBindingModelOptimizerStepDeSerializer0(constantBindingModelOptimizerStepDeSerializer0):  # noqa
    def _klass_default(self):
        from kromatography.compute.brute_force_binding_model_optimizer_step import BruteForceBindingModelOptimizerStep  # noqa
        return BruteForceBindingModelOptimizerStep


class bruteForceBindingModelOptimizerStepDeSerializer1(bruteForceBindingModelOptimizerStepDeSerializer):  # noqa
    protocol_version = 1

    def get_instance(self, constructor_data):
        # Remove the cost function, since now only its name is stored (and
        # currently, there is support for only 1 of them):
        kwargs = constructor_data['kwargs']
        kwargs.pop('cost_function', None)
        rename_cost_data_df(kwargs)
        return super(bruteForceBindingModelOptimizerStepDeSerializer1, self).get_instance(constructor_data)  # noqa


class bruteForceOptimizerDeSerializer0(bruteForceOptimizerDeSerializer):
    protocol_version = 0

    def get_instance(self, constructor_data):
        kwargs = constructor_data['kwargs']
        kwargs.pop('cost_function', None)
        starting_point_sim = kwargs.pop('starting_point_simulation', None)
        if starting_point_sim:
            kwargs['starting_point_simulations'] = [starting_point_sim]
        return super(bruteForceOptimizerDeSerializer0, self).get_instance(constructor_data)  # noqa


class bruteForceOptimizerDeSerializer1(bruteForceOptimizerDeSerializer):
    protocol_version = 1

    def get_instance(self, constructor_data):
        # Remove the cost function, since now only its name is stored (and
        # currently, there is support for only 1 of them):
        kwargs = constructor_data['kwargs']
        kwargs.pop('cost_function', None)
        return super(bruteForceOptimizerDeSerializer1, self).get_instance(constructor_data)  # noqa


class bruteForceOptimizerStepDeSerializer1(bruteForceOptimizerStepDeSerializer):  # noqa
    protocol_version = 1

    def get_instance(self, constructor_data):
        rename_cost_data_df(constructor_data['kwargs'])
        return super(bruteForceOptimizerStepDeSerializer1, self).get_instance(
            constructor_data)  # noqa


class bruteForceOptimizerStepDeSerializer0(bruteForceOptimizerStepDeSerializer1):  # noqa
    protocol_version = 0

    def get_instance(self, constructor_data):
        # Remove the cost function, since now only its name is stored (and
        # currently, there is support for only 1 of them):
        kwargs = constructor_data['kwargs']
        kwargs.pop('cost_function', None)
        return super(bruteForceOptimizerStepDeSerializer0, self).get_instance(constructor_data)  # noqa


class bruteForce2StepBindingModelOptimizerDeSerializer2(bruteForce2StepBindingModelOptimizerDeSerializer):  # noqa
    protocol_version = 2

    def get_instance(self, constructor_data):
        # Remove the cost function, since now only its name is stored (and
        # currently, there is support for only 1 of them):
        kwargs = constructor_data['kwargs']
        kwargs.pop('cost_function', None)
        return super(bruteForce2StepBindingModelOptimizerDeSerializer2, self).get_instance(constructor_data)  # noqa


class bruteForce2StepBindingModelOptimizerDeSerializer1(bruteForce2StepBindingModelOptimizerDeSerializer):  # noqa
    protocol_version = 1

    def get_instance(self, constructor_data):
        kwargs = constructor_data['kwargs']
        kwargs.pop('cost_function', None)
        starting_point_sim = kwargs.pop('starting_point_simulation', None)
        if starting_point_sim:
            kwargs['starting_point_simulations'] = [starting_point_sim]
        return super(bruteForce2StepBindingModelOptimizerDeSerializer1, self).get_instance(constructor_data)  # noqa


class bruteForce2StepBindingModelOptimizerDeSerializer0(bruteForce2StepBindingModelOptimizerDeSerializer1):  # noqa
    protocol_version = 0

    def get_instance(self, constructor_data):
        kwargs = constructor_data['kwargs']
        kwargs.pop('transport_model', None)
        kwargs.pop('center_binding_model', None)
        return super(bruteForce2StepBindingModelOptimizerDeSerializer0, self).get_instance(constructor_data)  # noqa


class experimentResultsDeSerializer0(experimentResultsDeSerializer):
    protocol_version = 0

    def get_instance(self, constructor_data):
        instance = super(experimentResultsDeSerializer0, self).get_instance(
            constructor_data
        )
        # Before version 0.6, settings couldn't be set by the user. They were
        # automatically applied.
        import_settings = {
            "time_of_origin": UnitScalar(0., units="minute"),
            "holdup_volume": UnitScalar(0., units="minute"),
            "col_name_patterns": LEGACY_AKTA_COL_SEARCH_PATTERNS}
        instance.import_settings = import_settings
        return instance


class experimentResultsDeSerializer1(experimentResultsDeSerializer):
    protocol_version = 1

    def get_instance(self, constructor_data):
        # Attribute was renamed: akta_settings -> import_settings
        settings = constructor_data['kwargs'].pop("akta_settings")
        # We used to store the value as a float: convert to UnitScalar
        too = settings["time_of_origin"]
        settings["time_of_origin"] = UnitScalar(too, units="minute")
        settings["holdup_volume"] = UnitScalar(0., units="minute")
        constructor_data['kwargs']["import_settings"] = settings
        return super(experimentResultsDeSerializer, self).get_instance(
            constructor_data)


class simpleDataSourceDeSerializer0(simpleDataSourceDeSerializer):
    """ This is only needed for deserializing the very first set of files v0,
    where the simpleDataSource was serialized with its data_catalog.
    """
    protocol_version = 0

    def get_instance(self, constructor_data):
        constructor_data['kwargs'].pop('data_catalog', None)
        instance = super(simpleDataSourceDeSerializer0, self).get_instance(
            constructor_data
        )
        return instance


class studyDeSerializer1(studyDeSerializer):
    protocol_version = 1

    def get_instance(self, constructor_data):
        constructor_data["kwargs"].pop("job_ids", None)
        instance = super(studyDeSerializer1, self).get_instance(
            constructor_data
        )
        return instance


class studyDeSerializer0(studyDeSerializer1):
    protocol_version = 0

    def get_instance(self, constructor_data):
        instance = super(studyDeSerializer0, self).get_instance(
            constructor_data
        )
        self.update_target_products_in_datasource(instance)
        return instance

    def update_target_products_in_datasource(self, instance):
        """ Until this version, the binding and transport models were not
        created with a binding and transport model. Since we will allow copying
        them into the user DS, their target_product attr need to be set.
        """
        from kromatography.compute.brute_force_binding_model_optimizer import \
            BruteForce2StepBindingModelOptimizer as BindModelOptim

        prod_name = instance.product.name
        binds = instance.study_datasource.binding_models
        transps = instance.study_datasource.transport_models
        optimizers = [optim for optim in instance.analysis_tools.optimizations
                      if isinstance(optim, BindModelOptim)]
        optim_models = []
        for optim in optimizers:
            optim_models += [model for model in optim.optimal_models]

        models = binds + transps + optim_models
        for model in models:
            model.target_product = prod_name


class columnDeSerializer1(columnDeSerializer):
    protocol_version = 1

    def get_instance(self, constructor_data):
        kwargs = constructor_data["kwargs"]
        hetp_asymmetry = kwargs.pop('hetp_assymetry')
        kwargs["hetp_asymmetry"] = hetp_asymmetry
        return super(columnDeSerializer1, self).get_instance(constructor_data)


class columnDeSerializer0(columnDeSerializer1):
    protocol_version = 0

    def get_instance(self, constructor_data):
        # column_lot_number attribute was renamed column_lot_id
        kwargs = constructor_data["kwargs"]
        lot_id = kwargs.pop('column_lot_number')
        kwargs["column_lot_id"] = lot_id
        return super(columnDeSerializer0, self).get_instance(constructor_data)


class transportModelDeSerializer0(chromatographyDataDeSerializer):
    protocol_version = 0

    def get_instance(self, constructor_data):
        import kromatography.model.transport_model
        instance = getattr(kromatography.model.transport_model,
                           constructor_data['metadata']['type'])(
                           constructor_data['args'],
                           **constructor_data['kwargs'])
        return instance


class inStudyDataSourceDeSerializer0(chromatographyDataDeSerializer):
    protocol_version = 0

    def get_instance(self, constructor_data):
        entries_to_keep = ["object_catalog", "name"]
        new_kwargs = {}
        for entry in constructor_data["kwargs"]:
            if entry in entries_to_keep:
                new_kwargs[entry] = constructor_data["kwargs"][entry]

        import kromatography.model.data_source
        instance = getattr(kromatography.model.data_source,
                           constructor_data['metadata']['type'])(**new_kwargs)
        return instance


class solverDeSerializer0(solverDeSerializer):
    protocol_version = 0

    def get_instance(self, constructor_data):
        instance = super(solverDeSerializer0, self).get_instance(
            constructor_data
        )
        # Change old sims so they print timing information so copies also print
        # timing info
        instance.print_timing = 1
        return instance


LEGACY_DESERIALIZER_MAP = {
    "unitArray": {0: unitArrayDeSerializer0},
    "dataFrame": {0: dataFrameDeSerializer0},
    "ndarray": {0: ndarrayDeSerializer0},
    "simulation": {0: simulationDeSerializer0, 1: simulationDeSerializer1},
    "methodStep": {0: methodStepDeSerializer0},
    "simulationGroup": {0: simulationGroupDeSerializer0},
    "bindingModelCostFunction0": {0: bindingModelCostFunction0DeSerializer0},
    "constantBindingModelOptimizerStep": {0: constantBindingModelOptimizerStepDeSerializer0},  # noqa
    "constantBruteForceBindingModelOptimizerStep": {0: constantBruteForceBindingModelOptimizerStepDeSerializer0},  # noqa
    "bruteForceBindingModelOptimizerStep": {0: bruteForceBindingModelOptimizerStepDeSerializer0,  # noqa
                                            1: bruteForceBindingModelOptimizerStepDeSerializer1},  # noqa
    "bruteForce2StepBindingModelOptimizer": {
        0: bruteForce2StepBindingModelOptimizerDeSerializer0,
        1: bruteForce2StepBindingModelOptimizerDeSerializer1,
        2: bruteForce2StepBindingModelOptimizerDeSerializer2
    },
    "bruteForceOptimizer": {0: bruteForceOptimizerDeSerializer0,
                            1: bruteForceOptimizerDeSerializer1},
    "experimentResults": {0: experimentResultsDeSerializer0,
                          1: experimentResultsDeSerializer1},
    "simpleDataSource": {0: simpleDataSourceDeSerializer0},
    "study": {0: studyDeSerializer0, 1: studyDeSerializer1},
    "column": {0: columnDeSerializer0,
               1: columnDeSerializer1},
    "lazyLoadingSimulation": {0: lazyLoadingSimulationDeSerializer0},
    "generalRateModel": {0: transportModelDeSerializer0},
    "inStudyDataSource": {0: inStudyDataSourceDeSerializer0},
    "bruteForceOptimizerStep": {0: bruteForceOptimizerStepDeSerializer0,
                                1: bruteForceOptimizerStepDeSerializer1},
    "solver": {0: solverDeSerializer0}
}
