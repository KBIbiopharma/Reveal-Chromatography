""" Factory functions for creating the model objects needed for the plots.
"""

import logging
from scimath.units.api import convert_str

from .utilities import get_base_properties_for_family, \
    get_plot_container_properties_for_family, get_renderer_properties, \
    interpolate_properties
from .data_models import ChromatogramModel, ChromeFamily, ChromeLog, \
    ChromeLogCollection
from kromatography.utils.string_definitions import FRACTION_TOTAL_DATA_KEY, \
    LOG_FAMILY_UV

logger = logging.getLogger(__name__)


def create_chrome_family(name):
    """ Create a new ChromeFamily for a (known) family name.
    """
    # get base properties for a family (this is typically stuff like units etc)
    family_props = get_base_properties_for_family(name)

    # get plot specific properties for family (might depend on `family_traits`)
    plot_container_props = get_plot_container_properties_for_family(name)
    family_props.update({
        'plot_container_properties': plot_container_props
    })

    # interpolate props specified as a fmt string (keys that end with `_fmt`)
    family_traits = interpolate_properties(family_props)
    # create the family
    return ChromeFamily(**family_traits)


def create_chrome_log(name, source_name, family_name, source_type, x_data,
                      y_data, data_mask=None):
    """ Build a chromatography log, specifying the name, family and data.

    Parameters
    ----------
    name : str
        Name of the log being created.

    source_name : str
        Name of the collection's source, that is the experiment name if
        experimental data is used, or the source experiment's name if simulated
        data is used. Used to select the log's color.

    family_name : str
        Name of the log type: UV, conductivity, pH, ... Used to control which
        plot container to display the log in.

    source_type : str
        Type of collection containing the log: experiment, simulation,
        fractions? Used to control the curve type (solid, dashed, symbols).

    x_data : ndarray
        Data points along the x axis.

    y_data : ndarray
        Data points along the y axis.

    data_mask : slice [OPTIONAL]
        Slice of the data to display.
    """
    # create the family from family name.
    family = create_chrome_family(family_name)

    # FIXME: some of the prop. should be generators / callables
    # initialized for a family and then customized for a particular
    # instance of a log.
    renderer_props = get_renderer_properties(source_name, family,
                                             source_type)

    if data_mask is None:
        data_mask = slice(None, None)

    # create the chrome log
    log = ChromeLog(
        name=name,
        x_data=x_data[data_mask],
        y_data=y_data[data_mask],
        source_type=source_type,
        family=family,
        renderer_properties=renderer_props,
    )
    return log


def build_chrome_log_collection_from_experiment(expt):
    """ Build a collection of Chromatography logs (plots) from all expt data.

    Note: no filtering based on time is applied: it is therefore assumed that
    the load phase starts at the beginning of the AKTA recording.

    FIXME: Once units can be reliably parsed from AKTA and Excel readers make
    sure that the units are set for all results.
    Also, create unit converters that might be specific to
    experiment/simulation (e.g. cv_to_duration, cv_to_time, AU_to_AU/cm etc.)
    """

    # NOTES: Target units
    # time units -> minutes
    # concentrations/absorbance -> AU/cm
    # conductivity -> mS/cm

    collection_name = expt.name
    if expt.output is None or not expt.output.continuous_data:
        collection_name += " (no data)"

    expt_logs = ChromeLogCollection(name=collection_name,
                                    source_type="experiment", source=None)
    expt_results = expt.output
    if expt_results is None:
        return expt_logs

    # Total product concentration (UV data)
    uv_data = expt_results.continuous_data.get('uv')
    if uv_data is not None:
        # FIXME: The AKTA data seems to have the units (mAU). So convert
        # to AU/cm.
        y_data = uv_data.y_data / 1000. / expt.system.abs_path_length[()]

        # FIXME: need a mapping to plot labels.
        uv_name = "{}_Expt UV".format(expt.name)
        expt_logs.logs[uv_name] = create_chrome_log(
            name=uv_name,
            source_name=collection_name,
            family_name=LOG_FAMILY_UV,
            source_type='experiment',
            x_data=uv_data.x_data,
            y_data=y_data,
        )

    # pH data
    pH_data = expt_results.continuous_data.get('pH')
    if pH_data is not None:
        # FIXME: need a mapping to plot labels.
        pH_name = "{}_Expt pH".format(expt.name)
        expt_logs.logs[pH_name] = create_chrome_log(
            name=pH_name,
            source_name=collection_name,
            family_name='pH',
            source_type='experiment',
            x_data=pH_data.x_data,
            y_data=pH_data.y_data,
            )

    # Conductivity data
    cond_data = expt_results.continuous_data.get('conductivity')
    if cond_data is not None:
        # FIXME: need a mapping to plot labels.
        cond_name = "{}_Expt Conductivity".format(expt.name)
        expt_logs.logs[cond_name] = create_chrome_log(
            name=cond_name,
            source_name=collection_name,
            family_name='Chemical Concentrations',
            source_type='experiment',
            x_data=cond_data.x_data,
            y_data=cond_data.y_data,
        )

    # Product component concentration (fraction data)
    prod_comp_names = expt.product.product_component_names
    uv_keys = prod_comp_names + [FRACTION_TOTAL_DATA_KEY]
    for key in uv_keys:
        frac_data = expt_results.fraction_data.get(key)
        if frac_data is None:
            continue
        frac_x_data = frac_data.x_data
        mask = frac_x_data > 0
        expt_logs.logs[key] = create_chrome_log(
            name=key,
            source_name=collection_name,
            family_name=LOG_FAMILY_UV,
            source_type='fraction',
            x_data=frac_x_data,
            y_data=frac_data.y_data,
            data_mask=mask,
        )

    return expt_logs


def build_chrome_log_collection_from_simulation(sim):
    """ Build a collection of Chromatography logs (plots) from all data in an
    experiment.
    """
    # FIXME: use stored units instead of hardcoding units
    # Also, create unit converters that might be specific to
    # experiment/simulation (e.g. cv_to_duration, cv_to_time, AU_to_AU/cm etc.)

    sim_collection = ChromeLogCollection(name=sim.name,
                                         source_type="simulation")
    if sim.source_experiment:
        source_name = sim.source_experiment.name
    else:
        source_name = sim.name

    sim_collection.source = source_name

    sim_results = sim.output
    if sim_results is None:
        return sim_collection

    total = sim_results.continuous_data['Total_Sim']
    time_factor = convert_str(1, from_unit_string=total.x_metadata["units"],
                              to_unit_string="min")
    sim_time = total.x_data * time_factor

    prod_comp_names = sim.product.product_component_names
    uv_data_names = [name + '_Sim' for name in prod_comp_names]
    uv_data_names += ['Total_Sim']

    for name in uv_data_names:
        xy_data = sim_results.continuous_data[name]
        sim_collection.logs[xy_data.name] = create_chrome_log(
            name=xy_data.name,
            source_name=source_name,
            family_name=LOG_FAMILY_UV,
            source_type='simulation',
            x_data=sim_time,
            y_data=xy_data.y_data,
        )

    # There might be no simulated cation concentration, for example if the
    # binding model was Langmuir
    if 'cation_Sim' in sim_results.continuous_data:
        cation = sim_results.continuous_data['cation_Sim']
        sim_collection.logs['cation'] = create_chrome_log(
            name='cation',
            source_name=source_name,
            family_name='Chemical Concentrations',
            source_type='simulation',
            x_data=sim_time,
            y_data=cation.y_data,
        )

    return sim_collection


def build_chromatogram_model(study, expts=None, sims=None, sim_group=None):
    """ Takes a study, and builds a model to plot data from its experiments
    and simulations. Defaults to showing all experiment and simulation data.
    Only one of experiment_name or simulation_name should be specified
    at a time, or neither.

    Parameters
    ----------
    study : Study
        Study containing all simulations to display against 1 or more
        experiment.

    expts : list(Experiment) (OPTIONAL)
        List of Experiments to display. Only simulations for which
        it is set as `source_experiment` will be displayed against.

    sims : list(Simulation) (OPTIONAL)
        List of simulations to display. Their `source_experiment` will be
        displayed along with it.

    sim_group : SimulationGroup (OPTIONAL)
        Simulation group to plot all the simulations from.
    """

    # Create the model.
    model_data = ChromatogramModel()

    # Specify which experiments and sims to use
    if expts and sims is None and sim_group is None:
        sims = [sim for sim in study.simulations
                if sim.source_experiment in expts]
    elif sims and expts is None and sim_group is None:
        expts = [sim.source_experiment for sim in sims
                 if sim.source_experiment is not None]
    elif sim_group and sims is None and expts is None:
        sims = sim_group.simulations
        expts = [sim.source_experiment for sim in sims
                 if sim.source_experiment is not None]
    elif sims is None and expts is None and sim_group is None:
        # Nothing is requested: plot all sims and exps
        sims = study.simulations
        expts = study.experiments
    else:
        msg = "The combination of object to plot isn't support. Please " \
              "provide a list of simulations, or a list of experiments or 1 " \
              "simulation group."
        logger.exception(msg)
        raise ValueError(msg)

    # generate model data for expts and sims
    for expt in expts:
        try:
            coll = build_chrome_log_collection_from_experiment(expt)
            model_data.log_collections[coll.name] = coll
        except Exception as e:
            logger.error("Failed to load data from experiment {}. Error was "
                         "{}".format(expt.name, e))

    for sim in sims:
        if sim.output is not None:
            coll = build_chrome_log_collection_from_simulation(sim)
            model_data.log_collections[coll.name] = coll

    return model_data
