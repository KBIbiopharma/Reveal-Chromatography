from traits.api import HasStrictTraits

from app_common.traits.custom_trait_factories import PositiveFloat, PositiveInt


class TimeIntegrator(HasStrictTraits):
    """ Represents the properties associated with the time integrator.
    """
    # -------------------------------------------------------------------------
    # Time Integrator traits
    # -------------------------------------------------------------------------

    #: Absolute tolerance in the solution of the original system
    abstol = PositiveFloat(1.0e-8, exclude_low=True)

    #: Factor which is multiplied by the section length to get initial
    #: integrator stepsize (0.0:IDAS default value), see IDAS guide 4.5, 36f.
    init_step_size = PositiveFloat(1.0e-6)

    #: Maximum number of timesteps taken by IDAS (0: IDAS default = 500),
    #: see IDAS guide 4.5, 36
    max_steps = PositiveInt(10000)

    #: Relative tolerance in the solution of the original system
    reltol = PositiveFloat(0.0)
