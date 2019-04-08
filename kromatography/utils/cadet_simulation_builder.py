""" Utility module to build CADET models from Simulation data.
"""
import logging
import numpy as np

from scimath.units import SI

from kromatography.model.cadet_input import CADETInput
from kromatography.model.cadet_model import ALL_CADET_TYPES, CADETModel
from kromatography.utils.chromatography_units import convert_units
from kromatography.utils.units_utils import unitted_list_to_array
from kromatography.model.binding_model import PH_STERIC_BINDING_MODEL, \
    PH_LANGMUIR_BINDING_MODEL, STERIC_BINDING_MODEL
from kromatography.model.cadet_ph_external_profile import \
    CADETPhExternalProfile
from kromatography.model.method_step import GRADIENT_ELUT_STEP_TYPE, \
    LOAD_STEP_TYPE

logger = logging.getLogger(__name__)


def build_cadet_input(simulation):
    """ Builds a valid CADETModel and CADETInput from the given Simulation.

    Note: sections and steps mean the same thing in the CADET and the
    experimental language respectively.

    Parameters
    ----------
    simulation : Simulation
        Simulation for which to build the CADET input file.

    Returns
    -------
    CADETInput
        Valid CADET input object that can be serialized to HDF5 and run by
        CADET.
    """
    # FIXME: modularize this function!

    # Collect simulation components -------------------------------------------

    column = simulation.column
    method = simulation.method
    simulated_steps = method.method_steps
    binding_model = simulation.binding_model
    transport_model = simulation.transport_model
    binding_type = binding_model.model_type
    lig_density = column.resin.ligand_density
    col_porosity = transport_model.column_porosity
    bead_porosity = transport_model.bead_porosity

    # Input validation
    if column.resin.resin_type != 'CEX':
        msg = 'The simulation is only supported for resins of type `CEX`'
        logger.exception(msg)
        raise NotImplementedError(msg)

    num_sections = len(simulated_steps)
    section_times = simulation.section_times

    # Build CadetInput instance -----------------------------------------------

    velocities = [step.flow_rate for step in simulated_steps]
    velocities = convert_units(
        unitted_list_to_array(velocities), SI.meter/SI.second
    )

    num_components = len(simulation.product.product_component_names)
    sma_binding_type = binding_type in [STERIC_BINDING_MODEL,
                                        PH_STERIC_BINDING_MODEL]

    if sma_binding_type:
        # +1 for the cation component (salt) if using the SMA binding model:
        num_components += 1

    # configure CADETModel
    model = CADETModel(num_components, num_sections)

    # interstitial velocity for each step
    model.velocity[:] = velocities / transport_model.column_porosity

    # Initialize boundary conditions ------------------------------------------

    inlet = model.inlet
    inlet.section_times[:] = section_times

    # Initial condition for component concentration (bulk mobile and bead
    # mobile phases):
    # FIXME: this assumes that first step isn't
    if sma_binding_type:
        model.init_c[0] = method.initial_buffer.cation_concentration[()]
        model.init_cp[0] = model.init_c[0]
        # This in theory should be equal to sma_lambda: if it is not, CADET
        # will enforce it.
        model.init_q[0] = float(
            lig_density / (1 - col_porosity) / (1 - bead_porosity)
        )
    # Component concentration evolution parameters ----------------------------

    for ii, section in enumerate(inlet.section):
        step = simulated_steps[ii]
        # Computing concentrations for the step. By default,
        # concentration = const_coeff + lin_coeff t + quad_coeff t**2

        if step.step_type == LOAD_STEP_TYPE:
            # This is a constant
            const_coeff = section.const_coeff
            sol = step.solutions[0]
            scalars = [comp.molecular_weight
                       for comp in sol.product.product_components]
            molecular_weights = unitted_list_to_array(scalars)
            prod_comp_conc = (sol.product_component_concentrations /
                              molecular_weights)
            if sma_binding_type:
                const_coeff[0] = sol.cation_concentration
                prod_comp_idx = slice(1, None)
            else:
                prod_comp_idx = slice(None, None)

            const_coeff[prod_comp_idx] = prod_comp_conc[:]

        elif step.step_type == GRADIENT_ELUT_STEP_TYPE and sma_binding_type:
            # This step has two solutions and implements sol -> sol2, so
            # cation concentration will see a gradient:
            sol_1, sol_2 = step.solutions
            const_coeff = section.const_coeff
            const_coeff[0] = sol_1.cation_concentration

            lin_coeff = section.lin_coeff
            conc_change = (sol_2.cation_concentration -
                           sol_1.cation_concentration)
            section_duration = np.diff(section_times[ii:][:2])
            lin_coeff[0] = conc_change / section_duration
        elif sma_binding_type:
            # There are no products at the inlet, so just buffer concentrations
            const_coeff = section.const_coeff
            const_coeff[0] = step.solutions[0].cation_concentration

    # Configure column/resin properties and set to SI units to make CADET-ready
    model.col_length = float(convert_units(column.bed_height_actual, SI.meter))
    bead_radius = column.resin.average_bead_diameter / 2.
    model.par_radius = float(convert_units(bead_radius, SI.meter))

    # No unit conversion is needed here as the transport model is assumed to be
    # in the right units
    model.col_porosity = transport_model.column_porosity
    model.col_dispersion = transport_model.axial_dispersion
    model.par_porosity = transport_model.bead_porosity
    # Vector quantities: remove the cation component for langmuir models:
    if sma_binding_type:
        transport_idx = slice(None, None)
    else:
        transport_idx = slice(1, None)

    model.film_diffusion = transport_model.film_mass_transfer[transport_idx]
    model.par_diffusion = transport_model.pore_diffusion[transport_idx]
    model.par_surfdiffusion = transport_model.surface_diffusion[transport_idx]

    # Attached binding model to CADETModel
    model.adsorption_type = ALL_CADET_TYPES[binding_type]
    model.adsorption = binding_model

    profile_models = [PH_STERIC_BINDING_MODEL, PH_LANGMUIR_BINDING_MODEL]
    if binding_type in profile_models:
        model.external = CADETPhExternalProfile.from_simulation(simulation)

    # finally, create the CADETInput model and return.
    cadet_input = CADETInput(
        chromatography_type=transport_model.model_type,
        model=model,
        discretization=simulation.discretization,
        solver=simulation.solver,
    )

    return cadet_input
