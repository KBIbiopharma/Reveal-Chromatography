import numpy as np
import logging
from shutil import copy

from kromatography.model.chromatography_results import SimulationResults
from kromatography.model.x_y_data import XYData
from kromatography.utils.io_utils import read_from_h5
from kromatography.compute.performance_parameters import \
    calculate_performance_data

logger = logging.getLogger(__name__)


def update_simulation_results(simulation, output_fname=None):
    """ Load simulation results from `output_fname` and update `simulation`.

    Parameters
    ----------
    simulation : Simulation
        The simulation object to update.

    output_fname : str [OPTIONAL]
        The CADET output h5 file path to update the simulation from. If not
        provided, the filepath is retrieved from the simulation object.
    """
    from kromatography.model.lazy_simulation import LazyLoadingSimulation

    if output_fname is None:
        output_fname = simulation.cadet_filepath

    msg = "Updating simulation {} from CADET run file {}"
    msg = msg.format(simulation.name, output_fname)
    logger.debug(msg)

    if not isinstance(simulation, LazyLoadingSimulation):
        simulation.output = build_simulation_results(simulation, output_fname)
    else:
        if output_fname != simulation.cadet_filepath:
            copy(output_fname, simulation.cadet_filepath)

    simulation.fire_perf_param_data_event()


def build_simulation_results(simulation, output_fname):
    """ Load simulation results from `output_fname` and update `simulation`.

    Parameters
    ----------
    simulation : Instance(Simulation)
        The simulation object.

    output_fname : str (file path)
        The CADET output h5 file path.
    """
    product = simulation.product
    step_names = [step.name for step in simulation.method.method_steps]
    continuous_data = read_continuous_data_from_cadet_h5(output_fname, product,
                                                         step_names)

    performance_data = calculate_performance_data(simulation, continuous_data)

    sim_res = SimulationResults(
        name='{}_Results'.format(simulation.name),
        continuous_data=continuous_data,
        performance_data=performance_data
    )

    return sim_res


def read_continuous_data_from_cadet_h5(output_fname, product, step_names):
    """ Returns a dictionary of output data found in the provided.

    Parameters
    ----------
    output_fname : str
        Path to the HDF5 file produced by CADET.

    product : Product
        Product this file is modeling.

    step_names : list(str)
        List of the step/section names.
    """
    output_data = read_from_h5(output_fname, root='/output/solution')
    input_data = read_from_h5(output_fname, root='/input')
    bind_type = input_data["adsorption_type"]

    continuous_data = {}

    # The timestamps for the simulation correspond to the CADET output
    # timestamps
    solution_timestamps = output_data['solution_times']

    # FIXME: should x_data be copied for each data entry ?
    # FIXME: should we create UnitArrays ?
    x_data = solution_timestamps
    x_metadata = {
        'name': 'time',
        'units': 's',
        'source': 'simulation',
    }

    # Read in 1D component chromatograms --------------------------------------

    data_shape = input_data['number_user_solution_points']
    total_conc = np.zeros(data_shape)

    key_fmt = 'solution_column_outlet_comp_{:03d}'
    # These are CADET binding model types, not Reveal:
    if bind_type in ['STERIC_MASS_ACTION', 'EXTERNAL_STERIC_MASS_ACTION_PH']:
        # Read in cation concentration
        cation_conc = output_data[key_fmt.format(0)]
        y_metadata = {'name': 'cation_Sim', 'type': 'cation',
                      'source': 'simulation', 'units': 'mM'}

        continuous_data['cation_Sim'] = XYData(
            name='cation_Sim',
            x_data=x_data, x_metadata=x_metadata,
            y_data=cation_conc, y_metadata=y_metadata
        )
        offset = 1
    else:
        offset = 0

    # Read in product concentrations:
    for ii, comp in enumerate(product.product_components):
        comp_name = comp.name
        molecular_weight = comp.molecular_weight[()]
        ext_coeff = comp.extinction_coefficient[()]

        name = comp_name + '_Sim'
        y_metadata = {'name': name, 'type': 'chromatogram',
                      'source': 'simulation', 'units': 'AU/cm'}
        y_data = output_data[key_fmt.format(ii + offset)]
        y_data = y_data * molecular_weight * ext_coeff

        continuous_data[name] = XYData(
            name=name,
            x_data=x_data, x_metadata=x_metadata,
            y_data=y_data, y_metadata=y_metadata
        )

        # Aggregate all component to build the total UV
        total_conc += y_data

    # create total concentration var
    y_metadata = {'name': 'Total_Sim', 'type': 'chromatogram',
                  'source': 'simulation', 'units': 'AU/cm'}
    continuous_data['Total_Sim'] = XYData(
        name='Total_Sim',
        x_data=x_data, x_metadata=x_metadata,
        y_data=total_conc, y_metadata=y_metadata
    )

    # Read 3D column comp concentrations (across column and over time)---------

    # Read in component concentrations inside the column liquid phase
    key_fmt = 'solution_column'
    column = output_data[key_fmt]
    column = np.array(column)
    for i, comp in enumerate(product.product_components):
        # Collect component attributes:
        comp_name = comp.name
        molecular_weight = comp.molecular_weight[()]
        ext_coeff = comp.extinction_coefficient[()]

        name = comp_name + '_Column_Sim'
        y_metadata = {'name': name, 'type': 'column_liquid',
                      'source': 'simulation', 'units': 'AU/cm'}
        y_data = column[:, i+offset, :] * molecular_weight * ext_coeff
        continuous_data[name] = XYData(
            name=name,
            x_data=x_data, x_metadata=x_metadata,
            y_data=y_data, y_metadata=y_metadata
        )

    # Read in component concentrations inside the bead liquid phase
    key_fmt = 'solution_particle'
    data = np.array(output_data[key_fmt])
    for i, comp in enumerate(product.product_components):
        # Collect component attributes:
        comp_name = comp.name
        molecular_weight = comp.molecular_weight[()]
        ext_coeff = comp.extinction_coefficient[()]

        name = comp_name + '_Particle_Liq_Sim'
        y_metadata = {'name': name, 'type': 'particle_liquid',
                      'source': 'simulation', 'units': 'AU/cm'}

        y_data = data[:, :, :, 0, i+offset] * molecular_weight * ext_coeff
        continuous_data[name] = XYData(
            name=name,
            x_data=x_data, x_metadata=x_metadata,
            y_data=y_data, y_metadata=y_metadata
        )

    # Read in component concentrations inside the bead bound phase
    key_fmt = 'solution_particle'
    data = np.array(output_data[key_fmt])
    for i, comp in enumerate(product.product_components):
        # Collect component attributes:
        comp_name = comp.name
        molecular_weight = comp.molecular_weight[()]
        ext_coeff = comp.extinction_coefficient[()]

        name = comp_name + '_Particle_Bound_Sim'
        y_metadata = {'name': name, 'type': 'particle_bound',
                      'source': 'simulation', 'units': 'AU/cm'}
        y_data = data[:, :, :, 1, i+offset] * molecular_weight * ext_coeff
        continuous_data[name] = XYData(
            name=name,
            x_data=x_data, x_metadata=x_metadata,
            y_data=y_data, y_metadata=y_metadata
        )

    # Build tags for steps in simulation --------------------------------------

    inlet_data = read_from_h5(output_fname, root='/input/model/inlet')
    key_fmt = 'section_times'
    section_times = inlet_data[key_fmt]
    x_data = section_times[:-1]
    x_metadata = {
        'name': 'time',
        'units': 's',
        'source': 'simulation',
    }

    y_data = step_names
    name = 'Section_Tags_Sim'
    y_metadata = {'name': name, 'type': 'section_tags',
                  'source': 'simulation', 'units': ''}
    continuous_data[name] = XYData(
        name=name,
        x_data=x_data, x_metadata=x_metadata,
        y_data=y_data, y_metadata=y_metadata
    )

    return continuous_data
