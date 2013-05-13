What is SkoolKit?
=================
SkoolKit is a collection of utilities that can be used to disassemble a
Spectrum_ game (or indeed any piece of Spectrum software written in machine
code) into a format known as a `skool` file. Then, from this `skool` file, you
can use SkoolKit to create a browsable disassembly in HTML format, or a
re-assemblable disassembly in ASM format. So the `skool` file is - from start
to finish as you develop it by organising and annotating the code - the common
'source' for both the reader-friendly HTML version of the disassembly, and the
developer- and assembler-friendly ASM version of the disassembly.

.. _Spectrum: http://en.wikipedia.org/wiki/ZX_Spectrum

The latest stable release of SkoolKit can always be obtained from
`pyskool.ca <http://pyskool.ca/?page_id=177>`__; the latest development version
can be found on `GitHub <http://github.com/skoolkid/skoolkit>`__.

Features
--------
Besides disassembling a Spectrum game into a list of Z80 instructions, SkoolKit
can also:

* Build PNG or GIF images from graphic data in the game snapshot (using the
  :ref:`UDG`, :ref:`UDGARRAY`, :ref:`FONT` and :ref:`SCR` macros)
* Create hyperlinks between routines and data blocks that refer to each other
  (by use of the :ref:`R` macro in annotations, and automatically in the
  operands of ``CALL`` and ``JP`` instructions)
* Neatly render lists of bugs, trivia and POKEs on separate pages (using
  :ref:`ref-Bug`, :ref:`ref-Fact` and :ref:`ref-Poke` sections in a `ref` file)
* Produce ASM files that include bugfixes declared in the `skool` file (with
  :ref:`ofix`, :ref:`bfix` and other ASM directives)
* Produce TAP files from assembled code (using :ref:`bin2tap.py`)

For a demonstration of SkoolKit's capabilities, take a look at the complete
disassemblies of `Skool Daze`_, `Back to Skool`_ and `Contact Sam Cruise`_. The
latest stable releases of the source `skool` files for these disassemblies can
always be obtained from `pyskool.ca <http://pyskool.ca/?page_id=113>`__; the
latest development versions can be found on
`GitHub <http://github.com/skoolkid/disassemblies>`__.

.. _Skool Daze: http://pyskool.ca/disassemblies/skool_daze/
.. _Back to Skool: http://pyskool.ca/disassemblies/back_to_skool/
.. _Contact Sam Cruise: http://pyskool.ca/disassemblies/contact_sam_cruise/

Licence
-------
SkoolKit is free software: you can redistribute it and/or modify it under the
terms of the GNU General Public License as published by the Free Software
Foundation, either version 3 of the License, or (at your option) any later
version.

See the file 'COPYING' (distributed with SkoolKit) for the full text of the
licence.
