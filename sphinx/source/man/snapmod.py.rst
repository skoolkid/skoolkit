:orphan:

==========
snapmod.py
==========

SYNOPSIS
========
``snapmod.py`` [options] infile [outfile]

DESCRIPTION
===========
``snapmod.py`` modifies the registers and RAM in an SZX or Z80 snapshot.

OPTIONS
=======
-m, --move `[s:]src,size,[d:]dest`
  Copy a block of bytes of the given size from 'src' in RAM bank 's' to 'dest'
  in RAM bank 'd'. This option may be used multiple times. 'src', 'size' and
  'dest' must each be a decimal number, or a hexadecimal number prefixed by
  '0x'.

-p, --poke `[p:]a[-b[-c]],[^+]v`
  POKE N,v in RAM bank p for N in {a, a+c, a+2c..., b}. Prefix 'v' with '^' to
  perform an XOR operation, or '+' to perform an ADD operation. This option may
  be used multiple times. 'a', 'b', 'c' and 'v' must each be a decimal number,
  or a hexadecimal number prefixed by '0x'.

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

|
|  ``7ffd``    - last OUT to port 0x7ffd (128K only)
|  ``ay[N]``   - contents of AY register N (N=0-15; 128K only)
|  ``border``  - border colour
|  ``fe``      - last OUT to port 0xfe (SZX only)
|  ``fffd``    - last OUT to port 0xfffd (128K only)
|  ``iff``     - interrupt flip-flop: 0=disabled, 1=enabled
|  ``im``      - interrupt mode
|  ``issue2``  - issue 2 emulation: 0=disabled, 1=enabled
|  ``tstates`` - T-states elapsed since start of frame

EXAMPLES
========
1. Set the value of the HL register pair to 0 in ``game.z80``:

   |
   |   ``snapmod.py -r hl=0 game.z80``

2. POKE the value 23 into address 32768 in ``game.szx``, and write the
   resultant snapshot to ``poked.szx``:

   |
   |   ``snapmod.py -p 32768,23 game.szx poked.szx``
