Changelog
=========

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

5.4 (2017-01-08)
----------------
* Added the :ref:`sna2img.py` command (for converting the screenshot in a SCR
  file or SNA/SZX/Z80 snapshot into a PNG or GIF file)
* Added the :ref:`equ` ASM directive (which produces an EQU directive in the
  ASM output)
* The :ref:`REG` macro now accepts an arbitrary text parameter (e.g.
  ``#REG(hlh'l')``)
* When the :ref:`LINK` macro links to an entry on a :ref:`box page <boxpages>`,
  the link text defaults to the title of the entry if left blank
* Added the ``SectionType`` parameter to the :ref:`page` section (for
  specifying how to parse and render the ref file sections from which a
  :ref:`box page <boxpages>` is built)
* Added the ``--asm-one-page`` option to :ref:`skool2html.py` (for writing all
  routines and data blocks to a single page)
* Added the ``--variables`` option to :ref:`snapinfo.py` (for showing the
  contents of the variables area)
* :ref:`snapinfo.py` now shows special symbols for UDGs in a BASIC program
  (e.g. ``{UDG-A}``)
* Improved how :ref:`end`, :ref:`org`, :ref:`replace`, :ref:`set`, :ref:`start`
  and :ref:`writer` directives are preserved and restored via a control file
* Added support for :ref:`page-specific HTML subtemplates <ps_templates>`
* The :ref:`UDGARRAY` macro now pads out the bottom row of an array with extra
  UDGs if necessary (to prevent the creation of a broken image file)

5.3 (2016-09-05)
----------------
* Dropped support for Python 3.2
* Added the :ref:`snapinfo.py` command (for showing information on the
  registers and RAM in a SNA, SZX or Z80 snapshot)
* Added the :ref:`snapmod.py` command (for modifying the registers and RAM in a
  48K Z80 snapshot)
* Added the :ref:`INCLUDE` macro (which expands to the contents of a ref file
  section)
* Added the ability to write the HTML disassembly to a single page (by using
  the ``AsmSinglePageTemplate`` parameter in the :ref:`ref-Game` section and
  the :ref:`t_AsmAllInOne` and :ref:`t_asm_entry` templates)
* Added the ``SectionPrefix`` parameter to the :ref:`page` section (for
  specifying the prefix of the names of ref file sections from which to build
  a :ref:`box page <boxpages>`)
* Added the ``--screen`` option to :ref:`bin2tap.py` (for adding a loading
  screen to the TAP file)
* Added the ``--stack`` and ``--start`` options to :ref:`tap2sna.py` (for
  specifying the stack and start addresses)
* Added support to the :ref:`REG` macro for the F and F' registers
* Improved how :ref:`skool2asm.py` scans annotations for addresses not
  converted to labels
* Fixed how a memory block that ends with a single ED byte is compressed in a
  Z80 snapshot
* Removed the Spectrum ROM disassembly from the SkoolKit distribution; it is
  now being developed separately `here <https://github.com/skoolkid/rom>`__

5.2 (2016-05-02)
----------------
* Added the :ref:`bin2sna.py` command (for converting a binary file into a Z80
  snapshot)
* Added the :ref:`N` macro (which renders a numeric value in hexadecimal format
  when the ``--hex`` option is used with `skool2asm.py` or `skool2html.py`)
* Added the :ref:`rfix` ASM directive (which makes an instruction substitution
  in ``@rfix`` mode)
* Added the ``UDGFilename`` parameter to the :ref:`ref-Game` section (for
  specifying the format of the default filename for images created by the
  :ref:`UDG` macro)
* :ref:`bin2tap.py` can now read a binary file from standard input
* :ref:`skool2bin.py` can now write to standard output (and so its output can
  be piped to :ref:`bin2sna.py` or :ref:`bin2tap.py`)
* When the :ref:`LINK` macro links to an entry on a memory map page, the anchor
  is converted to the format specified by the ``AddressAnchor`` parameter
* Fixed how required integer macro parameters are handled when left blank (e.g.
  ``#POKES30000,,8``)

5.1 (2016-01-09)
----------------
* Added the :ref:`replace` ASM directive (which replaces strings that match a
  regular expression in skool file annotations and ref file sections)
* Added the :ref:`hash`, :ref:`EVAL`, :ref:`FOR`, :ref:`FOREACH`, :ref:`IF`,
  :ref:`MAP` and :ref:`PEEK` macros (which can be used to programmatically
  specify the parameters of any macro)
* Added support for arithmetic expressions and skool macros in numeric macro
  parameters
* Added the ``--bfix``,  ``--ofix`` and ``--ssub`` options to
  :ref:`skool2bin.py` (for parsing the skool file in ``@bfix``, ``@ofix`` and
  ``@ssub`` mode)
* Added the ``DefaultAnimationFormat`` parameter to the :ref:`ref-ImageWriter`
  section (for specifying the default format for animated images)
* The :ref:`R` macro now converts an anchor that matches the entry address to
  the format specified by the ``AddressAnchor`` parameter (making it easier to
  link to the first instruction in an entry when using a custom anchor format)
* :ref:`skool2ctl.py` now appends a terminal ``i`` directive if the skool file
  ends before 65536
* :ref:`skool2sft.py` now preserves ``i`` blocks in the same way as code and
  data blocks (instead of verbatim), which enables their conversion to decimal
  or hexadecimal when restored from a skool file template
* Fixed how the colours in flashing blank tiles are detected when writing an
  uncropped image file
* Fixed how a 2-colour PNG image is created when it contains an attribute with
  equal INK and PAPER colours

5.0 (2015-10-04)
----------------
* Added the :ref:`skool2bin.py` command (for converting a skool file into a
  binary file)
* Added the :ref:`tapinfo.py` command (for showing information on the blocks in
  a TAP or TZX file)
* Converted the :ref:`htmlTemplates` from XHTML 1.0 to HTML5
* Added the :ref:`t_footer` template (for formatting the ``<footer>`` element
  of a page)
* Added the :ref:`assemble` ASM directive
* Added the ``--set`` option to :ref:`skool2asm.py` (for setting ASM writer
  property values)
* Added the ``RefFiles`` parameter to the :ref:`ref-Config` section (for
  specifying extra ref files to use)
* Added support to :ref:`sna2skool.py` for reading SpecEmu's 64K code execution
  map files
* Fixed how :ref:`tap2sna.py` does a standard load from a TZX file

Older versions
--------------
.. toctree::
   :maxdepth: 1

   changelog4
   changelog3
   changelog2
   changelog1
