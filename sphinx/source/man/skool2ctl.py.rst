:orphan:

============
skool2ctl.py
============

SYNOPSIS
========
``skool2ctl.py`` [options] FILE

DESCRIPTION
===========
``skool2ctl.py`` converts a skool file into a control file. The control file is
written to stdout. When FILE is '-', ``skool2ctl.py`` reads from standard
input.

OPTIONS
=======
-b, --preserve-base
  Preserve the base of decimal and hexadecimal values in instruction operands
  and DEFB, DEFM, DEFS and DEFW statements. (By default, only binary values and
  character values are preserved.)

-E, --end `ADDR`
  Stop converting at this address. `ADDR` must be a decimal number, or a
  hexadecimal number prefixed by '0x'.

-h, --hex
  Write addresses in upper case hexadecimal format.

-I, --ini `param=value`
  Set the value of a configuration parameter (see ``CONFIGURATION``),
  overriding any value found in ``skoolkit.ini``. This option may be used
  multiple times.

-k, --keep-lines
  Preserve line breaks in comments.

-l, --hex-lower
  Write addresses in lower case hexadecimal format.

--show-config
  Show configuration parameter values.

-S, --start `ADDR`
  Start converting at this address. `ADDR` must be a decimal number, or a
  hexadecimal number prefixed by '0x'.

-V, --version
  Show the SkoolKit version number and exit.

-w, --write `X`
  Write only these elements, where `X` is one or more of:

  |
  |   ``a`` = ASM directives
  |   ``b`` = block types and addresses
  |   ``t`` = block titles
  |   ``d`` = block descriptions
  |   ``r`` = registers
  |   ``m`` = mid-block comments and block start/end comments
  |   ``s`` = sub-block types and addresses
  |   ``c`` = instruction-level comments

  The default is to write all of these elements.

CONFIGURATION
=============
``skool2ctl.py`` will read configuration from a file named ``skoolkit.ini`` in
the current working directory or in ``~/.skoolkit``, if present. The recognised
configuration parameters are:

:Hex: Write addresses in decimal (``0``, the default), lower case hexadecimal
  (``1``),  or upper case hexadecimal (``2``).
:KeepLines: Preserve line breaks in comments (``1``), or don't (``0``, the
  default).
:PreserveBase: Preserve the base of decimal and hexadecimal values in
  instruction operands and DEFB/DEFM/DEFS/DEFW statements (``1``), or don't
  (``0``, the default).

Configuration parameters must appear in a ``[skool2ctl]`` section. For example,
to make ``skool2ctl.py`` write upper case hexadecimal addresses by default
(without having to use the ``-h`` option on the command line), add the
following section to ``skoolkit.ini``::

  [skool2ctl]
  Hex=2

Configuration parameters may also be set on the command line by using the
``--ini`` option. Parameter values set this way will override any found in
``skoolkit.ini``.

EXAMPLES
========
1. Convert ``game.skool`` into a control file named ``game.ctl``:

   |
   |   ``skool2ctl.py game.skool > game.ctl``

2. Convert ``game.skool`` into a control file containing only block types,
   addresses and titles:

   |
   |   ``skool2ctl.py -w bt game.skool > game.ctl``
