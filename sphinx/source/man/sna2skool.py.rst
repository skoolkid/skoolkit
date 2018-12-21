:orphan:

============
sna2skool.py
============

SYNOPSIS
========
``sna2kool.py`` [options] FILE

DESCRIPTION
===========
``sna2skool.py`` converts a binary (raw memory) file or a SNA, SZX or Z80
snapshot into a skool file. The skool file is written to standard output. When
FILE is '-', ``sna2skool.py`` reads from standard input.

OPTIONS
=======
-c, --ctl `FILE`
  Specify a control file to use (which may be '-' for standard input). By
  default, any files whose names start with the input snapshot name (minus
  the .bin, .sna, .szx or .z80 suffix, if any) and end with .ctl will be used,
  if present. This option may be used multiple times.

-e, --end `ADDR`
  Stop disassembling at this address; the default end address is 65536. `ADDR`
  must be a decimal number, or a hexadecimal number prefixed by '0x'.

-H, --hex
  Write hexadecimal addresses and operands in the disassembly.

-I, --ini `param=value`
  Set the value of a configuration parameter (see ``CONFIGURATION``),
  overriding any value found in ``skoolkit.ini``. This option may be used
  multiple times.

-l, --lower
  Write the disassembly in lower case.

-o, --org `ADDR`
  Specify the origin address of a binary (.bin) file; the default origin
  address is 65536 minus the length of the file. `ADDR` must be a decimal
  number, or a hexadecimal number prefixed by '0x'.

-p, --page `PAGE`
  Specify the page (0-7) of a 128K snapshot to map to 49152-65535.

--show-config
  Show configuration parameter values.

-s, --start `ADDR`
  Start disassembling at this address; the default start address is 16384.
  `ADDR` must be a decimal number, or a hexadecimal number prefixed by '0x'.

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

CONFIGURATION
=============
``sna2skool.py`` will read configuration from a file named ``skoolkit.ini`` in
the current working directory or in ``~/.skoolkit``, if present. The recognised
configuration parameters are:

:Base: Write addresses and instruction operands in hexadecimal (``16``) or
  decimal (``10``, the default).
:Case: Write the disassembly in lower case (``1``) or upper case (``2``, the
  default).
:CommentWidthMin: Minimum width of the instruction comment field in the skool
  file (default: ``10``).
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
:InstructionWidth: Minimum width of the instruction field in the skool file
  (default: ``13``).
:LineWidth: Maximum line width of the skool file (default: ``79``).
:ListRefs: When to add a comment that lists routine or entry point referrers:
  never (``0``), if no other comment is defined at the entry point (``1``, the
  default), or always (``2``).
:Ref: Template used to format the comment for a routine with exactly one
  referrer (default: ``Used by the routine at {ref}.``).
:Refs: Template used to format the comment for a routine with two or more
  referrers (default: ``Used by the routines at {refs} and {ref}.``).
:Semicolons: Block types (``b``, ``c``, ``g``, ``i``, ``s``, ``t``, ``u``,
  ``w``) in which comment semicolons are written for instructions that have no
  comment (default: ``c``).
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

4. Convert ``game.szx`` into a skool file, using the skool file template
   ``blocks.sft``:

   |
   |   ``sna2skool.py -T blocks.sft game.szx > game.skool``
