:orphan:

============
skool2bin.py
============

SYNOPSIS
========
``skool2bin.py`` [options] file.skool [file.bin]

DESCRIPTION
===========
``skool2bin.py`` converts a skool file into a binary (raw memory) file.
'file.skool' may be a regular file, or '-' for standard input. If 'file.bin' is
not given, it defaults to the name of the input file with '.skool' replaced by
'.bin'. 'file.bin' may be a regular file, or '-' for standard output.

OPTIONS
=======
-B, --banks
  Process @bank directives and write RAM banks 0-7 to a 128K file.

-b, --bfix
  Apply @ofix and @bfix directives.

-d, --data
  Process @defb, @defs and @defw directives.

-E, --end `ADDR`
  Stop converting at this address. `ADDR` must be a decimal number, or a
  hexadecimal number prefixed by '0x'.

-I, --ini `param=value`
  Set the value of a configuration parameter (see ``CONFIGURATION``),
  overriding any value found in ``skoolkit.ini``. This option may be used
  multiple times.

-i, --isub
  Apply @isub directives.

-o, --ofix
  Apply @ofix directives.

-r, --rsub
  Apply @isub, @ssub and @rsub directives (implies ``--ofix``).

-R, --rfix
  Apply @ofix, @bfix and @rfix directives (implies ``--rsub``).

--show-config
  Show configuration parameter values.

-s, --ssub
  Apply @isub and @ssub directives.

-S, --start `ADDR`
  Start converting at this address. `ADDR` must be a decimal number, or a
  hexadecimal number prefixed by '0x'.

-v, --verbose
  Show info on each converted instruction.

-V, --version
  Show the SkoolKit version number and exit.

-w, --no-warnings
  Suppress warnings.

CONFIGURATION
=============
``skool2bin.py`` will read configuration from a file named ``skoolkit.ini`` in
the current working directory or in ``~/.skoolkit``, if present. The recognised
configuration parameters are:

  :Banks: Process ``@bank`` directives and write RAM banks 0-7 to a 128K file
    (``1``), or don't (``0``, the default).
  :Data: Process ``@defb``, ``@defs`` and ``@defw`` directives (``1``), or
    don't (``0``, the default).
  :PadLeft: Address at which to start padding the output on the left with
    zeroes. The default value is ``65536``, which produces no padding.
  :PadRight: Address at which to stop padding the output on the right with
    zeroes. The default value is ``0``, which produces no padding.
  :Verbose: Show info on each converted instruction (``1``), or don't (``0``,
    the default).
  :Warnings: Show warnings (``1``, the default), or suppress them (``0``).

Configuration parameters must appear in a ``[skool2bin]`` section. For example,
to make ``skool2bin.py`` suppress warnings (without having to use the ``-w``
option on the command line), add the following section to ``skoolkit.ini``::

  [skool2bin]
  Warnings=0

Configuration parameters may also be set on the command line by using the
``--ini`` option. Parameter values set this way will override any found in
``skoolkit.ini``.

EXAMPLES
========
1. Convert ``game.skool`` into a binary file named ``game.bin``:

   |
   |   ``skool2bin.py game.skool``

2. Apply @isub and @ofix directives in ``game.skool`` and convert it into a
   binary file named ``game-io.bin``:

   |
   |   ``skool2bin.py -io game.skool game-io.bin``
