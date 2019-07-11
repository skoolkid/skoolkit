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

HTML templates
--------------
The :ref:`htmlTemplates` have been overhauled in SkoolKit 8. As a result, the
following templates that were available in SkoolKit 7 no longer exist:

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
* ``list_items`` (renamed to :ref:`t_item_list`)
* ``map_entry``
* ``paragraph``
* ``reference_entry``
* ``stylesheet``
* ``table_cell``
* ``table_header_cell``
* ``table_row``

In addition, the following templates have been rewritten to use the
:ref:`td_foreach`, :ref:`td_if` and :ref:`td_include` directives, which are
new in SkoolKit 8:

* :ref:`t_Asm`
* :ref:`t_AsmAllInOne`
* :ref:`t_GameIndex`
* :ref:`t_MemoryMap`
* :ref:`t_Reference`
* :ref:`t_item_list` (previously named ``list_items``)
* :ref:`t_list`
* :ref:`t_table`
