[![Tests](https://github.com/skoolkid/skoolkit/actions/workflows/tests.yml/badge.svg)](https://github.com/skoolkid/skoolkit/actions/workflows/tests.yml)
[![Coverage](https://codecov.io/github/skoolkid/skoolkit/coverage.svg?branch=master)](https://codecov.io/github/skoolkid/skoolkit?branch=master)

SkoolKit
========

SkoolKit is a collection of utilities that can be used to disassemble a
[Spectrum](https://en.wikipedia.org/wiki/ZX_Spectrum) game (or indeed any piece
of Spectrum software written in machine code) into a format known as a *skool*
file. Then, from this *skool* file, you can use SkoolKit to create a browsable
disassembly in HTML format, or a re-assemblable disassembly in assembly
language. So the *skool* file is - from start to finish as you develop it by
organising and annotating the code - the common 'source' for both the
reader-friendly HTML version of the disassembly, and the developer- and
assembler-friendly version of the disassembly.

Requirements
------------

SkoolKit requires [Python](https://www.python.org) 3.10+. If you're running
Linux or one of the BSDs, you probably already have Python installed. If you're
running Windows or Mac OS X, you can get Python
[here](https://www.python.org/downloads/).

Features
--------

With SkoolKit you can:

* use [sna2ctl.py](https://skoolkid.github.io/skoolkit/commands.html#sna2ctl-py)
  to generate a [control file](https://skoolkid.github.io/skoolkit/control-files.html)
  (an attempt to identify routines and data blocks by static analysis) from a
  snapshot (SNA, SZX or Z80) or raw memory file
* enable [sna2ctl.py](https://skoolkid.github.io/skoolkit/commands.html#sna2ctl-py)
  to generate a much better control file that more reliably distinguishes code
  from data by using a code execution map produced by an emulator,
  [rzxplay.py](https://skoolkid.github.io/skoolkit/commands.html#rzxplay-py) or
  [trace.py](https://skoolkid.github.io/skoolkit/commands.html#trace-py)
* use [sna2skool.py](https://skoolkid.github.io/skoolkit/commands.html#sna2skool-py)
  along with this control file to produce a disassembly of a snapshot or raw
  memory file
* add annotations to this disassembly (or the control file) as you discover the
  purpose of each routine and data block
* use [skool2html.py](https://skoolkid.github.io/skoolkit/commands.html#skool2html-py)
  to convert a disassembly into a bunch of HTML files (with annotations in
  place, and the operands of CALL and JP instructions converted into
  hyperlinks)
* use [skool2asm.py](https://skoolkid.github.io/skoolkit/commands.html#skool2asm-py)
  to convert a disassembly into an assembler source file (also with annotations
  in place)
* use [skool2ctl.py](https://skoolkid.github.io/skoolkit/commands.html#skool2ctl-py)
  to convert a disassembly back into a control file (with annotations retained)
* use [skool2bin.py](https://skoolkid.github.io/skoolkit/commands.html#skool2bin-py)
  to convert a disassembly into a raw memory file
* use [tap2sna.py](https://skoolkid.github.io/skoolkit/commands.html#tap2sna-py)
  to convert a PZX, TAP or TZX file into a 'pristine' Z80 or SZX snapshot
* use [snapinfo.py](https://skoolkid.github.io/skoolkit/commands.html#snapinfo-py)
  to analyse a snapshot or raw memory file and list the BASIC program it
  contains, show register values, produce a call graph, find tile graphic data,
  find text, or find sequences of arbitrary byte values
* use [trace.py](https://skoolkid.github.io/skoolkit/commands.html#trace-py)
  to trace the execution of machine code in a snapshot or raw memory file
* use [rzxplay.py](https://skoolkid.github.io/skoolkit/commands.html#rzxplay-py)
  to trace the execution of machine code in an RZX file, and produce a code
  execution map for
  [sna2ctl.py](https://skoolkid.github.io/skoolkit/commands.html#sna2ctl-py)
* use [tapinfo.py](https://skoolkid.github.io/skoolkit/commands.html#tapinfo-py)
  to analyse the blocks in a PZX, TAP or TZX file, and list the BASIC program
  it contains
* use [rzxinfo.py](https://skoolkid.github.io/skoolkit/commands.html#rzxinfo-py)
  to analyse the blocks in an RZX file, and extract snapshots from it
* use [bin2tap.py](https://skoolkid.github.io/skoolkit/commands.html#bin2tap-py)
  to convert a snapshot or raw memory file into a PZX or TAP file
* use [bin2sna.py](https://skoolkid.github.io/skoolkit/commands.html#bin2sna-py)
  to convert a raw memory file into a Z80 or SZX snapshot
* use [snapmod.py](https://skoolkid.github.io/skoolkit/commands.html#snapmod-py)
  to modify the register values or memory contents in a Z80 or SZX snapshot
* use [sna2img.py](https://skoolkid.github.io/skoolkit/commands.html#sna2img-py)
  to convert graphic data in a disassembly, SCR file, snapshot or raw memory
  file into a PNG image

In an HTML disassembly produced by
[skool2html.py](https://skoolkid.github.io/skoolkit/commands.html#skool2html-py)
you can also:

* use the [image macros](https://skoolkid.github.io/skoolkit/skool-macros.html#image-macros)
  to build still and animated PNG images from graphic data
* use the [#AUDIO](https://skoolkid.github.io/skoolkit/skool-macros.html#audio)
  macro to build WAV files for sound effects and tunes
* use the [#R](https://skoolkid.github.io/skoolkit/skool-macros.html#r) macro
  in annotations to create hyperlinks between routines and data blocks that
  refer to each other
* use [[Bug:\*]](https://skoolkid.github.io/skoolkit/ref-files.html#box-pages),
  [[Fact:\*]](https://skoolkid.github.io/skoolkit/ref-files.html#box-pages) and
  [[Poke:\*]](https://skoolkid.github.io/skoolkit/ref-files.html#box-pages)
  sections in a ref file to neatly render lists of bugs, trivia and POKEs on
  separate pages

See the [user manual](https://skoolkid.github.io/skoolkit/) for more details
(mirror [here](https://skoolkid.gitlab.io/skoolkit/)).
