:orphan:

==========
sna2ctl.py
==========

SYNOPSIS
========
``sna2ctl.py`` [options] FILE

DESCRIPTION
===========
``sna2ctl.py`` generates a control file for a binary (raw memory) file or a
SNA, SZX or Z80 snapshot. The control file is written to standard output. When
FILE is '-', ``sna2ctl.py`` reads standard input as a binary file.

OPTIONS
=======
-e, --end `ADDR`
  Stop at this address. The default end address is 65536. `ADDR` must be a
  decimal number, or a hexadecimal number prefixed by '0x'.

-h, --hex
  Write upper case hexadecimal addresses.

-I, --ini `param=value`
  Set the value of a configuration parameter (see ``CONFIGURATION``),
  overriding any value found in ``skoolkit.ini``. This option may be used
  multiple times.

-l, --hex-lower
  Write lower case hexadecimal addresses.

-o, --org `ADDR`
  Specify the origin address of a binary file. The default origin address is
  65536 minus the length of the file. `ADDR` must be a decimal number, or a
  hexadecimal number prefixed by '0x'.

-p, --page `PAGE`
  Specify the page (0-7) of a 128K snapshot to map to 49152-65535.

--show-config
  Show configuration parameter values.

-s, --start `ADDR`
  Start at this address. The default start address is 16384. `ADDR` must be a
  decimal number, or a hexadecimal number prefixed by '0x'.

-V, --version
  Show the SkoolKit version number and exit.

CONFIGURATION
=============
``sna2ctl.py`` will read configuration from a file named ``skoolkit.ini`` in
the current working directory or in ``~/.skoolkit``, if present. The recognised
configuration parameters are:

:Dictionary: The name of a file containing a list of allowed words, one per
  line. If specified, a string of characters will be marked as text only if it
  contains at least one of the words in this file.
:Hex: Write addresses in decimal (``0``, the default), lower case hexadecimal
  (``1``),  or upper case hexadecimal (``2``).
:TextChars: Characters eligible for being marked as text (default: letters,
  digits, space, and the following non-alphanumeric characters:
  ``!"$%&\'()*+,-./:;<=>?[]``).
:TextMinLengthCode: The minimum length of a string of characters eligible for
  being marked as text in a block identified as code (default: ``12``).
:TextMinLengthData: The minimum length of a string of characters eligible for
  being marked as text in a block identified as data (default: ``3``).

Configuration parameters must appear in a ``[sna2ctl]`` section. For example,
to make ``sna2ctl.py`` write upper case hexadecimal addresses by default
(without having to use the ``-h`` option on the command line), add the
following section to ``skoolkit.ini``::

  [sna2ctl]
  Hex=2

Configuration parameters may also be set on the command line by using the
``--ini`` option. Parameter values set this way will override any found in
``skoolkit.ini``.

EXAMPLES
========
1. Generate a control file (using rudimentary static code analysis) for
   ``game.z80`` named ``game.ctl``:

   |
   |   ``sna2ctl.py game.z80 > game.ctl``

2. Generate a control file (using a profile produced by the Fuse emulator) for
   ``game.sna`` named ``game.ctl``:

   |
   |   ``sna2ctl.py -m game.profile game.sna > game.ctl``
