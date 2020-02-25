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

-d, --data
  Process @defb, @defs and @defw directives.

-E, --end `ADDR`
  Stop converting at this address. `ADDR` must be a decimal number, or a
  hexadecimal number prefixed by '0x'.

-i, --isub
  Apply @isub directives.

-o, --ofix
  Apply @ofix directives.

-r, --rsub
  Apply @isub, @ssub and @rsub directives (implies ``--ofix``).

-R, --rfix
  Apply @ofix, @bfix and @rfix directives (implies ``--rsub``).

-s, --ssub
  Apply @isub and @ssub directives.

-S, --start `ADDR`
  Start converting at this address. `ADDR` must be a decimal number, or a
  hexadecimal number prefixed by '0x'.

-v, --verbose
  Show info on each converted instruction.

-V, --version
  Show the SkoolKit version number and exit.

-w, --no-warnings
  Suppress warnings.

EXAMPLES
========
1. Convert ``game.skool`` into a binary file named ``game.bin``:

   |
   |   ``skool2bin.py game.skool``

2. Apply @isub and @ofix directives in ``game.skool`` and convert it into a
   binary file named ``game-io.bin``:

   |
   |   ``skool2bin.py -io game.skool game-io.bin``
