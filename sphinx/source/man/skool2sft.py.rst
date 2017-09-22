:orphan:

============
skool2sft.py
============

SYNOPSIS
========
``skool2sft.py`` [options] FILE

DESCRIPTION
===========
``skool2sft.py`` converts a skool file into a skool file template. The skool
file template is written to stdout. When FILE is '-', ``skool2sft.py`` reads
from standard input.

OPTIONS
=======
-b, --preserve-base
  Preserve the base of decimal and hexadecimal values in instruction operands
  and DEFB, DEFM, DEFS and DEFW statements. (By default, only binary values and
  character values are preserved.)

-E, --end `ADDR`
  Stop converting at this address. `ADDR` must be a decimal number, or a
  hexadecimal number prefixed by '0x'.

-h, --hex
  Write addresses in upper case hexadecimal format.

-l, --hex-lower
  Write addresses in lower case hexadecimal format.

-S, --start `ADDR`
  Start converting at this address. `ADDR` must be a decimal number, or a
  hexadecimal number prefixed by '0x'.

-V, --version
  Show the SkoolKit version number and exit.

EXAMPLE
=======
Convert ``game.skool`` into a skool file template named ``game.sft``:

|
|   ``skool2sft.py game.skool > game.sft``
