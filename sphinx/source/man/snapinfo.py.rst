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

-f, --find `A[,B...[-M[-N]]]`
  Search for the byte sequence `A`, `B`... with distance ranging from `M` to
  `N` (default=1) between bytes. `A`, `B`, etc. and `M` and `N` must each be a
  decimal number, or a hexadecimal number prefixed by '0x'.

-p, --peek `A[-B[-C]]`
  Show the contents of addresses `A` TO `B` STEP `C`. This option may be used
  multiple times. `A`, `B` and `C` must each be a decimal number, or a
  hexadecimal number prefixed by '0x'.

-t, --find-text `TEXT`
  Search for a text string.

-T, --find-tile `X,Y[-M[-N]]`
  Search for the graphic data of the tile at (X,Y) with distance ranging from M
  to N (default=1) between bytes. `M` and `N` must each be a decimal number, or
  a hexadecimal number prefixed by '0x'.

-v, --variables
  List the contents of the variables area.

-V, --version
  Show the SkoolKit version number and exit.

-w, --word `A[-B[-C]]`
  Show the words (2-byte values) at addresses `A` TO `B` STEP `C`. This option
  may be used multiple times. `A`, `B` and `C` must each be a decimal number,
  or a hexadecimal number prefixed by '0x'.

EXAMPLES
========
1. Display the contents of the registers in ``game.z80``:

|
|   ``snapinfo.py game.z80``

2. Search for the graphic data of the tile currently at (2,3) on screen in
   ``game.z80``, with a distance of 1 or 2 between bytes:

|
|   ``snapinfo.py -T 2,3-1-2 game.z80``
