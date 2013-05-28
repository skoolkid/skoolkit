Installing and using SkoolKit
=============================

Requirements
------------
SkoolKit requires `Python <http://www.python.org/>`_ 2.7 or 3.1+. If you're
running Linux or one of the BSDs, you probably already have Python installed.
If you're running Windows, you can get Python
`here <http://www.python.org/download/>`_.

Installation
------------
SkoolKit can be used wherever the zip archive or tarball was unpacked - it does
not need to be installed in any particular location. However, if you would like
to install SkoolKit as a Python package, you can do so by using the supplied
``setup.py`` script. After installation, the :ref:`command scripts <commands>`
included in SkoolKit can be run from anywhere, instead of just the directory in
which the SkoolKit zip archive or tarball was unpacked.

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
