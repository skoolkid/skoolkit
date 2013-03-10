==========
bin2tap.py
==========

----------------------------------------------
convert a binary snapshot file into a TAP file
----------------------------------------------

:Author: rjdymond@gmail.com
:Date: 2012-06-11
:Manual section: 1

SYNOPSIS
========
``bin2tap.py`` [options] FILE.bin

DESCRIPTION
===========
``bin2tap.py`` converts a binary snapshot file (as created by an assembler, or
exported from a Spectrum emulator) into a TAP file.

OPTIONS
=======
-o ORG  Set the origin address (default: 65536 - length of FILE.bin)
-s ADD  Set the start address to JP to (default: `ORG`)
-p STK  Set the stack pointer (default: `ORG`)
-t TAP  Set the TAP filename (default: FILE.tap)

EXAMPLES
========
1. Convert ``game.bin`` into a TAP file named ``game.tap``:

   |
   |   ``bin2tap.py game.bin``

2. Convert ``game.bin`` into a TAP file that starts execution at 32768 when
   loaded:

   |
   |   ``bin2tap.py -s 32768 game.bin``
