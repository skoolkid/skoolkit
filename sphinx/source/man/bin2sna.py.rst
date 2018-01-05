:orphan:

==========
bin2sna.py
==========

SYNOPSIS
========
``bin2sna.py`` [options] file.bin [file.z80]

DESCRIPTION
===========
``bin2sna.py`` converts a binary (raw memory) file into a Z80 snapshot.
'file.bin' may be a regular file, or '-' for standard input. If 'file.z80' is
not given, it defaults to the name of the input file with '.bin' replaced by
'.z80', or 'program.z80' if reading from standard input.

OPTIONS
=======
-b, --border `BORDER`
  Set the border colour. This option is equivalent to
  ``--state border=BORDER``. The default border colour is 7 (white).

-o, --org `ORG`
  Set the origin address. The default origin address is 65536 minus the length
  of file.bin. `ORG` must be a decimal number, or a hexadecimal number prefixed
  by '0x'.

-p, --stack `STACK`
  Set the stack pointer. This option is equivalent to ``--reg sp=STACK``. The
  default value is `ORG`. `STACK` must be a decimal number, or a hexadecimal
  number prefixed by '0x'.

-P, --poke `a[-b[-c]],[^+]v`
  POKE N,v for N in {a, a+c, a+2c..., b}. Prefix 'v' with '^' to perform an
  XOR operation, or '+' to perform an ADD operation. This option may be used
  multiple times. 'a', 'b', 'c' and 'v' must each be a decimal number, or a
  hexadecimal number prefixed by '0x'.

-r, --reg `name=value`
  Set the value of a register. Do ``--reg help`` for more information, or see
  the section on ``REGISTERS`` below. This option may be used multiple times.

-s, --start `START`
  Set the address at which to start execution when the snapshot is loaded. This
  option is equivalent to ``--reg pc=START``. The default start address is
  `ORG`. `START` must be a decimal number, or a hexadecimal number prefixed by
  '0x'.

-S, --state `name=value`
  Set a hardware state attribute. Do ``--state help`` for more information, or
  see the section on ``HARDWARE STATE`` below. This option may be used multiple
  times.

-V, --version
  Show the SkoolKit version number and exit.

REGISTERS
=========
The ``--reg`` option sets the value of a register in the snapshot.

|
|  ``--reg name=value``

For example:

|
|  ``--reg hl=32768``
|  ``--reg b=0x1f``

To set the value of an alternate (shadow) register, use the '^' prefix:

|
|  ``--reg ^hl=10072``

Recognised register names are:

|
|  ``^a``, ``^b``, ``^bc``, ``^c``, ``^d``, ``^de``, ``^e``, ``^f``, ``^h``, ``^hl``, ``^l``,
|  ``a``, ``b``, ``bc``, ``c``, ``d``, ``de``, ``e``, ``f``, ``h``, ``hl``, ``l``,
|  ``i``, ``ix``, ``iy``, ``pc``, ``r``, ``sp``

HARDWARE STATE
==============
The ``--state`` option sets a hardware state attribute.

|
|  ``--state name=value``

Recognised attribute names are:

``border``
  border colour

``iff``
  interrupt flip-flop: 0=disabled, 1=enabled

``im``
  interrupt mode

EXAMPLES
========
1. Convert ``game.bin`` into a Z80 snapshot named ``game.z80``:

   |
   |   ``bin2sna.py game.bin``

2. Convert ``ram.bin`` into a Z80 snapshot named ``game.z80`` that starts
   execution at 32768:

   |
   |   ``bin2sna.py -s 32768 ram.bin game.z80``
