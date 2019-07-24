.. _htmlTemplates:

HTML templates
==============
Every page in an HTML disassembly is built from the :ref:`t_Layout` template
and zero or more subtemplates defined by :ref:`template` sections in the ref
file.

A template may contain 'replacement fields' - identifiers enclosed by braces
(``{`` and ``}``) - that are replaced by appropriate content (typically derived
from the skool file or a ref file section) when the template is formatted. The
following 'universal' identifiers are available in every template:

* ``Game`` - a dictionary of the parameters in the :ref:`ref-game` section
* ``SkoolKit`` - a dictionary of parameters relevant to the page currently
  being built

The parameters in the ``SkoolKit`` dictionary are:

* ``include`` - the name of the subtemplate used to format the content between
  the page header and footer
* ``index_href`` - the relative path to the disassembly index page
* ``page_header`` - a two-element list containing the page header prefix and
  suffix (as defined in the :ref:`pageHeaders` section)
* ``page_id`` - the page ID (e.g. ``GameIndex``, ``MemoryMap``)
* ``path`` - the page's filename, including the full path relative to the root
  of the disassembly
* ``title`` - the title of the page (as defined in the :ref:`titles` section)

The parameters in a dictionary are accessed using the ``[param]`` notation;
for example, wherever ``{Game[Copyright]}`` appears in a template, it is
replaced by the value of the ``Copyright`` parameter in the :ref:`ref-game`
section when the template is formatted.

In addition to the universal identifiers, the following page-level identifiers
are available in the :ref:`t_Layout` template, and any subtemplates it
includes:

* ``javascripts`` - a list of javascript objects; each one has a single
  attribute, ``src``, which holds the relative path to the JavaScript file
* ``stylesheets`` - a list of stylesheet objects; each one has a single
  attribute, ``href``, which holds the relative path to the CSS file

.. versionchanged:: 8.0
   ``SkoolKit[page_header]`` is a two-element list containing the page header
   prefix and suffix. Added ``SkoolKit[include]``.

.. versionchanged:: 6.4
   Added ``SkoolKit[path]``.

.. _t_Layout:

Layout
------
The ``Layout`` template is used to format every HTML page.

In any page defined by a :ref:`page` section, the following identifier is
available (in addition to the universal and page-level identifiers):

* ``Page`` - a dictionary of the parameters in the corresponding :ref:`page`
  section

In any page defined by a :ref:`memoryMap` section, the following identifier is
available (in addition to the universal and page-level identifiers):

* ``MemoryMap`` - a dictionary of the parameters in the corresponding
  :ref:`memoryMap` section

To see the default ``Layout`` template, run the following command::

  $ skool2html.py -r Template:Layout

.. _t_asm:

asm
---
The ``asm`` template is used to format the content between the header and
footer of a disassembly page.

The following identifiers are available (in addition to the universal and
page-level identifiers):

* ``entry`` - a dictionary of parameters corresponding to the current memory
  map entry (see below)
* ``next_entry`` - a dictionary of parameters corresponding to the next memory
  map entry (see below)
* ``prev_entry`` - a dictionary of parameters corresponding to the previous
  memory map entry (see below)

The parameters in the ``prev_entry`` and ``next_entry`` dictionaries are:

* ``address`` - the address of the entry (may be in decimal or hexadecimal
  format, depending on how it appears in the skool file, and the options passed
  to :ref:`skool2html.py`)
* ``anchor`` - the anchor for the entry, formatted according to the value of
  the ``AddressAnchor`` parameter in the :ref:`ref-game` section
* ``byte`` - the LSB of the entry address
* ``description`` - a list of paragraphs comprising the entry description
* ``exists`` - '1' if the entry exists, '0' otherwise
* ``href`` - the relative path to the disassembly page for the entry
* ``label`` - the ASM label of the first instruction in the entry
* ``location`` - the address of the entry as a decimal number
* ``map_href`` - the relative path to the entry on the 'Memory Map' page
* ``page`` - the MSB of the entry address
* ``size`` - the size of the entry in bytes
* ``title`` - the title of the entry
* ``type`` - the block type of the entry ('b', 'c', 'g', 's', 't', 'u' or 'w')

The ``entry`` dictionary also contains these parameters, and the following
additional ones:

* ``annotated`` - '1' if any instructions in the entry have a non-empty comment
  field, '0' otherwise
* ``end_comment`` - a list of paragraphs comprising the entry's end comment
* ``input_registers`` - a list of input register objects
* ``instructions`` - a list of instruction objects
* ``labels`` - '1' if any instructions in the entry have an ASM label, '0'
  otherwise
* ``output_registers`` - a list of output register objects
* ``show_bytes`` - '1' if the entry contains at least one assembled instruction
  with byte values and the ``Bytes`` parameter in the :ref:`ref-Game` section
  is not blank, '0' otherwise

Each input and output register object has the following attributes:

* ``description`` - the register's description (as it appears in the register
  section for the entry in the skool file)
* ``name`` - the register's name (e.g. 'HL')

Each instruction object has the following attributes:

* ``address`` - the address of the instruction (may be in decimal or
  hexadecimal format, depending on how it appears in the skool file, and the
  options passed to :ref:`skool2html.py`)
* ``anchor`` - the anchor for the instruction, formatted according to the value
  of the ``AddressAnchor`` parameter in the :ref:`ref-game` section
* ``block_comment`` - a list of paragraphs comprising the instruction's
  mid-block comment
* ``bytes`` - the byte values of the assembled instruction (see below)
* ``called`` - '2' if the instruction is an entry point, '1' otherwise
* ``comment`` - the text of the instruction's comment field
* ``comment_rowspan`` - the number of instructions to which the comment field
  applies; this will be '0' if the instruction has no comment field
* ``label`` - the instruction's ASM label
* ``location`` - the address of the instruction as a decimal number
* ``operation`` - the assembly language operation (e.g. 'LD A,B'), with operand
  hyperlinked if appropriate

The ``bytes`` attribute can be used to render the byte values of an
instruction. In its simplest form, it provides a format specification that is
applied to each byte. For example::

  {$instruction[bytes]:02X}

would produce the string ``3E01`` for the instruction 'LD A,1'.

To render the byte values as 0-padded decimal integers separated by commas, use
the following syntax::

  {$instruction[bytes]:/03/,}

This would produce the string ``062,001`` for the instruction 'LD A,1'. The
delimiter used in this example (``/``) is arbitrary; it could be any character
that doesn't appear in the byte format specification itself.

By default, the ``Bytes`` parameter in the :ref:`ref-Game` section is used as
the byte format specification::

  {$instruction[bytes]:{Game[Bytes]}}

If you define a custom template that replaces ``{Game[Bytes]}`` with a
hard-coded byte format specification, it's a good idea to also remove the
``if({entry[show_bytes]})`` directive (and the corresponding ``endif``), to
ensure that the byte values are displayed.

Note that byte values are available only for regular assembly language
instructions (not DEFB, DEFM, DEFS or DEFW statements), and only if they have
actually been assembled by using :ref:`@assemble=2 <assemble>`. When no byte
values are available, or the format specification is blank, the ``bytes``
identifier produces an empty string.

To see the default ``asm`` template, run the following command::

  $ skool2html.py -r Template:asm$

.. versionadded:: 8.0

.. _t_asm_single_page:

asm_single_page
---------------
The ``asm_single_page`` template is used to format the content between the
header and footer of a single-page disassembly.

The following identifier is available (in addition to the universal and
page-level identifiers):

* ``entries`` - a list of memory map entry objects

The attributes of each memory map entry object are the same as those in the
``entry`` dictionary in the :ref:`t_asm` template.

To see the default ``asm_single_page`` template, run the following command::

  $ skool2html.py -r Template:asm_single_page

.. versionadded:: 8.0

.. _t_boxes:

boxes
-----
The ``boxes`` template is used to format the content between the header and
footer of a :ref:`box page <boxpages>`. A box page may contain either list
entries (when the page's ``SectionType`` is ``BulletPoints`` or ``ListItems``)
or regular entries.

The following identifiers are available (in addition to the universal and
page-level identifiers):

* ``contents`` - a list of contents list item objects
* ``entries`` - a list of regular entry objects (empty if the page contains
  list entries)
* ``list_entries`` - a list of list entry objects (empty if the page contains
  regular entries)

Each contents list item object corresponds to an entry on the page and has the
following attributes:

* ``href`` - the URL to the entry on the page
* ``title`` - the entry title

Each regular entry object has the following attributes:

* ``contents`` - a list of paragraphs comprising the contents of the entry
* ``num`` - '1' or '2', depending on the order of the entry on the page
* ``title`` - the entry title

Each list entry object has the following attributes:

* ``anchor`` - the anchor for the entry
* ``description`` - the entry intro text
* ``item_list`` - replaced by a copy of the :ref:`t_item_list` subtemplate
* ``num`` - '1' or '2', depending on the order of the entry on the page
* ``title`` - the entry title

To see the default ``boxes`` template, run the following command::

  $ skool2html.py -r Template:boxes

.. versionadded:: 8.0

.. _t_footer:

footer
------
The ``footer`` template is the subtemplate included in the :ref:`t_Layout`
template to format the ``<footer>`` element of a page.

To see the default ``footer`` template, run the following command::

  $ skool2html.py -r Template:footer

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

.. _t_home:

home
----
The ``home`` template is used to format the content between the header and
footer of the disassembly home page.

The following identifier is available (in addition to the universal and
page-level identifiers):

* ``sections`` - a list of section objects

Each section object represents a group of links and has the following
attributes:

* ``header`` - the header text for the group of links (as defined in the name
  of the :ref:`indexGroup` section)
* ``items`` - a list of items in the group

Each item represents a link to a page and has the following attributes:

* ``href`` - the relative path to the page being linked to
* ``link_text`` - the link text for the page (as defined in the :ref:`links`
  section)
* ``other_text`` - the supplementary text displayed alongside the link (as
  defined in the :ref:`links` section)

To see the default ``home`` template, run the following command::

  $ skool2html.py -r Template:home

.. versionadded:: 8.0

.. _t_item_list:

item_list
---------
The ``item_list`` template is the subtemplate used by the :ref:`t_boxes`
template to format a list of items (or subitems, or subsubitems etc.) in an
entry on a :ref:`box page <boxpages>` whose ``SectionType`` is ``BulletPoints``
or ``ListItems``.

The following identifiers are available (in addition to the universal
identifiers):

* ``indent`` - the indentation level of the item list: '' (blank string) for
  the list of top-level items, '1' for a list of subitems, '2' for a list of
  subsubitems etc.
* ``items`` - a list of item objects

Each item object has the following attributes:

* ``subitems`` - a preformatted list of subitems (may be blank)
* ``text`` - the text of the item

Note that the ``item_list`` template is used to format the ``subitems``
attribute of each item (this template is recursive).

To see the default ``item_list`` template, run the following command::

  $ skool2html.py -r Template:item_list

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
* ``items`` - the list items

To see the default ``list`` template, run the following command::

  $ skool2html.py -r Template:list

.. versionadded:: 4.2

.. _t_memory_map:

memory_map
----------
The ``memory_map`` template is used to format the content between the header
and footer of memory map pages and the 'Game status buffer' page.

The following identifiers are available (in addition to the universal and
page-level identifiers):

* ``entries`` - a list of memory map entry objects

The attributes of each memory map entry object are the same as those in the
``prev_entry`` and ``next_entry`` dictionaries in the :ref:`t_asm` template.

To see the default ``memory_map`` template, run the following command::

  $ skool2html.py -r Template:memory_map

.. versionadded:: 8.0

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

.. _t_section:

section
-------
The ``section`` template is used to format the paragraphs in a ref file section
processed by the :ref:`INCLUDE` macro.

The following identifier is available (in addition to the universal
identifiers):

* ``section`` - a list of paragraphs

To see the default ``section`` template, run the following command::

  $ skool2html.py -r Template:section

.. _t_table:

table
-----
The ``table`` template is used by the :ref:`TABLE` macro to format a table.

The following identifiers are available (in addition to the universal
identifiers):

* ``class`` - the CSS class name for the table
* ``rows`` - a list of row objects

Each row object has a ``cells`` attribute, which is a list of cell objects for
that row. Each cell object has the following attributes:

* ``class`` - the CSS class name for the cell
* ``colspan`` - the number of columns spanned by the cell
* ``contents`` - the contents of the cell
* ``header`` - 1 if the cell is a header cell, 0 otherwise
* ``rowspan`` - the number of rows spanned by the cell

To see the default ``table`` template, run the following command::

  $ skool2html.py -r Template:table

.. versionadded:: 4.2

.. _template_directives:

Template directives
-------------------
HTML templates may contain directives enclosed by ``<#`` and ``#>`` to
conditionally include or repeat content. To take effect, a directive must
appear on a line of its own.

.. _td_foreach:

foreach
^^^^^^^
The ``foreach`` directive repeats the content between it and the corresponding
``endfor`` directive, once for each object in a list. ::

  <# foreach(var,list) #>
  content
  <# endfor #>

* ``var`` is the loop variable, representing each object in the list
* ``list`` is the list of objects to iterate over

Wherever the string ``var`` appears in ``content``, it is replaced by
``list[0]``, ``list[1]``, etc. Care should be taken to name the loop variable
such that no unwanted replacements are made.

For example, if ``names`` contains the strings 'Alice', 'Bob' and 'Carol',
then::

  <# foreach(name,names) #>
  {name}
  <# endfor #>

would produce the following output::

  Alice
  Bob
  Carol

.. _td_if:

if
^^
The ``if`` directive includes the content between it and the corresponding
``endif`` directive if a given expression is true, and excludes it otherwise.
::

  <# if(expr) #>
  content
  <# endif #>

``expr`` may be any syntactically valid Python expression, and may contain the
names of any fields that are available in the template.

The ``if`` directive follows the same rules as Python when determining the
truth of an expression: ``None``, ``False``, zero, and any empty string or
collection is false; everything else is true.

Note that any replacement fields in ``expr`` are replaced with their string
representations before the expression is evaluated. For example, if the value
of the field 'val' is the string '0', then ``val`` evaluates to '0' (which is
true, because it's a non-empty string); but ``{val}`` evaluates to 0 (which is
false).

.. _td_include:

include
^^^^^^^
The ``include`` directive includes content from another template. ::

  <# include(template) #>

``template`` is the name of the template to include; it may contain replacement
fields.

For example, if there is a template named ``title`` that contains
``<title>{title}</title>``, and the ``title`` field holds the string 'My Page',
then::

  <head>
  <# include(title) #>
  </head>

would produce the following output::

  <head>
  <title>My Page</title>
  </head>

.. _ps_templates:

Page-specific templates
-----------------------
When SkoolKit builds an HTML page, it uses the template whose name matches the
page ID (``PageID``) if it exists, or the :ref:`t_Layout` template otherwise.
For example, when building the ``RoutinesMap`` memory map page, SkoolKit will
use the ``RoutinesMap`` template if it exists.

+-------------------------------+----------------------------+--------------------------+
| Page type                     | Preferred template(s)      | Stock template           |
+===============================+============================+==========================+
| Home (index)                  | ``GameIndex``              | :ref:`t_home`            |
+-------------------------------+----------------------------+--------------------------+
| :ref:`Other code <otherCode>` | ``CodeID-Index``           | :ref:`t_memory_map`      |
| index                         |                            |                          |
+-------------------------------+----------------------------+--------------------------+
| Routine/data block            | ``[CodeID-]Asm[-*]``       | :ref:`t_asm`             |
+-------------------------------+----------------------------+--------------------------+
| Disassembly (single page)     | ``[CodeID-]AsmSinglePage`` | :ref:`t_asm_single_page` |
+-------------------------------+----------------------------+--------------------------+
| :ref:`Memory map <memoryMap>` | ``PageID``                 | :ref:`t_memory_map`      |
+-------------------------------+----------------------------+--------------------------+
| :ref:`Box page <boxpages>`    | ``PageID``                 | :ref:`t_boxes`           |
+-------------------------------+----------------------------+--------------------------+
| :ref:`Custom page <Page>`     | ``PageID``                 | :ref:`t_Layout`          |
| (non-box)                     |                            |                          |
+-------------------------------+----------------------------+--------------------------+

Where ``Asm-*`` appears in the table above, it means one of ``Asm-b``,
``Asm-c``, ``Asm-g``, ``Asm-s``, ``Asm-t``, ``Asm-u`` or ``Asm-w``, depending
on the type of code or data block.

When SkoolKit builds an element of an HTML page whose format is defined by a
subtemplate, it uses the subtemplate whose name starts with ``PageID-`` if it
exists, or one of the stock subtemplates otherwise. For example, when building
the footer of the ``Changelog`` page, SkoolKit uses the ``Changelog-footer``
template if it exists, or the stock :ref:`t_footer` template otherwise.

+-------------------------------+--------------------------------------+------------------------------+
| Element type                  | Preferred template(s)                | Stock subtemplate            |
+===============================+======================================+==============================+
| :ref:`Box page <boxpages>`    | ``PageID-item_list``                 | :ref:`t_item_list`           |
| entry list                    |                                      |                              |
+-------------------------------+--------------------------------------+------------------------------+
| ``<img>`` element             | ``PageID-img``                       | :ref:`t_img`                 |
+-------------------------------+--------------------------------------+------------------------------+
| Hyperlink                     | ``PageID-link``                      | :ref:`t_link`                |
+-------------------------------+--------------------------------------+------------------------------+
| Page footer                   | ``PageID-footer``                    | :ref:`t_footer`              |
+-------------------------------+--------------------------------------+------------------------------+
| Section rendered by the       | ``PageID-section``                   | :ref:`t_section`             |
| :ref:`INCLUDE` macro          |                                      |                              |
+-------------------------------+--------------------------------------+------------------------------+
| Register name rendered by the | ``PageID-reg``                       | :ref:`t_reg`                 |
| :ref:`REG` macro              |                                      |                              |
+-------------------------------+--------------------------------------+------------------------------+
| List created by the           | ``PageID-list``                      | :ref:`t_list`                |
| :ref:`LIST` macro             |                                      |                              |
+-------------------------------+--------------------------------------+------------------------------+
| Table created by the          | ``PageID-table``                     | :ref:`t_table`               |
| :ref:`TABLE` macro            |                                      |                              |
+-------------------------------+--------------------------------------+------------------------------+
