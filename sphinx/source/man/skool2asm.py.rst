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
  Stop converting at this address. `ADDR` must be a decimal number, or a
  hexadecimal number prefixed by '0x'.

-f, --fixes `N`
  Apply fixes; `N` may be one of:

  |
  |   0: None (default)
  |   1: @ofix only
  |   2: @ofix and @bfix
  |   3: @ofix, @bfix and @rfix (implies ``-r``)

-F, --force
  Force conversion of the entire skool file, ignoring any ``@start`` and
  ``@end`` directives.

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
  Set the value of an ASM writer property (see ``ASM WRITER PROPERTIES``). This
  option may be used multiple times.

-q, --quiet
  Be quiet. This option suppresses both the timing information, and the message
  about the AsmWriter class being used, but does not suppress warnings.

-r, --rsub
  Apply safe substitutions (@ssub) and relocatability substitutions (@rsub)
  (implies ``-f 1``).

--show-config
  Show configuration parameter values.

-s, --ssub
  Apply safe substitutions (@ssub).

-S, --start `ADDR`
  Start converting at this address. `ADDR` must be a decimal number, or a
  hexadecimal number prefixed by '0x'.

-u, --upper
  Write the disassembly in upper case.

--var `name=value`
  Define a variable that can be used by the ``@if`` directive and the ``#IF``
  and ``#MAP`` macros. This option may be used multiple times.

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
:Set-property: Set an ASM writer property value (see ``ASM WRITER
  PROPERTIES``), e.g. ``Set-bullet=+``.
:Templates: File from which to read custom ASM templates.
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

ASM WRITER PROPERTIES
=====================
Recognised ASM writer property names and their default values are:

:bullet: the bullet character(s) to use for list items specified in a
  :ref:`LIST` macro (default: ``*``).
:comment-width-min: the minimum width of the instruction comment field
  (default: ``10``).
:crlf: ``1`` to use CR+LF to terminate lines, or ``0`` to use the system
  default (default: ``0``).
:handle-unsupported-macros: how to handle an unsupported macro: ``1`` to expand
  it to an empty string, or ``0`` to exit with an error (default: ``0``).
:indent: the number of spaces by which to indent instructions (default: ``2``).
:instruction-width: the width of the instruction field (default: ``23``).
:label-colons: ``1`` to append a colon to labels, or ``0`` to leave labels
  unadorned (default: ``1``).
:line-width: the maximum width of each line (default: ``79``).
:tab: ``1`` to use a tab character to indent instructions, or ``0`` to use
  spaces (default: ``0``).
:warnings: ``1`` to print any warnings that are produced while writing ASM
  output (after parsing the skool file), or ``0`` to suppress them (default:
  ``1``).
:wrap-column-width-min: the minimum width of a wrappable table column (default:
  ``10``).

Property values may be set in ``skoolkit.ini`` by using the ``Set-property``
configuration parameter (see ``CONFIGURATION``), or on the command line by
using the ``--set`` option.

EXAMPLES
========
1. Convert ``game.skool`` into an ASM file named ``game.asm``:

   |
   |   ``skool2asm.py game.skool > game.asm``

2. Convert ``game.skool`` into an ASM file, applying @ssub substitutions and
   creating default labels for unlabelled instructions in the process:

   |
   |   ``skool2asm.py -s -c game.skool > game.asm``
