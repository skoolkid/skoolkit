:orphan:

===========
snapinfo.py
===========

SYNOPSIS
========
``snapinfo.py`` [options] FILE

DESCRIPTION
===========
``snapinfo.py`` shows information on the registers and RAM in a SNA, SZX or Z80
snapshot.

OPTIONS
=======
-b, --basic
  List the BASIC program.

-f, --find `A[,B...[-N]]`
  Search for the byte sequence A,B... with distance N (default=1) between
  bytes.

-p, --peek `A[-B[-C]]`
  Show the contents of addresses A TO B STEP C. This option may be used
  multiple times.

-t, --find-text `TEXT`
  Search for a text string.

-V, --version
  Show the SkoolKit version number and exit.

EXAMPLE
=======
Display the contents of the registers in ``game.z80``:

|
|   ``snapinfo.py game.z80``
