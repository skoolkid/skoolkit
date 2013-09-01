Installing and using SkoolKit
=============================

Requirements
------------
SkoolKit requires `Python <http://www.python.org/>`_ 2.7 or 3.2+. If you're
running Linux or one of the BSDs, you probably already have Python installed.
If you're running Windows, you can get Python
`here <http://www.python.org/download/>`_.

Installation
------------
There are various ways to install the latest stable release of SkoolKit:

* from the zip archive or tarball available at
  `pyskool.ca <http://pyskool.ca/?page_id=177>`_
* from the DEB package or RPM package available at `pyskool.ca`_
* from `PyPI <https://pypi.python.org/pypi/skoolkit>`_ by using
  `easy_install <https://pythonhosted.org/setuptools/easy_install.html>`_ or
  `pip <http://www.pip-installer.org/>`_
* from the `SkoolKit PPA <https://launchpad.net/~rjdymond/+archive/ppa>`_ for
  Ubuntu

If you choose the zip archive or tarball, note that SkoolKit can be used
wherever it is unpacked: it does not need to be installed in any particular
location. However, if you would like to install SkoolKit as a Python package,
you can do so by using the supplied ``setup.py`` script.

Windows
^^^^^^^
To install SkoolKit as a Python package on Windows, open a command prompt,
change to the directory where SkoolKit was unpacked, and run the following
command::

  > setup.py install

This should install the SkoolKit command scripts in `C:\\Python27\\Scripts`
(assuming you have installed Python in `C:\\Python27`), which means you can
run them from anywhere (assuming you have added `C:\\Python27\\Scripts` to the
``Path`` environment variable).

Linux/\*BSD
^^^^^^^^^^^
To install SkoolKit as a Python package on Linux/\*BSD, open a terminal window,
change to the directory where SkoolKit was unpacked, and run the following
command as root::

  # ./setup.py install

This should install the SkoolKit command scripts in `/usr/local/bin` (or some
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
Linux/\*BSD, a dot-slash (``./``) prefix should be added to ``some-script.py``
if it is being run from the current working directory.
