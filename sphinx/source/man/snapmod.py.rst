:orphan:

==========
snapmod.py
==========

SYNOPSIS
========
``snapmod.py`` [options] in.z80 [out.z80]

DESCRIPTION
===========
``snapmod.py`` modifies the registers and RAM in a 48K Z80 snapshot.

OPTIONS
=======
-f, --force
  Overwrite an existing snapshot.

-m, --move `src,size,dest`
  Move a block of bytes of the given size from 'src' to 'dest'. This option may
  be used multiple times. 'src', 'size' and 'dest' must each be a decimal
  number, or a hexadecimal number prefixed by '0x'.

-p, --poke `a[-b[-c]],[^+]v`
  POKE N,v for N in {a, a+c, a+2c..., b}. Prefix 'v' with '^' to perform an
  XOR operation, or '+' to perform an ADD operation. This option may be used
  multiple times. 'a', 'b', 'c' and 'v' must each be a decimal number, or a
  hexadecimal number prefixed by '0x'.

-r, --reg `name=value`
  Set the value of a register. Do ``--reg help`` for more information, or see
  the section on ``REGISTERS`` below. This option may be used multiple times.

-s, --state `name=value`
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
1. Set the value of the HL register pair to 0 in game.z80:

   |
   |   ``snapmod.py -f -r hl=0 game.z80``

2. POKE the value 23 into address 32768 in game.z80, and write the resultant
   snapshot to poked.z80:

   |
   |   ``snapmod.py -p 32768,23 game.z80 poked.z80``
