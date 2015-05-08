:orphan:

============
sna2skool.py
============

SYNOPSIS
========
``sna2kool.py`` [options] FILE

DESCRIPTION
===========
``sna2kool.py`` converts a binary (raw memory) file or a SNA, SZX or Z80
snapshot into a skool file. The skool file is written to stdout.

OPTIONS
=======
-c, --ctl `FILE`
  Specify the control file to use. By default, any control file whose name
  (minus the .ctl suffix) matches the input snapshot name (minus
  the .bin, .sna, .szx or .z80 suffix, if any) will be used, if present.

-e, --end `ADDR`
  Stop disassembling at this address; the default end address is 65536.

-g, --generate-ctl `FILE`
  Generate a control file in `FILE`.

-h, --ctl-hex
  Write upper case hexadecimal addresses in the generated control file.

-H, --skool-hex
  Write hexadecimal addresses and operands in the disassembly.

-i, --ctl-hex-lower
  Write lower case hexadecimal addresses in the generated control file.

-l, --defm-size `CHARS`
  Set the maximum number of characters that may appear in a DEFM statement; the
  default number is 66.

-L, --lower
  Write the disassembly in lower case.

-m, --defb-mod `MOD`
  Group DEFB blocks by addresses that are divisible by `MOD`.

-M, --map `FILE`
  Specify a code execution map to use when generating a control file. Code
  execution maps produced by the Fuse, SpecEmu, Spud, Zero and Z80 Spectrum
  emulators are supported.

-n, --defb-size `BYTES`
  Set the maximum number of bytes that may appear in a DEFB statement; the
  default number is 8.

-o, --org `ADDR`
  Specify the origin address of a binary (.bin) file; the default origin
  address is 65536 minus the length of the file.

-p, --page `PAGE`
  Specify the page (0-7) of a 128K snapshot to map to 49152-65535.

-r, --no-erefs
  Every routine entry point is decorated with a comment that lists the other
  routines that use it (unless an alternative comment is defined in a control
  file). This option suppresses those comments.

-R, --erefs
  Decorate every routine entry point with a comment that lists the other
  routines that use it; the comment will precede any additional comment defined
  in a control file.

-s, --start `ADDR`
  Start disassembling at this address; the default start address is 16384.

-t, --text
  Show ASCII text in the comment fields of the disassembly.

-T, --sft `FILE`
  Specify the skool file template to use. By default, any skool file template
  whose name (minus the .sft suffix) matches the input snapshot name (minus
  the .bin, .sna, .szx or .z80 suffix, if any) will be used, if present.

-V, --version
  Show the SkoolKit version number and exit.

-w, --line-width `WIDTH`
  Set the maximum line width of the skool file (79 by default). This option has
  no effect when creating a skool file from a skool file template.

-z, --defb-zfill
  Pad decimal values in DEFB statements with leading zeroes.

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
