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
-w X  Write only these elements, where `X` is one or more of:

      |
      |   ``b`` = block types and addresses
      |   ``t`` = block titles
      |   ``d`` = block descriptions
      |   ``r`` = registers
      |   ``m`` = mid-block comments and block end comments
      |   ``s`` = sub-block types and addresses
      |   ``c`` = instruction-level comments
-h    Write addresses in hexadecimal format
-a    Do not write ASM directives

EXAMPLES
========
1. Convert ``game.skool`` into a control file named ``game.ctl``:

   |
   |   ``skool2ctl.py game.skool > game.ctl``

2. Convert ``game.skool`` into a control file containing only block types,
   addresses and titles:

   |
   |   ``skool2ctl.py -w bt -a game.skool > game.ctl``
