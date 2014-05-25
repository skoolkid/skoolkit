.. _migrating:

Migrating from SkoolKit 3
=========================
SkoolKit 4 includes some changes that make it incompatible with SkoolKit 3. If
you have developed a disassembly using SkoolKit 3 and find that `skool2html.py`
no longer works with your `skool` files or `ref` files, or produces broken
output, look through the following sections for tips on how to migrate your
disassembly to SkoolKit 4.

[Info]
------
The ``[Info]`` section, introduced in SkoolKit 2.0, is not supported in
SkoolKit 4. If you have one in your `ref` file, copy its contents to the
:ref:`ref-Game` section.

[Graphics]
----------
The ``[Graphics]`` section, introduced in SkoolKit 2.0.5, is not supported in
SkoolKit 4. If you have one in your `ref` file, you can migrate it thus:

* Rename the ``[Graphics]`` section ``[PageContent:Graphics]``

* Create a ``[Paths]`` section if you don't already have one, and add a line
  for the Graphics page::

    [Paths]
    Graphics=graphics/graphics.html

* Create an ``[Index:Graphics:Graphics]`` section if you don't already have
  one, and add the Graphics page ID (to make a link to it appear on the
  disassembly index page); for example::

    [Index:Graphics:Graphics]
    Graphics
    GraphicGlitches

[Page:\*]
---------
The following parameters are no longer supported:

* ``BodyClass``
* ``Link``
* ``Path``
* ``Title``

The CSS class for the ``<body>`` element of a custom page is now set to the
page ID. The path, title, header and link text for a custom page can be defined
in the :ref:`paths`, :ref:`titles`, :ref:`pageHeaders` and :ref:`links`
sections.

[OtherCode:\*]
--------------
The following parameters are no longer supported:

* ``Header``
* ``Index``
* ``IndexPageId``
* ``Link``
* ``Path``
* ``Title``

The paths, titles, headers and link text for the pages in a secondary
disassembly can be defined in the :ref:`paths`, :ref:`titles`,
:ref:`pageHeaders` and :ref:`links` sections; see the documentation on
:ref:`otherCode` sections for more details.

'z' and 'Z' directives
----------------------
The 'z' and 'Z' control directives (and the corresponding 'z' blocks in `skool`
files) are not supported in SkoolKit 4; they should be replaced by 's' and 'S'
directives.

Register table headers
----------------------
Input and output register table headers on disassembly pages are now displayed
by default, with header text 'Input' and 'Output'.

To hide the register table headers (as was the default behaviour in SkoolKit
3), use the following CSS rule::

  tr.asm-input-header, tr.asm-output-header {display: none;}

CSS selectors
-------------
The `class` attributes of many HTML elements have changed in SkoolKit 4.

The following table lists the selectors that appeared in the CSS files in
SkoolKit 3, and their replacements (if any) in SkoolKit 4.

=========================  ==========
SkoolKit 3                 SkoolKit 4
=========================  ==========
a.link
a.link:hover
div.box
div.box1                   div.box-1
div.box2                   div.box-2
div.boxTitle               div.box-title
div.changelog
div.changelog1             div.changelog-1
div.changelog2             div.changelog-2
div.changelogDesc          div.changelog-desc
div.changelogTitle         div.changelog-title
div.comments
div.description
div.details
div.footer
div.gbufDesc               div.map-entry-title-11
div.headerText             div.section-header
div.mapIntro               div.map-intro
div.paragraph
span.register
table.dataDisassembly      table.disassembly
table.default
table.disassembly
table.gbuffer              table.map
table.header
table.input                table.input-1
table.map
table.output               table.output-1
table.prevNext             table.asm-navigation
td.address                 td.address-1
td.asmLabel                td.asm-label-1
td.centre
td.comment                 td.comment-11
td.data                    td.map-b, td.map-w
td.dataComment             td.comment-11
td.dataDesc                td.map-b-desc, td.map-w-desc
td.gbufAddress             td.map-b, td.map-c, td.map-g, td.map-s, td.map-t, td.map-u, td.map-w
td.gbuffer                 td.map-g
td.gbufferDesc             td.map-g-desc
td.gbufLength              td.map-length-1
td.headerText              td.page-header
td.instruction
td.label                   td.address-2
td.mapByte                 td.map-byte-1
td.mapPage                 td.map-page-1
td.message                 td.map-t
td.messageDesc             td.map-t-desc
td.next
td.prev
td.register
td.routine                 td.map-c
td.routineComment          td.routine-comment
td.routineDesc             td.map-c-desc
td.transparent
td.transparentComment      td.comment-10
td.transparentDataComment  td.comment-10
td.unused                  td.map-s, td.map-u
td.unusedDesc              td.map-s-desc, td.map-u-desc
td.up
ul.changelog
ul.indexList               ul.index-list
ul.linkList                ul.contents
=========================  ==========

The following table lists selectors for the classes that were unstyled (i.e.
did not appear in any CSS files) in SkoolKit 3, and their replacements (if any)
in SkoolKit 4.

===================  ==========
SkoolKit 3           SkoolKit 4
===================  ==========
body.bugs            body.Bugs
body.changelog       body.Changelog
body.disassembly     body.Asm-b, body.Asm-c, body.Asm-g, body.Asm-s, body.Asm-t, body.Asm-u, body.Asm-w
body.facts           body.Facts
body.gbuffer         body.GameStatusBuffer
body.glossary        body.Glossary
body.main            body.GameIndex
body.map             body.DataMap, body.MemoryMap, body.MessagesMap, body.RoutinesMap, body.UnusedMap
body.pokes           body.Pokes
div.copyright
div.created
div.gbufDetails      div.map-entry-desc-1
div.release
td.gbufDesc          td.map-b-desc, td.map-c-desc, td.map-g-desc, td.map-s-desc, td.map-t-desc, td.map-u-desc, td.map-w-desc
td.headerLogo        td.logo
td.registerContents  td.register-desc
===================  ==========

skoolkit3to4.py
---------------
The `skoolkit3to4.py`_ script may be used to convert a `skool` file, `ref`
file, control file, skool file template or CSS file that is compatible with
SkoolKit 3 into a file that will work with SkoolKit 4. For example, to convert
`game.ref`::

  $ skoolkit3to4.py game.ref > game4.ref

Note, however, that `skoolkit3to4.py` converts a CSS file by simply replacing
each selector that is used in SkoolKit 3 with its SkoolKit 4 equivalent(s),
which means that complex CSS rules may not be converted correctly.

.. _skoolkit3to4.py: https://github.com/skoolkid/skoolkit/raw/master/utils/skoolkit3to4.py
