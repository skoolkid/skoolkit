Changelog
=========

9.3 (2024-08-10)
----------------
* Added support to :ref:`tapinfo.py` and :ref:`tap2sna.py` for reading PZX
  files
* Added support to :ref:`bin2tap.py` for writing PZX files
* Added support to :ref:`tap2sna.py <tap2sna-conf>` for the ``m`` (memory)
  replacement field in the ``TraceLine`` configuration parameter
* Added support to :ref:`trace.py <trace-conf>` for the ``m`` (memory)
  replacement field in the ``TraceLine*`` configuration parameters
* Added the ``--state`` option to :ref:`trace.py` (for setting hardware state
  attributes before code execution begins)
* Added support to :ref:`trace.py` for writing a WAV file after code execution
  has completed
* Added the ``Opcodes`` configuration parameter to
  :ref:`sna2skool.py <sna2skool-conf>` (for specifying additional opcode
  sequences to disassemble)
* Added the :ref:`bytes` directive (for specifying the byte values to which an
  instruction should assemble)
* Added the ``--tape-start`` and ``--tape-stop`` options to :ref:`tapinfo.py`
  (for specifying the block numbers at which to start or stop showing info)
* :ref:`tapinfo.py` now shows info for TZX block types 0x18 (CSW recording) and
  0x2B (set signal level), and also recognises the deprecated TZX block types
  0x16, 0x17, 0x34 and 0x40
* The ``--find``, ``--find-text`` and ``--find-tile`` options of
  :ref:`snapinfo.py` now search all RAM banks in a 128K snapshot by default
* Added support for path ID replacement fields in the ``destDir`` parameter of
  items in the :ref:`resources` section
* Fixed the bug that prevents the ``--reg`` option of :ref:`trace.py` from
  accepting hexadecimal values prefixed by '0x'

9.2 (2024-05-11)
----------------
* Added a Z80 instruction set simulator implemented in C (as a faster
  alternative to the pure Python Z80 simulator)
* Added the :ref:`rzxplay.py` command (for playing an RZX file)
* Added the :ref:`rzxinfo.py` command (for showing the blocks in or extracting
  the snapshots from an RZX file)
* Added support to :ref:`sna2ctl.py` for reading code execution maps produced
  by :ref:`rzxplay.py`
* Added support to :ref:`tap2sna.py` for TZX block type 0x15 (direct recording)
* :ref:`tapinfo.py` now shows info for TZX block type 0x15 (direct recording)
* Added support to :ref:`trace.py` for executing machine code in +2 snapshots
* Added the ``python`` simulated LOAD configuration parameter to
  :ref:`tap2sna.py <tap2sna-sim-load>` (for forcing usage of the pure Python
  Z80 simulator even if the C version is available)
* Added the ``--python`` option to :ref:`trace.py` (for forcing usage of the
  pure Python Z80 simulator even if the C version is available)
* Fixed the lazy evaluation bug that can make the :ref:`FONT`, :ref:`SCR` and
  :ref:`UDG` macros create frames with incorrect graphic content
* Fixed the bug that can make :ref:`trace.py` stop too soon when the
  ``--max-tstates`` option is used
* Fixed the contention pattern for the OUTI/OUTD/OTIR/OTDR instructions

9.1 (2024-02-03)
----------------
* Added support to :ref:`snapmod.py` for modifying SZX snapshots and 128K
  snapshots
* Added support to :ref:`bin2sna.py` for writing 128K snapshots (by using the
  ``--page`` and ``--bank`` options, or by providing a 128K input file)
* Added support to :ref:`bin2tap.py` for writing 128K TAP files (by using the
  ``--7ffd``, ``--banks`` and ``--loader`` options)
* Added support to :ref:`bin2sna.py`, :ref:`snapmod.py`, :ref:`tap2sna.py` and
  :ref:`trace.py` for modifying 128K RAM banks (via the ``--move``, ``--poke``,
  ``--ram move`` and ``--ram poke`` options)
* Added the :ref:`BANK` macro (for switching the RAM bank that is mapped to
  49152-65535)
* Added the :ref:`asm-bank` directive (for specifying the RAM bank that is
  mapped to 49152-65535, and for populating a RAM bank from the contents of
  another skool file)
* Added the ``--banks`` option to :ref:`skool2bin.py` (for processing
  :ref:`asm-bank` directives and writing RAM banks 0-7 to a 128K file)
* Added the ``cmio`` simulated LOAD configuration parameter to
  :ref:`tap2sna.py <tap2sna-sim-load>` (to specify whether to simulate memory
  and I/O contention)
* Added the ``--cmio`` option to :ref:`trace.py` (to enable simulation of
  memory and I/O contention)
* Added the ``cmio`` parameter to the :ref:`AUDIO`, :ref:`SIM` and
  :ref:`TSTATES` macros (to specify whether to simulate memory and I/O
  contention)
* Added the ``execint`` parameter to the :ref:`AUDIO`, :ref:`SIM` and
  :ref:`TSTATES` macros (to specify whether to simulate the execution of
  interrupt routines)
* Added the ``tstates`` parameter to the :ref:`SIM` macro (to set the value of
  the simulator's clock)
* Added the ``iff`` parameter to the :ref:`SIM` macro (to set whether
  interrupts are enabled)
* Added the ``im`` parameter to the :ref:`SIM` macro (to set the interrupt
  mode)
* Made the ``stop`` parameter of the :ref:`SIM` macro optional
* Added support to the :ref:`AUDIO`, :ref:`SIM` and :ref:`TSTATES` macros for
  executing code in a 128K memory snapshot
* Fixed how :ref:`trace.py` handles the value of the SP register in a 128K SNA
  file
* Fixed how :ref:`tap2sna.py` and :ref:`trace.py` log timestamps when an
  interrupt occurs
* Fixed how interrupts are accepted when :ref:`tap2sna.py` and :ref:`trace.py`
  execute code in a simulator
* Fixed how the Z80 instruction set simulator updates bit 2 of the flags
  register when executing an 'LD A,I' or 'LD A,R' instruction just before an
  interrupt is accepted
* Fixed the bug that makes the ``--basic`` option of :ref:`snapinfo.py` fail
  when the value of PROG is 65535
* Fixed the bug that prevents an :ref:`mDirective` from being repeated in a
  :ref:`control file loop <ctlLoops>`

9.0 (2023-11-04)
----------------
* Dropped support for Python 3.7
* :ref:`tap2sna.py` now performs a :ref:`simulated LOAD <tap2sna-sim-load>` by
  default, and will also overwrite an existing snapshot by default
* Added the ``machine`` simulated LOAD configuration parameter to
  :ref:`tap2sna.py <tap2sna-sim-load>` (to specify whether to simulate a 48K or
  a 128K Spectrum)
* Added the ``load`` simulated LOAD configuration parameter to
  :ref:`tap2sna.py <tap2sna-sim-load>` (to specify an alternative command line
  to use to load the tape)
* Added the ``polarity`` simulated LOAD configuration parameter to
  :ref:`tap2sna.py <tap2sna-sim-load>` (to specify the EAR bit reading produced
  by the first pulse on the tape)
* Added the ``in-flags`` simulated LOAD configuration parameter to
  :ref:`tap2sna.py <tap2sna-sim-load>` (to specify how to handle 'IN'
  instructions)
* The output snapshot argument of :ref:`tap2sna.py` is now optional
* Added the ``DefaultSnapshotFormat`` configuration parameter for
  :ref:`tap2sna.py <tap2sna-conf>` (to specify the default output snapshot
  format)
* Added support to :ref:`tap2sna.py <tap2sna-conf>` for register pairs
  (``r[bc]``, ``r[de]`` etc.) in the ``TraceLine`` configuration parameter
* Added the ``antirom``, ``ernieware`` and ``housenka`` tape-sampling loop
  :ref:`accelerators <tap2sna-accelerators>`
* Statistics for 'DEC A' tape-sampling delay loops are now shown by
  :ref:`tap2sna.py` when ``accelerator=list``
* Added support to :ref:`trace.py` for executing machine code in 128K snapshots
* Added support to :ref:`trace.py <trace-conf>` for reading configuration
  from `skoolkit.ini`
* Added the ``--ini`` and ``--show-config`` options to :ref:`trace.py` (for
  setting the value of a configuration parameter and for showing all
  configuration parameter values)
* Added the ``--no-interrupts`` option to :ref:`trace.py` (to prevent the
  execution of interrupt routines, which are now executed by default)
* Added support to :ref:`bin2sna.py`, :ref:`tap2sna.py` and :ref:`trace.py` for
  writing SZX snapshots
* Added support to :ref:`bin2sna.py` and :ref:`tap2sna.py` for setting the
  ``fe`` hardware state attribute (i.e. the last value written to port 0xFE in
  SZX snapshots)
* Added support to the :ref:`AUDIO` macro for passing delays through a moving
  average filter (which can produce higher quality audio, especially for
  multi-channel tunes)
* Added support to :ref:`control directive loops <ctlLoops>` for avoiding
  repetition of an ``N`` directive at the start of a loop
* :ref:`tapinfo.py` now shows the LINE number (if present) for 'Program:'
  header blocks, and renders BASIC tokens in header block names
* :ref:`snapinfo.py` now shows the current AY register in 128K SZX and Z80
  snapshots
* Changed the default value of ``H`` and ``A`` for the :ref:`assemble`
  directive to 2
* Fixed the bug that prevents :ref:`tap2sna.py` from loading a tape that has a
  hash character (``#``) in its filename

Older versions
--------------
.. toctree::
   :maxdepth: 1

   changelog8
   changelog7
   changelog6
   changelog5
   changelog4
   changelog3
   changelog2
   changelog1
