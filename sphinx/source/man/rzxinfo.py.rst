:orphan:

==========
rzxinfo.py
==========

SYNOPSIS
========
``rzxinfo.py`` [options] FILE

DESCRIPTION
===========
``rzxinfo.py`` shows the blocks in or extracts the snapshots from an RZX file.

OPTIONS
=======
--extract
  Extract snapshots.

--frames
  Show the contents of every frame.

-V, --version
  Show the SkoolKit version number and exit.

EXAMPLES
========
1. Show information on the blocks in ``game.rzx``:

|
|   ``rzxinfo.py game.rzx``

2. Extract all the snapshots from ``game.rzx``:

|
|   ``rzxinfo.py --extract game.rzx``
