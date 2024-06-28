:orphan:

==========
bin2tap.py
==========

SYNOPSIS
========
``bin2tap.py`` [options] FILE [OUTFILE]

DESCRIPTION
===========
``bin2tap.py`` converts a binary (raw memory) file or a SNA, SZX or Z80
snapshot into a PZX or TAP file. FILE may be a regular file, or '-' to read a
binary file from standard input. If OUTFILE is not given, a TAP file is
created.

OPTIONS
=======
--7ffd `N`
  Add 128K RAM banks to the tape file and write `N` to port 0x7ffd after
  they've loaded.

--banks `N[,N...]`
  Add only these 128K RAM banks to the tape file (default: 0,1,3,4,6,7).

-b, --begin `BEGIN`
  Begin conversion at this address. The default begin address is the origin
  address (`ORG`) for a binary file, or 16384 for a snapshot. `BEGIN` must be a
  decimal number, or a hexadecimal number prefixed by '0x'.

-c, --clear `N`
  Use a ``CLEAR N`` command in the BASIC loader, and leave the stack pointer
  alone. This option overrides the ``--stack`` option. `N` must be a decimal
  number, or a hexadecimal number prefixed by '0x'.

-e, --end `END`
  End conversion at this address. `END` must be a decimal number, or a
  hexadecimal number prefixed by '0x'.

--loader `ADDR`
  Place the 128K RAM bank loader at this address (default: CLEAR address + 1).
  `ADDR` must be a decimal number, or a hexadecimal number prefixed by '0x'.

-o, --org `ORG`
  Set the origin address for a binary file. The default origin address is 65536
  minus the length of FILE. `ORG` must be a decimal number, or a hexadecimal
  number prefixed by '0x'.

-p, --stack `STACK`
  Set the stack pointer. The default value is `BEGIN`. `STACK` must be a
  decimal number, or a hexadecimal number prefixed by '0x'.

-s, --start `START`
  Set the start address to JP to. The default start address is `BEGIN`. `START`
  must be a decimal number, or a hexadecimal number prefixed by '0x'.

-S, --screen `FILE`
  Add a loading screen to the tape file. `FILE` may be a snapshot or a
  6912-byte SCR file.

-V, --version
  Show the SkoolKit version number and exit.

STACK POINTER
=============
The ROM tape loading routine at 1366 (0x0556) and the load routine used by
``bin2tap.py`` together require 14 bytes for stack operations, and so `STACK`
must be at least 16384+14=16398 (0x400E). This means that if `ORG` is less than
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
Spectrum is 23952 (0x5D90).

128K TAPES
==========
To create a tape file that loads a 128K game, use the ``--7ffd``, ``--begin``
and ``--clear`` options along with a 128K snapshot or a 128K binary file as
input, where:

* ``--7ffd`` specifies the value to write to port 0x7FFD after all the RAM
  banks have loaded and before starting the game
* ``--begin`` specifies the start address of the code/data below 49152 (0xC000)
  to include on the tape
* ``--clear`` specifies the address of the CLEAR command in the BASIC loader

By default, the 128K RAM bank loader (which is 39-45 bytes long, depending on
the number of RAM banks to load) is placed one above the CLEAR address. Use the
``--loader`` option to place it at an alternative address. The lowest usable
address with the ``--clear`` option on a bare 128K Spectrum is 23977 (0x5DA9).

By default, 128K RAM banks 0, 1, 3, 4, 6 and 7 are added to the tape file. If
one or more of these RAM banks are not required, use the ``--banks`` option to
specify a smaller set of RAM banks to add. If none of these RAM banks are
required, use ``,`` (a single comma) as the argument to the ``--banks`` option.
The contents of RAM banks 5 and 2 - from the ``--begin`` address and up to but
not including the ``--end`` address (if given) - are included in the main code
block on the tape.

EXAMPLES
========
1. Convert ``game.bin`` into a TAP file named ``game.tap``:

   |
   |   ``bin2tap.py game.bin``

2. Convert ``game.bin`` into a PZX file that starts execution at 32768 when
   loaded:

   |
   |   ``bin2tap.py -s 32768 game.bin game.pzx``
