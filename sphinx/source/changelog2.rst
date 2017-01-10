.. _skoolkit2x:

SkoolKit 2.x changelog
======================
2.5 (2012-02-22)
----------------
* Added support for :ref:`memoryMap` sections in ref files (for defining the
  properties of memory map pages); removed support for the ``[MapDetails]``
  section accordingly
* Added support for multiple style sheets per HTML disassembly (by separating
  file names with a semicolon in the ``StyleSheet`` parameter in the
  :ref:`paths` section of the ref file)
* Added support for multiple JavaScript files per HTML disassembly (by
  separating file names with a semicolon in the ``JavaScript`` parameter in the
  :ref:`paths` section of the ref file)

2.4.1 (2012-01-30)
------------------
* The :ref:`ignoreua` directive can now be used on entry titles, entry
  descriptions, mid-block comments and block end comments in addition to
  instruction-level comments; the `@ignoredua` and `@ignoremrcua` directives
  are correspondingly deprecated
* The :ref:`space` macro now supports the syntax ``#SPACE([num])``, which can
  be useful to distinguish it from adjacent text where necessary

2.4 (2012-01-10)
----------------
* Added the :ref:`skool2sft.py` command (for creating
  :ref:`skool file templates <skoolFileTemplates>`)
* Added support to :ref:`skool2ctl.py` for preserving some ASM directives in
  control files
* Enhanced the :ref:`UDG` and :ref:`UDGARRAY` macros so that images can be
  rotated
* Added the ability to separate paragraphs in a skool file by using a dot
  (``.``) on a line of its own; removed support for the redundant ``#P`` macro
  accordingly

2.3.1 (2011-11-15)
------------------
* Added support to :ref:`skool2html.py` for multiple ref files per disassembly
* Enhanced the :ref:`UDG` and :ref:`UDGARRAY` macros so that images can be
  flipped horizontally and vertically
* Enhanced the :ref:`POKES` macro so that multiple pokes may be specified
* Added support for the ``#FACT`` and ``#POKE`` macros in ASM mode
* When the link text of a ``#BUG``, ``#FACT`` or ``#POKE`` macro is left blank,
  the title of the corresponding bug, trivia or poke entry is substituted
* Fixed the parsing of link text in skool macros in ASM mode so that nested
  parentheses are handled correctly
* Fixed the rendering of table borders in ASM mode where cells with rowspan > 1
  in columns other than the first extend to the bottom row

2.3 (2011-10-31)
----------------
* Fixed the bug where the operands in substitute instructions defined by
  ``@bfix``, ``@ofix``, ``@isub``, ``@ssub`` and ``@rsub`` directives are not
  converted to decimal or hexadecimal when using the ``-D`` or ``-H`` option of
  :ref:`skool2asm.py` or :ref:`skool2html.py`
* Removed the source files for the Skool Daze, Back to Skool and Contact Sam
  Cruise disassemblies from the SkoolKit distribution; they are now available
  as `separate downloads`_

.. _separate downloads: http://skoolkit.ca/?page_id=113

2.2.5 (2011-10-17)
------------------
* Enhanced the :ref:`UDGARRAY` macro so that masks can be specified
* Added the ``-p`` option to :ref:`bin2tap.py` (to set the stack pointer)
* Fixed the parsing of link text in ``#BUG``, ``#FACT``, ``#POKE`` and other
  skool macros so that nested parentheses are handled correctly
* Fixed the handling of version 1 Z80 snapshots by :ref:`sna2skool.py`
* Added support for the ``IndexPageId`` and ``Link`` parameters in
  ``[OtherCode:*]`` sections of the ref file
* Reintroduced support for ``[Changelog:*]`` sections in ref files
* Added 'Changelog' pages to the Skool Daze, Back to Skool and Contact Sam
  Cruise disassemblies
* Updated the Contact Sam Cruise disassembly

2.2.4 (2011-08-10)
------------------
* Added support for the `@ignoredua` ASM directive
* :ref:`skool2asm.py <skool2asm.py>` automatically decreases the width of the
  comment field for a 'wide' instruction instead of printing a warning
* :ref:`bin2tap.py <bin2tap.py>` can handle binary snapshot files with ORG
  addresses as low as 16398
* Fixed the bug in :ref:`bin2tap.py <bin2tap.py>` that prevents the START
  address from defaulting to the ORG address when the ORG address is specified
  with the ``-o`` option
* Added ASM directives to `csc.skool` so that it works with
  :ref:`skool2asm.py <skool2asm.py>`
* Updated the Contact Sam Cruise disassembly

2.2.3 (2011-07-15)
------------------
Updated the Contact Sam Cruise disassembly; it is now 'complete'.

2.2.2 (2011-06-02)
------------------
* Added support for the :ref:`end` ASM directive
* Added ASM directives to `{bts,csc,sd}-{load,save,start}.skool` to make them
  work with :ref:`skool2asm.py <skool2asm.py>`
* :ref:`skool2asm.py <skool2asm.py>`, :ref:`skool2ctl.py <skool2ctl.py>` and
  :ref:`skool2html.py <skool2html.py>` can read from standard input
* Fixed the bug that made :ref:`sna2skool.py <sna2skool.py>` generate a control
  file with a code block at 65535 for a snapshot that ends with a sequence of
  zeroes
* Unit test `test_skool2html.py:Skool2HtmlTest.test_html` now works without an
  internet connection

2.2.1 (2011-05-24)
------------------
* SkoolKit can now be installed as a Python package using ``setup.py install``
* Unit tests are included in the `tests` directory
* Man pages for SkoolKit's :ref:`command scripts <commands>` are included in
  the `man` directory
* Added 'Developer reference' documentation
* Fixed the bugs that made :ref:`skool2html.py <skool2html.py>` produce invalid
  XHTML

2.2 (2011-05-10)
----------------
* Changed the syntax of the :ref:`skool2html.py <skool2html.py>` command (it no
  longer writes the Skool Daze and Back to Skool disassemblies by default)
* Fixed the bug that prevented :ref:`skool2asm.py <skool2asm.py>` from working
  with a zero-argument skool macro (such as ``#C``) at the end of a sentence
* Fixed the ``-w`` option of :ref:`skool2asm.py <skool2asm.py>` (it really does
  suppress all warnings now)
* Fixed how :ref:`sna2skool.py <sna2skool.py>` handles ``#P`` macros (it now
  writes a newline before and after each one)
* Fixed the bug that made :ref:`sna2skool.py <sna2skool.py>` omit the '*'
  control directive from routine entry points when the ``-L`` option was used
* ASM labels are now unaffected by the ``-l`` (lower case) and ``-u`` (upper
  case) options of :ref:`skool2asm.py <skool2asm.py>`
* Added support for the '*' notation in statement length lists in sub-block
  control directives (e.g. ``B 32768,239,16*14,15``)
* Updated the Skool Daze disassembly
* Updated the Back to Skool disassembly

2.1.2 (2011-04-28)
------------------
* Added the ``-L`` option to :ref:`sna2skool.py <sna2skool.py>` (to write the
  disassembly in lower case)
* Added the ``-i`` option to :ref:`skool2html.py <skool2html.py>` (to specify
  the image library to use)
* In control files, DEFM, DEFW and DEFS statement lengths in ``T``, ``W`` and
  ``Z`` sub-blocks may be declared
* Fixed the bug in :ref:`skool2asm.py <skool2asm.py>`'s handling of the
  ``#SPACE`` macro that prevented it from working with `csc.skool`
* Fixed the bug that made :ref:`skool2asm.py <skool2asm.py>` produce invalid
  output when run on `sd.skool` with the ``-H`` and ``-f3`` options

2.1.1 (2011-04-16)
------------------
* Added the ``-l``, ``-u``, ``-D`` and ``-H`` options to
  :ref:`skool2html.py <skool2html.py>` (to write the disassembly in lower case,
  upper case, decimal or hexadecimal)
* Added the ``-u``, ``-D`` and ``-H`` options to
  :ref:`skool2asm.py <skool2asm.py>` (to write the disassembly in upper case,
  decimal or hexadecimal)
* In control files, an instruction-level comment that spans a group of two or
  more sub-blocks of different types may be declared with an ``M`` directive
* Updated the incomplete Contact Sam Cruise disassembly

2.1 (2011-04-03)
----------------
* Added support for hexadecimal disassemblies
* Added the :ref:`LINK` macro (for creating hyperlinks to other pages in an
  HTML disassembly)
* Added the ability to define custom pages in an HTML disassembly using
  ``[Page:*]`` and ``[PageContent:*]`` sections in the ref file
* Added the ``-o`` option to :ref:`skool2html.py <skool2html.py>` (to overwrite
  existing image files)
* Optional parameters in any position in a skool macro may be left blank
* In control files, DEFB statement lengths in multi-line ``B`` sub-blocks may
  be declared
* Updated the Skool Daze disassembly
* Updated the Back to Skool disassembly
* Updated the incomplete Contact Sam Cruise disassembly

2.0.6 (2011-03-09)
------------------
* :ref:`sna2skool.py <sna2skool.py>` can read and write hexadecimal numbers in
  a control file
* :ref:`skool2ctl.py <skool2ctl.py>` can write hexadecimal numbers in a control
  file
* :ref:`sna2skool.py <sna2skool.py>` no longer chokes on blank lines in a
  control file
* Updated the incomplete Contact Sam Cruise disassembly

2.0.5 (2011-02-09)
------------------
* Added the :ref:`UDGARRAY` macro (for creating images of blocks of UDGs)
* Enhanced the :ref:`FONT` macro so that it works with regular 8x8 fonts as
  well as the Skool game fonts
* Enhanced the :ref:`SCR` macro so that it can take screenshots of rectangular
  portions of the screen
* The contents of the 'Other graphics' page of a disassembly are now defined in
  the ``[Graphics]`` section of the ref file
* Added the ability to define the layout of the disassembly index page in the
  ``[Index]`` and ``[Index:*:*]`` sections of the ref file
* Added the ability to define page titles in the ``[Titles]`` section of the
  ref file
* Added the ability to define page link text in the ``[Links]`` section of the
  ref file
* Added the ability to define the image colour palette in the ``[Colours]``
  section of the ref file
* Fixed the bug in :ref:`sna2skool.py <sna2skool.py>` that prevented it from
  generating a control file for a snapshot with the final byte of a 'RET',
  'JR d', or 'JP nn' instruction at 65535
* Updated the incomplete Contact Sam Cruise disassembly

2.0.4 (2010-12-16)
------------------
Updated the incomplete Contact Sam Cruise disassembly.

2.0.3 (2010-12-08)
------------------
Updated the incomplete Contact Sam Cruise disassembly.

2.0.2 (2010-12-01)
------------------
* Fixed the ``#EREFS``, ``#REFS`` and ``#TAPS`` macros
* Fixed the bug where the end comment for the last entry in a skool file is not
  parsed
* Updated the incomplete Contact Sam Cruise disassembly

2.0.1 (2010-11-28)
------------------
* Added the ``-r`` option to :ref:`skool2html.py <skool2html.py>` (for
  specifying a ref file)
* Added the ``-o``, ``-r``, and ``-l`` options to
  :ref:`sna2skool.py <sna2skool.py>`, along with the ability to read binary
  (raw memory) files
* Fixed :ref:`skool2ctl.py <skool2ctl.py>` so that it correctly creates
  sub-blocks for commentless DEF{B,M,S,W} statements, and writes the length of
  a sub-block that is followed by a mid-routine comment
* Updated the incomplete Contact Sam Cruise disassembly

2.0 (2010-11-23)
----------------
* Updated the Back to Skool disassembly
* Enhanced the :ref:`R` macro to support 'other code' disassemblies, thus
  making the ``#ASM``, ``#LOAD``, ``#SAVE`` and ``#START`` macros obsolete
* Split `load.skool`, `save.skool` and `start.skool` into separate files for
  each Skool game
* Added documentation on the :ref:`ref file sections <refFiles>`
* Simplified SkoolKit by removing all instances of and support for ref file
  macros and skool directives
* Added files that were missing from SkoolKit 1.4: `csc-load.skool`,
  `csc-save.skool` and `csc-start.skool`
