What is SkoolKit?
=================
SkoolKit is a collection of utilities that can be used to disassemble a
Spectrum_ game (or indeed any piece of Spectrum software written in machine
code) into a format known as a skool file. Then, from this skool file, you can
use SkoolKit to create a browsable disassembly in HTML format, or a
re-assemblable disassembly in assembly language. So the skool file is - from
start to finish as you develop it by organising and annotating the code - the
common 'source' for both the reader-friendly HTML version of the disassembly,
and the developer- and assembler-friendly version of the disassembly.

.. _Spectrum: https://en.wikipedia.org/wiki/ZX_Spectrum

The latest stable release of SkoolKit can always be obtained from
`skoolkit.ca`_; the latest development version can be found on GitHub_.

.. _skoolkit.ca: https://skoolkit.ca
.. _GitHub: https://github.com/skoolkid/

Features
--------
With SkoolKit you can:

* use :ref:`sna2ctl.py` to generate a :ref:`control file <controlFiles>` (an
  attempt to identify routines and data blocks by static analysis) from a
  snapshot (SNA, SZX or Z80) or raw memory file
* enable :ref:`sna2ctl.py` to generate a much better control file that more
  reliably distinguishes code from data by using a code execution map produced
  by an emulator
* use :ref:`sna2skool.py` along with this control file to produce a disassembly
  of a snapshot or raw memory file
* add annotations to this disassembly (or the control file) as you discover the
  purpose of each routine and data block
* use :ref:`skool2html.py` to convert a disassembly into a bunch of HTML files
  (with annotations in place, and the operands of CALL and JP instructions
  converted into hyperlinks)
* use :ref:`skool2asm.py` to convert a disassembly into an assembler source
  file (also with annotations in place)
* use :ref:`skool2ctl.py` to convert a disassembly back into a control file
  (with annotations retained)
* use :ref:`skool2bin.py` to convert a disassembly into a raw memory file
* use :ref:`tap2sna.py` to convert a TAP or TZX file into a 'pristine' Z80
  snapshot
* use :ref:`snapinfo.py` to analyse a snapshot or raw memory file and list the
  BASIC program it contains, show register values, produce a call graph, find
  tile graphic data, find text, or find sequences of arbitrary byte values
* use :ref:`tapinfo.py` to analyse the blocks in a TAP or TZX file, and list
  the BASIC program it contains
* use :ref:`bin2tap.py` to convert a snapshot or raw memory file into a TAP
  file
* use :ref:`bin2sna.py` to convert a raw memory file into a Z80 snapshot
* use :ref:`snapmod.py` to modify the register values or memory contents in a
  Z80 snapshot
* use :ref:`sna2img.py` to convert graphic data in a disassembly, SCR file,
  snapshot or raw memory file into a PNG image

In an HTML disassembly produced by :ref:`skool2html.py` you can also:

* use the :ref:`image macros <imageMacros>` to build still and animated PNG
  images from graphic data
* use the :ref:`AUDIO` macro to build WAV files for sound effects and tunes
* use the :ref:`R` macro in annotations to create hyperlinks between routines
  and data blocks that refer to each other
* use :ref:`[Bug:*] <boxpages>`, :ref:`[Fact:*] <boxpages>` and
  :ref:`[Poke:*] <boxpages>` sections in a ref file to neatly render lists of
  bugs, trivia and POKEs on separate pages

For a demonstration of SkoolKit's capabilities, take a look at the complete
disassemblies of `Skool Daze`_, `Back to Skool`_, `Contact Sam Cruise`_,
`Manic Miner`_, `Jet Set Willy`_ and `Hungry Horace`_. The latest stable
releases of the source skool files for these disassemblies can always be
obtained from `skoolkit.ca`_; the latest development versions can be found on
GitHub_.

.. _Skool Daze: https://skoolkit.ca/disassemblies/skool_daze/
.. _Back to Skool: https://skoolkit.ca/disassemblies/back_to_skool/
.. _Contact Sam Cruise: https://skoolkit.ca/disassemblies/contact_sam_cruise/
.. _Manic Miner: https://skoolkit.ca/disassemblies/manic_miner/
.. _Jet Set Willy: https://skoolkit.ca/disassemblies/jet_set_willy/
.. _Hungry Horace: https://skoolkit.ca/disassemblies/hungry_horace/

Authors
-------
SkoolKit is developed and maintained by Richard Dymond, and contains
contributions from Philip M Anderson.

Licence
-------
SkoolKit is free software: you can redistribute it and/or modify it under the
terms of the GNU General Public License as published by the Free Software
Foundation, either version 3 of the License, or (at your option) any later
version.

See the file 'COPYING' (distributed with SkoolKit) for the full text of the
licence.

48K ZX Spectrum ROM
-------------------
A copy of the 48K ZX Spectrum ROM is included with SkoolKit
(`skoolkit/resources/48.rom`). The copyright in this ROM is held by Amstrad,
who have kindly `given permission`_ for it to be redistributed.

.. _given permission: https://groups.google.com/g/comp.sys.amstrad.8bit/c/HtpBU2Bzv_U/m/HhNDSU3MksAJ
