Changelog
=========

10.2b1
------
* Added support to :ref:`rzxplay.py <rzxplay-conf>` for reading configuration
  from `skoolkit.ini`
* Added the ``--ini`` and ``--show-config`` options to :ref:`rzxplay.py` (for
  setting the value of a configuration parameter and for showing all
  configuration parameter values)
* Added the ``TraceHeader`` configuration parameter for
  :ref:`tap2sna.py <tap2sna-conf>` (to specify the header for a trace log file)

10.1 (2026-08-14)
-----------------
* Added the ``--screen`` option to :ref:`tap2sna.py` (to display screen
  contents while running)
* Added the ``ScreenFps`` and ``ScreenScale`` configuration parameters for
  :ref:`tap2sna.py <tap2sna-conf>` (to specify the frame rate and scale factor
  when displaying screen contents)
* Added the ``--volume`` option to :ref:`trace.py` (for setting the audio
  volume when writing a WAV file)
* Added the ``vol`` parameter to the :ref:`AUDIO` macro (to set the audio
  volume)
* Added the ``--ay-mode`` option to :ref:`trace.py` (for setting the AY stereo
  mode when writing a WAV file)
* Added the ``aymode`` parameter to the :ref:`AUDIO` macro (to set the AY
  stereo mode)
* Added the ``--ay-res`` option to :ref:`trace.py` (for setting the AY sampling
  resolution when writing a WAV file)
* Added the ``ayres`` parameter to the :ref:`AUDIO` macro (to set the AY
  sampling resolution)
* Added the ``--cmio`` option to :ref:`rzxplay.py` (to enable simulation of
  memory and I/O contention and the MEMPTR register)
* Added support for multiple colours in the border area of the screen displayed
  by :ref:`rzxplay.py` and :ref:`trace.py`
* Made the :ref:`AY audio writer <ayAudioWriter>` a pluggable component
* Made the :ref:`screen <screen>` a pluggable component
* Fixed how :ref:`trace.py` sets the frame duration when the input file
  argument is '128' or '+2'
* Fixed how :ref:`rzxinfo.py` detects a signed RZX file and encrypted frames
* Fixed the bug in :ref:`sna2ctl.py` that enables the :ref:`rstHandler` when
  the :ref:`comment generator <commentGenerator>` is enabled

10.0 (2026-04-04)
-----------------
* Dropped support for Python 3.9
* Added the ``--ay`` option to :ref:`trace.py` (for capturing AY audio when
  writing a WAV file)
* Added the ``ay`` parameter to the :ref:`AUDIO` macro (to set whether AY
  audio is captured)
* Added the ``--beeper`` option to :ref:`trace.py` (for capturing beeper audio
  as well when ``--ay`` is specified)
* Added the ``bpr`` parameter to the :ref:`AUDIO` macro (to set whether beeper
  audio is captured along with AY audio)
* Added support for the MEMPTR register to CMIOSimulator and CCMIOSimulator
* Added the ``memptr`` parameter to the :ref:`SIM` macro (to set the MEMPTR
  register)
* :ref:`snapinfo.py` now shows the MEMPTR register value in SZX snapshots
* Added support to :ref:`trace.py` for setting the MEMPTR register before
  execution begins, for reading and writing MEMPTR in SZX snapshots, and for
  tracing its value via the ``r[memptr]`` replacement field in the
  ``TraceLine*`` configuration parameters
* Added support to :ref:`tap2sna.py` for setting the MEMPTR register in SZX
  snapshots, and for tracing its value via the ``r[memptr]`` replacement field
  in the ``TraceLine`` configuration parameter
* Added support to :ref:`bin2sna.py` and :ref:`snapmod.py` for setting the
  MEMPTR register in SZX snapshots
* Added the ``TraceHeader`` and ``TraceHeader2`` configuration parameters for
  :ref:`trace.py <trace-conf>` (to specify headers to print before a trace)
* Added support to the :ref:`AUDIO` macro for keyword arguments
* Added support to :ref:`rzxplay.py` for ignoring any snapshots after the first
  one (which is useful for playing some RZX files created by the Fuse emulator)
* Added a border area to the screen displayed by :ref:`rzxplay.py` and
  :ref:`trace.py`
* Updated the comments generated for 'IN r,(C)' immediately after 'LD BC,$XXFE'
  and 'IN A,($FE)' immediately after 'LD A,n' when a single half-row of the
  keyboard is read
* Updated the default values of ``ContentionBegin``, ``ContentionEnd`` and
  ``InterruptDelay`` in the :ref:`ref-AudioWriter` section
* Added support for multiple values to the ``InterruptDelay`` parameter in the
  :ref:`ref-AudioWriter` section
* Fixed the bug in CSimulator that restricts the ``timeout`` simulated load
  configuration parameter to a maximum value of 1227 seconds
* Fixed how :ref:`tap2sna.py` handles zero-length pulses in the encodings of 0s
  and 1s in a PZX DATA block

Older versions
--------------
.. toctree::
   :maxdepth: 1

   changelog9
   changelog8
   changelog7
   changelog6
   changelog5
   changelog4
   changelog3
   changelog2
   changelog1
