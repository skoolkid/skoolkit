:orphan:

==========
bin2sna.py
==========

SYNOPSIS
========
``bin2sna.py`` [options] file.bin [file.z80]

DESCRIPTION
===========
``bin2sna.py`` converts a binary (raw memory) file into a Z80 snapshot.
'file.bin' may be a regular file, or '-' for standard input. If 'file.z80' is
not given, it defaults to the name of the input file with '.bin' replaced by
'.z80', or 'program.z80' if reading from standard input.

OPTIONS
=======
-b, --border `BORDER`
  Set the border colour. The default border colour is 7 (white).

-o, --org `ORG`
  Set the origin address. The default origin address is 65536 minus the length
  of file.bin.

-p, --stack `STACK`
  Set the stack pointer. The default value is `ORG`.

-s, --start `START`
  Set the address at which to start execution when the snapshot is loaded. The
  default start address is `ORG`.

-V, --version
  Show the SkoolKit version number and exit.

EXAMPLES
========
1. Convert ``game.bin`` into a Z80 snapshot named ``game.z80``:

   |
   |   ``bin2sna.py game.bin``

2. Convert ``ram.bin`` into a Z80 snapshot named ``game.z80`` that starts
   execution at 32768:

   |
   |   ``bin2sna.py -s 32768 ram.bin game.z80``
