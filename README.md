[![Build Status](https://travis-ci.org/skoolkid/skoolkit.svg?branch=master)](https://travis-ci.org/skoolkid/skoolkit)
[![Coverage](https://codecov.io/github/skoolkid/skoolkit/coverage.svg?branch=master)](https://codecov.io/github/skoolkid/skoolkit?branch=master)

SkoolKit
========

SkoolKit is a collection of utilities that can be used to disassemble a
[Spectrum](https://en.wikipedia.org/wiki/ZX_Spectrum) game (or indeed any piece
of Spectrum software written in machine code) into a format known as a *skool*
file. Then, from this *skool* file, you can use SkoolKit to create a browsable
disassembly in HTML format, or a re-assemblable disassembly in ASM format. So
the *skool* file is - from start to finish as you develop it by organising and
annotating the code - the common 'source' for both the reader-friendly HTML
version of the disassembly, and the developer- and assembler-friendly ASM
version of the disassembly.

Requirements
------------

SkoolKit requires [Python](https://www.python.org) 3.5+. If you're running
Linux or one of the BSDs, you probably already have Python installed. If you're
running Windows or Mac OS X, you can get Python
[here](https://www.python.org/downloads/).

Features
--------

SkoolKit can:

* convert a TAP or TZX file into a 'pristine' snapshot (using ``tap2sna.py``)
* disassemble SNA, Z80 and SZX snapshots as well as raw memory files
* distinguish code from data by using a code execution map produced by an
  emulator
* build still and animated PNG images from graphic data in the game snapshot
  (using the ``#UDG``, ``#UDGARRAY``, ``#FONT`` and ``#SCR`` macros)
* create hyperlinks between routines and data blocks that refer to each other
  (by use of the ``#R`` macro in annotations, and automatically in the
  operands of CALL and JP instructions)
* neatly render lists of bugs, trivia and POKEs on separate pages (using
  ``Bug``, ``Fact`` and ``Poke`` sections in a *ref* file)
* produce ASM files that include bugfixes declared in the *skool* file (with
  ``@ofix``, ``@bfix`` and other ASM directives)
* produce TAP files from assembled code (using ``bin2tap.py``)

See the [user manual](https://skoolkid.github.io/skoolkit/) for more details
(mirror [here](https://skoolkid.gitlab.io/skoolkit/)).
