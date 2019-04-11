""" Driver class to build the optimal binding model given a (set of) target
experiment(s) and a transport model.
"""
from traits.api import Constant, Dict, Property

from kromatography.compute.brute_force_optimizer_step import \
    BruteForceOptimizerStep

BRUTE_FORCE_OPTIMIZER_STEP_TYPE = "Brute-Force binding model optimizer step"


class BruteForceBindingModelOptimizerStep(BruteForceOptimizerStep):
    """ Driver to build the optimal SMA binding model given an experiment and a
    transport model using the brute force approach.
    """
    #: Dict mapping each component to best binding models to minimize cost
    optimal_model_for_comp = Property(
        Dict, depends_on="optimal_simulation_for_comp[]"
    )

    #: Type of the optimizer step
    optimizer_step_type = Constant(BRUTE_FORCE_OPTIMIZER_STEP_TYPE)

    # Traits property getters/setters -----------------------------------------

    def _get_optimal_model_for_comp(self):
        """ Collect the binding model from the optimal simulation for each
        product component.
        """
        best_models = {}
        for comp, sim_list in self.optimal_simulation_for_comp.items():
            # Grabbing the first binding model because all sims have the same
            # binding model, just differing by their target experiments
            best_models[comp] = sim_list[0].binding_model
        return best_models
