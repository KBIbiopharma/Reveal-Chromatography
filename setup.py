from os.path import abspath, dirname, isfile, join
from setuptools import setup, find_packages
from glob import glob

HERE = dirname(abspath(__file__))

PKG_NAME = "kromatography"

info = {}
init_file = join(HERE, PKG_NAME, "__init__.py")
exec(open(init_file).read(), globals(), info)


def read(fname):
    """ Returns content of the passed file.
    """
    return open(join(HERE, fname)).read()


# Build package data ----------------------------------------------------------
# Documentation files
html_doc_source_files = glob(join(PKG_NAME, "doc", "*.html"))
html_doc_api_files = glob(join(PKG_NAME, "doc", "api", "*.html"))
html_doc_files = glob(join(PKG_NAME, "doc", "*.html"))
html_doc_files += glob(join(PKG_NAME, "doc", "*.inv"))
html_doc_files += glob(join(PKG_NAME, "doc", "*.js"))
html_doc_static_files = glob(join(PKG_NAME, "doc", "_static", "*.*"))
html_doc_image_files = glob(join(PKG_NAME, "doc", "_images", "*.*"))
html_doc_download_files = glob(join(PKG_NAME, "doc", "_downloads", "*.*"))
html_doc_txt_source_files = glob(join(PKG_NAME, "doc", "_sources", "*.txt"))
html_doc_txt_api_files = glob(join(PKG_NAME, "doc", "_sources", "api",
                                   "*.txt"))

# Sample input files. Only collect the most recent version:
path_to_tutorial_data = join(PKG_NAME, "data", "tutorial_data")
tutorial_files = []
for ext in ["*.xlsx", "*.asc", "*.chrom"]:
    tutorial_files += glob(join(path_to_tutorial_data, ext))

# build.txt if any
build_fname = join(PKG_NAME, "build.txt")
build_number_files = []
if isfile(build_fname):
    build_number_files.append(build_fname)

# Application image files -----------------------------------------------------
ui_images_files = glob(join(PKG_NAME, "ui", "images", "*.png"))
ui_task_images_files = glob(join(PKG_NAME, "ui", "tasks", "images", "*.png"))
ui_task_images_files += [join(PKG_NAME, "ui", "tasks", "images",
                              "image_LICENSE.txt")]
ui_app_images_files = glob(join(PKG_NAME, "app", "images", "*.png"))

setup(
    name=PKG_NAME,
    version=info["__version__"],
    author='KBI Biopharma Inc',
    author_email='reveal-support@kbibiopharma.com',
    license='GNU GPL',
    url='https://www.kbibiopharma.com/capabilities/services/mechanistic-modeling-optimize-characterize-purification-process',  # noqa
    description='Chromatography modeling tool',
    long_description=read('README.rst'),
    ext_modules=[],
    packages=find_packages(),
    install_requires=[],
    requires=[],
    # Additional data files
    data_files=[
        (".", ["CHANGES.rst", "README.rst", "LICENSE", "ROADMAP.txt"]),
        (PKG_NAME, build_number_files),
        # Documentation files:
        (join(PKG_NAME, "doc"), html_doc_source_files),
        (join(PKG_NAME, "doc", "api"), html_doc_api_files),
        (join(PKG_NAME, "doc"), html_doc_files),
        (join(PKG_NAME, "doc", "_static"), html_doc_static_files),
        (join(PKG_NAME, "doc", "_images"), html_doc_image_files),
        (join(PKG_NAME, "doc", "_downloads"), html_doc_download_files),
        (join(PKG_NAME, "doc", "_sources"), html_doc_txt_source_files),
        (join(PKG_NAME, "doc", "_sources", "api"), html_doc_txt_api_files),  # noqa
        # Sample input data files:
        (path_to_tutorial_data, tutorial_files),
        # Image files:
        (join(PKG_NAME, "ui", "images"), ui_images_files),
        (join(PKG_NAME, "ui", "tasks", "images"), ui_task_images_files),
        (join(PKG_NAME, "app", "images"), ui_app_images_files),
    ],
    entry_points={
        'console_scripts': [
            'reveal-chrom = kromatography.app.main:main',
            'run-cadet = kromatography.app.run_cadet_simulation:main',
        ],
      },
)
