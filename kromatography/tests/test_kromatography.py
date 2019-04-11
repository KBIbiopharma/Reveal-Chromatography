import os
import sys
from os.path import dirname, isfile, join
from contextlib import contextmanager
from unittest import TestCase

HERE = dirname(__file__)

BUILD_FILE_PATH = join(HERE, "..", "build.txt")


@contextmanager
def temp_delete_build_file():
    """ Save the content of the build file if it exists, delete the file and
    make sure that it gets reset to its original content after context manager
    is used.
    """
    if isfile(BUILD_FILE_PATH):
        build_content = open(BUILD_FILE_PATH).read()
        os.remove(BUILD_FILE_PATH)
    else:
        build_content = None

    try:
        yield
    finally:
        if build_content:
            with open(BUILD_FILE_PATH, "w") as f:
                f.write(build_content)
        else:
            if isfile(BUILD_FILE_PATH):
                os.remove(BUILD_FILE_PATH)


class TestBuildNumber(TestCase):

    def test_build_number_without_build_num(self):
        with temp_delete_build_file():
            sys.modules.pop('kromatography', None)
            from kromatography import __build__
            # No file: we read the git hash
            self.assertGreaterEqual(len(__build__), 7)

    def test_build_number_with_build_file(self):
        with temp_delete_build_file():
            with open(BUILD_FILE_PATH, "w") as f:
                f.write("45\n")

            # Make sure that kromatography module isn't already loaded:
            sys.modules.pop('kromatography', None)
            from kromatography import __build__
            self.assertEqual(__build__, "45")


class TestVersionNumber(TestCase):

    def test_version_number(self):
        from kromatography import __version__
        self.assertIsInstance(__version__, basestring)


class TestTarget(TestCase):

    def test_version_number(self):
        from kromatography import __target__
        self.assertIn(__target__, ["INTERNAL", "EXTERNAL"])
