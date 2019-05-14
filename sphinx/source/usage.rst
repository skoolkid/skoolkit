Installing and using SkoolKit
=============================

Requirements
------------
SkoolKit requires `Python <https://www.python.org>`_ 3.4+. If you're running
Linux or one of the BSDs, you probably already have Python installed. If you're
running Windows, you can get Python `here <https://www.python.org/downloads>`_.

Installation
------------
There are various ways to install the latest stable release of SkoolKit:

* from the zip archive or tarball available at `skoolkit.ca`_
* from `PyPI`_ by using `pip`_
* from the `PPA`_ for Ubuntu
* from the `copr repo`_ for Fedora

If you choose the zip archive or tarball, note that SkoolKit can be used
wherever it is unpacked: it does not need to be installed in any particular
location. However, if you would like to install SkoolKit as a Python package,
you can do so by using the supplied ``setup.py`` script.

.. _skoolkit.ca: https://skoolkit.ca/?page_id=177
.. _PyPI: https://pypi.org/project/skoolkit/
.. _pip: https://pip.pypa.io/
.. _PPA: https://launchpad.net/~rjdymond/+archive/ppa
.. _copr repo: https://copr.fedorainfracloud.org/coprs/rjdymond/SkoolKit/

Windows
^^^^^^^
To install SkoolKit as a Python package on Windows, open a command prompt,
change to the directory where SkoolKit was unpacked, and run the following
command::

  > setup.py install

This will install the SkoolKit command scripts in `C:\\Python36\\Scripts`
(assuming you have installed Python in `C:\\Python36`), which means you can
run them from anywhere (assuming you have added `C:\\Python36\\Scripts` to the
``Path`` environment variable).

Linux/\*BSD
^^^^^^^^^^^
To install SkoolKit as a Python package on Linux/\*BSD, open a terminal window,
change to the directory where SkoolKit was unpacked, and run the following
command as root::

  # ./setup.py install

This will install the SkoolKit command scripts in `/usr/local/bin` (or some
other suitable location in your ``PATH``), which means you can run them from
anywhere.

Linux/\*BSD v. Windows command line
-----------------------------------
Throughout this documentation, commands that must be entered in a terminal
window ('Command Prompt' in Windows) are shown on a line beginning with a
dollar sign (``$``), like this::

  $ some-script.py some arguments

On Windows, and on Linux/\*BSD if SkoolKit has been installed as a Python
package (see above), the commands may be entered exactly as they are shown. On
Linux/\*BSD, use a dot-slash prefix (e.g. ``./some-script.py``) if the script
is being run from the current working directory.
