.. _migrating:

Migrating from SkoolKit 6
=========================
SkoolKit 7 includes some changes that make it incompatible with SkoolKit 6. If
you have developed a disassembly using SkoolKit 6 and find that the SkoolKit
commands no longer work with your skool files or ref files, or produce broken
output, look through the following sections for tips on how to migrate your
disassembly to SkoolKit 7.

skool2html.py
-------------
In SkoolKit 6, :ref:`skool2html.py` wrote a separate disassembly for each skool
file and ref file named on the command line. In SkoolKit 7, it writes a single
disassembly from the skool file given as the first positional argument; any
other positional arguments are interpreted as extra ref files.

For example::

  $ skool2html.py game.skool data.ref

will convert the following files into a single HTML disassembly:

* `game.skool`
* any files named `game*.ref`
* any files named in the ``RefFiles`` parameter in the :ref:`ref-Config`
  section
* `data.ref`

sna2skool.py
------------
The ``-l``, ``-m``, ``-n``, ``-r``, ``-R``, ``-t`` and ``-z`` options of
:ref:`sna2skool.py` that were available in SkoolKit 6 are not supported in
SkoolKit 7. However, the corresponding features are still supported, and each
one can be controlled by the ``-I`` option with an appropriate configuration
parameter:

* instead of ``-l/--defm-size L``, use ``-I DefmSize=L``
* instead of ``-m/--defb-mod M``, use ``-I DefbMod=M``
* instead of ``-n/--defb-size N``, use ``-I DefbSize=N``
* instead of ``-r/--no-erefs``, use ``-I ListRefs=0``
* instead of ``-R/--erefs``, use ``-I ListRefs=2``
* instead of ``-t/--text``, use ``-I Text=1``
* instead of ``-z/--defb-zfill``, use ``-I DefbZfill=1``

In addition, the ability to generate a control file has been moved to the
:ref:`sna2ctl.py` command; accordingly, the ``-g``, ``-h`` and ``-M`` options
are no longer supported.

Finally, the ``-L`` (``--lower``) option has been renamed ``-l`` and the
``--skool-hex`` (``-H``) option has been renamed ``--hex`` (for consistency
with the corresponding options of :ref:`skool2asm.py` and
:ref:`skool2html.py`).

GameStatusBufferIncludes
------------------------
In SkoolKit 6, the ``GameStatusBufferIncludes`` parameter in the
:ref:`ref-Game` section specified the addresses of entries to include on the
'Game status buffer' page in addition to those that are marked with a ``g``. In
SkoolKit 7, this parameter is not supported; instead, use the ``Includes``
parameter in the :ref:`[MemoryMap:GameStatusBuffer] <memoryMap>` section.

@assemble
---------
In SkoolKit 6, the :ref:`assemble` directive accepted the values -1, 0 and 1.
In SkoolKit 7, the accepted values are 0, 1 and 2.

@nolabel
--------
The ``@nolabel`` directive is not supported in SkoolKit 7. Instead you should
use the :ref:`label` directive with a blank label: ``@label=``.

Image-related methods
---------------------
In SkoolKit 6, the following image-related methods were available on
HtmlWriter:

* :meth:`image_path`
* :meth:`img_element`
* :meth:`need_image`
* :meth:`write_animated_image`
* :meth:`write_image`

These methods are not available in SkoolKit 7; instead, use the
:meth:`~skoolkit.skoolhtml.HtmlWriter.handle_image` method.

In addition, the default value of the `path_id` parameter of
:meth:`handle_image` has changed from ``UDGImagePath`` to ``ImagePath``.

Data definition entries
-----------------------
Data definition entries ('d' blocks) are not supported in SkoolKit 7. Use the
:ref:`defb`, :ref:`defs` and :ref:`defw` directives instead.

Remote entries
--------------
Defining a remote entry with an 'r' block is not supported in SkoolKit 7. Use
the :ref:`remote` directive instead.

skoolkit6to7.py
---------------
The `skoolkit6to7.py`_ script may be used to convert a control file, ref file,
skool file or skool file template that is compatible with SkoolKit 6 into a
file that will work with SkoolKit 7. For example, to convert `game.ref`::

  $ skoolkit6to7.py game.ref > game7.ref

.. _skoolkit6to7.py: https://github.com/skoolkid/skoolkit/raw/master/utils/skoolkit6to7.py
