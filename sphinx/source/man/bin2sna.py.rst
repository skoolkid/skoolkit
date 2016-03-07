:orphan:

==========
bin2sna.py
==========

SYNOPSIS
========
``bin2sna.py`` [options] file.bin [file.z80]

DESCRIPTION
===========
``bin2sna.py`` converts a binary (raw memory) file into a Z80 snapshot. If
'file.z80' is not given, it defaults to the name of the input file with '.bin'
replaced by '.z80'.

OPTIONS
=======
-o, --org `ORG`
  Set the origin address. The default origin address is 65536 minus the length
  of file.bin.

-V, --version
  Show the SkoolKit version number and exit.

EXAMPLES
========
1. Convert ``game.bin`` into a Z80 snapshot named ``game.z80``:

   |
   |   ``bin2sna.py game.bin``

2. Convert ``ram.bin`` into a Z80 snapshot named ``game.z80``:

   |
   |   ``bin2tap.py ram.bin game.z80``
