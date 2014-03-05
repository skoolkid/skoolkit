#!/usr/bin/env python
# -*- coding: utf-8 -*-
from distutils.core import setup
import shutil

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
Besides disassembling a Spectrum game into a list of Z80 instructions, SkoolKit
can also:

* Build PNG or GIF images from graphic data in the game snapshot (using the
  ``#UDG``, ``#UDGARRAY``, ``#FONT`` and ``#SCR`` macros)
* Create hyperlinks between routines and data blocks that refer to each other
  (by use of the ``#R`` macro in annotations, and automatically in the
  operands of ``CALL`` and ``JP`` instructions)
* Neatly render lists of bugs, trivia and POKEs on separate pages (using
  ``[Bug]``, ``[Fact]`` and ``[Poke]`` sections in a `ref` file)
* Produce ASM files that include bugfixes declared in the `skool` file (with
  ``@ofix``, ``@bfix`` and other ASM directives)
* Produce TAP files from assembled code (using `bin2tap.py`)

For a demonstration of SkoolKit's capabilities, take a look at the complete
disassemblies of `Skool Daze`_, `Back to Skool`_ and `Contact Sam Cruise`_.

.. _Skool Daze: http://pyskool.ca/disassemblies/skool_daze/
.. _Back to Skool: http://pyskool.ca/disassemblies/back_to_skool/
.. _Contact Sam Cruise: http://pyskool.ca/disassemblies/contact_sam_cruise/

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

.. _documentation: http://pyskool.ca/docs/skoolkit/
.. _control file: http://pyskool.ca/docs/skoolkit/control-files.html
"""

PACKAGE_DIR = 'build/skoolkit-pkg'

shutil.rmtree(PACKAGE_DIR, True)
shutil.copytree('skoolkit', PACKAGE_DIR, ignore=shutil.ignore_patterns('*.pyc'))
shutil.copytree('resources', '{0}/resources'.format(PACKAGE_DIR))
shutil.copytree('examples', '{0}/examples'.format(PACKAGE_DIR))

setup(
    name='skoolkit',
    version=VERSION,
    author='Richard Dymond',
    author_email='rjdymond@gmail.com',
    license='GPLv3',
    url='http://pyskool.ca/?page_id=177',
    description="A suite of tools for creating disassemblies of ZX Spectrum games",
    long_description=LONG_DESCRIPTION,
    packages=['skoolkit'],
    package_dir={'skoolkit': PACKAGE_DIR},
    package_data={'skoolkit': ['resources/*', 'examples/*']},
    scripts=['bin2tap.py', 'skool2asm.py', 'skool2ctl.py', 'skool2html.py', 'skool2sft.py', 'sna2skool.py', 'tap2sna.py'],
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3',
        'Topic :: Software Development :: Disassemblers',
        'Topic :: Utilities'
    ]
)
