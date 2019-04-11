""" Top level package to support Reveal Chromatography.
"""
import os
from os.path import dirname, isfile, join
from subprocess import check_output
from collections import namedtuple

from traits.etsconfig.api import ETSConfig  # noqa

# Set the Qt variables:
ETSConfig.toolkit = 'qt4'
os.environ["QT_API"] = "pyside"

__version__ = "1.1.0.dev0"


try:
    _build_file = join(dirname(__file__), "build.txt")
    if isfile(_build_file):
        with open(_build_file) as f:
            __build__ = f.read().strip()
    else:
        # If no build file, we are on a dev machine: display the git hash
        # instead:
        git_hash = check_output("git rev-parse --short HEAD", shell=True)
        __build__ = git_hash.strip()
except Exception as e:
    msg = "Exception while trying to collect the build number. Error was {}"
    print(msg.format(e))
    __build__ = "XX"


# API version of the version:
_VersionInfo = namedtuple("_VersionInfo", ["version", "build"])


def _repr_version_info(self):
    """ __repr__ for a _VersionInfo object. """
    return "version: {}, build: {}".format(self.version, self.build)

_VersionInfo.__repr__ = _repr_version_info

version_info = _VersionInfo(__version__, __build__)
