:orphan:

============
skool2bin.py
============

SYNOPSIS
========
``skool2bin.py`` [options] file.skool [file.bin]

DESCRIPTION
===========
``skool2bin.py`` converts a skool file into a binary (raw memory) file.
'file.skool' may be a regular file, or '-' for standard input. If 'file.bin' is
not given, it defaults to the name of the input file with '.skool' replaced by
'.bin'. 'file.bin' may be a regular file, or '-' for standard output.

OPTIONS
=======
-b, --bfix
  Apply @ofix and @bfix directives.

-E, --end `ADDR`
  Stop converting at this address. `ADDR` must be a decimal number, or a
  hexadecimal number prefixed by '0x'.

-i, --isub
  Apply @isub directives.

-o, --ofix
  Apply @ofix directives.

-s, --ssub
  Apply @isub and @ssub directives.

-S, --start `ADDR`
  Start converting at this address. `ADDR` must be a decimal number, or a
  hexadecimal number prefixed by '0x'.

-V, --version
  Show the SkoolKit version number and exit.

EXAMPLE
=======
Convert ``game.skool`` into a binary file named ``game.bin``:

|
|   ``skool2bin.py game.skool``
