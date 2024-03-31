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
