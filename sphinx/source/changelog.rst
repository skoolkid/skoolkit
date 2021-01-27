Changelog
=========

8.4b1
-----
* Changed the default value of the ``DefmSize`` configuration parameter for
  :ref:`sna2skool.py <sna2skool-conf>` from 66 to 65; this makes it compliant
  with the default maximum line width of 79 defined by the ``LineWidth``
  configuration parameter

8.3 (2020-11-08)
----------------
* Added the :ref:`PLOT` macro (for setting, resetting or flipping a pixel in a
  frame already created by an image macro)
* Added the ``--begin`` option to :ref:`bin2tap.py` (for specifying the address
  at which to begin conversion)
* The ``--end`` option of :ref:`bin2tap.py` now applies to raw memory files as
  well as SNA, SZX and Z80 snapshots
* Added the ``--data`` option to :ref:`tapinfo.py` (for showing the entire
  contents of header and data blocks)
* Added support to the ``--ctl`` option of :ref:`sna2skool.py` and
  :ref:`snapinfo.py` for reading control files from a directory
* Added the ``x`` and ``y`` parameters to the frame specification of the
  :ref:`#UDGARRAY* <Animation>` macro (for specifying the coordinates at which
  to render a frame of an animated image)
* Added support for replacement fields in the ``args`` parameter of the
  :ref:`CALL` macro, in the integer parameters of the :ref:`CHR`, :ref:`D`,
  :ref:`INCLUDE`, :ref:`N`, :ref:`POKES`, :ref:`R` and :ref:`SPACE` macros, and
  in the integer parameters and cropping specification of the :ref:`FONT`,
  :ref:`SCR`, :ref:`UDG` and :ref:`UDGARRAY` macros
* Fixed the bug that causes 'e+1' to be interpreted as a floating point number
  when it appears in a BASIC program

8.2 (2020-07-19)
----------------
* Added the ``--call-graph`` option to :ref:`snapinfo.py <snapinfo-call-graph>`
  (for generating a call graph in DOT format)
* Added the ``--ctl`` option to :ref:`snapinfo.py` (for specifying a control
  file to use when generating a call graph)
* Added the ``--org`` option to :ref:`snapinfo.py` along with the ability to
  read binary (raw memory) files
* Added support to :ref:`snapinfo.py <snapinfo-conf>` for reading configuration
  from `skoolkit.ini`
* Added the ``--ini`` and ``--show-config`` options to :ref:`snapinfo.py` (for
  setting the value of a configuration parameter and for showing all
  configuration parameter values)
* Added the :ref:`DEFINE` macro (for defining new skool macros)
* Added the :ref:`LET` macro (for defining variables that can be retrieved by
  other macros via replacement fields)
* Added the :ref:`FORMAT` macro (for performing a Python-style string
  formatting operation on an arbitrary piece of text)
* Added the :ref:`expand` directive (for specifying skool macros to be expanded
  during ASM writer or HTML writer initialisation)
* Added the ``tindex`` parameter to the :ref:`FONT`, :ref:`SCR`, :ref:`UDG` and
  :ref:`UDGARRAY` macros (for specifying a transparent colour to use other than
  the default)
* Added the ``alpha`` parameter to the :ref:`FONT`, :ref:`SCR`, :ref:`UDG` and
  :ref:`UDGARRAY` macros (for specifying the alpha value to use for the
  transparent colour)
* Added the :ref:`refs` directive (for managing the addresses of routines that
  jump to or call an entry point)
* Added support for replacement fields in the integer parameters of the
  :ref:`FOR` and :ref:`PEEK` macros
* Added the ``--page`` option to :ref:`snapinfo.py` (for specifying the page of
  a 128K snapshot to map to 49152-65535)

8.1 (2020-03-29)
----------------
* Added the ``--rsub`` and ``--rfix`` options to :ref:`skool2bin.py` (for
  parsing the skool file in :ref:`rsubMode` and :ref:`rfixMode`)
* Added the ``--data`` option to :ref:`skool2bin.py` (for processing
  :ref:`defb`, :ref:`defs` and :ref:`defw` directives)
* Added the ``--verbose`` option to :ref:`skool2bin.py` (for showing
  information on each converted instruction)
* Added the ``--no-warnings`` option to :ref:`skool2bin.py` (to suppress the
  warnings that are now shown by default)
* The ``address`` parameter of the :ref:`defb`, :ref:`defs` and :ref:`defw`
  directives is now optional
* :ref:`defb`, :ref:`defs` and :ref:`defw` directives in non-entry blocks are
  now processed when reading a control file
* Register name fields in the registers section of an
  :ref:`entry header <entryHeaderFormat>` may now contain whitespace and skool
  macros
* The :ref:`CALL` macro now accepts keyword arguments
* :ref:`tapinfo.py` now shows the contents of TZX block types 0x33 (hardware
  type) and 0x35 (custom info)
* Added the ``LabelColumn`` parameter to the :ref:`memoryMap` section (for
  specifying whether to display the 'Label' column on a memory map page
  whenever any entries have ASM labels defined)
* Added the ``fmt`` parameter to the format specifier for the ``bytes``
  attribute of instruction objects in the :ref:`t_asm` template (for formatting
  the entire string of byte values)
* Added support to the :ref:`set` directive for the `table-row-separator`
  property
* The :ref:`ignoreua` and :ref:`nowarn` directives can now specify the
  addresses for which to suppress warnings
* Added support to :ref:`sna2skool.py` for ignoring default control files (by
  specifying ``--ctl 0``)
* Fixed how :ref:`sna2skool.py` works with dot directives in a control file
  when an end address is specified

8.0 (2019-11-09)
----------------
* Dropped support for Python 3.4
* Made several :ref:`components` pluggable
* Added support for the :ref:`td_foreach`, :ref:`td_if` and :ref:`td_include`
  directives in HTML templates
* Added the :ref:`PC` macro (which expands to the address of the closest
  instruction in the current entry)
* Added support to the :ref:`set` directive for the `table-border-horizontal`,
  `table-border-join` and `table-border-vertical` properties
* Added the ``DefwSize`` configuration parameter for
  :ref:`sna2skool.py <sna2skool-conf>` (for setting the maximum number of words
  in a DEFW statement)
* Added support for the ``**`` pattern (which matches any files and zero or
  more directories and subdirectories) in the :ref:`resources` section
* Added support for replacement fields (such as ``{base}`` and ``{case}``) in
  the parameter string of the :ref:`EVAL` macro
* Added the ``max_reg_len`` identifier to the :ref:`t_register` template
* Added support for specifying page header prefixes and suffixes in the
  :ref:`pageHeaders` section
* An ``entry`` dictionary is available when formatting the title and header of
  a disassembly page (as defined by the ``Asm-*`` parameters in the
  :ref:`titles` and :ref:`pageHeaders` sections)
* Added the ``GameIndex`` parameter to the :ref:`pageHeaders` section
* Replaced the ``AsmSinglePageTemplate`` parameter with the ``AsmSinglePage``
  parameter in the :ref:`ref-Game` section
* Fixed the bug that prevents the ``JavaScript`` parameter from working for a
  box page whose ``SectionType`` is ``ListItems`` or ``BulletPoints``
* Fixed how a table row separator that crosses a cell with rowspan > 1 is
  rendered in ASM mode
* Fixed the bug that prevents :ref:`sna2skool.py` from wrapping referrer
  comments

Older versions
--------------
.. toctree::
   :maxdepth: 1

   changelog7
   changelog6
   changelog5
   changelog4
   changelog3
   changelog2
   changelog1
