:orphan:

==========
tap2sna.py
==========

SYNOPSIS
========
| ``tap2sna.py`` [options] INPUT snapshot.z80
| ``tap2sna.py`` @FILE [args]

DESCRIPTION
===========
``tap2sna.py`` converts a TAP or TZX file (which may be inside a zip archive)
into a Z80 snapshot. INPUT may be the full URL to a remote zip archive or
TAP/TZX file, or the path to a local file. Arguments may be read from FILE
instead of (or as well as) being given on the command line.

OPTIONS
=======
-c, --sim-load-config name=value
  Set the value of a ``--sim-load`` configuration parameter. Do ``-c help`` for
  more information, and see the section on ``SIMULATED LOAD`` below. This
  option may be used multiple times.

-d, --output-dir `DIR`
  Write the snapshot file in this directory.

-f, --force
  Overwrite an existing snapshot.

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

-s, --start `START`
  Set the start address to JP to. This option is equivalent to
  ``--reg pc=START``. `START` must be a decimal number, or a hexadecimal number
  prefixed by '0x'.

--sim-load
  Simulate a 48K ZX Spectrum running LOAD "". See the section on ``SIMULATED
  LOAD`` below.

--state name=value
  Set a hardware state attribute. Do ``--state help`` for more information, or
  see the section on ``HARDWARE STATE`` below. This option may be used multiple
  times.

--tape-name NAME
  Specify the name of a TAP/TZX file in a zip archive. By default, the first
  TAP/TZX file found in the zip archive is selected.

--tape-start BLOCK
  Start the tape at this block number. In a TAP/TZX file, the first block is
  number 1, the second is 2, etc.

--tape-stop BLOCK
  Stop the tape at this block number. In a TAP/TZX file, the first block is
  number 1, the second is 2, etc.

--tape-sum MD5SUM
  Specify the MD5 checksum of the TAP/TZX file. ``tap2sna.py`` will abort if
  there is a checksum mismatch.

-u, --user-agent `AGENT`
  Set the User-Agent header used in an HTTP(S) request.

-V, --version
  Show the SkoolKit version number and exit.

TZX SUPPORT
===========
``tap2sna.py`` can read data from TZX block types 0x10 (standard speed data),
0x11 (turbo speed data) and 0x14 (pure data), but not block types 0x15 (direct
recording), 0x18 (CSW recording) or 0x19 (generalized data block).

SIMULATED LOAD
==============
The ``--sim-load`` option simulates a freshly booted 48K ZX Spectrum running
LOAD "" (or LOAD ""CODE, if the first block on the tape is a 'Bytes' header).
Whenever the Spectrum ROM's load routine at $0556 is called, a shortcut is
taken by "fast loading" the next block on the tape. All other code (including
any custom loader) is fully simulated. Simulation continues until the program
counter hits the start address given by the ``--start`` option, or 10 minutes
of simulated Z80 CPU time has elapsed, or the end of the tape is reached and
one of the following conditions is satisfied:

* a custom loader was detected
* the program counter hits an address outside the ROM
* more than one second of simulated Z80 CPU time has elapsed since the end of
  the tape was reached

A simulated LOAD can also be aborted by pressing Ctrl-C. When a simulated LOAD
has completed or been aborted, the values of the registers (including the
program counter) in the simulator are used to populate the Z80 snapshot.

A simulated LOAD can be configured via parameters that are set by the
by the ``--sim-load-config`` (or ``-c``) option. The recognised configuration
parameters are:

* ``accelerator`` - the tape-sampling loop accelerator to use (default:
  automatically selected - see below); use this to specify a particular
  accelerator (which may produce a faster simulated LOAD), or to disable
  acceleration entirely (``accelerator=none``)
* ``fast-load`` - enable fast loading (``1``, the default), or disable it
  (``0``); fast loading significantly reduces the load time for many tapes, but
  can also cause some loaders to fail
* ``finish-tape`` - run the tape to the end before stopping the simulation at
  the address specified by the ``--start`` option (``1``), or stop the
  simulation as soon as that address is reached, regardless of whether the tape
  has finished (``0``, the default)
* ``first-edge`` - the time (in T-states) from the start of the tape at which
  to place the leading edge of the first pulse (default: ``-2168``); the
  default value places the trailing edge of the first pulse at time 0, but some
  loaders (e.g. polarity-sensitive loaders) require ``first-edge=0``
* ``pause`` - pause the tape between blocks and resume playback when port 254
  is read (``1``, the default), or run the tape continuously (``0``); pausing
  can help with tapes that require (but do not actually contain) long pauses
  between blocks, but can cause some loaders to fail
* ``timeout`` - the number of seconds of Z80 CPU time after which to abort the
  simulated LOAD if it's still in progress (default: 900)
* ``trace`` - the file to which to log all instructions executed during the
  simulated LOAD (default: none)

The names of the available tape-sampling loop accelerators are:

|
|  ``alkatraz`` - Alkatraz
|  ``alkatraz2`` - Alkatraz 2
|  ``bleepload`` - Firebird BleepLoad
|  ``cyberlode`` - Cyberlode 1.1
|  ``digital-integration`` - Digital Integration
|  ``dinaload`` - Dinaload
|  ``edge`` - Edge
|  ``elite-uni-loader`` - Elite Uni-Loader
|  ``excelerator`` - The Excelerator Loader
|  ``flash-loader`` - Flash Loader
|  ``ftl`` - FTL
|  ``gargoyle`` - Gargoyle
|  ``gremlin`` - various games published by Gremlin Graphics
|  ``hewson-slowload`` - Hewson Slowload
|  ``injectaload`` - Injectaload
|  ``microsphere`` - Back to Skool, Skool Daze, Sky Ranger
|  ``none`` - no accelerator
|  ``paul-owens`` - Paul Owens Protection System
|  ``poliload`` - Poliload
|  ``power-load`` - Power-Load
|  ``rom`` - any loader whose sampling loop is the same as the ROM's
|  ``search-loader`` - Search Loader
|  ``softlock`` - SoftLock
|  ``speedlock`` - Speedlock (all versions)
|  ``zydroload`` - Zydroload

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
By default, ``tap2sna.py`` loads bytes from every data block on the tape, using
the start address given in the corresponding header. For tapes that contain
headerless data blocks, headers with incorrect start addresses, or irrelevant
blocks, the ``--ram`` option can be used to load bytes from specific blocks at
the appropriate addresses. The syntax is:

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
The ``--ram`` option can be used to move a block of bytes from one location to
another before saving the snapshot.

|
|  ``--ram move=src,N,dest``

This moves a block of ``N`` bytes from ``src`` to ``dest``. For example:

|
|  ``--ram move=32512,256,32768``     # Move 32512-32767 to 32768-33023
|  ``--ram move=0x9c00,0x100,0x9d00`` # Move 39936-40191 to 40192-40447

POKE OPERATIONS
===============
The ``--ram`` option can be used to POKE values into the snapshot before saving
it.

|
|  ``--ram poke=A[-B[-C]],[^+]V``

This does ``POKE N,V`` for ``N`` in ``{A, A+C, A+2C..., B}``, where:

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
|  ``border``  - border colour (default=0)
|  ``iff``     - interrupt flip-flop: 0=disabled, 1=enabled (default=1)
|  ``im``      - interrupt mode (default=1)
|  ``tstates`` - T-states elapsed since start of frame (default=0)

READING ARGUMENTS FROM A FILE
=============================
For complex snapshots that require many ``--ram``, ``--reg`` or ``--state``
options to build, it may be more convenient to store the arguments to
``tap2sna.py`` in a file. For example, if the file ``game.t2s`` has the
following contents:

|
|    ;
|    ; tap2sna.py file for GAME
|    ;
|    \http://example.com/pub/games/GAME.zip
|    game.z80
|    --ram load=4,32768         # Load the fourth block at 32768
|    --ram move=40960,512,43520 # Move 40960-41471 to 43520-44031
|    --ram call=:ram.modify     # Call modify(snapshot) in ./ram.py
|    --ram sysvars              # Initialise the system variables
|    --state iff=0              # Disable interrupts
|    --stack 32768              # Stack at 32768
|    --start 34816              # Start at 34816

then:

|
|   ``tap2sna.py @game.t2s``

will create ``game.z80`` as if the arguments specified in ``game.t2s`` had been
given on the command line.

EXAMPLES
========
1. Extract the TAP or TZX file from a remote zip archive and convert it into a
   Z80 snapshot:

   |
   |   ``tap2sna.py ftp://example.com/game.zip game.z80``

2. Extract the TAP or TZX file from a zip archive, and convert it into a Z80
   snapshot with the program counter set to 32768:

   |
   |   ``tap2sna.py --reg pc=32768 game.zip game.z80``

3. Convert a TZX file into a Z80 snapshot by loading the third block on the
   tape at 25000:

   |
   |   ``tap2sna.py --ram load=3,25000 game.tzx game.z80``

4. Convert a TZX file into a Z80 snapshot using options read from the file
   ``game.t2s``:

   |
   |   ``tap2sna.py @game.t2s game.tzx game.z80``
