""" Factory to translate optimizer builders into optimizer instances.
"""
import logging

from kromatography.compute.brute_force_binding_model_optimizer import \
    BRUTE_FORCE_2STEP_OPTIMIZER_TYPE, BruteForce2StepBindingModelOptimizer
from kromatography.compute.brute_force_optimizer import BruteForceOptimizer, \
    GRID_BASED_OPTIMIZER_TYPE

OPTIMIZERS = {
    BRUTE_FORCE_2STEP_OPTIMIZER_TYPE: BruteForce2StepBindingModelOptimizer,
    GRID_BASED_OPTIMIZER_TYPE: BruteForceOptimizer,
}

logger = logging.getLogger(__name__)


def optimizer_builder_to_optimizer(builder, **kw):
    """ Factory to build an optimizer from a BruteForceOptimizerBuilder.

    Parameters
    ----------
    builder : OptimizerBuilder
        Builder containing all necessary information to build the optimizer.

    kw : dict
        Additional BruteForceOptimizer attributes to override defaults. Any
        parameter in the following list will be overridden by the
        optimizer_builder value: name, target_experiments, cost_function_type,
        and starting_point_simulations.
    """
    if not builder.experiment_selected:
        msg = "Unable to build an ExperimentOptimizer because no experiment" \
              " was selected."
        logger.exception(msg)
        raise ValueError(msg)

    search = builder.target_study.search_experiment_by_name
    exps = [search(exp_name) for exp_name in builder.experiment_selected]
    step0_scanned_params = builder.parameter_scans

    kw["name"] = builder.optimizer_name
    kw["target_experiments"] = exps
    kw["cost_function_type"] = builder.cost_function_name
    kw["target_components"] = builder.component_selected
    kw['starting_point_simulations'] = builder.starting_point_simulations

    if builder.optimizer_type == BRUTE_FORCE_2STEP_OPTIMIZER_TYPE:
        for param in ['refining_step_spacing', 'refining_factor',
                      'refining_step_num_values', 'do_refine']:
            kw[param] = getattr(builder, param)

    return build_optimizer(step0_scanned_params,
                           optimizer_type=builder.optimizer_type, **kw)


def build_optimizer(step0_scan_params,
                    optimizer_type=GRID_BASED_OPTIMIZER_TYPE, **kw):
    """ Build a brute force optimizer from all necessary parameters.

    Parameters
    ----------
    optimizer_type : str
        Name of the optimizer type. Should be one of the types listed in the
        OPTIMIZERS dict.

    step0_scan_params : list(SMAParameterScanDescription)
        List of parameter scans, describing the parameters to be explored.

    kw : dict
        Additional parameters to override the defaults in the optimizer class.
        Typical elements in this dict are the name, target_experiments (list of
        Experiments), cost_function_type and starting_point_simulations.
    """
    optimizer_klass = OPTIMIZERS[optimizer_type]

    if optimizer_type == BRUTE_FORCE_2STEP_OPTIMIZER_TYPE:
        kw["constant_step_parameter_list"] = [param.to_param_scan_desc()
                                              for param in step0_scan_params]
    elif optimizer_type == GRID_BASED_OPTIMIZER_TYPE:
        kw["parameter_list"] = step0_scan_params
    else:
        msg = "Unknown optimizer type: {}".format(optimizer_type)
        logger.exception(msg)
        raise ValueError(msg)

    optimizer = optimizer_klass(**kw)
    return optimizer
