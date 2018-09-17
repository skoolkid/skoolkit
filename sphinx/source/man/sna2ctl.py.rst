:orphan:

==========
sna2ctl.py
==========

SYNOPSIS
========
``sna2ctl.py`` [options] FILE

DESCRIPTION
===========
``sna2ctl.py`` generates a control file for a binary (raw memory) file or a
SNA, SZX or Z80 snapshot. The control file is written to standard output. When
FILE is '-', ``sna2ctl.py`` reads standard input as a binary file.

OPTIONS
=======
-e, --end `ADDR`
  Stop at this address. The default end address is 65536. `ADDR` must be a
  decimal number, or a hexadecimal number prefixed by '0x'.

-h, --hex
  Write upper case hexadecimal addresses.

-l, --hex-lower
  Write lower case hexadecimal addresses.

-o, --org `ADDR`
  Specify the origin address of a binary file. The default origin address is
  65536 minus the length of the file. `ADDR` must be a decimal number, or a
  hexadecimal number prefixed by '0x'.

-p, --page `PAGE`
  Specify the page (0-7) of a 128K snapshot to map to 49152-65535.

-s, --start `ADDR`
  Start at this address. The default start address is 16384. `ADDR` must be a
  decimal number, or a hexadecimal number prefixed by '0x'.

-V, --version
  Show the SkoolKit version number and exit.

EXAMPLES
========
1. Generate a control file (using rudimentary static code analysis) for
   ``game.z80`` named ``game.ctl``:

   |
   |   ``sna2ctl.py game.z80 > game.ctl``

2. Generate a control file (using a profile produced by the Fuse emulator) for
   ``game.sna`` named ``game.ctl``:

   |
   |   ``sna2ctl.py -m game.profile game.sna > game.ctl``
