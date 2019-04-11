# -*- coding: utf-8 -*-
""" Script to build a new splash screen image based on the current version of
the Kromatography application.
"""
from __future__ import print_function, division
from PIL import Image, ImageDraw, ImageFont
from os.path import abspath, dirname, join
import sys
import logging

from app_common.std_lib.sys_utils import IS_WINDOWS, IS_OSX

import kromatography
from kromatography.ui.branding import SPLASH_CONTENT

logger = logging.getLogger(__name__)


def simplify_version(version):
    return ".".join(version.split(".")[:2])


def build_splash(img_path, target_filepath):
    """ Generate a new splash screen for the Kromatography application.

    Parameters
    ----------
    img_path : str
        Path to the images/ folder with all logos and resources.

    target_filepath : str
        Path to the file to create.
    """
    splash_width = 500
    splash_height = 400
    splash_margin = 20

    product_logo = Image.open(join(img_path, 'RevealChromLogo.png'))
    ratio = product_logo.size[1] / product_logo.size[0]
    width = splash_width - 2 * splash_margin
    product_logo = product_logo.resize((width, int(ratio * width)),
                                       resample=Image.LANCZOS)
    background = (225, 225, 225, 255)  # Gray
    kbi_blue = (41, 86, 143, 255)

    platform = sys.platform
    if IS_OSX:
        fonts_folder = '/Library/Fonts'
        arial_font = join(fonts_folder, 'arial.ttf')
    elif IS_WINDOWS:
        arial_font = 'arial.ttf'
    else:
        msg = 'Platform {} not supported'.format(platform)
        logger.exception(msg)
        raise NotImplementedError(msg)

    arialFont30 = ImageFont.truetype(arial_font, 30)
    arialFont20 = ImageFont.truetype(arial_font, 20)
    arialFontCopyright = ImageFont.truetype(arial_font, 10)

    im = Image.new('RGBA', (splash_width, splash_height), background)

    draw = ImageDraw.Draw(im)

    pkg_version = simplify_version(kromatography.__version__)
    prod_logo_y = 40
    x = compute_x_to_center(product_logo, splash_width)
    im.paste(product_logo, (x, prod_logo_y), product_logo)
    y = prod_logo_y + product_logo.size[1] + 30
    x = splash_width // 2 - 80
    version_font = arialFont30

    draw.text((x, y), 'Version ' + pkg_version, fill=kbi_blue,
              font=version_font)

    # Add KBI logo
    kbi_logo_y = y + 80
    kbi_logo_width = 220
    x = splash_width - kbi_logo_width - splash_margin
    kbi_logo = Image.open(join(img_path, 'KBILogo.png'))
    ratio = kbi_logo.size[1] / kbi_logo.size[0]
    kbi_logo = kbi_logo.resize((kbi_logo_width, int(ratio * kbi_logo_width)),
                               resample=Image.LANCZOS)
    im.paste(kbi_logo, (x, kbi_logo_y), kbi_logo)

    # Add fine prints/copyright information
    draw.text((splash_margin, splash_height - 40 - 20), SPLASH_CONTENT,
              fill='black', font=arialFontCopyright)

    im.save(target_filepath)
    print("New version of the splash screen generated at "
          "{}".format(target_filepath))


def compute_x_to_center(img, full_width):
    """ Computes the position of an image to be centered.

    Parameters
    ----------
    img : Image
        image object to paste centered

    full_width : Int
        Size of the screen to paste into.

    Returns
    -------
    int: x position to paste the image.
    """
    return full_width // 2 - img.size[0] // 2


if __name__ == "__main__":
    target = abspath(join(".", "Splash.png"))
    img_path = join(dirname(kromatography.__file__), "ui", "images")
    build_splash(img_path, target)
