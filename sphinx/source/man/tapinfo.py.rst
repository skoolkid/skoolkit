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

-B, --basic `N[,A]`
  List the BASIC program in block number `N` loaded at address `A` (default
  23755). `A` must be a decimal number, or a hexadecimal number prefixed by
  '0x'.

-V, --version
  Show the SkoolKit version number and exit.

EXAMPLES
========
1. Show information on the standard speed (0x10) and turbo speed (0x11) data
   blocks only in  ``game.tzx``:

|
|   ``tapinfo.py -b 10,11 game.tzx``

2. List the BASIC program in the second block in ``game.tap``:

|
|   ``tapinfo.py -B 2 game.tap``
