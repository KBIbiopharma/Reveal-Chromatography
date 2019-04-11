*********************
Reveal Chromatography
*********************

This contains the Reveal Chromatography project for exploring and generating
Chromatography data and profiles. This exposes a C++ Chromatography process
simulator, ``CADET`` [0], to generate chromatography simulations and compare
them to experimental results observed in laboratories. Its goal is to provide a
graphical user interface frontend for these explorations.

Other documents
===============

This README details how to use the project. Other documents discuss other
aspect of the project:
 * See the CONTRIBUTING.txt document for how to contribute to this repository.
 * See the RELEASE.txt for details about the evolution of this project.
 * See the ROADMAP.txt document for details about where this project is going.
   To accelerate that effort, and steer the tool in directions you need, please
   contact us at `release-support@kbibiopharma.com`.


Installing Reveal-Chromatography
================================
If you are not a developer, the easiest way to use Reveal Chromatography is to
download a 1-click installed from https://www.kbibiopharma.com/capabilities/services/mechanistic-modeling-optimize-characterize-purification-process .
If you are a developer, see the section below.

Installing Reveal-Chromatography in a development environment
=============================================================
To develop on this project, you need a Python 2.7 environment that contains the
right list of package dependencies. The list of dependencies and their precise
versions are to be found in :file:`deploy/requirement_py27_**_x86_64.txt`,
where the ** should be replaced by the name of the OS you want to run on. Of
course, in addition, this project must also be added to the development
environment by running::

    python setup.py develop

or::

    python setup.py install

using the appropriate python environment. To make sure the installation is
successful, it is recommended to run the entire test suite, using `nose`::

    nosetests -v kromatography

To launch the GUI tool, the entry point is in the :file:`app` sub-package::

    python kromatography/app/main.py

or use the entry point named `reveal-chrom`.

You are report issues using the Github issue tracker or submit contributions to
the code base using Github's Pull Requests. Please review the CONTRIBUTING
document before doing so.


Creating/removing a development environment for EDM users
=========================================================

Bootstrap environment
---------------------

To develop on the PICTS tools, you will need a "bootstrap" python environment
to create the development environment. It will need to be based on Python
version 2.7. That environment can created using Enthought's EDM
(https://www.enthought.com/products/edm/). Note that EDM is an environment
management tool, and a python, so once installed, a 2.7 environment can be
created by running
```bash
edm environments create bootstrap --version 2.7
```
To make subsequent commands easier, it is recommended to add the path to
the new environment to the `PATH` environment variable. For example on
UNIX like systems, the following should be added to the `~/.bashrc` or
`~/.bash_profile`::

     export PATH="~/.edm/envs/bootstrap/bin":$PATH

That environment also will need to contain the following packages: `fabric`,
and `hatcher`::

    edm install hatcher fabric -e bootstrap

Using that environment, you will need create an Enthought (hatcher) token
following [this](http://pythonhosted.org/hatcher/user-guide/getting-started.html#token-authentication) ::

    hatcher -U you@kbibiopharma.com -u https://packages.enthought.com api-tokens create YOUR_NAME

Note that this will require for your email to be registered with
Enthought.

You will also need to edit the EDM file `~/.edm.yaml` to include
`kbi/kromatography` in the list of repositories. Also the following must
be added to the bottom of the file::

  authentication:
      api_token: <YOUR HATCHER TOKER HERE>

After that, you can install `ci-tools` (pulled from the kbi repository):

     edm install ci_tools 0.1.2.dev0-2 -e bootstrap

Note that this will require for your Enthought account to be added
to the list of accounts authorized to see KBI's private repository.


Development environment
-----------------------
Once the bootstrap environment has all the needed dependencies (`fabric`
and `ci-tools`), a python 2.7 development environment can be created
using::

    fab build_devenv


Installing kromatography
========================
Once you have an environment set up, you need to install the Kromatography
project itself into it. First, activate the development environment (see
above). Then you can install the ``Kromatography`` package as a standalone
install or as a development version.

Standalone install
------------------
To install the latest stable release of kromatography, simply activate the
environment (see section above) and run::

    edm install kromatography

To see the list of available versions, run ``edm search kromatography``.

Development install
-------------------
To install Kromatography in the development environment and develop on it,
from the top of the kromatography repository, run::

    ~/.edm/env/kromatography/bin/python setup.py develop

or on Windows, from the HOME directory::

    .edm\envs\kromatography\python.exe setup.py develop

Of course, you can omit the path if the EDM environment has been activated. See
below for uninstalling kromatography.

Generating the documentation
============================
The source files for the documentation are stored in the docs/sources folder. 
After doing some modifications, the HTML documentation can be regenerated, by 
running ``fab build_docs`` from the home folder. That will regenerate the 
docs and copy the webpage structure into the project's ``doc/`` sub-package.

.. note:: If you are generating documentation for an external user, you need
    to delete the HTML files containing the source code from the documentation
    with::

        fab build_docs:remove_source_code=True


Running the application
=======================
Run the GUI application using::

    fab run

Note that this requires that whatever default python on your system has the
fabric package installed.

It is also possible to pass a study file (excel file) to open on startup,
using::

    fab run:PATH/TO/FILE

This is equivalent to invoking the krom_app application launcher automatically
from the devenv python executable::

    ~/.edm/env/kromatography/bin/python kromatography/app/krom_app.py -i PATH/TO/FILE

Uninstalling kromatography
==========================

If you have installed the latest stable release of kromatography, simply
activate the environment (see section above) and run::

    edm environments remove kromatography


Building an MSI installer (Windows only)
========================================

Building an MSI installer relies on an open source tool called WIXToolset [1].
To build an installer refer to the steps described in the ``RELEASE.rst``
document.

Testing
=======
The project contains a unit test suite. It can be run using::

    fab test

[0] https://github.com/modsim/CADET
[1] http://wixtoolset.org/
