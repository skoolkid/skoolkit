SkoolKit 4.x changelog
======================

4.5 (2015-07-04)
----------------
* Added support to :ref:`tap2sna.py` for TZX block type 0x14 (pure data), for
  loading the first and last bytes of a tape block (which are usually, but not
  always, the flag and parity bytes), and for modifying memory with XOR and ADD
  operations
* Added the ``--clear`` option to :ref:`bin2tap.py` (to use a CLEAR command in
  the BASIC loader and leave the stack pointer alone)
* Added the ``--end`` option to :ref:`bin2tap.py` and the ability to convert
  SNA, SZX and Z80 snapshots
* Added ``--start`` and ``--end`` options to :ref:`skool2asm.py`,
  :ref:`skool2ctl.py` and :ref:`skool2sft.py`
* The ``--start`` and ``--end`` options of :ref:`sna2skool.py` now take effect
  when reading a control file or a skool file template
* Added support to :ref:`skool2ctl.py` and :ref:`skool2sft.py` for preserving
  characters in DEFW statements (e.g. ``DEFW "!"``)
* Added support for characters in DEFS statements (e.g. ``DEFS 10,"!"``)
* Fixed how :ref:`tap2sna.py` compresses a RAM block that contains a single
  ``ED`` followed by five or more identical values (e.g. ``ED0101010101``)
* Fixed the erroneous replacement of DEFS operands with labels
* Fixed how instruction-level comments that contain braces are restored from a
  control file
* Fixed the handling of terminal compound sublengths on 'S' directives (e.g.
  ``S 30000,10,5:32``)

4.4 (2015-05-23)
----------------
* Added support to control files and skool file templates for specifying that
  numeric values in instruction operands be rendered as characters or in a
  specific base
* Added support for :ref:`ssubBlockDirectives`
* Added the ``--end`` option to :ref:`sna2skool.py` (for specifying the address
  at which to stop disassembling)
* Added the ``--ctl-hex-lower`` option to :ref:`sna2skool.py` (for writing
  addresses in lower case hexadecimal format in the generated control file)
* Added the ``--hex-lower`` option to :ref:`skool2ctl.py` and
  :ref:`skool2sft.py` (for writing addresses in lower case hexadecimal format)
* Fixed the parsing of DEFB and DEFM statements that contain semicolons
* Fixed the base conversion of ``LD (HL),n`` instructions that contain
  extraneous whitespace (e.g. ``LD ( HL ),5``)
* Fixed the erroneous replacement of RST operands with labels in HTML output
* Fixed the handling of uncompressed version 1 Z80 snapshots by
  :ref:`sna2skool.py`

4.3 (2015-02-14)
----------------
* Added support for block start comments (which appear after the register
  section and before the first instruction in a routine or data block)
* Added the ``CodeFiles`` parameter to the :ref:`paths` section (for specifying
  the format of a disassembly page filename based on the address of the routine
  or data block)
* Added the ``AddressAnchor`` parameter to the :ref:`ref-game` section (for
  specifying the format of the anchors attached to instructions on disassembly
  pages and entries on memory map pages)
* The :ref:`font`, :ref:`scr` and :ref:`udg` macros now have the ability to
  create frames for an animated image
* Added the ``--line-width`` option to :ref:`sna2skool.py` (for specifying the
  maximum line width of the skool file)
* Writing an ASM directive in a skool file can now be done by starting a line
  with ``@``; writing an ASM directive by starting a line with ``; @`` is
  deprecated
* Added the ``@`` directive for declaring ASM directives in a control file; the
  old style of declaring ASM directives (``; @directive:address[=value]``) is
  deprecated
* Fixed the *flip_udgs()* and *rotate_udgs()* methods on HtmlWriter so that
  they work with a UDG array that contains the same UDG in more than one place
* Fixed the bug that prevents register descriptions from being HTML-escaped
* Fixed the erroneous substitution of address labels in instructions that have
  8-bit numeric operands

4.2 (2014-12-07)
----------------
* Added support for :ref:`control directive loops <ctlLoops>` using the ``L``
  directive
* Added support to control files for preserving the location of :ref:`ignoreua`
  directives
* Each :ref:`image macro <imageMacros>` now has the ability to specify alt text
  for the ``<img>`` element it produces
* Added support for splitting register descriptions over multiple lines
* :ref:`skool2asm.py` now warns about unconverted addresses in register
  descriptions, and the :ref:`ignoreua` directive can be used to suppress such
  warnings
* Added the :ref:`t_table`, :ref:`t_table_cell`, :ref:`t_table_header_cell` and
  :ref:`t_table_row` templates (for formatting tables produced by the
  :ref:`TABLE` macro)
* Added the :ref:`t_list` and :ref:`t_list_item` templates (for formatting
  lists produced by the :ref:`LIST` macro)
* Fixed the bug that prevents the expansion of skool macros in the intro text
  of a ``Changelog:*`` section

4.1.1 (2014-09-20)
------------------
* Updated links to SkoolKit's new home at `skoolkit.ca <http://skoolkit.ca>`_
* Added example control and ref files for `Hungry Horace`_
* Removed the Manic Miner disassembly from the SkoolKit distribution; it is now
  being developed separately `here <https://github.com/skoolkid/manicminer>`__

.. _Hungry Horace: http://www.worldofspectrum.org/infoseekid.cgi?id=0002390

4.1 (2014-08-30)
----------------
* Added the ``--search`` option to :ref:`skool2html.py` (to add a directory to
  the resource search path)
* Added the ``--writer`` option to :ref:`skool2html.py` (for specifying the
  HTML writer class to use)
* Added the ``--writer`` option to :ref:`skool2asm.py` (for specifying the
  ASM writer class to use)
* Added the ``LinkInternalOperands`` parameter to the :ref:`ref-Game` section
  (for specifying whether to hyperlink instruction operands that refer to an
  address in the same entry)
* Register sections in ``b``, ``g``, ``s``, ``t``, ``u`` and ``w`` blocks are
  now included in the output of :ref:`skool2asm.py` and :ref:`skool2html.py`
* Fixed how the address '0' is rendered in HTML output when converted to
  decimal or hexadecimal
* Fixed the bug that creates a broken hyperlink in a DEFW statement or LD
  instruction that refers to the address of an ignored entry
* Removed the Jet Set Willy disassembly from the SkoolKit distribution; it is
  now being developed separately here_

.. _here: https://github.com/skoolkid/jetsetwilly

4.0 (2014-05-25)
----------------
* Every HTML page is built from templates defined in :ref:`template` sections
  in the ref file
* Added support for keyword arguments to the :ref:`FONT`, :ref:`SCR`,
  :ref:`UDG` and :ref:`UDGARRAY` macros
* Added the ``mask`` parameter to the :ref:`UDG` and :ref:`UDGARRAY` macros
  (for specifying the type of mask to apply)
* Added support for defining page headers in the :ref:`pageHeaders` section of
  the ref file
* Added the ``--ref-file`` and ``--ref-sections`` options to
  :ref:`skool2html.py` (to show the entire default ref file or individual
  sections of it)
* Added the ``EntryDescriptions`` parameter to the :ref:`memoryMap` section
  (for specifying whether to display entry descriptions on a memory map page)
* Added the ``LengthColumn`` parameter to the :ref:`memoryMap` section (for
  specifying whether to display the 'Length' column on a memory map page)
