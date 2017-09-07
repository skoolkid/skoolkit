SkoolKit 5.x changelog
======================

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
