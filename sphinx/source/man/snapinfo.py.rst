:orphan:

===========
snapinfo.py
===========

SYNOPSIS
========
``snapinfo.py`` [options] FILE

DESCRIPTION
===========
``snapinfo.py`` shows information on the registers or RAM in a binary (raw
memory) file or a SNA, SZX or Z80 snapshot.

OPTIONS
=======
-b, --basic
  List the BASIC program.

-c, --ctl `FILE`
  Specify a control file to use when generating a call graph. By default, any
  files whose names start with the input snapshot name (minus
  the .bin, .sna, .szx or .z80 suffix, if any) and end with .ctl will be used,
  if present. If `FILE` is '-', standard input is used. This option may be used
  multiple times.

-f, --find `A[,B...[-M[-N]]]`
  Search for the byte sequence `A`, `B`... with distance ranging from `M` to
  `N` (default=1) between bytes. `A`, `B`, etc. and `M` and `N` must each be a
  decimal number, or a hexadecimal number prefixed by '0x'.

-g, --call-graph
  Generate a call graph in DOT format.

-I, --ini `param=value`
  Set the value of a configuration parameter (see ``CONFIGURATION``),
  overriding any value found in ``skoolkit.ini``. This option may be used
  multiple times.

-o, --org `ADDR`
  Specify the origin address of a binary (raw memory) file. The default origin
  address is 65536 minus the length of the file. `ADDR` must be a decimal
  number, or a hexadecimal number prefixed by '0x'.

-p, --peek `A[-B[-C]]`
  Show the contents of addresses `A` TO `B` STEP `C`. This option may be used
  multiple times. `A`, `B` and `C` must each be a decimal number, or a
  hexadecimal number prefixed by '0x'.

--show-config
  Show configuration parameter values.

-t, --find-text `TEXT`
  Search for a text string.

-T, --find-tile `X,Y[-M[-N]]`
  Search for the graphic data of the tile at (X,Y) with distance ranging from M
  to N (default=1) between bytes. `M` and `N` must each be a decimal number, or
  a hexadecimal number prefixed by '0x'.

-v, --variables
  List the contents of the variables area.

-V, --version
  Show the SkoolKit version number and exit.

-w, --word `A[-B[-C]]`
  Show the words (2-byte values) at addresses `A` TO `B` STEP `C`. This option
  may be used multiple times. `A`, `B` and `C` must each be a decimal number,
  or a hexadecimal number prefixed by '0x'.

CONFIGURATION
=============
``snapinfo.py`` will read configuration from a file named ``skoolkit.ini`` in
the current working directory or in ``~/.skoolkit``, if present. The recognised
configuration parameters are:

:NodeLabel: The format of the node labels in a call graph (default:
  ``{address} {address:04X}\n{label}``). This is a standard Python format
  string that recognises the replacement fields ``address`` (the entry address)
  and ``label`` (the label of the first instruction in the entry).

Configuration parameters must appear in a ``[snapinfo]`` section. For example,
to make ``snapinfo.py`` use upper case hexadecimal addresses for call graph
node labels by default, add the following section to ``skoolkit.ini``::

  [snapinfo]
  NodeLabel={address:04X}

Configuration parameters may also be set on the command line by using the
``--ini`` option. Parameter values set this way will override any found in
``skoolkit.ini``.

EXAMPLES
========
1. Display the contents of the registers in ``game.z80``:

|
|   ``snapinfo.py game.z80``

2. Search for the graphic data of the tile currently at (2,3) on screen in
   ``game.z80``, with a distance of 1 or 2 between bytes:

|
|   ``snapinfo.py -T 2,3-1-2 game.z80``
