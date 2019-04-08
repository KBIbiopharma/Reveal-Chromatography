""" Tests for the utility functions in build_splash module. """

import unittest
from os.path import dirname, isfile, join
from shutil import rmtree
from PIL import Image
from tempfile import mkdtemp

import kromatography
from kromatography.utils.build_splash import build_splash


class TestBuildSplash(unittest.TestCase):

    def test_build_splash(self):
        temp_dir = mkdtemp()
        try:
            target = join(temp_dir, "Splash.png")
            img_path = join(dirname(kromatography.__file__), "ui", "images")
            build_splash(img_path, target)
            assert isfile(target)
            im = Image.open(target)
            self.assertEqual(im.size, (500, 400))
            im.close()
            del im
        finally:
            rmtree(temp_dir)
