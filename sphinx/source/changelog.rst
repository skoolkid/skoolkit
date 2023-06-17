Changelog
=========

8.10 (2023-06-17)
-----------------
* Added the ``finish-tape`` simulated LOAD configuration parameter to
  :ref:`tap2sna.py <tap2sna-sim-load>` (to specify whether to finish the tape
  before stopping the simulation at the given start address)
* Added the ``contended-in`` simulated LOAD configuration parameter to
  :ref:`tap2sna.py <tap2sna-sim-load>` (to specify whether to interpret
  'IN A,($FE)' instructions in the address range $4000-$7FFF as reading the
  tape)
* Added the ``accelerate-dec-a`` simulated LOAD configuration parameter to
  :ref:`tap2sna.py <tap2sna-sim-load>` (to specify whether to accelerate
  'DEC A: JR NZ,$-1' or 'DEC A: JP NZ,$-1' delay loops)
* Added the ``alkatraz-05``, ``alkatraz-09``, ``alkatraz-0a``, ``alkatraz-0b``,
  ``alternative``, ``alternative2``, ``boguslaw-juza``, ``bulldog``, ``crl``,
  ``crl2``, ``crl3``, ``crl4``, ``cybexlab``, ``d-and-h``, ``delphine``,
  ``design-design``, ``gargoyle2``, ``gremlin2``, ``microprose``,
  ``micro-style``, ``mirrorsoft``, ``palas``, ``raxoft``, ``realtime``,
  ``silverbird``, ``software-projects``, ``sparklers``, ``suzy-soft``,
  ``suzy-soft2``, ``tiny``, ``us-gold`` and ``weird-science`` tape-sampling
  loop accelerators for use with :ref:`tap2sna.py <tap2sna-sim-load>`
* Added the special ``auto`` and ``list`` tape-sampling loop accelerator names
  for use with the ``accelerator`` simulated LOAD configuration parameter of
  :ref:`tap2sna.py <tap2sna-sim-load>`, and the ability to specify multiple
  accelerators
* Added support to :ref:`bin2sna.py`, :ref:`snapmod.py` and :ref:`tap2sna.py`
  for setting the ``issue2`` hardware state attribute (to enable or disable
  issue 2 emulation)
* Added support to :ref:`tap2sna.py` for loading tapes that end with a pulse
  sequence instead of data
* Added support to :ref:`tap2sna.py <tap2sna-conf>` for reading configuration
  from `skoolkit.ini`
* Added the ``--ini`` and ``--show-config`` options to :ref:`tap2sna.py` (for
  setting the value of a configuration parameter and for showing all
  configuration parameter values)
* Added support to :ref:`tap2sna.py <tap2sna-conf>` for configuring the format
  of a simulated LOAD trace log file via the ``TraceLine`` and ``TraceOperand``
  configuration parameters
* Added the ``--tape-analysis`` option to :ref:`tap2sna.py` (for showing an
  analysis of the tape's tones, pulse sequences and data blocks)
* :ref:`snapinfo.py` now shows the value of the T-states counter and the issue
  2 emulation flag in SZX and Z80 snapshots
* Fixed the bug that prevents :ref:`snapinfo.py` from displaying the value of a
  floating-point number in a BASIC line when the accompanying numeric string is
  a single decimal point (``.``)
* Fixed how the value of the R register is set in a Z80 snapshot when bit 7 is
  reset
* Fixed how tape-sampling loop accelerators affect the carry flag after at
  least one pass through the loop

8.9 (2023-02-19)
----------------
* Added support to :ref:`tap2sna.py` for TZX loops (block types 0x24 and 0x25),
  pauses (block types 0x10, 0x11, 0x14 and 0x20), and unused bits in data
  blocks (block types 0x11 and 0x14)
* :ref:`tap2sna.py` now accelerates the simulation of tape-sampling loops in
  loading routines, and also simulates the execution of interrupt routines when
  interrupts are enabled
* Added the ``--sim-load-config`` option to :ref:`tap2sna.py` (to set the value
  of a ``--sim-load`` configuration parameter: ``accelerator``, ``fast-load``,
  ``first-edge``, ``pause``, ``timeout``, ``trace``)
* Added the ``--tape-name`` option to :ref:`tap2sna.py` (to specify the name of
  a TAP/TZX file in a zip archive, in case there is more than one)
* Added the ``--tape-start`` and ``--tape-stop`` options to :ref:`tap2sna.py`
  (to start or stop the tape at a specific block number)
* Added the ``--tape-sum`` option to :ref:`tap2sna.py` (to specify the MD5
  checksum of the TAP/TZX file)
* Added support to :ref:`tap2sna.py` for quoted arguments in an arguments file
* Added the ``--interrupts`` option to :ref:`trace.py` (to enable the execution
  of interrupt routines)
* :ref:`trace.py` now reads and writes the T-states counter in Z80 snapshots
  and reads the T-states counter in SZX snapshots
* Added support to :ref:`bin2sna.py`, :ref:`snapmod.py` and :ref:`tap2sna.py`
  for setting the ``tstates`` hardware attribute (i.e. the T-states counter in
  Z80 snapshots)
* :ref:`tapinfo.py` now shows full info for TZX block types 0x10 (standard
  speed data) and 0x11 (turbo speed data)
* Fixed how the Z80 instruction set simulator updates the A and R registers in
  the 'LD A,R' and 'LD R,A' instructions
* Fixed how the Z80 instruction set simulator handles a CALL instruction that
  overwrites its own address operand
* Fixed how a Z80 snapshot memory block that ends with a single 0xED byte is
  decompressed
* Fixed how the ``--sim-load`` option of :ref:`tap2sna.py` transitions from a
  tape block that ends with data to the next block when there is no pause
  between them
* Fixed the bug that prevents the ``--find`` option of :ref:`snapinfo.py` from
  finding byte sequences below address 16384
* Fixed the bug that prevents the ``--find-text`` option of :ref:`snapinfo.py`
  from finding text strings below address 16384

8.8 (2022-11-19)
----------------
* Added the :ref:`trace.py` command (for tracing the execution of machine code
  in a 48K memory snapshot)
* The ``--sim-load`` option of :ref:`tap2sna.py` now performs any ``call``,
  ``move``, ``poke`` and ``sysvars`` operations specified by the ``--ram``
  option
* Improved the performance of the ``--sim-load`` option of :ref:`tap2sna.py`
* Improved the performance of the :ref:`SIM` macro
* Improved the performance of the :ref:`AUDIO` and :ref:`TSTATES` macros when
  they execute instructions in a simulator
* Removed the ``MaxAmplitude`` parameter from the :ref:`ref-AudioWriter`
  section

8.7 (2022-10-08)
----------------
* Dropped support for Python 3.6
* Added the :ref:`SIM` macro (for simulating the execution of machine code in
  the internal memory snapshot constructed from the contents of the skool file)
* Added the :ref:`AUDIO` macro (for creating HTML5 ``<audio>`` elements, and
  optionally creating audio files in WAV format)
* Added the :ref:`TSTATES` macro (which expands to the time taken, in T-states,
  to execute one or more instructions)
* Added the ``--sim-load`` option to :ref:`tap2sna.py` (to simulate a 48K ZX
  Spectrum running LOAD "")
* Added the :ref:`rom` directive (for inserting a copy of the 48K ZX Spectrum
  ROM into the internal memory snapshot constructed from the contents of the
  skool file)
* Added the ``AudioPath`` parameter to the :ref:`paths` section (for specifying
  where the :ref:`AUDIO` macro should look for or create audio files by
  default)
* Added the :ref:`t_audio` template (for formatting the ``<audio>`` element
  produced by the :ref:`AUDIO` macro)
* Added the :ref:`ref-AudioWriter` section (for configuring audio files created
  by the :ref:`AUDIO` macro)
* Added the ``--rebuild-audio`` option to and the ``RebuildAudio``
  configuration parameter for :ref:`skool2html.py` (to overwrite existing audio
  files)
* Added the ``AudioFormats`` parameter to the :ref:`ref-game` section (for
  specifying the alternative audio file formats that the :ref:`AUDIO` macro
  should look for before creating a WAV file)
* Added the ``--defb`` option to :ref:`sna2skool.py` (to disassemble as DEFB
  statements instead of as code)
* Added the ``Timings`` configuration parameter for
  :ref:`sna2skool.py <sna2skool-conf>` (for showing instruction timings in the
  comment fields)
* Added the ``flags`` parameter to the :ref:`FOR` macro (for affixing commas to
  and replacing variable names in each separator)
* Added support to the :ref:`mDirective` for applying its comment to each
  instruction in its range
* When :ref:`tap2sna.py` ignores a headerless block because no ``--ram load``
  options have been specified, it now prints a warning
* Amended the :ref:`t_register` ASM template so that it can handle empty
  register names
* Fixed the bug where the ``stop`` value of the :ref:`FOR` macro is used even
  when it does not differ from ``start`` by a multiple of ``step``
* Fixed the bug where an :ref:`mDirective` with an explicit length overrides
  the sublengths of an earlier sub-block directive at the same address

8.6 (2021-11-06)
----------------
* Added the :ref:`STR` macro (for retrieving the text string at a given address
  in the memory snapshot)
* Added the :ref:`WHILE` macro (for repeatedly expanding macros until a
  conditional expression becomes false)
* Added the :ref:`UDGS` macro (as an alternative to the :ref:`UDGARRAY` macro
  for creating an image of a rectangular array of UDGs)
* Added support to the :ref:`DEF` macro for using replacement fields to
  represent the defined macro's argument values, and for stripping leading and
  trailing whitespace from the defined macro's output
* Added support to the :ref:`LET` macro for defining dictionary variables
* Added support to the ``--ram`` option of :ref:`tap2sna.py` for the
  ``call`` operation (for calling a Python function to perform arbitrary
  manipulation of the memory snapshot)
* Added the ``flags`` parameter to the :ref:`CHR` macro (to produce a character
  in the UTF-8 encoding in HTML mode, and to map character codes 94, 96 and 127
  to '↑', '£' and '©')
* Added the ``Expand`` parameter to the :ref:`ref-Config` section (for
  specifying skool macros to be expanded during HTML writer initialisation)
* Added support to the :ref:`INCLUDE` macro for combining the contents of
  multiple ref file sections
* Added the ``tindex`` and ``alpha`` parameters to the :ref:`COPY` macro (for
  specifying the transparent colour and its alpha value in the new frame)
* Fixed the bug where macros inside a :ref:`LIST` or :ref:`TABLE` macro are
  expanded twice in HTML mode (which makes :ref:`RAW` ineffective)

8.5 (2021-07-03)
----------------
* Dropped support for Python 3.5
* Added the :ref:`OVER` macro (for superimposing one frame on another)
* Added the :ref:`COPY` macro (for copying all or part of an existing frame
  into a new frame)
* Added the :ref:`DEF` macro (as a more powerful alternative to the
  :ref:`DEFINE` macro, which is now deprecated)
* Added the ``Wrap`` configuration parameter for
  :ref:`sna2skool.py <sna2skool-conf>` (for controlling whether to disassemble
  an instruction that wraps around the 64K boundary)
* Added the ``RefFormat`` configuration parameter for
  :ref:`sna2skool.py <sna2skool-conf>` (for specifying the format of referrers
  in a comment that lists them for a routine or entry point)
* Added the ``EntryLabel`` and ``EntryPointLabel`` configuration parameters for
  :ref:`skool2asm.py <skool2asm-conf>` and
  :ref:`skool2html.py <skool2html-conf>` (for specifying the format of the
  default labels for routines and data blocks and their entry points)
* Added the ``Address`` configuration parameter for
  :ref:`skool2asm.py <skool2asm-conf>` (for specifying the format of the
  default link text for the :ref:`R` macro)
* The ``SnapshotReferenceOperations`` parameter in the :ref:`skoolkit` section
  of `skoolkit.ini` is now interpreted as a list of regular expression
  patterns (which enables any type of instruction to be designated by the
  :ref:`snapshot reference calculator <snapshotRefCalc>` as one whose address
  operand identifies an entry point in a routine or data block)
* Added support for identifying entries by address ranges in the
  :ref:`entryGroups` section and the ``Includes`` parameter in :ref:`memoryMap`
  sections
* Added the ``case`` parameter to the :ref:`FORMAT` macro (for converting
  formatted text to lower case or upper case)
* Added the ``DefaultDisassemblyStartAddress`` parameter to the :ref:`skoolkit`
  section of `skoolkit.ini` (for specifying the address at which to start
  disassembling a snapshot when no control file is provided)
* Added the ``InitModule`` parameter to the :ref:`ref-Config` section (for
  specifying a Python module to import before the HTML writer class is
  imported)
* Fixed the bug where a frame whose pixels are modified by the :ref:`PLOT`
  macro may have incorrect colours when converted to an image
* Fixed the bug where an ``M`` directive in a control file is ignored when it
  is followed by a sub-block that has sublengths

8.4 (2021-03-06)
----------------
* Made the :ref:`image writer component <imageWriter>` pluggable
* Added support for defining groups of entries (via the :ref:`entryGroups`
  section of the ref file) whose disassembly pages can be given custom titles
  and headers
* Added the ``Address`` parameter to the :ref:`ref-Game` section (for
  specifying the format of address fields on disassembly pages and memory map
  pages, and of the default link text for the :ref:`R` macro)
* Added the ``Length`` parameter to the :ref:`ref-Game` section (for specifying
  the format of the new ``length`` attribute of entry objects in
  :ref:`htmlTemplates`, which is now used instead of ``size`` in the Length
  column on :ref:`memory map pages <memoryMap>`)
* Added the ``Peek`` and ``Word`` configuration parameters for
  :ref:`snapinfo.py <snapinfo-conf>` (for specifying the format of each line of
  the output produced by the ``--peek`` and ``--word`` options)
* Added support for specifying an :ref:`expand` directive value over multiple
  lines by prefixing the second and subsequent lines with ``+``
* Added support to the ``--ram`` option of :ref:`tap2sna.py` for the
  ``sysvars`` operation (for initialising the system variables in a snapshot)
* Changed the default value of the ``DefmSize`` configuration parameter for
  :ref:`sna2skool.py <sna2skool-conf>` from 66 to 65; this makes it compliant
  with the default maximum line width of 79 defined by the ``LineWidth``
  configuration parameter
* Fixed the bug that prevents instruction comments from being repeated in a
  :ref:`control file loop <ctlLoops>`
* Fixed the bug that makes :ref:`sna2skool.py` ignore a given start address
  below 16384 when converting a snapshot

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
