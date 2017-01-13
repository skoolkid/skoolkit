:orphan:

============
skool2ctl.py
============

SYNOPSIS
========
``skool2ctl.py`` [options] FILE

DESCRIPTION
===========
``skool2ctl.py`` converts a skool file into a control file. The control file is
written to stdout. When FILE is '-', ``skool2ctl.py`` reads from standard
input.

OPTIONS
=======
-b, --preserve-base
  Preserve the base of decimal and hexadecimal values in instruction operands
  and DEFB, DEFM, DEFS and DEFW statements. (By default, only binary values and
  character values are preserved.)

-E, --end `ADDR`
  Stop converting at this address.

-h, --hex
  Write addresses in upper case hexadecimal format.

-l, --hex-lower
  Write addresses in lower case hexadecimal format.

-S, --start `ADDR`
  Start converting at this address.

-V, --version
  Show the SkoolKit version number and exit.

-w, --write `X`
  Write only these elements, where `X` is one or more of:

  |
  |   ``a`` = ASM directives
  |   ``b`` = block types and addresses
  |   ``t`` = block titles
  |   ``d`` = block descriptions
  |   ``r`` = registers
  |   ``m`` = mid-block comments and block start/end comments
  |   ``s`` = sub-block types and addresses
  |   ``c`` = instruction-level comments

  The default is to write all of these elements.

EXAMPLES
========
1. Convert ``game.skool`` into a control file named ``game.ctl``:

   |
   |   ``skool2ctl.py game.skool > game.ctl``

2. Convert ``game.skool`` into a control file containing only block types,
   addresses and titles:

   |
   |   ``skool2ctl.py -w bt game.skool > game.ctl``
