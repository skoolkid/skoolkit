Building the documentation
==========================

HTML documentation
------------------
In order to build SkoolKit's HTML documentation from the source files included
in the `docs-src` directory in the SkoolKit source distribution, you will need
to install `Sphinx <http://sphinx.pocoo.org/>`_. See :ref:`prerequisites` for
details on how to do that.

Once `Sphinx` is installed, building the HTML documentation can be achieved by
opening a terminal window, changing to the `docs-src` directory, and running
the following command::

  $ make html

Man pages
---------
In order to build the man pages (the sources for which are in the `man`
directory in the SkoolKit source distribution), you will need the `rst2man`
utility (`rst2man.py` on Windows, openSUSE, FreeBSD and NetBSD), which is part
of the Python `docutils` package (`python-docutils` in Debian, Ubuntu, openSUSE
and Fedora; `textproc/py-docutils` in FreeBSD, NetBSD and OpenBSD); `docutils`
should already be installed if you have installed `Sphinx` (see
:ref:`prerequisites`).

Once `rst2man` (or `rst2man.py`) is installed, building the man page for
`skool2html.py` (for example) can be achieved by opening a terminal window,
changing to the `man` directory, and running the following commands::

  $ rst2man skool2html.py.rst man1/skool2html.py.1

The man page can then be viewed thus::

  $ man -M . skool2html.py
