:orphan:

==========
tapinfo.py
==========

SYNOPSIS
========
``tapinfo.py`` [options] FILE

DESCRIPTION
===========
``tapinfo.py`` shows information on the blocks in a PZX, TAP or TZX file.

OPTIONS
=======
-b, --basic `N[,A]`
  List the BASIC program in block number `N` loaded at address `A` (default
  23755). `A` must be a decimal number, or a hexadecimal number prefixed by
  '0x'.

-d, --data
  Show the entire contents of header and data blocks.

--tape-start `BLOCK`
  Start at this tape block number.

--tape-stop `BLOCK`
  Stop at this tape block number.

-V, --version
  Show the SkoolKit version number and exit.

EXAMPLES
========
1. Show information on all the blocks in ``game.tzx``:

|
|   ``tapinfo.py game.tzx``

2. List the BASIC program in the second block in ``game.tap``:

|
|   ``tapinfo.py -b 2 game.tap``
