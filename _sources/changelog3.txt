.. _skoolkit3x:

SkoolKit 3.x changelog
======================
3.7 (2014-03-08)
----------------
* Added support for numbers in binary notation (e.g. %10101010)
* Added the ``s`` and ``S`` control directives for encoding DEFS statements
  (with optional non-zero byte values); the ``z`` and ``Z`` directives are now
  deprecated
* Added support to control files and skool file templates for specifying the
  base of numeric values in DEFB, DEFM, DEFS and DEFW statements
* Added the ``--preserve-base`` option to :ref:`skool2ctl.py` and
  :ref:`skool2sft.py` (to preserve the base of decimal and hexadecimal values
  in DEFB, DEFM, DEFS and DEFW statements)
* Added the ``JavaScript`` parameter to the :ref:`ref-Game` section (for
  specifying JavaScript files to include in every page of a disassembly)
* Fixed the bug that prevents DEFB statements containing only strings and DEFM
  statements containing only bytes from being restored from a control file or a
  skool file template
* Added changelog entries to `manic_miner.ref`, `jet_set_willy.ref` and
  `48.rom.ref`

3.6 (2013-11-02)
----------------
* Enhanced the :ref:`UDGARRAY` macro so that it can create an animated image
  from an arbitrary sequence of frames
* Enhanced the :ref:`FONT` macro so that it can create an image of arbitrary
  text
* Added support for copying arbitrary files into an HTML disassembly by using
  the :ref:`resources` section in the ref file
* Added the ``--join-css`` option to :ref:`skool2html.py` (to concatenate CSS
  files into a single file)
* Added the ``--search-dirs`` option to :ref:`skool2html.py` (to show the
  locations that `skool2html.py` searches for resources)
* Added support for creating disassemblies with a start address below 10000
* Added an example control file for the 48K Spectrum ROM: `48.rom.ctl`
* Control files can now preserve blank comments that span two or more
  instructions
* The ``[Config]`` section no longer has to be in the ref file named on the
  `skool2html.py` command line; it can be in any secondary ref file
* Fixed the bug that makes `skool2html.py` fail if the ``FontPath``,
  ``JavaScriptPath`` or ``StyleSheetPath`` parameter in the ``[Paths]`` section
  of the ref file is set to some directory other than the default

3.5 (2013-09-01)
----------------
* Added the :ref:`tap2sna.py` command (for building snapshots from TAP/TZX
  files)
* Added support to :ref:`skool2html.py` for multiple CSS themes
* Added the 'green', 'plum' and 'wide' CSS themes: `skoolkit-green.css`,
  `skoolkit-plum.css`, `skoolkit-wide.css`
* Moved the ``Font`` and ``StyleSheet`` parameters from the ``[Paths]`` section
  to the :ref:`ref-game` section
* Moved the ``JavaScript`` parameter from the ``[Paths]`` section to the
  :ref:`page` section
* Moved the ``Logo`` parameter from the ``[Paths]`` section to the
  :ref:`ref-game` section and renamed it ``LogoImage``
* The :ref:`r` macro now renders the addresses of remote entries in the
  specified case and base, and can resolve the addresses of remote entry points
* :ref:`skool2asm.py` now writes ORG addresses in the specified case and base
* Annotated the source code remnants at 39936 in `jet_set_willy.ctl`

3.4 (2013-07-08)
----------------
* Dropped support for Python 2.6 and 3.1
* Added long options to every command
* Added the ``--asm-labels`` and ``--create-labels`` options to
  :ref:`skool2html.py` (to use ASM labels defined by :ref:`label` directives,
  and to create default labels for unlabelled instructions)
* Added the ``--erefs`` option to :ref:`sna2skool.py` (to always add comments
  that list entry point referrers)
* Added the ``--package-dir`` option to :ref:`skool2asm.py` (to show the path
  to the skoolkit package directory)
* Added support for the ``LinkOperands`` parameter in the :ref:`ref-Game`
  section of the ref file, which may be used to enable the address operands
  of LD instructions to be hyperlinked
* Added support for defining image colours by using hex triplets in the
  :ref:`ref-Colours` section of the ref file
* Added support to the :ref:`set` ASM directive for the
  `handle-unsupported-macros` and `wrap-column-width-min` properties
* Fixed the ``#EREFS`` and ``#REFS`` macros so that they work with hexadecimal
  address parameters
* Fixed the bug that crashes :ref:`sna2skool.py` when generating a control file
  from a code execution map and a snapshot with a code block that terminates at
  65535
* Fixed how :ref:`skool2asm.py` renders table cells with rowspan > 1 and
  wrapped contents alongside cells with rowspan = 1
* Removed support for the ``#NAME`` macro (what it did can be done by the
  :ref:`html` macro instead)
* Removed the documentation sources and man page sources from the SkoolKit
  distribution (they can be obtained from GitHub_)

.. _GitHub: https://github.com/skoolkid/skoolkit

3.3.2 (2013-05-13)
------------------
* Added the ``-T`` option to :ref:`skool2html.py` (to specify a CSS theme)
* Added the ``-p`` option to :ref:`skool2html.py` (to show the path to the
  skoolkit package directory)
* `setup.py` now installs the `resources` directory (so a local copy is no
  longer required when SkoolKit has been installed via ``setup.py install``)
* Added `jet_set_willy-dark.css` (to complete the 'dark' theme for that
  disassembly)
* Added :ref:`documentation <bracesInComments>` on how to write an
  instruction-level comment that contains opening or closing braces when
  rendered
* Fixed the appearance of transparent table cells in HTML output
* Fixed :ref:`sna2skool.py` so that a control file specified by the ``-c``
  option takes precedence over a default skool file template
* Fixed `manic_miner.ctl` so that the comments at 40177-40191 apply to a
  pristine snapshot (before stack operations have corrupted those addresses)

3.3.1 (2013-03-04)
------------------
* Added support to the :ref:`set` ASM directive for the `comment-width-min`,
  `indent`, `instruction-width`, `label-colons`, `line-width` and `warnings`
  properties
* Added support to the ``HtmlWriterClass`` parameter (in the :ref:`ref-Config`
  section) and the :ref:`writer` directive for specifying a module outside the
  module search path (e.g. a standalone module that is not part of an installed
  package)
* :ref:`sna2skool.py` now correctly renders an empty block description as a
  dot (``.``) on a line of its own

3.3 (2013-01-08)
----------------
* Added support to :ref:`sna2skool.py` for reading code execution maps produced
  by the Fuse, SpecEmu, Spud, Zero and Z80 emulators (to generate more accurate
  control files)
* Increased the speed at which :ref:`sna2skool.py` generates control files
* Added support to :ref:`sna2skool.py` for disassembling 128K SNA snapshots

3.2 (2012-11-01)
----------------
* Added support to :ref:`sna2skool.py` for disassembling 128K Z80 snapshots and
  16K, 48K and 128K SZX snapshots
* Added the :ref:`LIST` macro (for rendering lists of bulleted items in both
  HTML mode and ASM mode)
* Added the :ref:`set` ASM directive (for setting properties on the ASM writer)
* Added trivia entries to `jet_set_willy.ref`
* Annotated the source code remnants at 32768 and 37708 in `manic_miner.ctl`

3.1.4 (2012-10-11)
------------------
* Added support to :ref:`skool2ctl.py` and :ref:`skool2sft.py` for DEFB and
  DEFM statements that contain both strings and bytes
* :ref:`skool2ctl.py` now correctly processes lower case DEFB, DEFM, DEFS and
  DEFW statements
* The length of a string (in a DEFB or DEFM statement) that contains one or
  more backslashes  is now correctly calculated by :ref:`skool2ctl.py` and
  :ref:`skool2sft.py`
* DEFB and DEFM statements that contain both strings and bytes are now
  correctly converted to lower case, upper case, decimal or hexadecimal (when
  using the ``-l``, ``-u``, ``-D`` and ``-H`` options of :ref:`skool2asm.py`
  and :ref:`skool2html.py`)
* Operations involving (IX+n) or (IY+n) expressions are now correctly converted
  to lower case decimal or hexadecimal (when using the ``-l``, ``-D`` and
  ``-H`` options of :ref:`skool2asm.py` and :ref:`skool2html.py`)

3.1.3 (2012-09-11)
------------------
* The 'Glossary' page is formatted in the same way as the 'Trivia', 'Bugs',
  'Pokes' and 'Graphic glitches' pages
* When the link text of a :ref:`link` macro is left blank, the link text of the
  page is substituted
* The disassembler escapes backslashes and double quotes in DEFM statements
  (so that :ref:`skool2asm.py` no longer has to)
* DEFB and DEFM statements that contain both strings and bytes are parsed
  correctly for the purpose of building a memory snapshot

3.1.2 (2012-08-01)
------------------
* Added the :ref:`HTML` macro (for rendering arbitrary text in HTML mode only)
* Added support for distinguishing input values from output values in a
  routine's register section (by using prefixes such as 'Input:' and 'Output:')
* Added support for the ``InputRegisterTableHeader`` and
  ``OutputRegisterTableHeader`` parameters in the :ref:`ref-Game` section of
  the ref file
* Added the 'default' CSS class for HTML tables created by the :ref:`table`
  macro

3.1.1 (2012-07-17)
------------------
* Enhanced the :ref:`UDGARRAY` macro so that it accepts both horizontal and
  vertical steps in UDG address ranges
* Added support for the ``Font`` and ``FontPath`` parameters in the
  :ref:`Paths` section of the ref file (for specifying font files used by CSS
  `@font-face` rules)
* Added a Spectrum theme CSS file that uses the Spectrum font and colours:
  `skoolkit-spectrum.css`
* Fixed :ref:`skool2asm.py` so that it escapes backslashes and double quotes in
  DEFM statements

3.1 (2012-06-19)
----------------
* Dropped support for Python 2.5
* Added documentation on :ref:`extending SkoolKit <extendingSkoolKit>`
* Added the :ref:`writer` ASM directive (to specify the class to use for
  producing ASM output)
* Added the :ref:`CHR` macro (for rendering arbitrary unicode characters);
  removed support for the redundant ``#C`` macro accordingly
* Added support for the :ref:`CALL`, ``#REFS``, ``#EREFS``, :ref:`PUSHS`,
  :ref:`POKES` and :ref:`POPS` macros in ASM mode
* Added the ``-c`` option to :ref:`skool2html.py` (to simulate adding lines to
  the ref file)
* Added a dark theme CSS file: `skoolkit-dark.css`

3.0.2 (2012-05-01)
------------------
* Added room images and descriptions to `manic_miner.ctl` and
  `jet_set_willy.ctl` (based on reference material from
  `Andrew Broad <http://webspace.webring.com/people/ja/andrewbroad/>`_ and
  `J. G. Harston <http://mdfs.net/Software/JSW/Docs/>`_)
* Fixed the bug that prevents the 'Data tables and buffers' section from
  appearing on the disassembly index page when the default ``DataTables`` link
  group is used

3.0.1 (2012-04-11)
------------------
* Added support for creating GIF files (including transparent and animated
  GIFs)
* Added support for creating animated PNGs in APNG format
* Added support for transparency in PNG images (by using the ``PNGAlpha``
  parameter in the :ref:`ref-ImageWriter` section of the ref file)
* Added an example control file: `jet_set_willy.ctl`
* Fixed the bug in how images are cropped by the :ref:`FONT`, :ref:`SCR`,
  :ref:`UDG` and :ref:`UDGARRAY` macros when using non-zero ``X`` and ``Y``
  parameters

3.0 (2012-03-20)
----------------
* SkoolKit now works with Python 3.x
* Added a native image creation library, which can be configured by using the
  :ref:`ref-ImageWriter` section of the ref file; `gd` and `PIL` are no
  longer required or supported
* Enhanced the :ref:`SCR` macro so that graphic data and attribute bytes in
  places other than the display file and attribute file may be used to build a
  screenshot
* Added image-cropping capabilities to the :ref:`FONT`, :ref:`SCR`, :ref:`UDG`
  and :ref:`UDGARRAY` macros
