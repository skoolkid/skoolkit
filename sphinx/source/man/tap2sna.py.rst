:orphan:

==========
tap2sna.py
==========

SYNOPSIS
========
| ``tap2sna.py`` [options] INPUT [OUTFILE]
| ``tap2sna.py`` @FILE [args]

DESCRIPTION
===========
``tap2sna.py`` converts a PZX, TAP or TZX file (which may be inside a zip
archive) into an SZX or Z80 snapshot. INPUT may be the full URL to a remote zip
archive or tape file, or the path to a local file. Arguments may be read from
FILE instead of (or as well as) being given on the command line.

OPTIONS
=======
-c, --sim-load-config name=value
  Set the value of a simulated LOAD configuration parameter. Do ``-c help`` for
  more information, or ``-c help-name`` for help on a specific parameter. Also
  see the section on ``SIMULATED LOAD`` below. This option may be used multiple
  times.

-d, --output-dir `DIR`
  Write the snapshot file in this directory.

-I, --ini `param=value`
  Set the value of a configuration parameter (see ``CONFIGURATION``),
  overriding any value found in ``skoolkit.ini``. This option may be used
  multiple times.

-p, --stack `STACK`
  Set the stack pointer. This option is equivalent to ``--reg sp=STACK``.
  `STACK` must be a decimal number, or a hexadecimal number prefixed by '0x'.

--ram OPERATION
  Perform a load operation or otherwise modify the memory snapshot being built.
  Do ``--ram help`` for more information, or see the sections on the ``CALL``,
  ``LOAD``, ``MOVE``, ``POKE`` and ``SYSVARS`` operations below. This option
  may be used multiple times.

--reg name=value
  Set the value of a register. Do ``--reg help`` for more information, or see
  the section on ``REGISTERS`` below. This option may be used multiple times.

--show-config
  Show configuration parameter values.

-s, --start `START`
  Set the start address to JP to. This option is equivalent to
  ``--reg pc=START``. `START` must be a decimal number, or a hexadecimal number
  prefixed by '0x'.

--state name=value
  Set a hardware state attribute. Do ``--state help`` for more information, or
  see the section on ``HARDWARE STATE`` below. This option may be used multiple
  times.

--tape-analysis
  Show an analysis of the tape's tones, pulse sequences and data blocks.

--tape-name NAME
  Specify the name of a tape file in a zip archive. By default, the first tape
  file found in the zip archive is selected.

--tape-start BLOCK
  Start the tape at this block number. In a tape file, the first block is
  number 1, the second is 2, etc.

--tape-stop BLOCK
  Stop the tape at this block number. In a tape file, the first block is number
  1, the second is 2, etc.

--tape-sum MD5SUM
  Specify the MD5 checksum of the tape file. ``tap2sna.py`` will abort if there
  is a checksum mismatch.

-u, --user-agent `AGENT`
  Set the User-Agent header used in an HTTP(S) request.

-V, --version
  Show the SkoolKit version number and exit.

TZX SUPPORT
===========
``tap2sna.py`` cannot read data from TZX block types 0x18 (CSW recording) or
0x19 (generalized data block).

SIMULATED LOAD
==============
By default, ``tap2sna.py`` simulates a freshly booted 48K ZX Spectrum running
LOAD "" (or LOAD ""CODE, if the first block on the tape is a 'Bytes' header).
Whenever the Spectrum ROM's load routine at $0556 is called, a shortcut is
taken by "fast loading" the next block on the tape. All other code (including
any custom loader) is fully simulated. Simulation continues until the program
counter hits the start address given by the ``--start`` option, or 15 minutes
of simulated Z80 CPU time has elapsed, or the end of the tape is reached and
one of the following conditions is satisfied:

* a custom loader was detected
* the program counter hits an address outside the ROM
* more than one second of simulated Z80 CPU time has elapsed since the end of
  the tape was reached

A simulated LOAD can also be aborted by pressing Ctrl-C. When a simulated LOAD
has completed or been aborted, the values of the registers (including the
program counter) in the simulator are used to populate the snapshot.

A simulated LOAD can be configured via parameters that are set by the
by the ``--sim-load-config`` (or ``-c``) option. The recognised configuration
parameters are:

* ``accelerate-dec-a`` - enable acceleration of 'DEC A: JR NZ,$-1' delay loops
  (``1``, the default), or 'DEC A: JP NZ,$-1' delay loops (``2``), or neither
  (``0``)
* ``accelerator`` - a comma-separated list of tape-sampling loop accelerators
  to use (see the ``ACCELERATORS`` section below)
* ``cmio`` - enable simulation of memory contention and I/O contention delays
  (``1``), or disable it (``0``); this is disabled by default to improve
  performance, but some loaders may require it; when this is enabled, all
  acceleration is disabled
* ``fast-load`` - enable fast loading whenever the ROM loader is called (``1``,
  the default), or disable it (``0``); fast loading (also known as "flash
  loading") significantly reduces the load time for many tapes, but can also
  cause some loaders to fail
* ``finish-tape`` - run the tape to the end before stopping the simulation at
  the address specified by the ``--start`` option (``1``), or stop the
  simulation as soon as that address is reached, regardless of whether the tape
  has finished (``0``, the default)
* ``first-edge`` - the time (in T-states) from the start of the tape at which
  to place the leading edge of the first pulse (default: ``0``)
* ``in-flags`` - various flags specifying how to handle 'IN' instructions (see
  below)
* ``load`` - a space-separated list of keys to press to build an alternative
  command line to load the tape (see the ``LOAD COMMAND`` section below)
* ``machine`` - the type of machine to simulate: a 48K Spectrum (``48``, the
  default), or a 128K Spectrum (``128``)
* ``pause`` - pause the tape between blocks and resume playback when port 254
  is read (``1``, the default), or run the tape continuously (``0``); pausing
  can help with tapes that require (but do not actually contain) long pauses
  between blocks, but can cause some loaders to fail
* ``polarity`` - the EAR bit reading produced by the first pulse on the tape:
  ``0`` (the default) or ``1``; subsequent pulses give readings that alternate
  between 0 and 1
* ``python`` - whether to use the pure Python Z80 simulator (``1``), or the
  much faster C version if available (``0``, the default)
* ``timeout`` - the number of seconds of Z80 CPU time after which to abort the
  simulated LOAD if it's still in progress (default: 900)
* ``trace`` - the file to which to log all instructions executed during the
  simulated LOAD (default: none)

The ``in-flags`` parameter is the sum of the following values, chosen according
to the desired behaviour:

* 1 - interpret 'IN A,($FE)' instructions in the address range $4000-$7FFF as
  reading the tape (by default they are ignored)
* 2 - ignore 'IN' instructions in the address range $4000-$FFFF (i.e. in RAM)
  that read port $FE
* 4 - yield a simulated port reading when executing an 'IN r,(C)' instruction
  (by default such an instruction always yields the value $FF)

By default, the EAR bit reading produced by a pulse is 0 if the 0-based index
of the pulse is even (i.e. first, third, fifth pulses etc.), or 1 otherwise.
This can be reversed by setting ``polarity=1``. Run ``tap2sna.py`` with the
``--tape-analysis`` option to see the timings and EAR bit readings of the
pulses on a tape.

ACCELERATORS
============
The ``accelerator`` simulated LOAD configuration parameter must be either a
comma-separated list of specific accelerator names or one of the following
special values:

* ``auto`` - select accelerators automatically (this is the default)
* ``list`` - list the accelerators used during a simulated LOAD, along with the
  hit/miss counts generated by the tape-sampling loop detector
* ``none`` - disable acceleration; the loading time for a game with a custom
  loader that uses an unrecognised tape-sampling loop may be reduced by
  specifying this value

A tape-sampling loop accelerator works by effectively fast-forwarding the tape
(and the state of the loop itself) to the next edge whenever the loop is
entered. This technique is known as "edge loading".

The output produced by ``accelerator=list`` looks something like this::

  Accelerators: microsphere: 6695; rom: 794013; misses: 19/9; dec-a: 800708/0/224

This means that:

* the ``microsphere`` and ``rom`` tape-sampling loops were detected, and were
  entered 6695 times and 794013 times respectively
* 19 instances of 'INC B' outside a recognised tape-sampling loop were
  executed, and the corresponding figure for 'DEC B' is 9
* 800708 'DEC A: JR NZ,$-1' delay loops were entered, no 'DEC A: JP NZ,$-1'
  delay loops were entered, and 224 instances of 'DEC A' outside such delay
  loops were executed

Specifying by name the types of tape-sampling loop used by a game's custom
loader may reduce the loading time. To show the names of the available
tape-sampling loop accelerators:

|
|  ``tap2sna.py -c help-accelerator``

LOAD COMMAND
============
The ``load`` simulated LOAD configuration parameter may be used to specify an
alternative command line to load the tape in cases where neither 'LOAD ""' nor
'LOAD ""CODE' works. Its value is a space-separated list of 'words' (a 'word'
being a sequence of any characters other than space), each of which is broken
down into a sequence of one or more keypresses. If a word contains the '+'
symbol, the tokens it separates are converted into keypresses made
simultaneously. If a word matches a BASIC token, the corresponding sequence of
keypresses to produce that token are substituted. Otherwise, each character in
the word is converted individually into the appropriate keypresses.

The following special tokens are also recognised:

|
|  ``CS`` - CAPS SHIFT
|  ``SS`` - SYMBOL SHIFT
|  ``SPACE`` - SPACE
|  ``ENTER`` - ENTER
|  ``DOWN`` - Cursor down ('CS+6')
|  ``GOTO`` - GO TO ('g')
|  ``GOSUB`` - GO SUB ('h')
|  ``DEFFN`` - DEF FN ('CS+SS SS+1')
|  ``OPEN#`` - OPEN # ('CS+SS SS+4')
|  ``CLOSE#`` - CLOSE # ('CS+SS SS+5')
|  ``PC=address`` - Stop the keyboard input simulation at this address

The ``PC=address`` token, if present, must appear last. The default address is
either 0x0605 (when a 48K Spectrum is being simulated) or 0x13BE (on a 128K
Spectrum). The simulated LOAD begins at this address.

``ENTER`` is automatically appended to the command line if not already present.

For example, the ``load`` parameter may be set to:

|
|  CLEAR 34999: LOAD "" CODE : RANDOMIZE USR 35000

Note that the spaces around ``CLEAR``, ``LOAD``, ``CODE``, ``RANDOMIZE`` and
``USR`` are required in order for them to be recognised as BASIC tokens.

CALL OPERATIONS
===============
The ``--ram`` option can be used to call a Python function to perform arbitrary
modification of the memory snapshot.

|
|  ``--ram call=[/path/to/moduledir:]module.function``

The function is called with the memory snapshot (a list of 65536 byte values)
as the sole positional argument. The function must modify the snapshot in
place. The path to the module's location may be omitted if the module is
already in the module search path.

For example:

|
|  ``--ram call=:ram.modify`` # Call modify(snapshot) in ./ram.py

LOAD OPERATIONS
===============
By default, ``tap2sna.py`` attempts to load a tape exactly as a 48K Spectrum
would (see the section on ``SIMULATED LOAD`` above). If that doesn't work, the
``--ram`` option can be used to load bytes from specific tape blocks at the
appropriate addresses. The syntax is:

|
|  ``--ram load=[+]block[+],start[,length,step,offset,inc]``

where the parameters have the following meanings:

``block``
  The tape block number; the first block is 1, the next is 2, etc. Attach a '+'
  prefix to load the first byte of the block (which is usually the flag byte),
  and a '+' suffix to load the last byte (which is usually the parity byte).

``start``
  The destination address at which to start loading.

``length``
  The number of bytes to load (optional; defaults to the number of bytes
  remaining in the block).

``step``
  This number is added to the destination address after each byte is loaded
  (optional; default=1).

``offset``
  This number is added to the destination address before a byte is loaded, and
  subtracted after the byte is loaded (optional; default=0). It is analogous to
  the offset ``d`` in the ``LD (IX+d),L`` operation that is commonly used in
  load routines to copy the byte just loaded from tape (``L``) into memory.

``inc``
  After ``step`` is added to the destination address, this number is added too
  if the result overflowed past 65535 (optional; default=0).

A single tape block can be loaded in two or more stages; for example:

|
|  ``--ram load=2,32768,2048`` # Load the first 2K at 32768
|  ``--ram load=2,0xC000``     # Load the remainder at 49152

MOVE OPERATIONS
===============
The ``--ram`` option can be used to copy a block of bytes from one location to
another before saving the snapshot.

|
|  ``--ram move=[s:]src,N,[d:]dest``

This copies a block of ``N`` bytes from ``src`` in RAM bank ``s`` to ``dest``
in RAM bank ``d``. For example:

|
|  ``--ram move=32512,256,32768``  # Copy 32512-32767 to 32768-33023
|  ``--ram move=3:0,8,4:0``        # Copy the first 8 bytes of bank 3 to bank 4

POKE OPERATIONS
===============
The ``--ram`` option can be used to POKE values into the snapshot before saving
it.

|
|  ``--ram poke=[P:]A[-B[-C]],[^+]V``

This does ``POKE N,V`` in RAM bank ``P`` for ``N`` in ``{A, A+C, A+2C..., B}``,
where:

``P`` is the RAM bank to POKE (0-7; 128K only)

``A`` is the first address to POKE

``B`` is the last address to POKE (optional; default is ``A``)

``C`` is the step (optional; default=1)

``V`` is the value to POKE; prefix the value with '^' to perform an XOR
operation, or '+' to perform an ADD operation

For example:

|
|  ``--ram poke=0x6000,0x10``     # POKE 24576,16
|  ``--ram poke=30000-30002,^85`` # Perform 'XOR 85' on addresses 30000-30002
|  ``--ram poke=40000-40004-2,1`` # POKE 40000,1: POKE 40002,1: POKE 40004,1

SYSVARS OPERATION
=================
The ``--ram`` option can be used to initialise the system variables at
23552-23754 (5C00-5CCA) with values suitable for a 48K ZX Spectrum.

|
|  ``--ram sysvars``

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

The default value for each register is 0, with the following exceptions:

|
|  ``i=63``
|  ``iy=23610``

HARDWARE STATE
==============
The ``--state`` option sets a hardware state attribute.

|
|  ``--state name=value``

Recognised attribute names and their default values are:

|
|  ``7ffd``    - last OUT to port 0x7ffd (128K only)
|  ``ay[N]``   - contents of AY register N (N=0-15; 128K only)
|  ``border``  - border colour (default=0)
|  ``fe``      - last OUT to port 0xfe (SZX only)
|  ``fffd``    - last OUT to port 0xfffd (128K only)
|  ``iff``     - interrupt flip-flop: 0=disabled, 1=enabled (default=1)
|  ``im``      - interrupt mode (default=1)
|  ``issue2``  - issue 2 emulation: 0=disabled, 1=enabled (default=0)
|  ``tstates`` - T-states elapsed since start of frame (default=34943)

READING ARGUMENTS FROM A FILE
=============================
For complex snapshots that require many options to build, it may be more
convenient to store the arguments to ``tap2sna.py`` in a file. For example, if
the file ``game.t2s`` has the following contents:

|
|    ;
|    ; tap2sna.py file for GAME
|    ;
|    \http://example.com/pub/games/GAME.zip
|    -c fast-load=0      # Disable fast loading
|    -c accelerator=none # Disable tape-sampling loop acceleration
|    --state issue2=1    # Enable issue 2 keyboard emulation
|    --start 34816       # Start at 34816

then:

|
|   ``tap2sna.py @game.t2s``

will create ``game.z80`` as if the arguments specified in ``game.t2s`` had been
given on the command line. When ``tap2sna.py`` reads arguments from a file
whose name ends with '.t2s', the output snapshot filename defaults to the name
of that arguments file with '.t2s' replaced by either '.z80' or '.szx'
(depending on the value of the ``DefaultSnapshotFormat`` configuration
parameter).

CONFIGURATION
=============
``tap2sna.py`` will read configuration from a file named ``skoolkit.ini`` in
the current working directory or in ``~/.skoolkit``, if present. The recognised
configuration parameters are:

  :DefaultSnapshotFormat: The format of the snapshot written when no output
    snapshot argument is specified. Valid values are ``z80`` (the default) and
    ``szx``.
  :TraceLine: The format of each line in the trace log file for a simulated
    LOAD (default: ``${pc:04X} {i}``).
  :TraceOperand: The prefix, byte format, and word format for the numeric
    operands of instructions in the trace log file for a simulated LOAD,
    separated by commas (default: ``$,02X,04X``). The byte and word formats are
    standard Python format specifiers for numeric values, and default to empty
    strings if not supplied.

``TraceLine`` is a standard Python format string that recognises the following
replacement fields:

|
|  ``i`` - the current instruction
|  ``m[address]`` - the contents of a memory address
|  ``pc`` - the address of the current instruction (program counter)
|  ``r[X]`` - the X register (see below)
|  ``t`` - the current timestamp

When using the ``m`` (memory) replacement field, ``address`` must be either a
decimal number, or a hexadecimal number prefixed by '$' or '0x'.

The register name ``X`` in ``r[X]`` must be one of the following::

  a b c d e f h l bc de hl
  ^a ^b ^c ^d ^e ^f ^h ^l ^bc ^de ^hl
  ix ixh ixl iy iyh iyl
  i r sp

The names that begin with ``^`` denote the shadow registers.

The current timestamp (``t``) is the number of T-states that have elapsed since
the start of the simulation, according to the simulator's internal clock. In
order to maintain synchronisation with the tape being loaded, the simulator's
clock is adjusted to match the timestamp of the first pulse in each block (as
shown by the ``--tape-analysis`` option) when that block is reached. (The
simulator's clock may at times become desynchronised with the tape because, by
default, the tape is paused between blocks, and resumed when port 254 is read.)

Configuration parameters must appear in a ``[tap2sna]`` section. For example,
to make ``tap2sna.py`` write instruction addresses and operands in a trace log
file in decimal format by default, add the following section to
``skoolkit.ini``::

  [tap2sna]
  TraceLine={pc:05} {i}
  TraceOperand=

Configuration parameters may also be set on the command line by using the
``--ini`` option. Parameter values set this way will override any found in
``skoolkit.ini``.

EXAMPLES
========
1. Extract the tape file from a remote zip archive and convert it into a Z80
   snapshot:

   |
   |   ``tap2sna.py ftp://example.com/game.zip game.z80``

2. Extract the tape file from a zip archive, and convert it into an SZX
   snapshot with the program counter set to 32768:

   |
   |   ``tap2sna.py --start 32768 game.zip game.szx``

3. Convert a TZX file into a Z80 snapshot by loading the third block on the
   tape at 25000:

   |
   |   ``tap2sna.py --ram load=3,25000 game.tzx game.z80``

4. Convert a TZX file into an SZX snapshot using options read from the file
   ``game.t2s``:

   |
   |   ``tap2sna.py @game.t2s game.tzx game.szx``
