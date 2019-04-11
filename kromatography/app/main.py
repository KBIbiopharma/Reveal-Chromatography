""" Module to update and launch the Reveal Chromatography application.

Since we want to be able to update the kromatography package, and its
dependencies, we need to protect any import that is not stricly necessary for
the update mechanism to be delayed until the last minute.
"""
import sys
from textwrap import dedent
import psutil


def create_and_run_app(debug=False):
    """ Create an application object, initialize it and run its GUI.

    Parameters
    ----------
    debug : bool [OPTIONAL, default=False]
        Override debug argument and run as debug? By default, conforms to the
        -d command line argument.
    """
    from kromatography.app.krom_app import instantiate_app
    from kromatography.utils.app_utils import get_minimal_parser, \
        initialize_unit_parser

    parser = get_minimal_parser()
    initialize_unit_parser()

    # add configuration specific to this tool.
    parser.description = dedent("""
        Run Chromatography GUI application. Some optional study data can be
        provided in the form of Excel input files.
    """)

    parser.add_argument(
        '-i', '--input-files', nargs='+',
        help='Project and study files to load on startup.',
    )
    parser.add_argument(
        '-u', '--user-datasource',
        help='User datasource file to start application from, instead of '
             'default datasource',
    )
    args = parser.parse_args()
    do_debug = args.debug or debug
    app = instantiate_app(init_files=args.input_files, verbose=args.verbose,
                          debug=do_debug, user_ds=args.user_datasource)
    if app:
        app.run()


def main(debug=False):
    """ Launch the application if it isn't already running.

    Parameters
    ----------
    debug : bool [OPTIONAL, default=False]
        Override debug argument and run as debug? By default, conforms to the
        -d command line argument.
    """
    from kromatography import __version__, __build__
    try:
        from app_updater.updater import initialize_local_egg_repo, \
            LOCAL_EGG_REPO
        app_updater_missing = False
    except ImportError:
        app_updater_missing = True

    if not app_updater_missing:
        # If first time running, create a updater folder and history file for
        # the updater to know what version is factory installed:
        initialize_local_egg_repo(local_egg_repo=LOCAL_EGG_REPO,
                                  version=__version__, build=__build__)

    # FIXME: this feels like a workaround more than a real solution.
    # The symptom is that only once the application is packaged in the msi, if
    # one tries to load a project and run a simulation without this lock, the
    # forking of processes when creating the multi-process job manager leads to
    # a rerun of this main module and another call to app.run() above, despite
    # the protection from `if __name__ == '__main__':`.
    # Bug seen on Windows 7 and Windows 10.
    if sys.platform == "win32":
        current_process_name = psutil.Process().exe()
        # List all processes that report their exe
        num_running_reveal = 0
        for p in psutil.process_iter():
            try:
                if p.exe() == current_process_name:
                    num_running_reveal += 1
            except psutil.AccessDenied:
                continue

        if num_running_reveal != 1:
            msg = "The application is already running. Please kill these " \
                  "processes or logout/login to be able to run Reveal."
            print(msg)
            return

    create_and_run_app(debug=debug)


def main_debug():
    """ Launch the application, forcing to be in debug mode.
    """
    main(debug=True)


if __name__ == '__main__':
    main()
