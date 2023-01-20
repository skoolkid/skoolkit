:orphan:

========
trace.py
========

SYNOPSIS
========
``trace.py`` [options] FILE

DESCRIPTION
===========
``trace.py`` simulates the execution of machine code in a 48K binary (raw
memory) file or a SNA, SZX or Z80 snapshot. If FILE is '.', no snapshot is
loaded, and the RAM is left blank (all zeroes).

OPTIONS
=======
--audio
  Show a list of the delays (in T-states) between changes in the state of the
  ZX Spectrum speaker made by the code that was executed.

--depth `N`
  Simplify audio delays to this depth (default: 2). When this option is given,
  any sequence of delays up to length `N` that repeats is shown in a simplified
  form. For example, if `N` is 3, the run of delay values [1, 2, 3, 1, 2, 3] is
  reduced to [1, 2, 3]*2.

-D, --decimal
  Show decimal values in verbose (``-v``, ``-vv``) mode.

--dump `FILE`
  Dump a Z80 snapshot to this file after execution.

-i, --interrupts
  Execute interrupt routines.

--max-operations `MAX`
  Maximum number of instructions to execute. Overrides the `STOP` address (if
  given).

--max-tstates `MAX`
  Maximum number of (simulated) T-states to run for. Overrides the `STOP`
  address (if given).

-o, --org `ORG`
  Specify the origin address of a binary (raw memory) file. The default origin
  address is 65536 minus the length of the file. `ORG` must be a decimal
  number, or a hexadecimal number prefixed by '0x'.

-p, --poke `a[-b[-c]],[^+]v`
  POKE N,v for N in {a, a+c, a+2c..., b}. Prefix 'v' with '^' to perform an
  XOR operation, or '+' to perform an ADD operation. This option may be used
  multiple times. 'a', 'b', 'c' and 'v' must each be a decimal number, or a
  hexadecimal number prefixed by '0x'.

-r, --reg `name=value`
  Set the value of a register before execution begins. Do ``--reg help`` for
  more information, or see the section on ``REGISTERS`` below. This option may
  be used multiple times.

--rom `FILE`
  Patch in a ROM at address 0 from this file. By default the 48K ZX Spectrum
  ROM is used.

-s, --start `ADDR`
  Start execution at this address. `ADDR` must be a decimal number, or a
  hexadecimal number prefixed by '0x'. If this option is omitted, execution
  starts either at the address given by the value of the program counter (for a
  SNA, SZX or Z80 snapshot), or at the origin address of the raw memory file.

-S, --stop `ADDR`
  Stop execution at this address. `ADDR` must be a decimal number, or a
  hexadecimal number prefixed by '0x'.

--stats
  Show statistics after execution.

-v, --verbose
  Show executed instructions. Repeat this option (``-vv``) to show register
  values too.

-V, --version
  Show SkoolKit version number and exit.

REGISTERS
=========
The ``--reg`` option sets the value of a register before execution begins.

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

EXAMPLES
========
1. Execute and show instructions in the routine at 32768-32798 in ``game.z80``:

|
|   ``trace.py -v -s 32768 -S 32798 game.z80``

2. Show delays between changes in the state of the ZX Spectrum speaker produced
   by the sound effect routine at 49152-49193 in ``game.z80``:

|
|   ``trace.py --audio -s 49152 -S 49193 game.z80``
