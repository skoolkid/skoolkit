:orphan:

==========
bin2tap.py
==========

SYNOPSIS
========
``bin2tap.py`` [options] FILE.bin

DESCRIPTION
===========
``bin2tap.py`` converts a binary snapshot file (as created by an assembler, or
exported from a Spectrum emulator) into a TAP file.

OPTIONS
=======
-o, --org `ORG`
  Set the origin address; the default origin address is 65536 minus the length
  of FILE.bin.

-p, --stack `STACK`
  Set the stack pointer; the default value is `ORG`.

-s, --start `START`
  Set the start address to JP to; the default start address is `ORG`.

-t, --tapfile `TAPFILE`
  Set the TAP filename; the default filename is FILE.tap.

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

EXAMPLES
========
1. Convert ``game.bin`` into a TAP file named ``game.tap``:

   |
   |   ``bin2tap.py game.bin``

2. Convert ``game.bin`` into a TAP file that starts execution at 32768 when
   loaded:

   |
   |   ``bin2tap.py -s 32768 game.bin``
