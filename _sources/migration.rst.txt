.. _migrating:

Migrating from SkoolKit 8
=========================
SkoolKit 9 includes some changes that make it incompatible with SkoolKit 8. If
you have developed a disassembly using SkoolKit 8 and find that the SkoolKit
commands no longer work with your source files, or produce broken output, look
through the following sections for tips on how to migrate your disassembly to
SkoolKit 9.

#DEFINE
-------
The ``#DEFINE`` macro is not supported in SkoolKit 9. Instead, the more
powerful :ref:`DEF` macro should be used.

For example, you might have used ``#DEFINE`` to define a ``#MIN`` macro that
expands to the smaller of its two integer arguments::

  #DEFINE2(MIN,#IF({0}<{1})({0},{1}))

This can be redefined by using the ``#DEF`` macro::

  #DEF(#MIN(a,b) #IF($a<$b)($a,$b))

snapmod.py
----------
In SkoolKit 8, :ref:`snapmod.py` would refuse to overwrite an existing snapshot
unless the ``--force`` option was given. In SkoolKit 9, `snapmod.py` will
overwrite an existing snapshot by default, and the ``--force`` option is no
longer supported.

tapinfo.py
----------
The ``--tzx-blocks`` option is no longer supported in SkoolKit 9. In addition,
the short option name for ``--basic`` has changed from ``-B`` to ``-b`` (for
consistency with the ``-b`` option of :ref:`snapinfo.py`).

tap2sna.py
----------
In SkoolKit 8, :ref:`tap2sna.py` performed a
:ref:`simulated LOAD <tap2sna-sim-load>` only if the ``--sim-load`` option was
given. In SkoolKit 9, `tap2sna.py` performs a simulated LOAD by default, and
the ``--sim-load`` option is no longer supported. Simulated LOADing is disabled
only if a ``--ram load`` option is given.

In SkoolKit 8, :ref:`tap2sna.py` would refuse to overwrite an existing snapshot
unless the ``--force`` option was given. In SkoolKit 9, `tap2sna.py` will
overwrite an existing snapshot by default, and the ``--force`` option is no
longer supported.

In SkoolKit 8, the default value of the ``first-edge`` simulated LOAD
configuration parameter was -2168. In SkoolKit 9, the default value is 0.

The ``contended-in`` simulated LOAD configuration parameter is no longer
supported. Use ``in-flags=1`` instead.

The following tape-sampling loop accelerator names are not available in
SkoolKit 9:

* ``cyberlode`` (use ``bleepload`` instead)
* ``edge`` (use ``rom`` instead)
* ``elite-uni-loader`` (use ``speedlock`` instead)
* ``excelerator`` (use ``bleepload`` instead)
* ``flash-loader`` (use ``rom`` instead)
* ``ftl`` (use ``speedlock`` instead)
* ``gargoyle`` (use ``speedlock`` instead)
* ``hewson-slowload`` (use ``rom`` instead)
* ``injectaload`` (use ``bleepload`` instead)
* ``poliload`` (use ``dinaload`` instead)
* ``power-load`` (use ``bleepload`` instead)
* ``softlock`` (use ``rom`` instead)
* ``zydroload`` (use ``speedlock`` instead)

The ``r[t]`` replacement field (for use in the ``TraceLine`` configuration
parameter) is no longer supported in SkoolKit 9. Use the ``t`` replacement
field instead.

trace.py
--------
In SkoolKit 8, :ref:`trace.py` had a ``--dump`` option for specifying an output
Z80 snapshot file. In SkoolKit 9, this option has been removed; instead the
output filename may be specified after the input filename. For example::

  $ trace.py --stop 32768 in.z80 out.z80

In SkoolKit 8, the ``--interrupts`` option enabled the execution of interrupt
routines. In SkoolKit 9, interrupt routines are executed by default, and the
``--interrupts`` option has been removed. Use the ``--no-interrupts`` option to
prevent the execution of interrupt routines.

In SkoolKit 8, if the input filename was '.', a blank 48K snapshot was
substituted. In SkoolKit 9, this no longer works; instead, use '48' for a
blank 48K snapshot, or '128' for a blank 128K snapshot.
