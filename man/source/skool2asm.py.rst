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
-V, --version
  Show the SkoolKit version number and exit.

-q, --quiet
  Be quiet. This option suppresses both the timing information, and the message
  about the AsmWriter class being used, but does not suppress warnings.

-w, --no-warnings
  Suppress warnings.

-d, --crlf
  Use CR+LF to end lines, instead of the system default (CR+LF is the default
  on Windows).

-t, --tabs
  Use tab to indent instructions; the default indentation is 2 spaces.

-l, --lower
  Write the disassembly in lower case.

-u, --upper
  Write the disassembly in upper case.

-D, --decimal
  Write the disassembly in decimal.

-H, --hex
  Write the disassembly in hexadecimal.

-i, --inst-width `N`
  Set the width of the instruction field; the default width is 23 characters.

-f, --fixes `N`
  Apply fixes; `N` may be one of:

  |
  |   0: None (default)
  |   1: @ofix only
  |   2: @ofix and @bfix
  |   3: @ofix, @bfix and @rfix (implies ``-r``)

-c, --labels
  Create default labels for unlabelled instructions.

-s, --ssub
  Apply safe substitutions (@ssub).

-r, --rsub
  Apply safe substitutions (@ssub) and relocatability substitutions (@rsub)
  (implies ``-f 1``).

EXAMPLES
========
1. Convert ``game.skool`` into an ASM file named ``game.asm``:

   |
   |   ``skool2asm.py game.skool > game.asm``

2. Convert ``game.skool`` into an ASM file, applying @ssub substitutions and
   creating default labels for unlabelled instructions in the process:

   |
   |   ``skool2asm.py -s -c game.skool > game.asm``
