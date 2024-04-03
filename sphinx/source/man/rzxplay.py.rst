:orphan:

==========
rzxplay.py
==========

SYNOPSIS
========
``rzxplay.py`` [options] FILE [OUTFILE]

DESCRIPTION
===========
``rzxplay.py`` plays an RZX file. If 'OUTFILE' is given, an SZX or Z80 snapshot
or an RZX file is written after playback has completed.

OPTIONS
=======
--flags FLAGS
  Set playback flags. Do ``--flags help`` for more information, or see the
  section on ``FLAGS`` below.

--force
  Force playback when unsupported hardware is detected.

--fps FPS
  Run at this many frames per second (default: 50). 0 means maximum speed.

--map FILE
  Log addresses of executed instructions to a file.

--no-screen
  Run without a screen.

--python
  Use the pure Python Z80 simulator even if the C version is available.

--quiet
  Don't print progress percentage during playback.

--scale SCALE
  Scale the display up by this factor (1-4; default: 2).

--snapshot FILE
  Specify an external snapshot file to start with.

--stop FRAMES
  Stop after playing this many frames.

--trace FILE
  Log executed instructions to a file.

-V, --version
  Show the SkoolKit version number and exit.

SUPPORTED MACHINES
==================
``rzxplay.py`` can play RZX files that were recorded in 48K, 128K or +2 mode
with no peripherals (e.g. Interface 1) attached. The ``--force`` option can be
used to make ``rzxplay.py`` attempt playback of files that were recorded on
unsupported machines or with unsupported hardware attached, but they are
unlikely to play to the end.

SCREEN
======
If pygame is installed, ``rzxplay.py`` will use it to render the Spectrum's
screen contents at 50 frames per second by default. Use the ``--fps`` option
to change the frame rate. Specifying ``--fps 0`` makes ``rzxplay.py`` run at
maximum speed. To disable the screen and make ``rzxplay.py`` run even faster,
use the ``--no-screen`` option.

CODE EXECUTION MAP
==================
The ``--map`` option can be used to log the addresses of instructions executed
during playback to a file. This file can then be used by ``sna2ctl.py`` to
produce a control file. If the file specified by the ``--map`` option already
exists, any addresses it contains will be merged with those of the instructions
executed.

FLAGS
=====
The ``--flags`` option sets flags that control the playback of RZX frames when
interrupts are enabled. If an RZX file fails to play to completion, setting one
or more of these flags may help. ``FLAGS`` is the sum of the following values,
chosen according to the desired outcome:

* 1 - When the last instruction in a frame is either 'LD A,I' or 'LD A,R',
  reset bit 2 of the flags register. This is the expected behaviour of a real
  Z80, but some RZX files fail when this flag is set.

* 2 - When the last instruction in a frame is 'EI', and the next frame is a
  short one (i.e. has a fetch count of 1 or 2), block the interrupt in the next
  frame. By default, and according to RZX convention, ``rzxplay.py`` accepts an
  interrupt at the start of every frame except the first, regardless of whether
  the instruction just executed would normally block it. However, some RZX
  files contain a short frame immediately after an 'EI' to indicate that the
  interrupt should in fact be blocked, and therefore require this flag to be
  set to play back correctly.

OUTPUT FILE
===========
If ``OUTFILE`` is given, and ends with either '.z80' or '.szx', then a snapshot
in the corresponding format is written when playback ends. Similarly, if
``OUTFILE`` ends with '.rzx', then an RZX file is written when playback ends.
However, this makes sense only if ``--stop`` is used to end playback somewhere
in the middle of the input RZX file, otherwise the output RZX file will be
empty (i.e. contain no frames).

EXAMPLES
========
1. Play ``game.rzx``:

|
|   ``rzxplay.py game.rzx``

2. Log the instructions executed while playing ``game.rzx``:

|
|   ``rzxplay.py --trace game.log game.rzx``

3. Play only 100 frames of ``game.rzx`` and then write ``game-100.rzx``:

|
|   ``rzxplay.py --stop 100 game.rzx game-100.rzx``
