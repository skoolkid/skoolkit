Changelog
=========

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
* Added the ``CommentWidthMin`` configuration parameter for :ref:`sna2skool.py`
  (to specify the minimum width of the instruction comment field in a skool
  file)
* Added the ``InstructionWidth`` configuration parameter for
  :ref:`sna2skool.py` (to specify the minimum width of the instruction field in
  a skool file)
* Added the ``Semicolons`` configuration parameter for :ref:`sna2skool.py` (to
  specify the block types in which comment semicolons are written for
  instructions that have no comment)
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

6.4 (2018-03-31)
----------------
* Added the :ref:`asm-if` directive (for conditionally processing other ASM
  directives)
* Added the :ref:`RAW` macro (which prevents any macros or macro-like tokens in
  its sole string argument from being expanded)
* Added the ``--var`` option to :ref:`skool2asm.py` and :ref:`skool2html.py`
  (for defining a variable that can be used by the :ref:`asm-if` directive and
  the :ref:`IF` and :ref:`MAP` macros)
* The ``asm`` replacement field available to the :ref:`IF` and :ref:`MAP`
  macros now indicates the exact ASM mode: 1 (:ref:`isubMode`), 2
  (:ref:`ssubMode`), 3 (:ref:`rsubMode`), or 0 (none)
* The :ref:`IF` and :ref:`MAP` macros can now use the ``fix`` replacement
  field, which indicates the fix mode: 1 (:ref:`ofixMode`), 2
  (:ref:`bfixMode`), 3 (:ref:`rfixMode`), or 0 (none)
* The :ref:`isub`, :ref:`ssub`, :ref:`rsub`, :ref:`ofix`, :ref:`bfix` and
  :ref:`rfix` directives can replace comments as well as instructions
* Added the ``entry`` identifier to the :ref:`t_footer` template when it is
  part of a disassembly page
* Added ``path`` to the ``SkoolKit`` dictionary in :ref:`htmlTemplates`
* In ASM mode, a :ref:`list` or :ref:`table` macro can now be used in an
  instruction-level comment and as a parameter of another macro
* In ASM mode, the :ref:`list` macro produces unindented items when the bullet
  character is an empty string, and the bullet character can be specified by
  the ``bullet`` parameter
* Commas that appear between parentheses are retained when a sequence of
  :ref:`string parameters <stringParameters>` is split, making it easier to
  nest macros (e.g. ``#FOR0,9(n,#IF(n%2)(Y,N))``)

6.3 (2018-02-19)
----------------
* Added the :ref:`defb`, :ref:`defs` and :ref:`defw` directives (for inserting
  byte values and word values into the memory snapshot)
* Added the :ref:`remote` directive (for creating a remote entry)
* Added the ``--poke`` option to :ref:`bin2sna.py` (for performing POKE
  operations on the snapshot)
* Added the ``--user-agent`` option to :ref:`tap2sna.py` (for setting the
  User-Agent header used in an HTTP request)
* Added support to the :ref:`Resources` section for specifying files using
  wildcard characters (``*``, ``?`` and ``[]``)
* Added the ``ImagePath`` parameter to the :ref:`Paths` section (for specifying
  the base directory in which to place images) and the ability to define one
  image path ID in terms of another
* Added support for image path ID replacement fields in the ``fname`` parameter
  of the :ref:`image macros <imageMacros>` (e.g. ``#SCR2({UDGImagePath}/scr)``)
* The :ref:`assemble` directive can specify what to assemble in HTML mode and
  ASM mode separately
* By default in ASM mode, DEFB/DEFM/DEFS/DEFW statements are no longer
  converted into byte values for the purpose of populating the memory snapshot
* The ``address`` parameter of the :ref:`org` directive is now optional and
  defaults to the address of the next instruction
* The ``LABEL`` parameter of the :ref:`label` directive may be left blank to
  prevent the next instruction from having a label automatically generated
* Added the ``location`` identifier to the :ref:`t_asm_instruction` template
* Added support for parsing block-level comments that are not left-padded by a
  space
* Fixed how an opening brace at the end of a line or a closing brace at the
  beginning of a line is handled in an instruction-level comment
* Fixed the bug in :ref:`skool2ctl.py` that prevents an :ref:`ignoreua`
  directive on a block end comment from being preserved correctly
* Fixed :ref:`sna2skool.py` so that it can generate a control file for a
  snapshot whose final byte (at 65535) is 24 or 237

6.2 (2018-01-01)
----------------
* Added the ``--reg`` option to :ref:`bin2sna.py` (for setting the value of a
  register)
* Added the ``--state`` option to :ref:`bin2sna.py` (for setting the value of a
  hardware state attribute)
* :ref:`sna2img.py` can now read a binary (raw memory) file when the
  ``--binary`` option is used, and with a specific origin address when the
  ``--org`` option is used
* Added the ``Includes`` parameter to the :ref:`memoryMap` section (for
  specifying addresses of entries to include on the memory map page in addition
  to those specified by the ``EntryTypes`` parameter)
* The :ref:`SkoolKit command <commands>` options now accept a hexadecimal
  integer prefixed by '0x' wherever an address, byte, length, step, offset or
  range limit value is expected
* Added the ``hex`` parameter to the :ref:`N` macro (for rendering a value in
  hexadecimal format unless the ``--decimal`` option is used with
  :ref:`skool2asm.py` or :ref:`skool2html.py`)
* Added the ``--show-config`` option to :ref:`skool2asm.py`,
  :ref:`skool2html.py` and :ref:`sna2skool.py` (for showing configuration
  parameter values)
* Added support for substituting labels in instruction operands and
  DEFB/DEFM/DEFW statements that contain multiple addresses (e.g.
  ``LD BC,30000+40000%256``), or where the address is the second or later term
  in an expression (e.g. ``DEFW 1+30000``)
* The :ref:`keep` directive can now specify the values to keep, and is applied
  to instructions that have been replaced by an :ref:`isub`, :ref:`ssub` or
  :ref:`rsub` directive
* The ``@nolabel`` directive is now processed in HTML mode

6.1 (2017-09-03)
----------------
* Added support for converting the base of every numerical term in an
  instruction operand or DEFB/DEFM/DEFS/DEFW statement that contains two or
  more (e.g. ``LD A,32768/256`` to ``LD A,$8000/$100``)
* Added support for assembling instructions and DEFB/DEFM/DEFS/DEFW statements
  whose operands contain arithmetic expressions (e.g. ``DEFM "H","i"+$80``)
* Added support to :ref:`skool2asm.py <skool2asm-conf>`,
  :ref:`skool2html.py <skool2html-conf>` and
  :ref:`sna2skool.py <sna2skool-conf>` for reading configuration from a file
  named `skoolkit.ini`, if present
* Added the ``--ini`` option to :ref:`skool2asm.py`, :ref:`skool2html.py` and
  :ref:`sna2skool.py` (for setting the value of a configuration parameter)
* :ref:`sna2img.py` can now read skool files, in either the default mode, or
  ``@bfix`` mode by using the ``--bfix`` option
* Added the ``--move`` option to :ref:`sna2img.py` (for copying the contents of
  a block of RAM to another location)
* Improved how :ref:`skool2asm.py` formats a comment that covers two or more
  instructions: now the comment is aligned to the widest instruction, and even
  blank lines are prefixed by a semicolon
* Improved how the :ref:`R` macro renders the address of an unavailable
  instruction (an instruction outside the range of the current disassembly, or
  in another disassembly) in ASM mode
* Removed the indent from EQU directives in ASM output (for compatibility with
  SjASMPlus)
* Fixed the bug that prevents the expansion of a macro whose numeric parameters
  contain a '<', '>' or '&' character
* Fixed how labels are substituted for addresses in DEFB/DEFM/DEFW statements
* Fixed :ref:`skool2asm.py` so that it processes ``@ssub`` directives when
  ``--fixes 3`` is specified
* Fixed the styling of entry descriptions for 't' blocks on a memory map page

6.0 (2017-05-06)
----------------
* Dropped support for Python 2.7 and 3.3
* Added the ``--expand`` option to :ref:`sna2img.py` (for expanding a
  :ref:`FONT`, :ref:`SCR`, :ref:`UDG` or :ref:`UDGARRAY` macro)
* Added the ``--basic`` option to :ref:`tapinfo.py` (for listing the BASIC
  program in a tape block)
* Added the ``--find-tile`` option to :ref:`snapinfo.py` (for searching for the
  graphic data of a tile currently on screen)
* Added the ``--word`` option to :ref:`snapinfo.py` (for showing the words at a
  range of addresses)
* Added support to the ``--find`` option of :ref:`snapinfo.py` for specifying a
  range of distances between byte values (e.g. ``--find 1,2,3-1-10``)
* The ``--peek`` option of :ref:`snapinfo.py` now shows UDGs and BASIC tokens
* Added support for replacement fields (such as ``{base}`` and ``{case}``) in
  the ``expr`` parameter of the :ref:`IF` macro and the ``key`` parameter of
  the :ref:`MAP` macro
* Added support for parsing a :ref:`box page <boxpages>` entry section as a
  sequence of multi-line list items prefixed by '-' (with
  ``SectionType=BulletPoints``)
* The following ref file components may now contain skool macros: the
  ``anchor`` and ``title`` of a :ref:`box page <boxpages>` entry section name;
  every parameter in the :ref:`ref-Game`, :ref:`memoryMap`, :ref:`page`,
  :ref:`pageHeaders`, :ref:`paths` and :ref:`titles` sections
* The :ref:`replace` directive now acts on ref file section names as well as
  their contents
* The :ref:`EVAL` macro now renders hexadecimal values in lower case when the
  ``--lower`` option of :ref:`skool2asm.py` or :ref:`skool2html.py` is used
* Added the :ref:`VERSION` macro (which expands to the version of SkoolKit)
* Fixed how an image is cropped when the crop rectangle is very narrow
* Fixed how a masked image with flashing cells is built
* Fixed how :ref:`sna2skool.py` handles a snapshot that contains a dangling
  IX/IY prefix (DD/FD) when generating a control file
* Fixed the bug that prevents the expansion of skool macros in a page's link
  text on the disassembly home page

Older versions
--------------
.. toctree::
   :maxdepth: 1

   changelog5
   changelog4
   changelog3
   changelog2
   changelog1
