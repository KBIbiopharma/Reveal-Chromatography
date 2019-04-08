""" Build Methods for simulations from existing (experimental?) methods.
"""
import logging

from kromatography.model.method import Method, UNSET
from kromatography.utils.string_definitions import INITIAL_CONDITION

logger = logging.getLogger(__name__)

POOLING_STEP = "Pooling step"


def build_sim_method_from_method(source_method, first_simulated_step,
                                 last_simulated_step, initial_buffer=None,
                                 **method_traits):
    """ Build a simulation method from a source/experiment method.

    Parameters
    ----------
    source_method : Instance(Method)
        Experiment or source method to build the simulation method from.

    first_simulated_step : str
        Name of the first MethodStep in method to simulate.

    last_simulated_step : str
        Name of the last MethodStep in method to simulate.

    initial_buffer : Buffer [OPTIONAL]
        Name of the buffer to set the method's initial condition. If not
        provided, this function will try to set it from the step before the
        first simulated step.

    Returns
    -------
    Method
        Generated method to build a simulation around.
    """
    expt_col_criteria = source_method.collection_criteria
    if expt_col_criteria is None:
        col_criteria = None
    else:
        col_criteria = expt_col_criteria.clone_traits(copy='deep')

    if "name" not in method_traits:
        method_traits["name"] = "Sim method from {}".format(source_method.name)

    method = Method(run_type=source_method.run_type,
                    collection_criteria=col_criteria, **method_traits)

    source_method_steps = source_method.method_steps
    _, start_step_num = source_method.get_step_of_name(first_simulated_step,
                                                       collect_step_num=True)
    _, stop_step_num = source_method.get_step_of_name(last_simulated_step,
                                                      collect_step_num=True)
    step_indices = {first_simulated_step: start_step_num,
                    last_simulated_step: stop_step_num}

    # Specify what step comes before the first one to set the first
    # simulated step's initial conditions
    if step_indices[first_simulated_step] == 0:
        step_indices[INITIAL_CONDITION] = None
    else:
        step_indices[INITIAL_CONDITION] = \
            step_indices[first_simulated_step] - 1

    # Pooling step, that is, step which creates the pool in the simulation
    # (used for performance parameter computation):
    if source_method.collection_step_number == UNSET:
        step_indices[POOLING_STEP] = UNSET
    else:
        pooling_step_num = source_method.collection_step_number - \
            start_step_num
        step_indices[POOLING_STEP] = pooling_step_num

    valid, check_msg = check_step_index_consistency(
        step_indices, first_simulated_step, last_simulated_step, initial_buffer
    )
    if not valid:
        msg = "Failed to build the simulation's method from method {}. Issue" \
              " is {}".format(method.name, check_msg)
        logger.error(msg)
        raise ValueError(msg)

    simulated_step_idx = range(step_indices[first_simulated_step],
                               step_indices[last_simulated_step] + 1)
    method.method_steps = build_sim_steps_from_exp_steps(
        source_method_steps, simulated_step_idx
    )

    set_method_initial_buffer(method, source_method, step_indices,
                              initial_buffer=initial_buffer)

    method.collection_step_number = step_indices[POOLING_STEP]
    return method


def set_method_initial_buffer(target_method, source_method, step_indices,
                              initial_buffer=None):
    """ Set initial conditions to provided initial_buffer or from source method

    Parameters
    ----------
    target_method : Instance(Method)
        Method being built from source_method.

    source_method : Instance(Method)
        Experiment or source method to build the simulation method from.

    step_indices : dict
        Mapping between step descriptions and step number in the source method.

    initial_buffer : Buffer [OPTIONAL]
        Name of the buffer to set the method's initial condition. Not needed if
        it should be set from the step before the first simulated step.
    """
    expt_steps = source_method.method_steps
    init_cond_step_idx = step_indices[INITIAL_CONDITION]
    if initial_buffer is not None:
        target_method.initial_buffer = initial_buffer
    elif init_cond_step_idx is not None:
        init_cond_step = expt_steps[init_cond_step_idx]
        initial_buffers = init_cond_step.solutions
        if len(initial_buffers) > 1:
            # FIXME: Should we do something smarter here?
            msg = "Initial condition set by a step that has more than 1 " \
                  "solution."
            logger.warning(msg)
        elif len(initial_buffers) == 0:
            msg = "No solution found on step {}: cannot set the initial " \
                  "buffer.".format(init_cond_step.name)
            logger.warning(msg)
            return

        target_method.initial_buffer = initial_buffers[0]
    else:
        msg = "Provided step indices doesn't specify initial condition and " \
              "explicit initial buffer not provided either. Unable to the " \
              "method's initial buffer."
        logger.exception(msg)
        raise ValueError(msg)


def build_sim_steps_from_exp_steps(expt_method_steps, simulated_step_idx):
    """ Build the list of method steps that a simulation must contain.

    Make a (deep) copy of the relevant experiment steps, keeping all uses of a
    solution pointing to the same object, though that object should be copies
    of the experiment's solutions.
    """
    # simulation's solution datasource: all steps using a buffer should be
    # looking at the same one so that changing it for example in a scanning job
    # affect all
    solutions = {}
    steps = [expt_method_steps[i].clone_traits(copy='deep')
             for i in simulated_step_idx]
    for step in steps:
        for i, sol in enumerate(step.solutions):
            if sol.name not in solutions:
                solutions[sol.name] = sol
            else:
                step.solutions[i] = solutions[sol.name]
    return steps


def check_step_index_consistency(step_indices, first_simulated_step,
                                 last_simulated_step, initial_buffer):
    """ Check that the step_indices found are consistent with expectations.

    Parameters
    ----------
    step_indices : dict
        Mapping between step descriptions and step number in the source method.

    first_simulated_step : str
        Name of the first step to simulate.

    last_simulated_step : str
        Name of the last step to simulate.

    initial_buffer : Buffer or None
        Name of the buffer to set the method's initial condition if any.

    Returns
    -------
    bool
        Whether the step_indices dict is consistent.

    str
        Message about what is inconsistent if anything.
    """
    initial_condition_idx = step_indices[INITIAL_CONDITION]
    first_step_idx = step_indices[first_simulated_step]
    last_step_idx = step_indices[last_simulated_step]
    pooling_step_idx = step_indices[POOLING_STEP]

    if initial_condition_idx is None:
        if initial_buffer is None:
            msg = ("No step found before the first simulated step and no "
                   "initial buffer specified.")
            logger.error(msg)
            return False, msg

    if last_step_idx < first_step_idx:
        msg = ("The last step isn't after the first step as expected. Their "
               "step indices are {} and {} resp.".format(last_step_idx,
                                                         first_step_idx))
        logger.error(msg)
        return False, msg

    if pooling_step_idx > last_step_idx:
        msg = ("The pooling step is found after the last simulated step. No "
               "performance parameters will be computed for this method.")
        logger.warning(msg)
    elif pooling_step_idx < 0 and pooling_step_idx != UNSET:
        msg = "The pooling step is negative: please check the calculation."
        logger.error(msg)
        return False, msg

    return True, ""
