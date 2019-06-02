What is SkoolKit?
=================
SkoolKit is a collection of utilities that can be used to disassemble a
Spectrum_ game (or indeed any piece of Spectrum software written in machine
code) into a format known as a skool file. Then, from this skool file, you can
use SkoolKit to create a browsable disassembly in HTML format, or a
re-assemblable disassembly in ASM format. So the skool file is - from start to
finish as you develop it by organising and annotating the code - the common
'source' for both the reader-friendly HTML version of the disassembly, and the
developer- and assembler-friendly ASM version of the disassembly.

.. _Spectrum: https://en.wikipedia.org/wiki/ZX_Spectrum

The latest stable release of SkoolKit can always be obtained from
`skoolkit.ca`_; the latest development version can be found on GitHub_.

.. _skoolkit.ca: https://skoolkit.ca
.. _GitHub: https://github.com/skoolkid/

Features
--------
SkoolKit can:

* convert a TAP or TZX file into a 'pristine' snapshot (using
  :ref:`tap2sna.py`)
* disassemble SNA, Z80 and SZX snapshots as well as raw memory files
* distinguish code from data by using a code execution map produced by an
  emulator
* build still and animated PNG/GIF images from graphic data in the game
  snapshot (using the :ref:`UDG`, :ref:`UDGARRAY`, :ref:`FONT` and :ref:`SCR`
  macros)
* create hyperlinks between routines and data blocks that refer to each other
  (by use of the :ref:`R` macro in annotations, and automatically in the
  operands of ``CALL`` and ``JP`` instructions)
* neatly render lists of bugs, trivia and POKEs on separate pages (using
  :ref:`[Bug:*] <boxpages>`, :ref:`[Fact:*] <boxpages>` and
  :ref:`[Poke:*] <boxpages>` sections in a ref file)
* produce ASM files that include bugfixes declared in the skool file (with
  :ref:`ofix`, :ref:`bfix` and other ASM directives)
* produce TAP files from assembled code (using :ref:`bin2tap.py`)

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
