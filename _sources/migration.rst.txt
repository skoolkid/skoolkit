.. _migrating:

Migrating from SkoolKit 7
=========================
SkoolKit 8 includes some changes that make it incompatible with SkoolKit 7. If
you have developed a disassembly using SkoolKit 7 and find that the SkoolKit
commands no longer work with your source files, or produce broken output, look
through the following sections for tips on how to migrate your disassembly to
SkoolKit 8.

GIF images
----------
Creating GIF images is not supported in SkoolKit 8. The :ref:`FONT`,
:ref:`SCR`, :ref:`UDG` and :ref:`UDGARRAY` macros now always create PNG images.
Accordingly, the following parameters from the :ref:`ref-ImageWriter` section
that were available in SkoolKit 7 are no longer supported:

* ``DefaultAnimationFormat``
* ``DefaultFormat``
* ``GIFEnableAnimation``
* ``GIFTransparency``

Skool file templates
--------------------
Skool file templates are not supported in SkoolKit 8. The `skool2sft.py`
command has been removed, along with the ``--sft`` option of
:ref:`sna2skool.py`.

Where you might have used skool file templates with SkoolKit 7, you should now
use :ref:`control files <controlFiles>` instead. However, note that control
files cannot preserve ASM block directives that occur inside a regular entry,
and so any such directives should be replaced before using :ref:`skool2ctl.py`.
See :ref:`Limitations` for more details.

[Game]
------
The ``TitlePrefix`` and ``TitleSuffix`` parameters are no longer supported. Use
the ``GameIndex`` parameter in the :ref:`pageHeaders` section instead.

The ``AsmSinglePageTemplate`` parameter is no longer supported. Use the
``AsmSinglePage`` parameter instead.

[Titles]
--------
In SkoolKit 7, the entry address in a disassembly page title was included in
the ``Asm`` template. In SkoolKit 8, the ``Asm`` template no longer exists, and
the entry address appears as a replacement field (``{entry[address]}``) in the
``Asm-b``, ``Asm-c``, ``Asm-g``, ``Asm-s``, ``Asm-t``, ``Asm-u`` and ``Asm-w``
parameters in the :ref:`titles` section.

Control directives
------------------
The ``B`` and ``T`` control directives no longer recognise the ``B`` (byte) and
``T`` (text) indicators. Use the ``n`` and ``c`` base indicators instead. For
example::

  B 30000,5,2:T3
  T 30005,5,B3:2

should be replaced by::

  B 30000,5,2:c3
  T 30005,5,n3:2

sna2skool.py
------------
The ``DefbMod`` configuration parameter is no longer supported. It could be
used to group DEFB blocks by addresses that are divisible by a certain number,
but the same effect can be achieved with appropriate control directives.

The ``DefbZfill`` configuration parameter is also no longer supported.

HTML templates
--------------
The :ref:`htmlTemplates` have been overhauled in SkoolKit 8. As a result, the
following templates that were available in SkoolKit 7 no longer exist:

* ``Asm``
* ``AsmAllInOne``
* ``GameIndex``
* ``MemoryMap``
* ``Page``
* ``Reference``
* ``anchor``
* ``asm_comment``
* ``asm_entry``
* ``asm_instruction``
* ``asm_register``
* ``contents_list_item``
* ``index_section``
* ``index_section_item``
* ``javascript``
* ``list_entry``
* ``list_item``
* ``list_items``
* ``map_entry``
* ``paragraph``
* ``reference_entry``
* ``stylesheet``
* ``table_cell``
* ``table_header_cell``
* ``table_row``

In addition, the following templates have been rewritten to use the
:ref:`td_foreach` and :ref:`td_if` directives, which are new in SkoolKit 8:

* :ref:`t_list`
* :ref:`t_table`

Finally, the signature of the :meth:`format_template` method on HtmlWriter has
changed in SkoolKit 8.0: the *default* parameter has been removed.

CSS selectors
-------------
The `class` attributes of some HTML elements have changed in SkoolKit 8.

The following table lists the selectors that appeared in the CSS files in
SkoolKit 7, and their replacements (if any) in SkoolKit 8.

====================  ==========
SkoolKit 7            SkoolKit 8
====================  ==========
div.map-entry-desc-0
div.map-entry-desc-1  div.map-entry-desc
span.next-0
span.prev-0
table.input-0
table.input-1         table.input
table.output-0
table.output-1        table.output
td.asm-label-0
td.asm-label-1        td.asm-label
td.bytes-0
td.bytes-1            td.bytes
td.comment-01
td.comment-10         td.comment-0
td.comment-11         td.comment-1
td.map-byte-0
td.map-byte-1         td.map-byte
td.map-length-0
td.map-length-1       td.map-length
td.map-page-0
td.map-page-1         td.map-page
th.map-byte-0
th.map-length-0
th.map-page-0
====================  ==========

The following table lists selectors for the classes that were unstyled (i.e.
did not appear in any CSS files) in SkoolKit 7, and their replacements (if any)
in SkoolKit 8.

====================  ==========
SkoolKit 7            SkoolKit 8
====================  ==========
span.next-1
span.prev-1
th.map-byte-1         th.map-byte
th.map-length-1       th.map-length
th.map-page-1         th.map-page
====================  ==========

skoolkit7to8.py
---------------
The `skoolkit7to8.py`_ script may be used to convert a control file or ref file
that is compatible with SkoolKit 7 into a file that will work with SkoolKit 8.
For example, to convert `game.ref`::

  $ skoolkit7to8.py game.ref > game8.ref

.. _skoolkit7to8.py: https://github.com/skoolkid/skoolkit/raw/master/utils/skoolkit7to8.py
