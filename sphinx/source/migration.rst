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
* Add an empty ``[Page:Graphics]`` section to the `ref` file::

    [Page:Graphics]

* Add the following line to the ``[Paths]`` section::

    Graphics=graphics/graphics.html

* Add the ``Graphics`` page ID to the ``[Index:Graphics:Graphics]`` section to
  make a link to it appear on the disassembly index page; for example::

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
