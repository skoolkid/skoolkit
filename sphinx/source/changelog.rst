Changelog
=========

7.2 (2019-06-02)
----------------
* Added support to control files for specifying comments over multiple lines
  (by using the :ref:`dot and colon directives <dotDirective>`)
* Added support to :ref:`skool2ctl.py <skool2ctl-conf>` for reading
  configuration from `skoolkit.ini`
* Added the ``--ini`` and ``--show-config`` options to :ref:`skool2ctl.py` (for
  setting the value of a configuration parameter and for showing all
  configuration parameter values)
* Added the ``--keep-lines`` option to :ref:`skool2ctl.py` (for preserving line
  breaks in comments)
* Added support for :ref:`asmTemplates` (used to format each line of output
  produced by :ref:`skool2asm.py`)
* Added the ``Templates`` configuration parameter for
  :ref:`skool2asm.py <skool2asm-conf>` (for reading custom ASM templates from a
  file)
* Added the ``Dictionary`` configuration parameter for
  :ref:`sna2ctl.py <sna2ctl-conf>` (to specify a file containing a list of
  words allowed in a text string)
* Added the ``bytes`` and ``show_bytes`` identifiers to the
  :ref:`t_asm_instruction` template, along with a table cell for displaying the
  byte values of an assembled instruction
* Added the ``Bytes`` parameter to the :ref:`ref-Game` section (for specifying
  the format of byte values in the :ref:`t_asm_instruction` template)
* Added the ``DisassemblyTableNumCols`` parameter to the :ref:`ref-Game`
  section (for specifying the number of columns in the disassembly table on
  disassembly pages)
* In ASM mode, :ref:`list` and :ref:`table` macros can now be used in register
  descriptions
* The :ref:`LINK` and :ref:`R` macros now work with address anchors that start
  with an upper case letter (as could happen when ``AddressAnchor`` is
  ``{address:04X}``)
* Fixed how ``#LIST`` and ``#TABLE`` markers inside a :ref:`RAW` macro are
  handled in ASM mode
* Fixed how skool macros are expanded in ``*ImagePath`` parameters in the
  :ref:`Paths` section
* Fixed the hyperlinking of lower case hexadecimal instruction operands

7.1 (2019-02-02)
----------------
* Improved the performance and accuracy of the control file generation
  algorithm used by :ref:`sna2ctl.py` when no code map is provided
* Added support to :ref:`sna2ctl.py <sna2ctl-conf>` for reading configuration
  from `skoolkit.ini`
* Added the ``--ini`` and ``--show-config`` options to :ref:`sna2ctl.py` (for
  setting the value of a configuration parameter and for showing all
  configuration parameter values)
* Added support to :ref:`sna2skool.py` for reading multiple default control
  files, and for using the ``--ctl`` option multiple times
* The :ref:`UDGARRAY` macro now has the ability to specify attribute addresses
  (as an alternative to specifying attribute values)
* Added support to control files and skool file templates for specifying that
  numeric values in instruction operands and DEFB, DEFM, DEFS and DEFW
  statements be rendered as negative numbers
* The :ref:`isub`, :ref:`ssub`, :ref:`rsub`, :ref:`ofix`, :ref:`bfix` and
  :ref:`rfix` directives can insert an instruction after the current one
  (without first specifying a replacement for it) by using the ``+`` marker
* :ref:`tapinfo.py` now shows pulse lengths in TZX block type 0x13 (pulse
  sequence) and full info for TZX block type 0x14 (pure data)
* :ref:`sna2skool.py` handles unprintable characters in a DEFM statement by
  rendering them as byte values
* :ref:`sna2skool.py` automatically determines the byte value of an 'S'
  directive and ignores any supplied value
* Added the ``CommentWidthMin`` configuration parameter for
  :ref:`sna2skool.py <sna2skool-conf>` (to specify the minimum width of the
  instruction comment field in a skool file)
* Added the ``InstructionWidth`` configuration parameter for
  :ref:`sna2skool.py <sna2skool-conf>` (to specify the minimum width of the
  instruction field in a skool file)
* Added the ``Semicolons`` configuration parameter for
  :ref:`sna2skool.py <sna2skool-conf>` (to specify the block types in which
  comment semicolons are written for instructions that have no comment)
* Fixed how :ref:`sna2skool.py` interprets the base prefix ``n`` in a 'B'
  directive
* Fixed how :ref:`skool2ctl.py` and :ref:`skool2sft.py` handle non-entry blocks
  when a start address or end address is supplied

7.0 (2018-10-13)
----------------
* The :ref:`isub`, :ref:`ssub`, :ref:`rsub`, :ref:`ofix`, :ref:`bfix` and
  :ref:`rfix` directives can specify the replacement comment over multiple
  lines, replace the label, and insert, overwrite and remove instructions
* :ref:`nonEntryBlocks` in a skool file are reproduced by :ref:`skool2asm.py`
  and preserved by :ref:`skool2ctl.py`
* Moved the ability to generate a control file from :ref:`sna2skool.py` to the
  new :ref:`sna2ctl.py` command
* :ref:`skool2bin.py` now processes :ref:`asm-if` directives (in case they
  contain :ref:`isub`, :ref:`ssub`, :ref:`ofix` or :ref:`bfix` directives)
* The :ref:`label` directive can now add an entry point marker to the next
  instruction, or remove one if present
* Added the ``--force`` option to :ref:`skool2asm.py` (to force conversion of
  the entire skool file, ignoring any :ref:`start` and :ref:`end` directives)
* Added support for appending content to an existing ref file section by adding
  a '+' suffix to the section name (e.g. ``[Game+]``)
* Added support for preserving 'inverted' characters (with bit 7 set) in and
  restoring them from a control file or skool file template
* Added support to the :ref:`list`, :ref:`table` and :ref:`udgtable` macros for
  the ``nowrap`` and ``wrapalign`` flags (which control how :ref:`sna2skool.py`
  renders each list item or table row when reading from a control file)
* :ref:`skool2html.py` now writes a single disassembly from the the skool file
  given as the first positional argument; any other positional arguments are
  interpreted as extra ref files
* Every entry title on a memory map page is now hyperlinked to the disassembly
  page for the corresponding entry
* Fixed the bug in :ref:`skool2ctl.py` that makes it incorrectly compute the
  length of an ``M`` directive covering a sub-block containing two or more
  instructions
* Fixed how blocks of zeroes are detected and how an ``--end`` address is
  handled when generating a control file

Older versions
--------------
.. toctree::
   :maxdepth: 1

   changelog6
   changelog5
   changelog4
   changelog3
   changelog2
   changelog1
