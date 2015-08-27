:orphan:

==========
tapinfo.py
==========

SYNOPSIS
========
``tapinfo.py`` [options] FILE

DESCRIPTION
===========
``tapinfo.py`` shows information on the blocks in a TAP or TZX file.

OPTIONS
=======
-b, --tzx-blocks `IDs`
  Show TZX blocks with these IDs only; `IDs` is a comma-separated list of
  hexadecimal block IDs, e.g. 10,11,2a.

-V, --version
  Show the SkoolKit version number and exit.

EXAMPLE
=======
Show information on the standard speed (0x10) and turbo speed (0x11) data
blocks only in  ``game.tzx``:

|
|   ``tapinfo.py -b 10,11 game.tzx``
