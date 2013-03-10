============
skool2asm.py
============

----------------------------------
convert a skool file to ASM format
----------------------------------

:Author: rjdymond@gmail.com
:Date: 2012-06-15
:Manual section: 1

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
-q    Be quiet
-w    Suppress warnings
-d    Use CR+LF to end lines (default on Windows)
-t    Use tab to indent instructions (default indentation is 2 spaces)
-l    Write the disassembly in lower case
-u    Write the disassembly in upper case
-D    Write the disassembly in decimal
-H    Write the disassembly in hexadecimal
-i N  Set instruction field width to `N` (default=23)
-f N  Apply fixes; `N` may be one of:

      |
      |   0: None (default)
      |   1: @ofix only
      |   2: @ofix and @bfix
      |   3: @ofix, @bfix and @rfix (implies ``-r``)
-c    Create default labels for unlabelled instructions
-s    Use safe substitutions (@ssub)
-r    Use relocatability substitutions too (@rsub) (implies ``-f 1``)

EXAMPLES
========
1. Convert ``game.skool`` into an ASM file named ``game.asm``:

   | 
   |   ``skool2asm.py game.skool > game.asm``

2. Convert ``game.skool`` into an ASM file, applying @ssub substitutions and
   creating default labels for unlabelled instructions in the process:

   |
   |   ``skool2asm.py -s -c game.skool > game.asm``
