.. _prerequisites:

Prerequisites
=============
Before engaging in developer-type activities with SkoolKit (e.g. building the
documentation from source, or running the unit tests), you will need to install
some extra software:

* `make` (for building the documentation on Linux/\*BSD)
* `distribute` and `pip` (for installing Python packages on Windows)
* `Sphinx` (for building the documentation)
* `nose` (for running unit tests)

Details on how to install this software depending on your platform are given in
the following sections.

Windows
-------

Python version
^^^^^^^^^^^^^^
The recommended version of Python to use in Windows is 2.7; `Sphinx` and `nose`
may not work in Python 3.x.

.. _windowsPath:

Path environment variable
^^^^^^^^^^^^^^^^^^^^^^^^^
It's a good idea to add the Python `Scripts` directory to the ``Path``
environment variable, so that any scripts or other executables installed there
can be run from anywhere by just typing their name at the command prompt. The
`Scripts` directory can be found at `C:\\Python2X\\Scripts` (assuming you have
Python 2.X installed in `C:\\Python2X`).

On most versions of Windows, you can change ``Path`` by right-clicking 'My
Computer', choosing 'Properties', selecting the 'Advanced' tab, and then
clicking the 'Environment Variables' button. ``Path`` will be in the 'System
Variables' section. You will need to exit and restart the command prompt for
the change to take effect. Remember to add a ``;`` after the last item on
``Path`` before adding `C:\\Python2X\\Scripts` to it.

distribute
^^^^^^^^^^
Download `distribute_setup.py` from
`python-distribute.org <http://python-distribute.org/>`__ and run it using the
Python interpreter::

  > C:\Python2X\python distribute_setup.py

This will download and install `distribute`. `distribute` includes the
`easy_install` script, which can be used to install `pip`::

  > easy_install pip

Sphinx
^^^^^^
To install `Sphinx`, open a command prompt and run the following command::

  > pip install Sphinx

nose
^^^^
To install `nose`, open a command prompt and run the following command::

  > pip install nose

Linux/\*BSD
-----------
make
^^^^
`make` is available in Debian, Ubuntu, openSUSE and Fedora in the package
`make`, and will already be installed on FreeBSD, NetBSD and OpenBSD systems.

Sphinx
^^^^^^
`Sphinx` is available in Debian, Ubuntu and Fedora in the package
`python-sphinx`, in openSUSE in the package `python-Sphinx`, and in FreeBSD,
NetBSD and OpenBSD in the package `textproc/py-sphinx`.

nose
^^^^
`nose` is available in Debian, Ubuntu, openSUSE and Fedora in the package
`python-nose`, and in FreeBSD, NetBSD and OpenBSD in the package
`devel/py-nose`.
