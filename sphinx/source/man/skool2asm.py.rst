:orphan:

============
skool2asm.py
============

SYNOPSIS
========
``skool2asm.py`` [options] FILE

DESCRIPTION
===========
``skool2asm.py`` converts a skool file into an ASM file that can be used by a
Z80 assembler. The ASM file is written to standard output. When FILE is '-',
``skool2asm.py`` reads from standard input.

OPTIONS
=======
-c, --create-labels
  Create default labels for unlabelled instructions.

-D, --decimal
  Write the disassembly in decimal.

-E, --end `ADDR`
  Stop converting at this address.

-f, --fixes `N`
  Apply fixes; `N` may be one of:

  |
  |   0: None (default)
  |   1: @ofix only
  |   2: @ofix and @bfix
  |   3: @ofix, @bfix and @rfix (implies ``-r``)

-H, --hex
  Write the disassembly in hexadecimal.

-l, --lower
  Write the disassembly in lower case.

-p, --package-dir
  Show the path to the skoolkit package directory and exit.

-P, --set `property=value`
  Set the value of an ASM writer property; this option may be used multiple
  times.

-q, --quiet
  Be quiet. This option suppresses both the timing information, and the message
  about the AsmWriter class being used, but does not suppress warnings.

-r, --rsub
  Apply safe substitutions (@ssub) and relocatability substitutions (@rsub)
  (implies ``-f 1``).

-s, --ssub
  Apply safe substitutions (@ssub).

-S, --start `ADDR`
  Start converting at this address.

-u, --upper
  Write the disassembly in upper case.

-V, --version
  Show the SkoolKit version number and exit.

-w, --no-warnings
  Suppress warnings.

-W, --writer `CLASS`
  Specify the ASM writer class to use; this will override any @writer directive
  in the skool file.

EXAMPLES
========
1. Convert ``game.skool`` into an ASM file named ``game.asm``:

   |
   |   ``skool2asm.py game.skool > game.asm``

2. Convert ``game.skool`` into an ASM file, applying @ssub substitutions and
   creating default labels for unlabelled instructions in the process:

   |
   |   ``skool2asm.py -s -c game.skool > game.asm``
