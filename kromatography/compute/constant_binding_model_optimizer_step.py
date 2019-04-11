# -*- coding: utf-8 -*-
""" Example of a brute force BindingModelOptimizerStep that scans ka, nu and
optionally sigma, applying the same binding model parameters to all product
components.
"""
import logging

from traits.api import Bool, cached_property, Constant, Enum, Int, List, \
    Property, Tuple

from kromatography.compute.brute_force_binding_model_optimizer_step import \
    BruteForceBindingModelOptimizerStep
from kromatography.model.parameter_scan_description import \
    ParameterScanDescription
from kromatography.model.parameter_scan_description import \
    DEFAULT_KA_LOW_HIGH, DEFAULT_NU_LOW_HIGH, DEFAULT_SIGMA_LOW_HIGH

logger = logging.getLogger(__name__)

CONSTANT_OPTIMIZER_STEP_TYPE = "Constant optimizer step"


class ConstantBruteForceBindingModelOptimizerStep(BruteForceBindingModelOptimizerStep):  # noqa
    """ Optimizer step that scans in a brute force fashion the binding model
    parameter space, applying the same values to all product components.
    """

    optimizer_step_type = Constant(CONSTANT_OPTIMIZER_STEP_TYPE)

    # -------------------------------------------------------------------------
    # Common parameter description attributes : Ignored if parameter_list is
    # provided
    # -------------------------------------------------------------------------

    #: Scan type, applied to all parameters.
    scan_type = Enum(['Log', 'Linear'])

    #: Number of values to select along each scanning dimensions
    scan_num_values = Int(5)

    #: Range of scanning for SMA Ka
    ka_low_high = Tuple(DEFAULT_KA_LOW_HIGH)

    #: Range of scanning for SMA Nu
    nu_low_high = Tuple(DEFAULT_NU_LOW_HIGH)

    #: Range of scanning for SMA sigma
    sigma_low_high = Tuple(DEFAULT_SIGMA_LOW_HIGH)

    #: Scan the SMA Ka parameter?
    scan_ka = Bool(True)

    #: Scan the SMA Nu parameter?
    scan_nu = Bool(True)

    #: Scan the SMA sigma parameter?
    scan_sigma = Bool

    #: List of all comps in target product. Not to confuse with
    #: :attr:`target_components` which is the subset used for cost computation
    component_names = Property(List, depends_on="target_experiments")

    # Traits default methods --------------------------------------------------

    def _parameter_list_default(self):
        """ Build parameter list from general parameters.
        """
        all_components = self.component_names

        # If available components are not known, abort
        if not all_components:
            return []

        if self.target_components == self.component_names:
            component_indices = ["1:"]
        else:
            component_indices = [all_components.index(comp)
                                 for comp in self.target_components]

        param_list = []
        # Even binding model optimizers use the general
        # ParameterScanDescription so that resulting objects can be handled
        # like general BruteForceOptimizers.
        klass = ParameterScanDescription
        scan_attrs = {"num_values": self.scan_num_values,
                      "spacing": self.scan_type}
        if self.scan_ka:
            low, high = self.ka_low_high
            param_names = ["binding_model.sma_ka[{}]".format(comp_num)
                           for comp_num in component_indices]
            param_list += [klass(name=name, low=low, high=high, **scan_attrs)
                           for name in param_names]
        if self.scan_nu:
            low, high = self.nu_low_high
            param_names = ["binding_model.sma_nu[{}]".format(comp_num)
                           for comp_num in component_indices]
            param_list += [klass(name=name, low=low, high=high, **scan_attrs)
                           for name in param_names]
        if self.scan_sigma:
            low, high = self.sigma_low_high
            param_names = ["binding_model.sma_sigma[{}]".format(comp_num)
                           for comp_num in component_indices]
            param_list += [klass(name=name, low=low, high=high, **scan_attrs)
                           for name in param_names]

        return param_list

    @cached_property
    def _get_component_names(self):
        if self.target_experiments:
            return self.target_experiments[0].product.product_component_names
        else:
            return []
