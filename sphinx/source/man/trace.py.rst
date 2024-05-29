:orphan:

========
trace.py
========

SYNOPSIS
========
``trace.py`` [options] FILE [OUTFILE]

DESCRIPTION
===========
``trace.py`` simulates the execution of machine code in a 48K, 128K or +2 SNA,
SZX or Z80 snapshot, or a binary (raw memory) file. If FILE is '48', '128' or
'+2', no snapshot is loaded, and the RAM is left blank (all zeroes). If
'OUTFILE' is given, an SZX/Z80 snapshot or WAV file is written after execution
has completed.

OPTIONS
=======
--audio
  Show a list of the delays (in T-states) between changes in the state of the
  ZX Spectrum speaker made by the code that was executed.

-c, --cmio
  Simulate memory contention and I/O contention delays.

--depth `N`
  Simplify audio delays to this depth (default: 2). When this option is given,
  any sequence of delays up to length `N` that repeats is shown in a simplified
  form. For example, if `N` is 3, the run of delay values [1, 2, 3, 1, 2, 3] is
  reduced to [1, 2, 3]*2.

-D, --decimal
  Show decimal values in verbose (``-v``, ``-vv``) mode.

-I, --ini `param=value`
  Set the value of a configuration parameter (see ``CONFIGURATION``),
  overriding any value found in ``skoolkit.ini``. This option may be used
  multiple times.

-m, --max-operations `MAX`
  Maximum number of instructions to execute. Overrides the `STOP` address (if
  given).

-M, --max-tstates `MAX`
  Maximum number of (simulated) T-states to run for. Overrides the `STOP`
  address (if given).

-n, --no-interrupts
  Don't execute interrupt routines.

-o, --org `ORG`
  Specify the origin address of a binary (raw memory) file. The default origin
  address is 65536 minus the length of the file. `ORG` must be a decimal
  number, or a hexadecimal number prefixed by '0x'.

-p, --poke `[p:]a[-b[-c]],[^+]v`
  POKE N,v in RAM bank p for N in {a, a+c, a+2c..., b} before execution begins.
  Prefix 'v' with '^' to perform an XOR operation, or '+' to perform an ADD
  operation. This option may be used multiple times. 'a', 'b', 'c' and 'v' must
  each be a decimal number, or a hexadecimal number prefixed by '0x'.

--python
  Use the pure Python Z80 simulator even if the C version is available.

-r, --reg `name=value`
  Set the value of a register before execution begins. Do ``--reg help`` for
  more information, or see the section on ``REGISTERS`` below. This option may
  be used multiple times.

--rom `FILE`
  Patch in a ROM at address 0 from this file.

--show-config
  Show configuration parameter values.

-s, --start `ADDR`
  Start execution at this address. `ADDR` must be a decimal number, or a
  hexadecimal number prefixed by '0x'. If this option is omitted, execution
  starts either at the address given by the value of the program counter (for a
  SNA, SZX or Z80 snapshot), or at the origin address of the raw memory file.

-S, --stop `ADDR`
  Stop execution at this address. `ADDR` must be a decimal number, or a
  hexadecimal number prefixed by '0x'.

--state name=value
  Set a hardware state attribute before execution begins. Do ``--state help``
  for more information, or see the section on ``HARDWARE STATE`` below. This
  option may be used multiple times.

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

HARDWARE STATE
==============
The ``--state`` option sets a hardware state attribute before execution begins.

|
|  ``--state name=value``

Recognised attribute names and their default values are:

|
|  ``7ffd``    - last OUT to port 0x7ffd (128K only)
|  ``ay[N]``   - contents of AY register N (N=0-15; 128K only)
|  ``border``  - border colour
|  ``fe``      - last OUT to port 0xfe (SZX only)
|  ``fffd``    - last OUT to port 0xfffd (128K only)
|  ``iff``     - interrupt flip-flop: 0=disabled, 1=enabled
|  ``im``      - interrupt mode
|  ``tstates`` - T-states elapsed since start of frame

CONFIGURATION
=============
``trace.py`` will read configuration from a file named ``skoolkit.ini`` in the
current working directory or in ``~/.skoolkit``, if present. The recognised
configuration parameters are:

  :TraceLine: The format of each instruction line when ``-v`` is used
    (default: ``${pc:04X} {i}``).
  :TraceLine2: The format of each instruction line when ``-vv`` is used. Use
    ``--show-config`` to see the default value.
  :TraceLineDecimal: The format of each instruction line when ``-Dv`` is used
    (default: ``{pc:05} {i}``).
  :TraceLineDecimal2: The format of each instruction line when ``-Dvv`` is
    used. Use ``--show-config`` to see the default value.
  :TraceOperand: The prefix, byte format, and word format for the numeric
    operands of instructions, separated by commas (default: ``$,02X,04X``); the
    byte and word formats are standard Python format specifiers for numeric
    values, and default to empty strings if not supplied.
  :TraceOperandDecimal: As ``TraceOperand`` when ``-D`` is used (default:
    ``,,``).

The ``TraceLine*`` parameters are standard Python format strings that recognise
the following replacement fields:

|
|  ``i`` - the current instruction
|  ``m[address]`` - the contents of a memory address
|  ``pc`` - the address of the current instruction (program counter)
|  ``r[X]`` - the 'X' register (see below)
|  ``t`` - the current timestamp (in T-states)

When using the ``m`` (memory) replacement field, ``address`` must be either a
decimal number, or a hexadecimal number prefixed by '$' or '0x'.

The register name ``X`` in ``r[X]`` must be one of the following::

  a b c d e f h l bc de hl
  ^a ^b ^c ^d ^e ^f ^h ^l ^bc ^de ^hl
  ix iy ixh iyh ixl iyl
  i r sp

The names that begin with ``^`` denote the shadow registers.

Wherever ``\n`` appears in a ``TraceLine*`` parameter value, it is replaced by
a newline character.

Configuration parameters must appear in a ``[trace]`` section. For example,
to make ``trace.py`` write a timestamp for each instruction when ``-v`` is
used, add the following section to ``skoolkit.ini``::

  [trace]
  TraceLine={t:>10} ${pc:04X} {i}

Configuration parameters may also be set on the command line by using the
``--ini`` option. Parameter values set this way will override any found in
``skoolkit.ini``.

EXAMPLES
========
1. Execute and show instructions in the routine at 32768-32798 in ``game.z80``:

|
|   ``trace.py -v -s 32768 -S 32798 game.z80``

2. Show delays between changes in the state of the ZX Spectrum speaker produced
   by the sound effect routine at 49152-49193 in ``game.z80``:

|
|   ``trace.py --audio -s 49152 -S 49193 game.z80``
