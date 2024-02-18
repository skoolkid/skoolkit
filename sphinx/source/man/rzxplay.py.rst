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

--no-screen
  Run without a screen.

--quiet
  Don't print progress percentage during playback.

--scale SCALE
  Scale the display up by this factor (1-4; default: 2).

--stop FRAMES
  Stop after playing this many frames.

--trace FILE
  Log executed instructions to a file.

-V, --version
  Show the SkoolKit version number and exit.

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
