""" Functions to build sample data models for testing purposes.
"""
import numpy as np
import pandas as pd
from itertools import product
from collections import OrderedDict

from kromatography.compute.experiment_optimizer_step import ALL_COST_COL_NAME
from kromatography.model.api import Experiment, Simulation
from kromatography.utils.app_utils import initialize_unit_parser
from kromatography.plotting.chromatogram_plot import ChromatogramPlot
from kromatography.ui.brute_force_optimizer_builder import \
    BruteForceOptimizerBuilder, ExperimentSelector
from kromatography.model.data_source import SimpleDataSource
from kromatography.utils.string_definitions import LOG_FAMILY_UV

initialize_unit_parser()

DEFAULT_INPUT = 'ChromExampleDataV2.xlsx'

DEFAULT_INPUT_WITH_STRIP = "ChromExampleDataV2_with_strip.xlsx"


def make_sample_app(initial_files=None):
    """ Returns a KromatographyApp instance, shorter splash time and optionally
    around the provided initial files.

    Parameters
    ----------
    initial_files : list of strings or None
        List of file names to open on launch of the application.
    """
    from kromatography.app.krom_app import instantiate_app
    from kromatography.ui.api import register_all_data_views

    register_all_data_views()
    SPLASH_DURATION = 0.25

    return instantiate_app(init_files=initial_files,
                           splash_duration=SPLASH_DURATION,
                           verbose=False, confirm_on_window_close=False,
                           warn_if_old_file=False)


def make_sample_user_ds(with_bind_trans=False, num_comp=4):
    """ Make a sample User datasource, optionally adding a sample binding and
    transport models to the data catalog content.
    """
    user_ds = SimpleDataSource()
    if with_bind_trans:
        # Add a sample binding and transport models to test their adaptation
        sample_bind_model = make_sample_binding_model(num_comp)
        user_ds.binding_models.append(sample_bind_model)
        sample_transp_model = make_sample_transport_model(num_comp)
        user_ds.transport_models.append(sample_transp_model)
    return user_ds


def make_sample_study(num_exp=0):
    """ Make a sample modeling study with a given number of experiments.
    """
    from kromatography.model.study import Study
    from kromatography.model.tests.example_model_data import STUDY_DATA
    study = Study(**STUDY_DATA)
    for i in range(num_exp):
        experim1 = make_sample_experiment(name="Experim" + str(i + 1))
        study.add_experiments(experim1)

    return study


def make_sample_study2(source=DEFAULT_INPUT, add_sims=0,
                       add_transp_bind_models=False, with_ph_bind=False):
    """ Load an simulation from a standard source file.
    """
    from kromatography.io.study import load_study_from_excel
    from kromatography.utils.testing_utils import io_data_path
    from kromatography.model.factories.transport_model import \
        create_transport_model
    from kromatography.model.factories.binding_model import \
        create_binding_model
    from kromatography.model.binding_model import PH_STERIC_BINDING_MODEL, \
        STERIC_BINDING_MODEL
    from kromatography.model.factories.simulation import \
        build_simulation_from_experiment

    filepath = io_data_path(source)
    test_study = load_study_from_excel(filepath, allow_gui=False)

    if add_transp_bind_models:
        study_ds = test_study.study_datasource
        num_comp = len(test_study.product.product_components) + 1
        tr_model = create_transport_model(num_comp)
        study_ds.set_object_of_type("transport_models", tr_model)
        if with_ph_bind:
            bind_model = create_binding_model(
                num_comp, model_type=PH_STERIC_BINDING_MODEL
            )
        else:
            bind_model = create_binding_model(
                num_comp, model_type=STERIC_BINDING_MODEL
            )

        study_ds.set_object_of_type("binding_models", bind_model)
    else:
        tr_model = None
        bind_model = None

    if isinstance(add_sims, int) and add_sims > 0:
        for i in range(add_sims):
            exp = test_study.experiments[i]
            sim = build_simulation_from_experiment(
                exp, transport_model=tr_model, binding_model=bind_model
            )
            test_study.simulations.append(sim)

    elif isinstance(add_sims, basestring):
        exp = test_study.search_experiment_by_name(add_sims)
        sim = build_simulation_from_experiment(
            exp, transport_model=tr_model, binding_model=bind_model
        )
        test_study.simulations.append(sim)

    return test_study


def make_sample_experimental_study(num_exp=0):
    """ Make a sample experimental study with a given number of experiments.
    """
    from kromatography.model.experimental_study import ExperimentalStudy
    from kromatography.model.tests.example_model_data import \
        EXPERIMENTAL_STUDY_DATA
    study = ExperimentalStudy(**EXPERIMENTAL_STUDY_DATA)
    for i in range(num_exp):
        experim1 = make_sample_experiment(name="Experim" + str(i + 1))
        study.add_experiments(experim1)

    return study


def make_sample_experiment(name='Run 1'):
    """ Make a sample experiment for testing purposes from example data.
    """
    from kromatography.model.column import Column, ColumnType
    from kromatography.model.resin import Resin
    from kromatography.model.method import Method
    from kromatography.model.system import System, SystemType
    from kromatography.model.experiment import Experiment
    from kromatography.model.tests.example_model_data import COLUMN_TYPE_DATA,\
        COLUMN_DATA, METHOD_DATA, RESIN_DATA, SYSTEM_TYPE_DATA, SYSTEM_DATA

    column_type = ColumnType(**COLUMN_TYPE_DATA)
    resin = Resin(**RESIN_DATA)
    column = Column(column_type=column_type, resin=resin, **COLUMN_DATA)
    system_type = SystemType(**SYSTEM_TYPE_DATA)
    system = System(system_type=system_type, **SYSTEM_DATA)
    method = Method(**METHOD_DATA)

    expr = Experiment(
        name=name, system=system, column=column, method=method,
        output=None
    )
    return expr


def make_sample_experiment2(name='Run_1', source=DEFAULT_INPUT):
    """ Load an experiment from a standard input file.
    """
    test_study = make_sample_study2(source=source)
    exp = test_study.search_experiment_by_name(name)
    return exp


def make_sample_experiment2_with_strip(exp_name="Run_1",
                                       source=DEFAULT_INPUT_WITH_STRIP):
    from kromatography.utils.api import load_default_user_datasource
    from kromatography.io.api import load_study_from_excel
    from kromatography.utils.testing_utils import io_data_path
    from kromatography.model.factories.product import add_strip_to_product

    ds = load_default_user_datasource()[0]
    prod1 = ds.get_object_of_type("products", "Prod000Complex")
    new_prod, new_comp = add_strip_to_product(prod1, 18.8, 0.75)
    new_prod.name = "Prod001_with_strip"
    ds.set_object_of_type("products", new_prod)
    ds.set_object_of_type("product_components", new_comp)

    filepath = io_data_path(source)
    study = load_study_from_excel(filepath, datasource=ds, allow_gui=False)
    experim = study.search_experiment_by_name(exp_name)
    return experim


def make_sample_simulation(name='Run_3', result_file=""):
    """ Load a simulation from the default input file.
    """
    from kromatography.model.factories.simulation import \
        build_simulation_from_experiment
    from kromatography.io.simulation_updater import update_simulation_results

    exp = make_sample_experiment2(name=name)
    simu = build_simulation_from_experiment(exp)

    if result_file:
        update_simulation_results(simu, result_file)

    return simu


def make_sample_simulation2():
    """ Build a simulation from scratch (no output).
    """
    from kromatography.model.factories.simulation import \
        build_simulation_from_experiment
    exp = make_sample_experiment(name='Run 1')
    sim = build_simulation_from_experiment(exp, fstep='whatever name',
                                           lstep='Gradient Elution')
    return sim


def make_sample_binding_model(num_comp=4, ph_dependence=False):
    """ Create a sample binding model."""
    from kromatography.model.binding_model import PhDependentStericMassAction,\
        StericMassAction

    if ph_dependence:
        binding_model = PhDependentStericMassAction(
            num_comp, name="Sample pH-dependent SMA"
        )
    else:
        binding_model = StericMassAction(num_comp, name="Sample SMA")

    binding_model.is_kinetic = 0
    binding_model.sma_ka = [0.0, 0.0000025, 0.00017, 0.001]
    binding_model.sma_kd = [0.0, 1.0, 1.0, 1.0]
    binding_model.sma_lambda = 646.0
    binding_model.sma_nu = [0.0, 5.0, 4.0, 5.0]
    binding_model.sma_sigma = [0.0, 5.0, 5.0, 5.0]
    if ph_dependence:
        binding_model.sma_ka_ph = [0.0, 0.001, 0.001, 0.001]
        binding_model.sma_ka_ph2 = [0.0, 0.001, 0.001, 0.001]
        binding_model.sma_nu_ph = [0.0, 0.0, 0.0, 0.0]
        binding_model.sma_sigma_ph = [0.0, 0.0, 0.0, 0.0]
    return binding_model


def make_sample_langmuir_binding_model(num_comp=3, ph_dependence=False):
    """ Create a sample binding model."""
    from kromatography.model.binding_model import ExternalLangmuir, \
        Langmuir

    if ph_dependence:
        binding_model = ExternalLangmuir(
            num_comp, name="Sample pH-dependent Langmuir"
        )
    else:
        binding_model = Langmuir(num_comp, name="Sample MC Langmuir")

    binding_model.is_kinetic = 0
    binding_model.mcl_ka = [1.0, 1.0, 1.0]
    binding_model.mcl_kd = [1.0, 1.0, 1.0]
    binding_model.mcl_qmax = [5.0, 5.0, 5.0]
    if ph_dependence:
        # add linear dependence on pH
        binding_model.extl_ka_t = [0.001, 0.001, 0.001]

    return binding_model


def make_sample_binding_model2(num_comp, ph_dependence=False, like_no_ph=True):
    """ Create a sample binding model."""
    from kromatography.model.factories.binding_model import \
        create_binding_model
    from kromatography.model.binding_model import PH_STERIC_BINDING_MODEL, \
        STERIC_BINDING_MODEL
    from kromatography.model.factories.binding_model import DEFAULT_SMA_VALUES

    if ph_dependence:
        model_type = PH_STERIC_BINDING_MODEL
    else:
        model_type = STERIC_BINDING_MODEL

    default_model = create_binding_model(num_comp,
                                         model_type=model_type)
    if ph_dependence and like_no_ph:
        default_model.sma_ka_ph = np.zeros(num_comp)
        default_model.sma_nu_ph = np.zeros(num_comp)
        default_model.sma_ka[1:] = \
            np.log10(DEFAULT_SMA_VALUES["sma_ka"]) * np.ones(num_comp-1)
        default_model.sma_kd = np.zeros(num_comp)

    return default_model


def make_sample_transport_model(num_comp=4):
    """ Create a sample Transport model. """
    from kromatography.model.transport_model import GeneralRateModel

    transport_model = GeneralRateModel(num_comp, name="Sample GRM")
    transport_model.column_porosity = 0.30
    transport_model.bead_porosity = 0.50
    transport_model.axial_dispersion = 6e-8
    transport_model.film_mass_transfer = [6.9e-6] + [5.0e-5] * (num_comp - 1)
    transport_model.pore_diffusion = [7.0e-10] + [1.0e-11] * (num_comp - 1)
    transport_model.surface_diffusion = [0.0] * num_comp
    return transport_model


def make_sample_chrom_model(exp_name="Run_1", include_sim=False):
    """ Create a sample experimental ChromatogramModel with 1 log of type
    protein concentration.
    """
    from kromatography.plotting.data_models import ChromeLogCollection, \
        ChromeLog, ChromeFamily
    from kromatography.plotting.api import ChromatogramModel

    chrom_model = ChromatogramModel()
    x = np.linspace(0, 2*np.pi, 10)
    y = np.sin(x)
    fam_data = {
        'data_label': 'Absorbance', 'plot_container_properties': {
            'axes_factory': {
                'vtitle': 'Absorbance (AU/cm)', 'htitle': 'Time (minutes)',
                'orientation': 'normal'
            },
            'legend': {'padding': 10, 'visible': True, 'align': 'ul'},
            'plot_context': {}
        },
        'description': 'desc', 'editable': True, 'time_label': 'Time',
        'time_unit_label': 'minutes', 'data_unit_label': 'AU/cm',
        'name': LOG_FAMILY_UV
    }
    family = ChromeFamily(**fam_data)
    renderer_props = {'origin': 'bottom left', 'line_width': 2,
                      'index_scale': 'linear', 'color': 'blue',
                      'line_style': 'solid', 'value_scale': 'linear',
                      'type': 'line'}
    log = ChromeLog(name='{}_Expt UV'.format(exp_name), x_data=x, y_data=y,
                    family=family, renderer_properties=renderer_props,
                    source_type='experiment')

    logs = OrderedDict({'{}_Expt UV'.format(exp_name): log})
    log_coll = ChromeLogCollection(name=exp_name, logs=logs,
                                   source_type="experiment")
    chrom_model.log_collections[exp_name] = log_coll

    if include_sim:
        sim_name = "Sim: "+exp_name
        sim_log_coll = ChromeLogCollection(name=sim_name, logs=logs,
                                           source_type="simulation",
                                           source=exp_name)
        chrom_model.log_collections[sim_name] = sim_log_coll

    return chrom_model


def make_sample_model_calibration_plot(exp_name="Run_1", family_names=None):
    """ Create a sample experimental ChromatogramPlot with the
        same number of logs as the number of family_names provided.
    """
    if not family_names:
        family_names = [LOG_FAMILY_UV]

    model_calibration_plot = ChromatogramPlot()
    model_calibration_plot.init()

    for name in family_names:
        log = make_sample_log()
        log.family.name = name
        model_calibration_plot.add_chrome_log(exp_name, log)
    return model_calibration_plot


def make_sample_log(exp_name='Run_1'):
    chrom_model = make_sample_chrom_model()
    log = chrom_model.log_collections[exp_name].logs.values()[0]
    return log


def make_sample_simulation_group(cp=None):
    from kromatography.model.simulation_group import SimulationGroup, \
        SingleParamSimulationDiff

    if cp is None:
        cp = make_sample_simulation2()

    diff = (SingleParamSimulationDiff("binding_model.sma_ka[1]", 0.01),)
    sim_group = SimulationGroup(center_point_simulation=cp, name="foo",
                                simulation_diffs=[diff])
    return sim_group


def make_sample_simulation_group2(size=3, cp=None):
    """ Build a sample simulation group scanning the sma_ka parameters.

    Parameters
    ----------
    size : int (default: 3)
        Number of values to scan.

    cp : Simulation or None (default: None)
        Center point simulation to build the simulation group from if any. By
        default a sample simulation is built from the std example data.
    """
    from kromatography.model.simulation_group import SimulationGroup, \
        SingleParamSimulationDiff

    if cp is None:
        cp = make_sample_simulation()

    orig_val = cp.binding_model.sma_ka[1]
    no_diff = (SingleParamSimulationDiff("binding_model.sma_ka[1]", orig_val),)
    simulation_map = {no_diff: cp}

    if size > 1:
        sim2 = cp.clone_traits(copy="deep")
        sim2.name = "sim2"
        sim2.binding_model.sma_ka[1] = 0.01
        diff2 = (SingleParamSimulationDiff("binding_model.sma_ka[1]", 0.01),)
        simulation_map[diff2] = sim2

    if size > 2:
        sim3 = cp.clone_traits(copy="deep")
        sim3.name = "sim3"
        sim3.binding_model.sma_ka[1] = 0.1
        diff3 = (SingleParamSimulationDiff("binding_model.sma_ka[1]", 0.1),)
        simulation_map[diff3] = sim3

    group = SimulationGroup(
        center_point_simulation=cp, name="foo",
        simulation_diffs=simulation_map.keys()
    )
    return group


def make_sample_mc_simulation_group(size=3, cp=None, num_params=1):
    """ Make a sample Monte Carlo group
    """
    from kromatography.model.factories.simulation_group import \
        build_random_simulation_group

    if cp is None:
        cp = make_sample_simulation()

    params = ["binding_model.sma_ka[1]"]
    if num_params == 2:
        params.append("binding_model.sma_nu[1]")
    elif num_params == 3:
        params.append("binding_model.sma_sigma[1]")

    group = build_random_simulation_group(center_sim=cp, group_size=size,
                                          param_names=params,
                                          dist_desc=[(0.5, 1)])
    return group


def make_sample_param_scan_list(num_values, num_params=2):
    from kromatography.model.parameter_scan_description import \
        ParameterScanDescription

    param_list = []
    klass = ParameterScanDescription
    scan_attrs = {"num_values": num_values, "spacing": "Log"}

    low, high = (1e-8, 50)
    name = "binding_model.sma_ka[1:]"
    param_list += [klass(name=name, low=low, high=high, **scan_attrs)]

    if num_params > 1:
        low, high = (0.1, 20)
        name = "binding_model.sma_nu[1:]"
        param_list += [klass(name=name, low=low, high=high, **scan_attrs)]
    return param_list


def make_sample_general_param_scan_list(num_values, num_params=2,
                                        target_sim=None):
    from kromatography.model.parameter_scan_description import \
        ParameterScanDescription

    param_list = []
    klass = ParameterScanDescription
    scan_attrs = {"num_values": num_values, "spacing": "Linear",
                  "target_simulation": target_sim}

    low, high = (300, 1000)
    name = "binding_model.sma_lambda"
    param_list += [klass(name=name, low=low, high=high, **scan_attrs)]

    if num_params > 1:
        low, high = (90, 110)
        name = "column.resin.ligand_density"
        param_list += [klass(name=name, low=low, high=high, **scan_attrs)]

    if num_params > 2:
        low, high = (0.1, 20)
        name = "binding_model.sma_nu[1]"
        param_list += [klass(name=name, low=low, high=high, **scan_attrs)]

    return param_list


def make_sample_binding_model_optimizer(num_values=5, num_params=2, exp=None,
                                        exp_source=DEFAULT_INPUT,
                                        with_data=False, **traits):
    from kromatography.compute.brute_force_binding_model_optimizer import \
        BruteForce2StepBindingModelOptimizer
    from kromatography.model.factories.simulation import \
        build_simulation_from_experiment
    from kromatography.model.api import LazyLoadingSimulation

    if exp is None:
        exp = make_sample_experiment2(source=exp_source)

    cp_sim = build_simulation_from_experiment(exp)
    # Center point sims coming from optimizer builder are LazyLoading
    cp_sim = LazyLoadingSimulation.from_simulation(cp_sim)
    starting_point_simulations = [cp_sim]
    param_list = make_sample_param_scan_list(num_values, num_params=num_params)
    optimizer_params = dict(
            target_experiments=[exp],
            starting_point_simulations=starting_point_simulations,
            constant_step_parameter_list=param_list,
            refining_step_num_values=num_values
        )
    optimizer_params.update(traits)

    optimizer = BruteForce2StepBindingModelOptimizer(**optimizer_params)

    if with_data:
        data = {}
        size = num_values**num_params
        data[ALL_COST_COL_NAME] = range(size)
        param_products = product(*[i+np.arange(num_values)
                                   for i in range(num_params)])
        cols = zip(*param_products)
        for param, col in zip(param_list, cols):
            data[param.name] = col

        cost_data = pd.DataFrame(data)
        ordered_cols = [p.name for p in param_list] + [ALL_COST_COL_NAME]
        optimizer.cost_data = cost_data[ordered_cols]

    return optimizer


def make_sample_brute_force_optimizer(num_values=5, num_params=2, exp=None,
                                      exp_source=DEFAULT_INPUT,
                                      target_sim=None, with_data=False,
                                      parallel_params=False, **traits):
    """ Create a sample Brute force optimizer.
    """
    from kromatography.compute.brute_force_optimizer import BruteForceOptimizer
    from kromatography.model.factories.simulation import \
        build_simulation_from_experiment
    from kromatography.model.lazy_simulation import is_lazy, \
        LazyLoadingSimulation

    if exp is None:
        exp = make_sample_experiment2(source=exp_source)

    if target_sim is None:
        target_sim = build_simulation_from_experiment(exp)

    if isinstance(exp, Experiment):
        target_exp = [exp]
    else:
        target_exp = exp

    if isinstance(target_sim, Simulation):
        target_sims = [target_sim]
    else:
        target_sims = target_sim

    for i, sim in enumerate(target_sims):
        if not is_lazy(sim):
            target_sims[i] = LazyLoadingSimulation.from_simulation(sim)

    param_list = make_sample_general_param_scan_list(num_values,
                                                     num_params=num_params,
                                                     target_sim=target_sims[0])

    if parallel_params:
        for i in range(num_params-1):
            param_list[0].parallel_parameters.append(param_list.pop(1))

    optimizer_params = dict(
            target_experiments=target_exp,
            starting_point_simulations=target_sims,
            parameter_list=param_list
    )
    optimizer_params.update(traits)
    optimizer = BruteForceOptimizer(**optimizer_params)

    if with_data:
        data = {}
        size = num_values**num_params
        data[ALL_COST_COL_NAME] = range(size)
        param_products = product(*[i+np.arange(num_values)
                                   for i in range(num_params)])
        cols = zip(*param_products)
        for param, col in zip(param_list, cols):
            data[param.name] = col

        cost_data = pd.DataFrame(data)
        ordered_cols = [p.name for p in param_list] + [ALL_COST_COL_NAME]
        optimizer.cost_data = cost_data[ordered_cols]

    return optimizer


def make_sample_optimizer_builder(study, select_exp_names=None, **builder_kw):
    """ Build an OptimizerBuilder.
    """
    from kromatography.model.factories.simulation import \
        build_simulation_from_experiment

    if not study.simulations:
        sim = build_simulation_from_experiment(study.experiments[1])
        study.simulations.append(sim)

    first_sim_name = study.simulations[0].name
    exp_selector = ExperimentSelector(study=study)
    optim_builder = BruteForceOptimizerBuilder(
        experiment_selector=exp_selector,
        target_study=study, starting_point_simulation_name=first_sim_name,
        **builder_kw
    )

    if select_exp_names is None:
        select_exp_names = []
    elif isinstance(select_exp_names, basestring):
        select_exp_names = [select_exp_names]

    optim_builder.experiment_selector.experiment_selected = select_exp_names
    return optim_builder
