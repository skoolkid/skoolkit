SkoolKit
========

SkoolKit is a collection of utilities that can be used to disassemble a
[Spectrum](http://en.wikipedia.org/wiki/ZX_Spectrum) game (or indeed any piece
of Spectrum software written in machine code) into a format known as a *skool*
file. Then, from this *skool* file, you can use SkoolKit to create a browsable
disassembly in HTML format, or a re-assemblable disassembly in ASM format. So
the *skool* file is - from start to finish as you develop it by organising and
annotating the code - the common 'source' for both the reader-friendly HTML
version of the disassembly, and the developer- and assembler-friendly ASM
version of the disassembly.

Features
--------

Besides disassembling a Spectrum game into a list of Z80 instructions, SkoolKit
can also:

* Build still and animated PNG/GIF images from graphic data in the game
  snapshot (using the ``#UDG``, ``#UDGARRAY``, ``#FONT`` and ``#SCR`` macros)
* Create hyperlinks between routines and data blocks that refer to each other
  (by use of the ``#R`` macro in annotations, and automatically in the
  operands of CALL and JP instructions)
* Neatly render lists of bugs, trivia and POKEs on separate pages (using
  ``Bug``, ``Fact`` and ``Poke`` sections in a *ref* file)
* Produce ASM files that include bugfixes declared in the *skool* file (with
  ``@ofix``, ``@bfix`` and other ASM directives)
* Produce TAP files from assembled code (using ``bin2tap.py``)

See the [user manual](http://skoolkid.github.io/skoolkit/) for more details.

Examples
--------

SkoolKit includes two (unfinished) example disassemblies:

* [Manic Miner](http://skoolkid.github.io/skoolkit/examples/manic_miner/)
* [Spectrum ROM](http://skoolkid.github.io/skoolkit/examples/rom/)
