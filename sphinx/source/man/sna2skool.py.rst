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
snapshot into a skool file. The skool file is written to standard output. When
FILE is '-', ``sna2skool.py`` reads from standard input.

OPTIONS
=======
-c, --ctl `FILE`
  Specify the control file to use (which may be '-' for standard input). By
  default, any control file whose name (minus the .ctl suffix) matches the
  input snapshot name (minus the .bin, .sna, .szx or .z80 suffix, if any) will
  be used, if present.

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

-I, --ini `param=value`
  Set the value of a configuration parameter (see ``CONFIGURATION``),
  overriding any value found in ``skoolkit.ini``. This option may be used
  multiple times.

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
  Specify the skool file template to use (which may be '-' for standard input).
  By default, any skool file template whose name (minus the .sft suffix)
  matches the input snapshot name (minus the .bin, .sna, .szx or .z80 suffix,
  if any) will be used, if present.

-V, --version
  Show the SkoolKit version number and exit.

-w, --line-width `WIDTH`
  Set the maximum line width of the skool file (79 by default). This option has
  no effect when creating a skool file from a skool file template.

-z, --defb-zfill
  Pad decimal values in DEFB statements with leading zeroes.

CONFIGURATION
=============
``sna2skool.py`` will read configuration from a file named ``skoolkit.ini`` in
the current working directory or in ``~/.skoolkit``, if present. The recognised
configuration parameters are:

:Base: Write addresses and instruction operands in hexadecimal (``16``) or
  decimal (``10``, the default).
:Case: Write the disassembly in lower case (``1``) or upper case (``2``, the
  default).
:CtlHex: Write addresses in a generated control file in decimal (``0``, the
  default), lower case hexadecimal (``1``), or upper case hexadecimal (``2``).
:DefbMod: Group DEFB blocks by addresses that are divisible by this number
  (default: ``1``).
:DefbSize: Maximum number of bytes per DEFB statement (default: ``8``).
:DefbZfill: Pad decimal values in DEFB statements with leading zeroes (``1``),
  or leave them unpadded (``0``, the default).
:DefmSize: Maximum number of characters in a DEFM statement (default: ``66``).
:EntryPointRef: Template used to format the comment for an entry point with
  exactly one referrer (default: ``This entry point is used by the routine at
  {ref}.``).
:EntryPointRefs: Template used to format the comment for an entry point with
  two or more referrers (default: ``This entry point is used by the routines at
  {refs} and {ref}.``).
:LineWidth: Maximum line width of the skool file (default: ``79``).
:ListRefs: When to add a comment that lists routine or entry point referrers:
  never (``0``), if no other comment is defined at the entry point (``1``, the
  default), or always (``2``).
:Ref: Template used to format the comment for a routine with exactly one
  referrer (default: ``Used by the routine at {ref}.``).
:Refs: Template used to format the comment for a routine with two or more
  referrers (default: ``Used by the routines at {refs} and {ref}.``).
:Text: Show ASCII text in the comment fields (``1``), or don't (``0``, the
  default).
:Title-b: Template used to format the title for an untitled 'b' block (default:
  ``Data block at {address}``).
:Title-c: Template used to format the title for an untitled 'c' block (default:
  ``Routine at {address}``).
:Title-g: Template used to format the title for an untitled 'g' block (default:
  ``Game status buffer entry at {address}``).
:Title-i: Template used to format the title for an untitled 'i' block (default:
  ``Ignored``).
:Title-s: Template used to format the title for an untitled 's' block (default:
  ``Unused``).
:Title-t: Template used to format the title for an untitled 't' block (default:
  ``Message at {address}``).
:Title-u: Template used to format the title for an untitled 'u' block (default:
  ``Unused``).
:Title-w: Template used to format the title for an untitled 'w' block (default:
  ``Data block at {address}``).

Configuration parameters must appear in a ``[sna2skool]`` section. For example,
to make ``sna2skool.py`` generate hexadecimal skool files with a line width of
120 characters by default (without having to use the ``-H`` and ``-w`` options
on the command line), add the following section to ``skoolkit.ini``::

  [sna2skool]
  Base=16
  LineWidth=120

Configuration parameters may also be set on the command line by using the
``--ini`` option. Parameter values set this way will override any found in
``skoolkit.ini``.

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
