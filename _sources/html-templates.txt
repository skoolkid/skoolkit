.. _htmlTemplates:

HTML templates
==============
Every page in an HTML disassembly is built from a single full-page template and
several subtemplates defined by :ref:`template` sections in the ref file.

A template may contain 'replacement fields' - identifiers enclosed by braces
(``{`` and ``}``) - that are replaced by appropriate content (typically derived
from the skool file or a ref file section) when the template is formatted. The
following 'universal' identifiers are available in every template:

* ``Game`` - a dictionary of the parameters in the :ref:`ref-game` section
* ``SkoolKit`` - a dictionary of parameters relevant to the page currently
  being built

The parameters in the ``SkoolKit`` dictionary are:

* ``index_href`` - the relative path to the disassembly index page
* ``page_header`` - the page header text (as defined in the :ref:`pageHeaders`
  section)
* ``page_id`` - the page ID (e.g. ``GameIndex``, ``MemoryMap``)
* ``path`` - the page's filename, including the full path relative to the root
  of the disassembly
* ``title`` - the title of the page (as defined in the :ref:`titles` section)

The parameters in a dictionary are accessed using the ``[param]`` notation;
for example, wherever ``{Game[Copyright]}`` appears in a template, it is
replaced by the value of the ``Copyright`` parameter in the :ref:`ref-game`
section when the template is formatted.

In addition to the universal identifiers, the following page-level identifiers
are available in every full-page template:

* ``m_javascript`` - replaced by any number of copies of the
  :ref:`t_javascript` subtemplate
* ``m_stylesheet`` - replaced by one or more copies of the :ref:`t_stylesheet`
  subtemplate
* ``t_footer`` - replaced by a copy of the :ref:`t_footer` subtemplate

.. versionchanged:: 6.4
   Added ``path`` to the ``SkoolKit`` dictionary.

.. _t_Asm:

Asm
---
The ``Asm`` template is the full-page template that is used to build
disassembly pages.

The following identifiers are available (in addition to the universal and
page-level identifiers):

* ``disassembly`` - replaced by sequences of copies of the
  :ref:`t_asm_instruction` subtemplate, punctuated by copies of the
  :ref:`t_asm_comment` subtemplate
* ``entry`` - a dictionary of parameters corresponding to the current memory
  map entry (see below)
* ``next_entry`` - a dictionary of parameters corresponding to the next memory
  map entry (see below)
* ``prev_entry`` - a dictionary of parameters corresponding to the previous
  memory map entry (see below)
* ``registers_input`` - replaced by any number of copies of the
  :ref:`t_asm_register` subtemplate
* ``registers_output`` - replaced by any number of copies of the
  :ref:`t_asm_register` subtemplate

The parameters in the ``prev_entry``, ``entry`` and ``next_entry`` dictionaries
are:

* ``address`` - the address of the entry (may be in decimal or hexadecimal
  format, depending on how it appears in the skool file, and the options passed
  to :ref:`skool2html.py`)
* ``annotated`` - '1' if any instructions in the entry have a non-empty comment
  field, '0' otherwise
* ``byte`` - the LSB of the entry address
* ``description`` - the entry description
* ``exists`` - '1' if the entry exists, '0' otherwise
* ``href`` - the relative path to the disassembly page for the entry (useful
  only for ``prev_entry`` and ``next_entry``)
* ``label`` - the ASM label of the first instruction in the entry
* ``labels`` - '1' if any instructions in the entry have an ASM label, '0'
  otherwise
* ``location`` - the address of the entry as a decimal number
* ``map_href`` - the relative path to the entry on the 'Memory Map' page
* ``page`` - the MSB of the entry address
* ``size`` - the size of the entry in bytes
* ``title`` - the title of the entry
* ``type`` - the block type of the entry ('b', 'c', 'g', 's', 't', 'u' or 'w')

The ``entry`` dictionary also contains the following parameters:

* ``input`` - '1' if there are input register values defined, '0' otherwise
* ``output`` - '1' if there are output register values defined, '0' otherwise

To see the default ``Asm`` template, run the following command::

  $ skool2html.py -r Template:Asm$

.. _t_AsmAllInOne:

AsmAllInOne
-----------
The ``AsmAllInOne`` template is a full-page template that may be used to build
a disassembly on a single page (by setting the ``AsmSinglePageTemplate``
parameter in the :ref:`ref-Game` section).

The following identifier is available (in addition to the universal and
page-level identifiers):

* ``m_asm_entry`` - replaced by one or more copies of the :ref:`t_asm_entry`
  subtemplate

To see the default ``AsmAllInOne`` template, run the following command::

  $ skool2html.py -r Template:AsmAllInOne

.. versionadded:: 5.3

.. _t_GameIndex:

GameIndex
---------
The ``GameIndex`` template is the full-page template that is used to build the
disassembly index page.

The following identifier is available (in addition to the universal and
page-level identifiers):

* ``m_index_section`` - replaced by any number of copies of the
  :ref:`t_index_section` subtemplate

To see the default ``GameIndex`` template, run the following command::

  $ skool2html.py -r Template:GameIndex

.. _t_MemoryMap:

MemoryMap
---------
The ``MemoryMap`` template is the full-page template that is used to build
memory map pages and the 'Game status buffer' page.

The following identifiers are available (in addition to the universal and
page-level identifiers):

* ``MemoryMap`` - a dictionary of the parameters in the corresponding
  :ref:`memoryMap` section
* ``m_map_entry`` - replaced by one or more copies of the :ref:`t_map_entry`
  subtemplate

To see the default ``MemoryMap`` template, run the following command::

  $ skool2html.py -r Template:MemoryMap

.. _t_Page:

Page
----
The ``Page`` template is the full-page template that is used to build custom
non-box pages defined by :ref:`page` sections.

The following identifier is available (in addition to the universal and
page-level identifiers):

* ``content`` - replaced by the value of the ``PageContent`` parameter in the
  corresponding :ref:`page` section

To see the default ``Page`` template, run the following command::

  $ skool2html.py -r Template:Page

.. _t_Reference:

Reference
---------
The ``Reference`` template is the full-page template that is used to build
:ref:`box pages <boxpages>`.

The following identifiers are available (in addition to the universal and
page-level identifiers):

* ``entries`` - replaced by one or more copies of the :ref:`t_list_entry`
  subtemplate (when the page's ``SectionType`` is ``BulletPoints`` or
  ``ListItems``), or the :ref:`t_reference_entry` subtemplate
* ``m_contents_list_item`` - replaced by one or more copies of the
  :ref:`t_contents_list_item` subtemplate

To see the default ``Reference`` template, run the following command::

  $ skool2html.py -r Template:Reference

.. _t_anchor:

anchor
------
The ``anchor`` template is the subtemplate used to format a page anchor (by
default, a ``<span>`` element with an ``id`` attribute).

The following identifier is available (in addition to the universal
identifiers):

* ``anchor`` - the value of the ``id`` attribute

To see the default ``anchor`` template, run the following command::

  $ skool2html.py -r Template:anchor

.. _t_asm_comment:

asm_comment
-----------
The ``asm_comment`` template is the subtemplate used by the :ref:`t_Asm`
full-page template and the :ref:`t_asm_entry` subtemplate to format block start
comments, mid-block comments and block end comments.

The following identifiers are available (in addition to the universal
identifiers):

* ``entry`` - a dictionary of parameters corresponding to the current memory
  map entry (see :ref:`t_Asm`)
* ``m_paragraph`` - replaced by one or more copies of the :ref:`t_paragraph`
  subtemplate
* ``t_anchor`` - replaced by a copy of the :ref:`t_anchor` subtemplate (when
  formatting a block start comment or a mid-block comment), or by an empty
  string (when formatting a block end comment)

To see the default ``asm_comment`` template, run the following command::

  $ skool2html.py -r Template:asm_comment

.. _t_asm_entry:

asm_entry
---------
The ``asm_entry`` template is the subtemplate used by the :ref:`t_AsmAllInOne`
full-page template to format the disassembly of a memory map entry.

The following identifiers are available (in addition to the universal
identifiers):

* ``disassembly`` - replaced by sequences of copies of the
  :ref:`t_asm_instruction` subtemplate, punctuated by copies of the
  :ref:`t_asm_comment` subtemplate
* ``entry`` - a dictionary of parameters corresponding to the memory map entry;
  the parameters in this dictionary are the same as those in the ``entry``
  dictionary in the :ref:`t_Asm` template
* ``registers_input`` - replaced by any number of copies of the
  :ref:`t_asm_register` subtemplate
* ``registers_output`` - replaced by any number of copies of the
  :ref:`t_asm_register` subtemplate

To see the default ``asm_entry`` template, run the following command::

  $ skool2html.py -r Template:asm_entry

.. versionadded:: 5.3

.. _t_asm_instruction:

asm_instruction
---------------
The ``asm_instruction`` template is the subtemplate used by the :ref:`t_Asm`
full-page template and the :ref:`t_asm_entry` subtemplate to format an
instruction (including its label, address, operation and comment).

The following identifiers are available (in addition to the universal
identifiers):

* ``address`` - the address of the instruction (may be in decimal or
  hexadecimal format, depending on how it appears in the skool file, and the
  options passed to :ref:`skool2html.py`)
* ``annotated`` - '1' if the instruction has a comment field, '0' otherwise
* ``bytes`` - the byte values of the assembled instruction (see below)
* ``called`` - '2' if the instruction is an entry point, '1' otherwise
* ``comment`` - the text of the instruction's comment field
* ``comment_rowspan`` - the number of instructions to which the comment field
  applies
* ``entry`` - a dictionary of parameters corresponding to the memory map entry
  that contains the instruction (see :ref:`t_Asm`)
* ``label`` - the instruction's ASM label
* ``location`` - the address of the instruction as a decimal number
* ``operation`` - the assembly language operation (e.g. 'LD A,B'), with operand
  hyperlinked if appropriate
* ``show_bytes`` - '1' if the entry contains at least one assembled instruction
  with byte values and the ``Bytes`` parameter in the :ref:`ref-Game` section
  is not blank, '0' otherwise
* ``t_anchor`` - replaced by a copy of the :ref:`t_anchor` subtemplate

The ``bytes`` identifier can be used to render the byte values of an
instruction. In its simplest form, it provides a format specification that is
applied to each byte. For example::

  {bytes:02X}

would produce the string ``3E01`` for the instruction 'LD A,1'.

To render the byte values as 0-padded decimal integers separated by commas, use
the following syntax::

  {bytes:/03/,}

This would produce the string ``062,001`` for the instruction 'LD A,1'. The
delimiter used in this example (``/``) is arbitrary; it could be any character
that doesn't appear in the byte format specification itself.

The default ``asm_instruction`` template uses the ``Bytes`` parameter in the
:ref:`ref-Game` section as the byte format specification::

  <td class="bytes-{show_bytes}">{bytes:{Game[Bytes]}}</td>

If you define a custom template that replaces ``{Game[Bytes]}`` with a
hard-coded byte format specification, it's a good idea to also replace the
``{show_bytes}`` field with ``1``, to ensure that the byte values are
displayed.

Note that byte values are available only for regular assembly language
instructions (not DEFB, DEFM, DEFS or DEFW statements), and only if they have
actually been assembled by using :ref:`@assemble=2 <assemble>`. When no byte
values are available, or the format specification is blank, the ``bytes``
identifier produces an empty string.

To see the default ``asm_instruction`` template, run the following command::

  $ skool2html.py -r Template:asm_instruction

.. versionchanged:: 7.2
   Added the ``bytes`` and ``show_bytes`` identifiers, and a table cell for
   displaying assembled instruction byte values.

.. versionchanged:: 6.3
   Added the ``location`` identifier.

.. _t_asm_register:

asm_register
------------
The ``asm_register`` template is the subtemplate used by the :ref:`t_Asm`
full-page template and the :ref:`t_asm_entry` subtemplate to format each row in
a table of input register values or output register values.

The following identifiers are available (in addition to the universal
identifiers):

* ``description`` - the register's description (as it appears in the register
  section for the current entry in the skool file)
* ``entry`` - a dictionary of parameters corresponding to the current memory
  map entry (see :ref:`t_Asm`)
* ``name`` - the register's name (e.g. 'HL')

To see the default ``asm_register`` template, run the following command::

  $ skool2html.py -r Template:asm_register

.. _t_contents_list_item:

contents_list_item
------------------
The ``contents_list_item`` template is the subtemplate used by the
:ref:`t_Reference` full-page template to format each item in the contents list
on a :ref:`box page <boxpages>`.

The following identifiers are available (in addition to the universal
identifiers):

* ``href`` - the URL to the entry on the page
* ``title`` - the entry title

To see the default ``contents_list_item`` template, run the following command::

  $ skool2html.py -r Template:contents_list_item

.. _t_footer:

footer
------
The ``footer`` template is the subtemplate used by the full-page templates to
format the ``<footer>`` element of a page.

When this template is part of a disassembly page, the following additional
identifier is available:

* ``entry`` - a dictionary of parameters corresponding to the current memory
  map entry (see :ref:`t_Asm`)

To see the default ``footer`` template, run the following command::

  $ skool2html.py -r Template:footer

.. versionchanged:: 6.4
   The ``entry`` identifier is available when the template is part of a
   disassembly page.

.. versionadded:: 5.0

.. _t_img:

img
---
The ``img`` template is the subtemplate used to format ``<img>`` elements.

The following identifiers are available (in addition to the universal
identifiers):

* ``alt`` - the 'alt' text for the image
* ``src`` - the relative path to the image file

To see the default ``img`` template, run the following command::

  $ skool2html.py -r Template:img

.. _t_index_section:

index_section
-------------
The ``index_section`` template is the subtemplate used by the
:ref:`t_GameIndex` full-page template to format each group of links on the
disassembly index page.

The following identifiers are available (in addition to the universal
identifiers):

* ``header`` - the header text for the group of links (as defined in the name
  of the :ref:`indexGroup` section)
* ``m_index_section_item`` - replaced by one or more copies of the
  :ref:`t_index_section_item` subtemplate

To see the default ``index_section`` template, run the following command::

  $ skool2html.py -r Template:index_section$

.. _t_index_section_item:

index_section_item
------------------
The ``index_section_item`` template is the subtemplate used by the
:ref:`t_index_section` subtemplate to format each link in a link group on the
disassembly index page.

The following identifiers are available (in addition to the universal
identifiers):

* ``href`` - the relative path to the page being linked to
* ``link_text`` - the link text for the page (as defined in the :ref:`links`
  section)
* ``other_text`` - the supplementary text displayed alongside the link (as
  defined in the :ref:`links` section)

To see the default ``index_section_item`` template, run the following
command::

  $ skool2html.py -r Template:index_section_item

.. _t_javascript:

javascript
----------
The ``javascript`` template is the subtemplate used by the full-page templates
to format each ``<script>`` element in the head of a page.

The following identifier is available (in addition to the universal
identifiers):

* ``src`` - the relative path to the JavaScript file

To see the default ``javascript`` template, run the following command::

  $ skool2html.py -r Template:javascript

.. _t_link:

link
----
The ``link`` template is the subtemplate used to format the hyperlinks created
by the :ref:`LINK` and :ref:`R` macros, and the hyperlinks in instruction
operands on disassembly pages.

The following identifiers are available (in addition to the universal
identifiers):

* ``href`` - the relative path to the page being linked to
* ``link_text`` - the link text for the page

To see the default ``link`` template, run the following command::

  $ skool2html.py -r Template:link

.. _t_list:

list
----
The ``list`` template is used by the :ref:`LIST` macro to format a list.

The following identifiers are available (in addition to the universal
identifiers):

* ``class`` - the CSS class name for the list
* ``m_list_item`` - replaced by any number of copies of the :ref:`t_list_item`
  subtemplate

To see the default ``list`` template, run the following command::

  $ skool2html.py -r Template:list$

.. versionadded:: 4.2

.. _t_list_entry:

list_entry
----------
The ``list_entry`` is the subtemplate used by the :ref:`t_Reference` full-page
template to format each entry on a :ref:`box page <boxpages>` whose
``SectionType`` is ``BulletPoints`` or ``ListItems``.

The following identifiers are available (in addition to the universal
identifiers):

* ``description`` - the entry intro text
* ``num`` - '1' or '2', depending on the order of the entry on the page
* ``t_anchor`` - replaced by a copy of the :ref:`t_anchor` subtemplate (with
  the entry title as the anchor name)
* ``t_list_items`` - replaced by a copy of the :ref:`t_list_items` subtemplate
* ``title`` - the entry title

To see the default ``list_entry`` template, run the following command::

  $ skool2html.py -r Template:list_entry

.. versionchanged:: 6.0
   The name of this template changed from ``changelog_entry`` to
   ``list_entry``; accordingly, the name of the ``t_changelog_item_list``
   identifier changed to ``t_list_items``.

.. _t_list_item:

list_item
---------
The ``list_item`` template is the subtemplate used by the :ref:`t_list`
template and the :ref:`t_list_items` subtemplate to format each item in the
list.

The following identifier is available (in addition to the universal
identifiers):

* ``item`` - replaced by the text of the list item

To see the default ``list_item`` template, run the following command::

  $ skool2html.py -r Template:list_item$

.. versionadded:: 4.2

.. _t_list_items:

list_items
----------
The ``list_items`` template is the subtemplate used by the :ref:`t_list_entry`
subtemplate to format a list of items in an entry on a
:ref:`box page <boxpages>` whose ``SectionType`` is ``BulletPoints`` or
``ListItems``, and also by the :ref:`t_list_item` subtemplate to format a list
of subitems or subsubitems etc.

The following identifiers are available (in addition to the universal
identifiers):

* ``indent`` - the indentation level of the item list: '' (blank string) for
  the list of top-level items, '1' for a list of subitems, '2' for a list of
  subsubitems etc.
* ``m_list_item`` - replaced by one or more copies of the :ref:`t_list_item`
  subtemplate

To see the default ``list_items`` template, run the following command::

  $ skool2html.py -r Template:list_items

.. versionchanged:: 6.0
   The name of this template changed from ``changelog_item_list`` to
   ``list_items``; accordingly, the name of the ``m_changelog_item``
   identifier changed to ``m_list_item``.

.. _t_map_entry:

map_entry
---------
The ``map_entry`` template is the subtemplate used by the :ref:`t_MemoryMap`
full-page template to format each entry on the memory map pages and the 'Game
status buffer' page.

The following identifiers are available (in addition to the universal
identifiers):

* ``MemoryMap`` - a dictionary of parameters from the corresponding
  :ref:`memoryMap` section
* ``entry`` - a dictionary of parameters corresponding to the current memory
  map entry

The parameters in the ``entry`` dictionary are:

* ``address`` - the address of the entry (may be in decimal or hexadecimal
  format, depending on how it appears in the skool file, and the options passed
  to :ref:`skool2html.py`)
* ``byte`` - the LSB of the entry address
* ``description`` - the entry description
* ``exists`` - '1'
* ``href`` - the relative path to the disassembly page for the entry
* ``label`` - the ASM label of the first instruction in the entry
* ``labels`` - '1' if any instructions in the entry have an ASM label, '0'
  otherwise
* ``location`` - the address of the entry as a decimal number
* ``page`` - the MSB of the entry address
* ``size`` - the size of the entry in bytes
* ``title`` - the title of the entry
* ``type`` - the block type of the entry ('b', 'c', 'g', 's', 't', 'u' or 'w')

To see the default ``map_entry`` template, run the following command::

  $ skool2html.py -r Template:map_entry

.. versionchanged:: 7.0
   The entry title is hyperlinked to the disassembly page for the corresponding
   entry.

.. _t_paragraph:

paragraph
---------
The ``paragraph`` template is the subtemplate used to format each paragraph in
the following items:

* memory map entry descriptions (on disassembly pages and memory map pages)
* block start comments, mid-block comments and block end comments on
  disassembly pages
* entries on a :ref:`box page <boxpages>`

The following identifier is available (in addition to the universal
identifiers):

* ``paragraph`` - the text of the paragraph

To see the default ``paragraph`` template, run the following command::

  $ skool2html.py -r Template:paragraph

.. _t_reference_entry:

reference_entry
---------------
The ``reference_entry`` template is the subtemplate used by the
:ref:`t_Reference` full-page template to format each entry on a
:ref:`box page <boxpages>` that has a default ``SectionType``.

The following identifiers are available (in addition to the universal
identifiers):

* ``contents`` - replaced by the pre-formatted contents of the relevant entry
* ``num`` - '1' or '2', depending on the order of the entry on the page
* ``title`` - the entry title

To see the default ``reference_entry`` template, run the following command::

  $ skool2html.py -r Template:reference_entry

.. _t_reg:

reg
---
The ``reg`` template is the subtemplate used by the :ref:`REG` macro to format
a register name.

The following identifier is available (in addition to the universal
identifiers):

* ``reg`` - the register name (e.g. 'HL')

To see the default ``reg`` template, run the following command::

  $ skool2html.py -r Template:reg

.. _t_stylesheet:

stylesheet
----------
The ``stylesheet`` template is the subtemplate used by the full-page templates
to format each ``<link>`` element for a CSS file in the head of a page.

The following identifier is available (in addition to the universal
identifiers):

* ``href`` - the relative path to the CSS file

To see the default ``stylesheet`` template, run the following command::

  $ skool2html.py -r Template:stylesheet

.. _t_table:

table
-----
The ``table`` template is used by the :ref:`TABLE` macro to format a table.

The following identifiers are available (in addition to the universal
identifiers):

* ``class`` - the CSS class name for the table
* ``m_table_row`` - replaced by any number of copies of the :ref:`t_table_row`
  subtemplate

To see the default ``table`` template, run the following command::

  $ skool2html.py -r Template:table$

.. versionadded:: 4.2

.. _t_table_cell:

table_cell
----------
The ``table_cell`` template is the subtemplate used by the :ref:`t_table_row`
template to format each non-header cell in the table row.

The following identifiers are available (in addition to the universal
identifiers):

* ``class`` - the CSS class name for the cell
* ``colspan`` - the number of columns spanned by the cell
* ``contents`` - the contents of the cell
* ``rowspan`` - the number of rows spanned by the cell

To see the default ``table_cell`` template, run the following command::

  $ skool2html.py -r Template:table_cell

.. versionadded:: 4.2

.. _t_table_header_cell:

table_header_cell
-----------------
The ``table_header_cell`` template is the subtemplate used by the
:ref:`t_table_row` template to format each header cell in the table row.

The following identifiers are available (in addition to the universal
identifiers):

* ``colspan`` - the number of columns spanned by the cell
* ``contents`` - the contents of the cell
* ``rowspan`` - the number of rows spanned by the cell

To see the default ``table_header_cell`` template, run the following command::

  $ skool2html.py -r Template:table_header_cell

.. versionadded:: 4.2

.. _t_table_row:

table_row
---------
The ``table_row`` template is the subtemplate used by the :ref:`t_table`
template to format each row in the table.

The following identifier is available (in addition to the universal
identifiers):

* ``cells`` - replaced by one or more copies of the :ref:`t_table_cell` or
  :ref:`t_table_header_cell` subtemplate

To see the default ``table_row`` template, run the following command::

  $ skool2html.py -r Template:table_row

.. versionadded:: 4.2

.. _ps_templates:

Page-specific templates
-----------------------
When SkoolKit builds an HTML page, it uses the template whose name matches the
page ID (``PageID``) if it exists, or one of the stock page-level templates
otherwise. For example, when building the ``RoutinesMap`` memory map page,
SkoolKit uses the ``RoutinesMap`` template if it exists, or the stock
:ref:`t_MemoryMap` template otherwise.

+-------------------------------+----------------------------+----------------------+
| Page type                     | Preferred template(s)      | Stock template       |
+===============================+============================+======================+
| Home (index)                  | ``GameIndex``              | :ref:`t_GameIndex`   |
+-------------------------------+----------------------------+----------------------+
| :ref:`Other code <otherCode>` | ``CodeID-Index``           | :ref:`t_MemoryMap`   |
| index                         |                            |                      |
+-------------------------------+----------------------------+----------------------+
| Routine/data block            | ``[CodeID-]Asm[-*]``       | :ref:`t_Asm`         |
+-------------------------------+----------------------------+----------------------+
| Disassembly (single page)     | ``[CodeID-]AsmSinglePage`` | :ref:`t_AsmAllInOne` |
+-------------------------------+----------------------------+----------------------+
| :ref:`Memory map <memoryMap>` | ``PageID``                 | :ref:`t_MemoryMap`   |
+-------------------------------+----------------------------+----------------------+
| :ref:`Box page <boxpages>`    | ``PageID``                 | :ref:`t_Reference`   |
+-------------------------------+----------------------------+----------------------+
| :ref:`Custom page <Page>`     | ``PageID``                 | :ref:`t_Page`        |
| (non-box)                     |                            |                      |
+-------------------------------+----------------------------+----------------------+

When SkoolKit builds an element of an HTML page whose format is defined by a
subtemplate, it uses the subtemplate whose name starts with ``PageID-`` if it
exists, or one of the stock subtemplates otherwise. For example, when building
the footer of the ``Changelog`` page, SkoolKit uses the ``Changelog-footer``
template if it exists, or the stock :ref:`t_footer` template otherwise.

+-------------------------------+--------------------------------------+------------------------------+
| Element type                  | Preferred template(s)                | Stock subtemplate            |
+===============================+======================================+==============================+
| Registers table               | ``[CodeID-]Asm[-*]-asm_register``    | :ref:`t_asm_register`        |
+-------------------------------+--------------------------------------+------------------------------+
| Routine/data block comment    | ``[CodeID-]Asm[-*]-asm_comment``     | :ref:`t_asm_comment`         |
+-------------------------------+--------------------------------------+------------------------------+
| Instruction                   | ``[CodeID-]Asm[-*]-asm_instruction`` | :ref:`t_asm_instruction`     |
+-------------------------------+--------------------------------------+------------------------------+
| Single-page disassembly       | ``[CodeID-]AsmSinglePage-asm_entry`` | :ref:`t_asm_entry`           |
| routine/data block            |                                      |                              |
+-------------------------------+--------------------------------------+------------------------------+
| :ref:`Box page <boxpages>`    | ``PageID-entry``                     | :ref:`t_reference_entry`     |
| entry (paragraphs)            |                                      |                              |
+-------------------------------+--------------------------------------+------------------------------+
| :ref:`Box page <boxpages>`    | ``PageID-entry``                     | :ref:`t_list_entry`          |
| entry (list items)            |                                      |                              |
+-------------------------------+--------------------------------------+------------------------------+
| :ref:`Box page <boxpages>`    | ``PageID-item_list``                 | :ref:`t_list_items`          |
| entry list                    |                                      |                              |
+-------------------------------+--------------------------------------+------------------------------+
| :ref:`Box page <boxpages>`    | ``PageID-list_item``                 | :ref:`t_list_item`           |
| entry list item               |                                      |                              |
+-------------------------------+--------------------------------------+------------------------------+
| :ref:`Box page <boxpages>`    | ``PageID-contents_list_item``        | :ref:`t_contents_list_item`  |
| contents list item            |                                      |                              |
+-------------------------------+--------------------------------------+------------------------------+
| Paragraph on a                | ``PageID-paragraph``                 | :ref:`t_paragraph`           |
| routine/data block page,      |                                      |                              |
| :ref:`box page <boxpages>` or |                                      |                              |
| :ref:`memory map <memoryMap>` |                                      |                              |
| page                          |                                      |                              |
+-------------------------------+--------------------------------------+------------------------------+
| Entry on a                    | ``PageID-map_entry``                 | :ref:`t_map_entry`           |
| :ref:`memory map <memoryMap>` |                                      |                              |
| page                          |                                      |                              |
+-------------------------------+--------------------------------------+------------------------------+
| ``<link>`` element for a CSS  | ``PageID-stylesheet``                | :ref:`t_stylesheet`          |
| file                          |                                      |                              |
+-------------------------------+--------------------------------------+------------------------------+
| ``<script>`` element          | ``PageID-javascript``                | :ref:`t_javascript`          |
+-------------------------------+--------------------------------------+------------------------------+
| ``<img>`` element             | ``PageID-img``                       | :ref:`t_img`                 |
+-------------------------------+--------------------------------------+------------------------------+
| Hyperlink                     | ``PageID-link``                      | :ref:`t_link`                |
+-------------------------------+--------------------------------------+------------------------------+
| Page anchor                   | ``PageID-anchor``                    | :ref:`t_anchor`              |
+-------------------------------+--------------------------------------+------------------------------+
| Page footer                   | ``PageID-footer``                    | :ref:`t_footer`              |
+-------------------------------+--------------------------------------+------------------------------+
| Register name rendered by the | ``PageID-reg``                       | :ref:`t_reg`                 |
| :ref:`REG` macro              |                                      |                              |
+-------------------------------+--------------------------------------+------------------------------+
| List created by the           | ``PageID-list``                      | :ref:`t_list`                |
| :ref:`LIST` macro             +--------------------------------------+------------------------------+
|                               | ``PageID-list_item``                 | :ref:`t_list_item`           |
+-------------------------------+--------------------------------------+------------------------------+
| Table created by the          | ``PageID-table``                     | :ref:`t_table`               |
| :ref:`TABLE` macro            +--------------------------------------+------------------------------+
|                               | ``PageID-table_row``                 | :ref:`t_table_row`           |
|                               +--------------------------------------+------------------------------+
|                               | ``PageID-table_header_cell``         | :ref:`t_table_header_cell`   |
|                               +--------------------------------------+------------------------------+
|                               | ``PageID-table_cell``                | :ref:`t_table_cell`          |
+-------------------------------+--------------------------------------+------------------------------+

Wherever ``Asm-*`` appears in the tables above, it means one of ``Asm-b``,
``Asm-c``, ``Asm-g``, ``Asm-s``, ``Asm-t``, ``Asm-u`` or ``Asm-w``, depending
on the type of code or data block.
