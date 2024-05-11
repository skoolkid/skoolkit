Installing and using SkoolKit
=============================

Requirements
------------
SkoolKit requires `Python <https://www.python.org>`_ 3.8+. If you're running
Linux or one of the BSDs, you probably already have Python installed. If you're
running Windows, you can get Python `here <https://www.python.org/downloads>`_.

Installation
------------
There are various ways to install the latest stable release of SkoolKit:

* from the zip archive or tarball available at `skoolkit.ca`_
* from the zip archive or tarball available at `GitHub`_
* from `PyPI`_ by using `pip`_

If you choose the zip archive or tarball, note that SkoolKit can be used
wherever it is unpacked: it does not need to be installed in any particular
location.

.. _skoolkit.ca: https://skoolkit.ca/skoolkit/
.. _GitHub: https://github.com/skoolkid/skoolkit/releases
.. _PyPI: https://pypi.org/project/skoolkit/
.. _pip: https://pip.pypa.io/

C extension modules
-------------------
If you obtained SkoolKit from a zip archive or tarball, and you want to make
use of the C extension modules (for faster Z80 simulation), then you will need
to build them first. This requires a compiler, the `setuptools`_ package, and
the development headers for the version of Python you're using. Once these are
ready, run the following command in the directory where SkoolKit was unpacked::

  $ python setup.py build_ext -i

You may need to replace the ``python`` in this command with ``python3``,
``py``, or the path to the Python executable, depending on the OS you're using.

To see a list of the compilers that may be used to build the C extension
modules, run the following command::

  $ python setup.py build_ext --help-compiler

.. _setuptools: https://pypi.org/project/setuptools/

Linux/\*BSD v. Windows command line
-----------------------------------
Throughout this documentation, commands that must be entered in a terminal
window ('Command Prompt' in Windows) are shown on a line beginning with a
dollar sign (``$``), like this::

  $ some-script.py some arguments

On Windows, and on Linux/\*BSD if SkoolKit has been installed as a Python
package (using 'pip'), the commands may be entered exactly as they are shown.
On Linux/\*BSD, use a dot-slash prefix (e.g. ``./some-script.py``) if the
script is being run from the current working directory.
