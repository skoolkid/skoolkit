#!/usr/bin/env python3
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

.. _Spectrum: https://en.wikipedia.org/wiki/ZX_Spectrum

Features
--------
With SkoolKit you can:

* use sna2ctl.py_ to generate a `control file`_ (an attempt to identify
  routines and data blocks by static analysis) from a snapshot (SNA, SZX or
  Z80) or raw memory file
* enable sna2ctl.py_ to generate a much better control file that more reliably
  distinguishes code from data by using a code execution map produced by an
  emulator
* use sna2skool.py_ along with this control file to produce a disassembly of a
  snapshot or raw memory file
* add annotations to this disassembly (or the control file) as you discover the
  purpose of each routine and data block
* use skool2html.py_ to convert a disassembly into a bunch of HTML files (with
  annotations in place, and the operands of CALL and JP instructions converted
  into hyperlinks)
* use skool2asm.py_ to convert a disassembly into an assembler source file
  (also with annotations in place)
* use skool2ctl.py_ to convert a disassembly back into a control file (with
  annotations retained)
* use skool2bin.py_ to convert a disassembly into a raw memory file
* use tap2sna.py_ to convert a TAP or TZX file into a 'pristine' Z80 snapshot
* use snapinfo.py_ to analyse a snapshot or raw memory file and list the BASIC
  program it contains, show register values, produce a call graph, find tile
  graphic data, find text, or find sequences of arbitrary byte values
* use tapinfo.py_ to analyse the blocks in a TAP or TZX file, and list the
  BASIC program it contains
* use bin2tap.py_ to convert a snapshot or raw memory file into a TAP file
* use bin2sna.py_ to convert a raw memory file into a Z80 snapshot
* use snapmod.py_ to modify the register values or memory contents in a Z80
  snapshot
* use sna2img.py_ to convert graphic data in a disassembly, SCR file, snapshot
  or raw memory file into a PNG image

In an HTML disassembly produced by skool2html.py_ you can also:

* use the `#UDG`_, `#UDGARRAY`_, `#FONT`_ and `#SCR`_ macros to build still and
  animated PNG images from graphic data
* use the `#R`_ macro in annotations to create hyperlinks between routines and
  data blocks that refer to each other
* use `[Bug:*]`_, `[Fact:*]`_ and `[Poke:*]`_ sections in a ref file to neatly
  render lists of bugs, trivia and POKEs on separate pages

For a demonstration of SkoolKit's capabilities, take a look at the complete
disassemblies of `Skool Daze`_, `Back to Skool`_, `Contact Sam Cruise`_,
`Manic Miner`_, `Jet Set Willy`_ and `Hungry Horace`_.

.. _bin2sna.py: https://skoolkid.github.io/skoolkit/commands.html#bin2sna-py
.. _bin2tap.py: https://skoolkid.github.io/skoolkit/commands.html#bin2tap-py
.. _skool2asm.py: https://skoolkid.github.io/skoolkit/commands.html#skool2asm-py
.. _skool2bin.py: https://skoolkid.github.io/skoolkit/commands.html#skool2bin-py
.. _skool2ctl.py: https://skoolkid.github.io/skoolkit/commands.html#skool2ctl-py
.. _skool2html.py: https://skoolkid.github.io/skoolkit/commands.html#skool2html-py
.. _sna2ctl.py: https://skoolkid.github.io/skoolkit/commands.html#sna2ctl-py
.. _sna2img.py: https://skoolkid.github.io/skoolkit/commands.html#sna2img-py
.. _sna2skool.py: https://skoolkid.github.io/skoolkit/commands.html#sna2skool-py
.. _snapinfo.py: https://skoolkid.github.io/skoolkit/commands.html#snapinfo-py
.. _snapmod.py: https://skoolkid.github.io/skoolkit/commands.html#snapmod-py
.. _tap2sna.py: https://skoolkid.github.io/skoolkit/commands.html#tap2sna-py
.. _tapinfo.py: https://skoolkid.github.io/skoolkit/commands.html#tapinfo-py
.. _#FONT: https://skoolkid.github.io/skoolkit/skool-macros.html#font
.. _#R: https://skoolkid.github.io/skoolkit/skool-macros.html#r
.. _#SCR: https://skoolkid.github.io/skoolkit/skool-macros.html#scr
.. _#UDG: https://skoolkid.github.io/skoolkit/skool-macros.html#udg
.. _#UDGARRAY: https://skoolkid.github.io/skoolkit/skool-macros.html#udgarray
.. _[Bug:*]: https://skoolkid.github.io/skoolkit/ref-files.html#box-pages
.. _[Fact:*]: https://skoolkid.github.io/skoolkit/ref-files.html#box-pages
.. _[Poke:*]: https://skoolkid.github.io/skoolkit/ref-files.html#box-pages
.. _Skool Daze: https://skoolkit.ca/disassemblies/skool_daze/
.. _Back to Skool: https://skoolkit.ca/disassemblies/back_to_skool/
.. _Contact Sam Cruise: https://skoolkit.ca/disassemblies/contact_sam_cruise/
.. _Manic Miner: https://skoolkit.ca/disassemblies/manic_miner/
.. _Jet Set Willy: https://skoolkit.ca/disassemblies/jet_set_willy/
.. _Hungry Horace: https://skoolkit.ca/disassemblies/hungry_horace/

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

.. _documentation: https://skoolkid.github.io/skoolkit/
.. _control file: https://skoolkid.github.io/skoolkit/control-files.html
"""

setup(
    name='skoolkit',
    version=VERSION,
    author='Richard Dymond',
    author_email='rjdymond@gmail.com',
    license='GPLv3',
    url='https://skoolkit.ca',
    description="A suite of tools for creating disassemblies of ZX Spectrum games",
    long_description=LONG_DESCRIPTION,
    packages=['skoolkit'],
    package_data={'skoolkit': ['resources/*.css']},
    scripts=[
        'bin2sna.py',
        'bin2tap.py',
        'skool2asm.py',
        'skool2bin.py',
        'skool2ctl.py',
        'skool2html.py',
        'sna2ctl.py',
        'sna2img.py',
        'sna2skool.py',
        'snapinfo.py',
        'snapmod.py',
        'tap2sna.py',
        'tapinfo.py'
    ],
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Topic :: Software Development :: Disassemblers',
        'Topic :: Utilities'
    ]
)
