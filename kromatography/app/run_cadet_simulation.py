""" Mini command line application to run CADET on an existing HDF5 input file.
"""
import logging

from os.path import isabs, join
from textwrap import dedent

from kromatography.utils.app_utils import get_minimal_parser, \
    initialize_logging
from kromatography.solve.api import run_cadet_simulator

logger = logging.getLogger(__name__)


def main():
    parser = get_minimal_parser()

    # add configuration specific to this tool.
    parser.description = dedent("""
        Run CADET simulator for a given input HDF5 file.
    """)
    parser.add_argument(
        'input_file', default=None,
        help='The name of the h5 file containing CADET inputs to run CADET on.'
    )

    args = parser.parse_args()

    if not isabs(args.log_dir):
        log_dir = join(args.output_dir, args.log_dir)
    else:
        log_dir = args.log_dir

    initialize_logging(
        'run-cadet-sim',
        verbose=args.verbose,
        log_file=args.log,
        log_dir=log_dir
    )

    run_cadet_simulator(args.input_file)
