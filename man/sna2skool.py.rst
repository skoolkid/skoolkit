============
sna2skool.py
============

------------------------------------
convert a snapshot into a skool file
------------------------------------

:Author: rjdymond@gmail.com
:Date: 2013-01-02
:Manual section: 1

SYNOPSIS
========
``sna2kool.py`` [options] FILE

DESCRIPTION
===========
``sna2kool.py`` converts a snapshot (``BIN``, ``SNA``, ``SZX`` or ``Z80`` file)
into a skool file. The skool file is written to stdout.

OPTIONS
=======
-c CTL  Specify the control file to use (default is FILE.ctl)
-T SFT  Specify the skool file template to use (default is FILE.sft)
-g CTL  Generate a control file with this name
-M MAP  Use MAP as a code execution map when generating the control file; maps
        (otherwise known as profiles or traces) produced by the Fuse, SpecEmu,
        Spud, Zero and Z80 emulators are supported
-h      Write hexadecimal addresses in the generated control file
-H      Write hexadecimal addresses and operands in the disassembly
-L      Write the disassembly in lower case
-s ORG  Specify the address at which to start disassembling
-o ORG  Specify the origin address of a ``BIN`` file (default: 65536 - length)
-p PAG  Specify the page (0-7) of a 128K snapshot to map to 49152-65535
-t      Show ASCII text in the comment fields
-r      Don't add comments that list entry point referrers
-n N    Set the maximum number of bytes per DEFB statement to `N` (default: 8)
-m M    Group DEFB blocks by addresses that are divisible by `M`
-z      Write bytes with leading zeroes in DEFB statements
-l L    Set the maximum number of characters per DEFM statement to `L`
        (default: 66)

EXAMPLES
========
1. Convert ``game.z80`` into a skool file named ``game.skool``:

   |
   |   ``sna2skool.py game.z80 > game.skool``

2. Convert ``game.sna`` into a skool file, beginning the disassembly at 24576:

   |
   |   ``sna2skool.py -s 24576 game.sna > game.skool``

3. Convert ``game.z80`` into a skool file, using the control file
   ``blocks.ctl`` to identify code and data blocks:

   |
   |   ``sna2skool.py -c blocks.ctl game.z80 > game.skool``

4. Generate a control file (using rudimentary static code analysis) for
   ``game.z80`` named ``game.ctl`` and use it to produce a corresponding skool
   file:

   |
   |   ``sna2skool.py -g game.ctl game.z80 > game.skool``

5. Generate a control file (using a profile produced by the Fuse emulator) for
   ``game.z80`` named ``game.ctl`` and use it to produce a corresponding skool
   file:

   |
   |   ``sna2skool.py -M game.profile -g game.ctl game.z80 > game.skool``

6. Convert ``game.szx`` into a skool file, using the skool file template
   ``blocks.sft``:

   |
   |   ``sna2skool.py -T blocks.sft game.szx > game.skool``
