""" Script similar to the Legacy script that runs a full cycle: load a study,
create simulation from an experiment, run CADET and plot both the simulation
and experiments together in a model calibration plot style.
"""
from __future__ import print_function

import logging
from os.path import isabs, join
from textwrap import dedent
import time

from app_common.std_lib.filepath_utils import string2filename

from kromatography.utils.app_utils import get_minimal_parser, \
    initialize_unit_parser, initialize_logging
from kromatography.utils.io_utils import write_to_h5
from kromatography.io.study import load_study_from_excel
from kromatography.utils.cadet_simulation_builder import build_cadet_input
from kromatography.solve.api import run_cadet_simulator
from kromatography.io.simulation_updater import update_simulation_results
from kromatography.plotting.mpl_plot_chromatogram import plot_chromatogram
from kromatography.plotting.mpl_column_animation import column_animation
from kromatography.model.factories.simulation import \
    build_simulation_from_experiment


logger = logging.getLogger(__name__)

initialize_unit_parser()


def run_chromatography_simulation(input_file, output_file=None,
                                  expt_id="Run_1", skip_cadet=False,
                                  skip_plot=False, skip_animation=False,
                                  binding_model=None, transport_model=None,
                                  allow_gui=True):
    """ Run chromatography simulation for the inputs given in `input_file`
    and plot the results.

    Parameters
    ----------
    input_file : str (file path)
        The file path for the excel file containing the experiment/simulation
        input data.

    output_file : str (file path)
        The file path for the CADET output h5 file. If None, then a default
        name is chosen based on the study and experiment ids.

    expt_id : str
        The name of the exeperiment to use for intializing the CADET
        simulation. If None, the first experiment in the study is chosen.

    skip_cadet : bool
        If True, the CADET simulation is not run but instead the output
        file is directly loaded (assuming one already exists). The main usecase
        here is for testing.

    skip_plot : bool
        If True, the chromatogram plot is not generated. This is useful for
        testing.

    Returns
    -------
    study : Study
        The Study instance containing the experiment and the simulation data.
    """
    study = load_study_from_excel(input_file, allow_gui=allow_gui)

    # lets just pick a single experiment
    if expt_id is None:
        expt = study.experiments[0]
    else:
        expt = study.search_experiment_by_name(expt_id)

    logger.info('Running simulation for experiment : {!r}'.format(expt_id))

    if output_file is None:
        output_file = (
            "{}_{}_{}.h5".format(study.name, expt.name, 'cadet_simulation')
        )
        output_file = string2filename(output_file)

    # create a simulation object from an experiment
    # FIXME: how to identify related expt and simulations !
    sim = build_simulation_from_experiment(expt, binding_model=binding_model,
                                           transport_model=transport_model)

    study.simulations.append(sim)

    # create the CADET inputs
    cadet_input = build_cadet_input(sim)

    # NOTE: This is primarily used for testing/debugging workflow when the
    # CADET simulation doesn't need to be run everytime.
    if not skip_cadet:
        # write the CADET inputs
        write_to_h5(output_file, cadet_input, root='/input', overwrite=True)
        logger.info("Output file {} was generated".format(output_file))

        # run simulation to generate outputs
        run_cadet_simulator(output_file)

    update_simulation_results(sim, output_file)

    if not skip_plot:
        plot_chromatogram(expt, sim)

    if not skip_animation:
        column_animation(sim)

    return study


def main():
    parser = get_minimal_parser()

    # add configuration specific to this tool.
    parser.description = dedent("""
        Run Chromatography simulation for a given experiment.
        The experiment data is read from the provided excel file.
    """)
    parser.add_argument(
        'input_file', default=None,
        help='The name of the excel file containing CADET inputs.'
    )
    parser.add_argument(
        '--expt-id', default=None,
        help='The name of the experiment to simulate.'
    )
    parser.add_argument(
        '--skip-cadet', action='store_true',
        help=('Skip running CADET analysis if the file '
              'already exisits.')
    )
    parser.add_argument(
        '--skip-plot', action='store_true',
        help=('Skip plotting the chromatograms.')
    )
    parser.add_argument(
        '--skip-anim', action='store_true',
        help=('Skip animations for each component concentrations.')
    )
    parser.add_argument(
        '-o', '--output', default=None,
        help='The name of CADET simulation file.'
    )
    args = parser.parse_args()

    if not isabs(args.log_dir):
        log_dir = join(args.output_dir, args.log_dir)
    else:
        log_dir = args.log_dir

    initialize_logging(
        'run-chrom-sim',
        verbose=args.verbose,
        log_file=args.log,
        log_dir=log_dir
    )

    t0 = time.time()
    run_chromatography_simulation(
        args.input_file, args.output, expt_id=args.expt_id,
        skip_cadet=args.skip_cadet, skip_plot=args.skip_plot,
        skip_animation=args.skip_anim
    )
    elapsed_time = time.time() - t0
    msg = 'Elapsed time : {:0.2f} seconds'.format(elapsed_time)
    logger.info(msg)
    print(msg)


if __name__ == '__main__':
    main()
