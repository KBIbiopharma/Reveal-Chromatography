""" Utilities to implement unit tests
"""

from os.path import abspath, dirname, join

from kromatography.io.study import load_exp_study_from_excel
from kromatography.model.factories.simulation import \
    build_simulation_from_experiment
from kromatography.io.simulation_updater import update_simulation_results
from kromatography.utils.cadet_simulation_builder import build_cadet_input
import kromatography
from kromatography.utils.app_utils import initialize_unit_parser
from kromatography.model.tests.sample_data_factories import make_sample_study

initialize_unit_parser()

_PACKAGE_PATH = dirname(abspath(kromatography.__file__))


# Data file path utilities ----------------------------------------------------

def plot_data_dir():
    """ Returns path containing plot example data for testing.
    """
    return join(_PACKAGE_PATH, 'plotting', 'tests', 'data')


def plot_data_path(filename):
    """ Returns the full path of the plot test data file named `filename`.
    """
    return join(plot_data_dir(), filename)


def model_data_dir():
    """ Returns the path containing model data files used in testing.
    """
    return join(_PACKAGE_PATH, 'model', 'tests', 'data')


def model_data_path(filename):
    """ Returns the full path of the model test data file named `filename`.
    """
    return join(model_data_dir(), filename)


def io_data_dir():
    """ Returns the path containing IO data files used in testing.
    """
    return join(_PACKAGE_PATH, 'io', 'tests', 'data')


def io_data_path(filename):
    """ Returns the full path of the IO test data file named `filename`.
    """
    return join(io_data_dir(), filename)


# Quick loader for experiment and simulation ----------------------------------

def load_default_experiment_simulation(expt_id='Run_1'):
    """ Load a default experiment and already run simulation.

    DEPRECATED: use
    kromatography.model.tests.sample_data_factories.make_sample_experiment2
    instead.
    """
    # Load the experiment
    input_file = io_data_path('ChromExampleDataV2.xlsx')
    study = load_exp_study_from_excel(input_file, datasource=None,
                                      allow_gui=False)
    expt = study.search_experiment_by_name(expt_id)

    # Build and load the simulation
    sim = build_simulation_from_experiment(expt)
    build_cadet_input(sim)
    output_file = io_data_path('Chrom_Example_Run_1_cadet_simulation.h5')
    update_simulation_results(sim, output_file)
    return expt, sim


def load_study_with_exps_and_ran_sims():
    """ Loads a study with two experiments and sims already ran.

    DEPRECATED: use
    kromatography.model.tests.sample_data_factories.make_sample_study instead.
    """
    study = make_sample_study()
    exp1, sim1 = load_default_experiment_simulation(expt_id='Run_1')
    exp2, sim2 = load_default_experiment_simulation(expt_id='Run_2')
    study.experiments = [exp1, exp2]
    study.simulations = [sim1, sim2]
    return study
