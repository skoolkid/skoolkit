.. _htmlTemplates:

HTML templates
==============
Every page in an HTML disassembly is built from a single full-page template and
several subtemplates defined by :ref:`template` sections in the `ref` file.

A template may contain 'replacement fields' - identifiers enclosed by braces
(``{`` and ``}``) - that are replaced by appropriate content (typically derived
from the `skool` file or a `ref` file section) when the template is formatted.
The following 'universal' identifiers are available in every template:

* ``Game`` - a dictionary of the parameters in the :ref:`ref-game` section
* ``SkoolKit`` - a dictionary of parameters relevant to the page currently
  being built

The parameters in the ``SkoolKit`` dictionary are:

* ``home`` - the relative path to the disassembly index page
* ``page_header`` - the page header text (as defined in the :ref:`pageHeaders`
  section)
* ``page_id`` - the page ID (e.g. ``GameIndex``, ``MemoryMap``)
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

.. _t_Asm:

Asm
---
The ``Asm`` template is the full-page template that is used to build
disassembly pages.

It contains the following identifiers (in addition to the universal and
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

* ``address`` - the address of the entry as it appears in the `skool` file (may
  be in hexadecimal format)
* ``byte`` - the LSB of the entry address
* ``description`` - the entry description
* ``exists`` - '1' if the entry exists, '0' otherwise
* ``label`` - the ASM label of the first instruction in the entry
* ``labels`` - '1' if any instructions in the entry have an ASM label, '0'
  otherwise
* ``location`` - the address of the entry as a decimal number
* ``map_url`` - the relative path to the entry on the 'Memory Map' page
* ``page`` - the MSB of the entry address
* ``size`` - the size of the entry in bytes
* ``title`` - the title of the entry
* ``type`` - the block type of the entry ('b', 'c', 'g', 's', 't', 'u' or 'w')
* ``url`` - the relative path to the disassembly page for the entry (useful
  only for ``prev_entry`` and ``next_entry``)

To see the default ``Asm`` template, run the following command::

  $ skool2html.py -r Template:Asm

.. _t_GameIndex:

GameIndex
---------
The ``GameIndex`` template is the full-page template that is used to build the
disassembly index page.

It contains the following identifier (in addition to the universal and
page-level identifiers):

* ``m_index_section`` - replaced by any number of copies of the
  :ref:`t_index_section` subtemplate

To see the default ``GameIndex`` template, run the following command::

  $ skool2html.py -r Template:GameIndex

.. _t_MemoryMap:

MemoryMap
---------
The ``MemoryMap`` template is the full-page template that is used to build the
memory map pages and the 'Game status buffer' page.

It contains the following identifiers (in addition to the universal and
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
pages defined by :ref:`page` and :ref:`pageContent` sections.

It contains the following identifier (in addition to the universal and
page-level identifiers):

* ``PageContent`` - replaced by the contents of the corresponding
  :ref:`pageContent` section, or the value of the ``PageContent`` parameter in
  the corresponding :ref:`page` section

To see the default ``Page`` template, run the following command::

  $ skool2html.py -r Template:Page

.. _t_Reference:

Reference
---------
The ``Reference`` template is the full-page template that is used to build the
'Bugs', 'Trivia', 'Pokes', 'Glossary', 'Graphic glitches' and 'Changelog'
pages.

It contains the following identifiers (in addition to the universal and
page-level identifiers):

* ``items`` - replaced by one or more copies of the :ref:`t_box` subtemplate
  (on the 'Bugs', 'Trivia', 'Pokes', 'Glossary' and 'Graphic glitches' pages)
  or the :ref:`t_changelog_entry` subtemplate (on the 'Changelog' page)
* ``m_contents_list_item`` - replaced by one or more copies of the
  :ref:`t_contents_list_item` subtemplate

To see the default ``Reference`` template, run the following command::

  $ skool2html.py -r Template:Reference

.. _t_anchor:

anchor
------

To see the default ``anchor`` template, run the following command::

  $ skool2html.py -r Template:anchor

.. _t_asm_comment:

asm_comment
-----------

To see the default ``asm_comment`` template, run the following command::

  $ skool2html.py -r Template:asm_comment

.. _t_asm_instruction:

asm_instruction
---------------

To see the default ``asm_instruction`` template, run the following command::

  $ skool2html.py -r Template:asm_instruction

.. _t_asm_register:

asm_register
------------

To see the default ``asm_register`` template, run the following command::

  $ skool2html.py -r Template:asm_register

.. _t_box:

box
---

To see the default ``box`` template, run the following command::

  $ skool2html.py -r Template:box

.. _t_changelog_entry:

changelog_entry
---------------

To see the default ``changelog_entry`` template, run the following command::

  $ skool2html.py -r Template:changelog_entry

.. _t_changelog_item:

changelog_item
--------------

To see the default ``changelog_item`` template, run the following command::

  $ skool2html.py -r Template:changelog_item

.. _t_changelog_item_list:

changelog_item_list
-------------------

To see the default ``changelog_item_list`` template, run the following
command::

  $ skool2html.py -r Template:changelog_item_list

.. _t_contents_list_item:

contents_list_item
------------------

To see the default ``contents_list_item`` template, run the following command::

  $ skool2html.py -r Template:contents_list_item

.. _t_img:

img
---

To see the default ``img`` template, run the following command::

  $ skool2html.py -r Template:img

.. _t_index_section:

index_section
-------------

To see the default ``index_section`` template, run the following command::

  $ skool2html.py -r Template:index_section

.. _t_index_section_item:

index_section_item
------------------

To see the default ``index_section_item`` template, run the following
command::

  $ skool2html.py -r Template:index_section_item

.. _t_javascript:

javascript
----------

To see the default ``javascript`` template, run the following command::

  $ skool2html.py -r Template:javascript

.. _t_link:

link
----

To see the default ``link`` template, run the following command::

  $ skool2html.py -r Template:link

.. _t_map_entry:

map_entry
---------

To see the default ``map_entry`` template, run the following command::

  $ skool2html.py -r Template:map_entry

.. _t_paragraph:

paragraph
---------

To see the default ``paragraph`` template, run the following command::

  $ skool2html.py -r Template:paragraph

.. _t_reg:

reg
---

To see the default ``reg`` template, run the following command::

  $ skool2html.py -r Template:reg

.. _t_stylesheet:

stylesheet
----------

To see the default ``stylesheet`` template, run the following command::

  $ skool2html.py -r Template:stylesheet
