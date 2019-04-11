"""
This fabric based file lists some tasks to manage development environments
using a bootstrap one, and uses that dev env to run unit tests, check flake8
compatibility, build and publish project eggs.

To use these tools, developers must have an Enthought account. The host system
must have Enthought's EDM installed, and have a Python 2.7 bootstrap
environment with fabric, hatcher and ci_tools version 0.1.2.dev0-2 in it. The
user must also have a hatcher token created and stored as the "HATCHER_TOKEN"
environment variable.

Otherwise, launching or managing the environment should be done manually. See
requirement files inside deploy/ folder, and kromatography/app/main.py for
launcher script.
"""
import sys
from platform import architecture
import os
from subprocess import STDOUT
import glob
from os.path import abspath, dirname, exists, expanduser, isdir, isfile, join,\
    relpath
import re
from contextlib import contextmanager
from subprocess import check_call, check_output
from fabric.decorators import task
from fabric.api import lcd, local
import yaml
import platform
import shutil
from six import string_types
import pkg_resources
from setuptools.command.easy_install import nt_quote_arg

from ci_tools.fabric_tasks import setup_devenv as setup_devenv_core
from ci_tools.configuration import Configuration
from ci_tools.python_environment import PythonEnvironment
from ci_tools.utils.general import remove_tree
from ci_tools.utils.testing import flake8 as flake8_ci, nosetests, \
    nosetests_with_coverage
from ci_tools.utils.build import setup_egg
from ci_tools.utils.tasks import install_binary_dependencies as \
    base_install_binary_dependencies, clean_eggs, parse_source_dependencies
from ci_tools.utils.requirements import merge_requirements


###############################################################################
# Project specific configuration variables
###############################################################################


HERE = dirname(__file__)
ROOT = abspath(HERE)
PKG_NAME = "kromatography"
APP_TITLE = "Reveal Chromatography"
DEPLOY_ROOT = join(HERE, 'deploy')
REQUIREMENTS_ROOT = DEPLOY_ROOT
APP_DIR = join(HERE, PKG_NAME, "app")

COVERAGE_PACKAGES = (PKG_NAME,)
FLAKE8_PACKAGES = (PKG_NAME, "setup.py", "fabfile.py")
EGG_DIR = join(HERE, "dist")

IS_WINDOWS = sys.platform == "win32"
IS_OSX = sys.platform == "darwin"
IS_LINUX = sys.platform == "linux2"

ENV_CONFIG_FILE = join(DEPLOY_ROOT, 'config.yaml')
ENV_CONFIG_FILE_PY27 = join(DEPLOY_ROOT, 'config27.yaml')
EDM_CONFIG = join(DEPLOY_ROOT, 'edm_config.yaml')
SOURCE_BUILD_FILE = join(DEPLOY_ROOT, 'source_builds.yaml')

if sys.platform == "win32":
    BIN_FOLDER = "Scripts"
else:
    BIN_FOLDER = "bin"

###############################################################################
# API Fabric Tasks
###############################################################################


@task
def build_devenv(config_fname=ENV_CONFIG_FILE_PY27, edm_platform=None,
                 hatcher_token=None):
    """ Complete setup of a development environment.
    """
    if devenv_exists():
        remove_devenv(config_fname=config_fname, edm_platform=edm_platform)

    if hatcher_token is None:
        hatcher_token = os.environ.get("HATCHER_TOKEN")

    setup_devenv(config_fname=config_fname, edm_platform=edm_platform,
                 hatcher_token=hatcher_token)
    print("Environment created!")
    install_dependencies(config_fname=config_fname, edm_platform=edm_platform)
    print("All binaries installed")


@task
def remove_devenv(config_fname=ENV_CONFIG_FILE_PY27, edm_platform=None):
    """ Remove all traces of the development environment.
    """
    pyenv = _get_python_environment(edm_platform, config_fname=config_fname)
    env_folder = pyenv.get_install_dir()
    remove_tree(env_folder)


# Utilities ###################################################################

def devenv_exists(config_fname=ENV_CONFIG_FILE_PY27):
    """ Check if the EDM devenv has been created.
    """
    config = read_pyenv_config(filepath=config_fname)
    edm_name = config["name"]
    cmd = ["edm", "environments", "list"]
    output = check_output(cmd, shell=True)
    words = output.split()
    return edm_name in words


def read_pyenv_config(filepath=ENV_CONFIG_FILE_PY27):
    """ Return content of yaml config file.
    """
    with open(filepath, 'r') as stream:
        try:
            return yaml.load(stream)
        except yaml.YAMLError as exc:
            print(exc)


###############################################################################
# Individual fabric Tasks
###############################################################################

# Devenv creation tools #######################################################

@task
def setup_devenv(config_fname=ENV_CONFIG_FILE_PY27, edm_platform=None,
                 hatcher_token=None):
    """ Setup a development environment using the bootstrap environment.
    """
    setup_devenv_core(
        edm_platform=edm_platform,
        config_file=config_fname,
        edm_config=EDM_CONFIG,
        api_token=hatcher_token
    )


@task
def install_dependencies(config_fname=ENV_CONFIG_FILE_PY27, edm_platform=None):
    """ Install the dependencies for the project.
    """
    if architecture()[0] != '64bit':
        raise RuntimeError("Only 64bit architecture are supported.")

    install_binary_dependencies(config_fname=config_fname,
                                edm_platform=edm_platform)
    install_pip_dependencies(config_fname=config_fname,
                             edm_platform=edm_platform)


@task
def install_binary_dependencies(config_fname=ENV_CONFIG_FILE_PY27,
                                edm_platform=None, reqs=None):
    """ Install dependencies using EDM.
    """
    pyenv = _get_python_environment(edm_platform, config_fname=config_fname)
    env_platform = pyenv.edm_platform

    if reqs is None:
        reqs = ["dev_requirements"]
    elif isinstance(reqs, string_types):
        reqs = [reqs]

    if config_fname == ENV_CONFIG_FILE_PY27:
        reqs += ["requirements_py27"]
    elif config_fname == ENV_CONFIG_FILE:
        reqs += ["requirements_py36"]
    else:
        raise ValueError("Unknown config file {}".format(config_fname))

    requirements = [join(DEPLOY_ROOT, req + '-{0}.txt'.format(env_platform))
                    for req in reqs]

    with merge_requirements(requirements) as requirements_file:
        print("Install binary dependencies. This will take some time...")
        base_install_binary_dependencies(pyenv, requirements_file)


@task
def install_pip_dependencies(config_fname=ENV_CONFIG_FILE_PY27,
                             edm_platform=None, reqs=""):
    """ Install dependencies using pip.
    """
    pyenv = _get_python_environment(edm_platform, config_fname=config_fname)
    env_platform = pyenv.edm_platform

    if reqs is "":
        reqs = "pip_requirements"

    requirements = join(DEPLOY_ROOT, reqs + '-{0}.txt'.format(env_platform))

    with open(requirements) as requirements_file:
        print("Install pip dependencies...")
        dep_list = requirements_file.readlines()
        for dep in dep_list:
            dep = dep.strip()
            pyenv.runpip("install {}".format(dep))


@task
def install_project(config_fname=ENV_CONFIG_FILE_PY27, edm_platform=None):
    """ Install the package in the current directory.
    """
    pyenv = _get_python_environment(edm_platform, config_fname=config_fname)
    setup_egg(pyenv, command='develop')


# Run tasks ###################################################################


@task
def run(input_file="", verbose='True', debug='True', epd_platform=None):
    """ Run the standalone kromatography application.

    Input files can be passed in to be opened on startup.

    Parameters
    ----------
    input_file : Str
        Path to an Excel file containing a Study to open on startup.

    debug : str
        Whether to set mode to verbose and shorten the splash screen duration.
        Only checks if the first letter is 't' to set to True.

    verbose : str
        Lower the logger level from WARNING to DEBUG? Set to a string whose
        lower case version is 'true' to do so. Ignored if debug is set to true.

    epd_platform :
        One of the supported epd platforms {rh5-64, osx-64, win-64}.
    """
    pyenv = _get_python_environment(epd_platform)

    cmd = join(APP_DIR, 'main.py')

    if debug.lower().startswith('t'):
        cmd += " -d"
    else:
        if verbose.lower().startswith('t'):
            cmd += " -v"

    if input_file:
        filename = input_file.replace(" ", "\ ")
        cmd += " -i " + filename

    # setup and start the standalone application.
    pyenv.runpy(cmd)


@task
def run_cmd(cmd, config_fname=ENV_CONFIG_FILE_PY27, edm_platform=None):
    """ Run a distribution command, such as ipython, jupyter notebook, ...

    Parameters
    ----------
    cmd : str
        Command to execute. Must exist in the bin/Scripts folder of the
        distribution.

    config_fname : str [OPTIONAL]
        Name of the configuration file describing which dev environment to run
        with. Defaults to the Python2.7 PICTS viewer EDM environment.

    edm_platform :
        One of the supported epd platforms {rh5-64, osx-64, win-64}.
    """
    pyenv = _get_python_environment(edm_platform, config_fname=config_fname)
    pyenv.edm_run(cmd)


@task
def run_script(py_file="", config_fname=ENV_CONFIG_FILE_PY27,
               edm_platform=None):
    """ Run python executable from project's distribution on a python script.

    Parameters
    ----------
    py_file : str [OPTIONAL]
        Name of the python script to run. Leave empty to start the python
        interactive interpreter. In this case, you may prefer `fab run_ipy`.

    config_fname : str [OPTIONAL]
        Name of the configuration file describing which dev environment to run
        with. Defaults to the Python2.7 PICTS viewer EDM environment.

    edm_platform :
        One of the supported epd platforms {rh5-64, osx-64, win-64}.
    """
    cmd = "python " + py_file
    run_cmd(cmd, config_fname=config_fname, edm_platform=edm_platform)


@task
def run_ipy(config_fname=ENV_CONFIG_FILE_PY27, edm_platform=None):
    """ Launch ipython executable from the project's distribution.

    Parameters
    ----------
    config_fname : str [OPTIONAL]
        Name of the configuration file describing which dev environment to run
        with. Defaults to the Python2.7 PICTS viewer EDM environment.

    edm_platform :
        One of the supported epd platforms {rh5-64, osx-64, win-64}.
    """
    run_cmd("ipython", config_fname=config_fname, edm_platform=edm_platform)


# Dev tools ###################################################################


@task
def reset_preference_file():
    """ Reset the preference file to all default values.
    """
    from kromatography.utils.preferences import reset_preferences
    reset_preferences()


@task
def flake8(config_fname=ENV_CONFIG_FILE_PY27, edm_platform=None):
    """ Run flake8 on all of the code.
    """
    pyenv = _get_python_environment(edm_platform, config_fname=config_fname)
    flake8_ci(pyenv, FLAKE8_PACKAGES)


@task
def test(config_fname=ENV_CONFIG_FILE_PY27, repo_url=None, edm_platform=None):
    """ Run unit tests for the project.

    Parameters
    ----------
    config_fname : str [OPTIONAL]
        Path to the config file to grab the python environment to run tests.
        Defaults to ENV_CONFIG_FILE.

    repo_url : str
        Hack to inject an environment variable to control where is used as the
        test repo.
    """
    if repo_url:
        os.environ["TEST_MFI_REPO_URL"] = repo_url

    pyenv = _get_python_environment(edm_platform, config_fname=config_fname)
    nosetests(pyenv)


@task
def test_with_coverage(config_fname=ENV_CONFIG_FILE_PY27, edm_platform=None,
                       html=False):
    """ Run tests under coverage

    Parameters
    ----------
    edm_platform :
        One of the supported epd platforms {rh5-64, osx-64, win-64}.
    html : bool
        Whether to convert the coverage report to html pages.
    """
    pyenv = _get_python_environment(edm_platform, config_fname=config_fname)
    nosetests_with_coverage(pyenv, COVERAGE_PACKAGES, html=html)


@task
def build_docs(skip_api=False, target_format="html", remove_source_code=None,
               config_fname=ENV_CONFIG_FILE_PY27, edm_platform=None):
    """ Build the docs and copy the html to the kromatography folder.

    Parameters
    ----------
    skip_api : bool or str [OPTIONAL, default=False]
        Whether to skip regenerating the API files from source code before
        building the documentation (saves time).

    target_format : str [OPTIONAL, default=html]
        Format to generate the docs into. Also supported are pdf, latex, epub,
        ...

    remove_source_code : bool [OPTIONAL]
        Force the absence of the source code files? If not set manually, the
        values of kromatography.__target__ is read.
    """
    if isinstance(skip_api, string_types):
        if skip_api.lower().startswith("t"):
            skip_api = True
        else:
            skip_api = False

    pyenv = _get_python_environment(edm_platform, config_fname=config_fname)

    if remove_source_code is None:
        remove_source_code = get_target_audience() != "internal"

    if not skip_api:
        regenerate_api_files()

    # Copy the change log:
    tgt = join("docs", "source")
    shutil.copy("CHANGES.rst", tgt)

    # Run sphinx
    with change_dir_temporarily("docs"):
        if IS_WINDOWS:
            sphinx_executable_name = 'sphinx-build-script.py'
        else:
            sphinx_executable_name = 'sphinx-build'

        sphinx_executable = join(pyenv.bindir,
                                 sphinx_executable_name)
        sphinx_options = ['-b', 'html', '-d', 'build/doctrees', 'source',
                          'build/html']
        sphinx_cmd = [sphinx_executable] + sphinx_options

        try:
            out = check_output("make clean".format(target_format),
                               stderr=STDOUT, shell=True)
            print(out)
            msg = "Generating {} documentation from rst files..."
            print(msg.format(target_format))
            if IS_WINDOWS:
                cmd = " ".join(sphinx_cmd)
                pyenv.runpy(cmd)
            else:
                out = check_output(sphinx_cmd, stderr=STDOUT)
                print(out)

            success = True
        except Exception as e:
            print("Failed to run make html: error was {}".format(e))
            success = False

    if not success:
        return False

    dest = join(PKG_NAME, "doc")
    print("Copying resulting html to {} folder...".format(dest))
    if isdir(dest):
        shutil.rmtree(dest)

    shutil.copytree(join("docs", "build", target_format), dest)
    if remove_source_code:
        print("Removing documentation files containing source code...")
        shutil.rmtree(join(dest, "_modules"))

    print("Successfully updated {} with newest version of the documentation"
          ".".format(dest))
    return True


def regenerate_api_files(config_fname=ENV_CONFIG_FILE_PY27, edm_platform=None):
    """ Utility to generate API files from source code using sphinx-apidoc.
    """
    print("Generating API rst files...")
    pyenv = _get_python_environment(edm_platform, config_fname=config_fname)

    target_dir = join("docs", "source", "api")
    if isdir(target_dir):
        shutil.rmtree(target_dir)

    files_to_exclude = []
    files_to_exclude += glob.glob(join(PKG_NAME, "*", "tests", "*.py"))
    files_to_exclude += glob.glob(join(PKG_NAME, "*", "*", "tests", "*.py"))
    script_glob = join(PKG_NAME, "data", "sample_scripts", "*.py")
    files_to_exclude += glob.glob(script_glob)

    apidoc_options = ['-f', '-M', '-o', target_dir, PKG_NAME] + \
        files_to_exclude

    devenv_dir = pyenv.get_install_dir()
    if IS_WINDOWS:
        executable = [join(devenv_dir, 'python.exe'),
                      join(pyenv.bindir, 'sphinx-apidoc-script.py')]
    else:
        executable = [join(pyenv.bindir, 'sphinx-apidoc')]

    # Note that this is a very long command line command, which overflows the
    # Windows limit, so it needs to be passed as a list rather than a string:
    cmd = executable + apidoc_options
    out = check_output(cmd, stderr=STDOUT)
    print(out)


@task
def run_2to3(config_fname=ENV_CONFIG_FILE_PY27, edm_platform=None):
    pyenv = _get_python_environment(edm_platform, config_fname=config_fname)
    executable = join(pyenv.bindir, "2to3")
    options = ' -W -p -n -o kromatography3 kromatography'
    cmd = executable + options

    try:
        out = check_output(cmd, stderr=STDOUT, shell=True)
        print(out)
    except Exception as e:
        msg = "Failed to run cmd {} with error {}".format(cmd, e)
        print(msg)


###############################################################################
# Utilities
###############################################################################


def get_package_version():
    info = _executed__init__()
    return info['__version__']


def build_python_egg(config_fname=ENV_CONFIG_FILE_PY27, edm_platform=None):
    """ Build a python egg of the current package state.
    """
    clean_egg_artefacts()
    pyenv = _get_python_environment(edm_platform, config_fname=config_fname)
    cmd = "setup.py bdist_egg"
    pyenv.runpy(cmd)


def clean_egg_artefacts(dirs_to_clean=None):
    if dirs_to_clean is None:
        dirs_to_clean = ["build", "{}.egg-info".format(PKG_NAME), EGG_DIR]

    for dir_to_clean in dirs_to_clean:
        if isdir(dir_to_clean):
            print("Removing {}".format(dir_to_clean))
            remove_tree(dir_to_clean)


def get_build_file_path():
    """ Path to the build.txt file in source, wrt the location of setup.py.
    """
    return join(PKG_NAME, "build.txt")


def _executed__init__():
    init_file = join(PKG_NAME, "__init__.py")
    if sys.version_info.major == 2:
        info = {}
        execfile(init_file, info)  # noqa
    else:
        import runpy
        info = runpy.run_path("file.py")
    return info


def get_build_version():
    """ Returns the build number as an integer, from the build.txt file.
    """
    build_file = get_build_file_path()
    with open(build_file, "r") as f:
        return int(f.read())


def get_py_version(config_fname=ENV_CONFIG_FILE_PY27, edm_platform=None):
    """ Extract reduced version (like 3.6) expression for specified environment
    """
    pyenv = _get_python_environment(edm_platform, config_fname=config_fname)
    command = [pyenv.python, "-c", "import sys; print('{}.{}'.format(sys.version_info.major, sys.version_info.minor))"]  # noqa
    out = check_output(command)
    return out.strip()


def _get_python_environment(edm_platform, config_fname=ENV_CONFIG_FILE_PY27,
                            **environment):
    """ Build and return an EDM python environment from specified config file.

    Parameters
    ----------
    edm_platform : str
        String code for the target platform to build the environment for.
        Should be one of "win-x86_64", "win-x86", "rh5-x86_64", "osx-x86_64".

    config_fname : str [OPTIONAL]
        Path to an environment config file containing the name of the EDM
        environment to use. Defaults to ENV_CONFIG_FILE.

    environment : dict [OPTIONAL]
        Additional parameters to build the environment's Configuration
        instance.
    """
    config = Configuration.from_file(config_fname, **environment)
    return PythonEnvironment(config, edm_platform=edm_platform)


@contextmanager
def change_dir_temporarily(temp_path):
    curr_dir = abspath(os.getcwd())
    try:
        os.chdir(temp_path)
        yield
    finally:
        os.chdir(curr_dir)
