:orphan:

==========
bin2tap.py
==========

SYNOPSIS
========
``bin2tap.py`` [options] FILE [file.tap]

DESCRIPTION
===========
``bin2tap.py`` converts a binary (raw memory) file or a SNA, SZX or Z80
snapshot into a TAP file. FILE may be a regular file, or '-' to read a binary
file from standard input.

OPTIONS
=======
-c, --clear `N`
  Use a ``CLEAR N`` command in the BASIC loader, and leave the stack pointer
  alone. This option overrides the ``--stack`` option. `N` must be a decimal
  number, or a hexadecimal number prefixed by '0x'.

-e, --end `ADDR`
  Set the end address when reading a snapshot. `ADDR` must be a decimal number,
  or a hexadecimal number prefixed by '0x'.

-o, --org `ORG`
  Set the origin address; the default origin address is 16384 for a snapshot,
  or 65536 minus the length of FILE for a binary file. `ORG` must be a decimal
  number, or a hexadecimal number prefixed by '0x'.

-p, --stack `STACK`
  Set the stack pointer; the default value is `ORG`. `STACK` must be a decimal
  number, or a hexadecimal number prefixed by '0x'.

-s, --start `START`
  Set the start address to JP to; the default start address is `ORG`. `START`
  must be a decimal number, or a hexadecimal number prefixed by '0x'.

-S, --screen `FILE`
  Add a loading screen to the TAP file. `FILE` may be a snapshot or a 6912-byte
  SCR file.

-V, --version
  Show the SkoolKit version number and exit.

STACK POINTER
=============
The ROM tape loading routine at 1366 ($0556) and the load routine used by
``bin2tap.py`` together require 14 bytes for stack operations, and so `STACK`
must be at least 16384+14=16398 ($400E). This means that if `ORG` is less than
16398, you should use the ``--stack`` option to set the stack pointer to
something appropriate. If the data block overlaps any of the last four bytes of
the stack, ``bin2tap.py`` will replace those bytes with the values required by
the tape loading routine for correct operation upon returning. Stack operations
will overwrite the bytes in the address range `STACK`-14 to `STACK`-1
inclusive, so those addresses should not be used to store essential code or
data.

If the input file contains a program that returns to BASIC, you should use the
``--clear`` option to add a CLEAR command to the BASIC loader. This option
leaves the stack pointer alone, enabling the program to return to BASIC without
crashing. The lowest usable address with the ``--clear`` option on a bare 48K
Spectrum is 23952 ($5D90).

EXAMPLES
========
1. Convert ``game.bin`` into a TAP file named ``game.tap``:

   |
   |   ``bin2tap.py game.bin``

2. Convert ``game.bin`` into a TAP file that starts execution at 32768 when
   loaded:

   |
   |   ``bin2tap.py -s 32768 game.bin``
