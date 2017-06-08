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

-I, --ini `param=value`
  Set the value of a configuration parameter (see ``CONFIGURATION``),
  overriding any value found in ``skoolkit.ini``. This option may be used
  multiple times.

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

CONFIGURATION
=============
``skool2asm.py`` will read configuration from a file named ``skoolkit.ini`` in
the current working directory or in ``~/.skoolkit``, if present. The recognised
configuration parameters are:

:Base: Convert addresses and instruction operands to hexadecimal (``16``) or
  decimal (``10``), or leave them as they are (``0``, the default).
:Case: Write the disassembly in lower case (``1``) or upper case (``2``), or
  leave it as it is (``0``, the default).
:CreateLabels: Create default labels for unlabelled instructions (``1``), or
  don't (``0``, the default).
:Quiet: Be quiet (``1``) or verbose (``0``, the default).
:Set-property: Set an ASM writer property value, e.g. ``Set-bullet=+``.
:Warnings: Show warnings (``1``, the default), or suppress them (``0``).

Configuration parameters must appear in a ``[skool2asm]`` section. For example,
to make ``skool2asm.py`` write the disassembly in hexadecimal with a line width
of 120 characters by default (without having to use the ``-H`` and ``-P``
options on the command line), add the following section to ``skoolkit.ini``::

  [skool2asm]
  Base=16
  Set-line-width=120

Configuration parameters may also be set on the command line by using the
``--ini`` option. Parameter values set this way will override any found in
``skoolkit.ini``.

EXAMPLES
========
1. Convert ``game.skool`` into an ASM file named ``game.asm``:

   |
   |   ``skool2asm.py game.skool > game.asm``

2. Convert ``game.skool`` into an ASM file, applying @ssub substitutions and
   creating default labels for unlabelled instructions in the process:

   |
   |   ``skool2asm.py -s -c game.skool > game.asm``
