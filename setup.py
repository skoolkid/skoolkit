#!/usr/bin/env python
# -*- coding: utf-8 -*-
from distutils.core import setup

from skoolkit import VERSION

LONG_DESCRIPTION = """
SkoolKit
========
SkoolKit is a collection of utilities that can be used to disassemble a
Spectrum_ game (or indeed any piece of Spectrum software written in machine
code) into a format known as a `skool` file. Then, from this `skool` file, you
can use SkoolKit to create a browsable disassembly in HTML format, or a
re-assemblable disassembly in ASM format. So the `skool` file is - from start
to finish as you develop it by organising and annotating the code - the common
'source' for both the reader-friendly HTML version of the disassembly, and the
developer- and assembler-friendly ASM version of the disassembly.

.. _Spectrum: http://en.wikipedia.org/wiki/ZX_Spectrum

Features
--------
SkoolKit can:

* convert a TAP or TZX file into a 'pristine' snapshot (using `tap2sna.py`)
* disassemble SNA, Z80 and SZX snapshots as well as raw memory files
* distinguish code from data by using a code execution map produced by an
  emulator
* build still and animated PNG/GIF images from graphic data in the game
  snapshot (using the ``#UDG``, ``#UDGARRAY``, ``#FONT`` and ``#SCR`` macros)
* create hyperlinks between routines and data blocks that refer to each other
  (by use of the ``#R`` macro in annotations, and automatically in the
  operands of ``CALL`` and ``JP`` instructions)
* neatly render lists of bugs, trivia and POKEs on separate pages (using
  ``[Bug]``, ``[Fact]`` and ``[Poke]`` sections in a `ref` file)
* produce ASM files that include bugfixes declared in the `skool` file (with
  ``@ofix``, ``@bfix`` and other ASM directives)
* produce TAP files from assembled code (using `bin2tap.py`)

For a demonstration of SkoolKit's capabilities, take a look at the complete
disassemblies of `Skool Daze`_, `Back to Skool`_, `Contact Sam Cruise`_,
`Manic Miner`_ and `Jet Set Willy`_.

.. _Skool Daze: http://skoolkit.ca/disassemblies/skool_daze/
.. _Back to Skool: http://skoolkit.ca/disassemblies/back_to_skool/
.. _Contact Sam Cruise: http://skoolkit.ca/disassemblies/contact_sam_cruise/
.. _Manic Miner: http://skoolkit.ca/disassemblies/manic_miner/
.. _Jet Set Willy: http://skoolkit.ca/disassemblies/jet_set_willy/

Quick start guide
-----------------
SkoolKit includes fairly detailed documentation_, but if you want to get up and
running quickly, here goes.

To convert a SNA, Z80 or SZX snapshot of a Spectrum game into a `skool` file
(so that it can be converted into an HTML or ASM disassembly)::

  $ sna2skool.py game.z80 > game.skool

To split the disassembly up into code and data blocks, you'll need a
`control file`_.

To turn this `skool` file into an HTML disassembly::

  $ skool2html.py game.skool

To turn it into an ASM file that can be fed to an assembler::

  $ skool2asm.py game.skool > game.asm

.. _documentation: http://skoolkit.ca/docs/skoolkit/
.. _control file: http://skoolkit.ca/docs/skoolkit/control-files.html
"""

setup(
    name='skoolkit',
    version=VERSION,
    author='Richard Dymond',
    author_email='rjdymond@gmail.com',
    license='GPLv3',
    url='http://skoolkit.ca/',
    description="A suite of tools for creating disassemblies of ZX Spectrum games",
    long_description=LONG_DESCRIPTION,
    packages=['skoolkit'],
    package_data={'skoolkit': ['resources/*.css']},
    scripts=[
        'bin2tap.py',
        'skool2asm.py',
        'skool2bin.py',
        'skool2ctl.py',
        'skool2html.py',
        'skool2sft.py',
        'sna2skool.py',
        'tap2sna.py',
        'tapinfo.py'
    ],
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Topic :: Software Development :: Disassemblers',
        'Topic :: Utilities'
    ]
)
