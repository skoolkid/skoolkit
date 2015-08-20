.. _refFiles:

Ref files
=========
If you want to configure or augment an HTML disassembly, you will need one or
more `ref` files. A `ref` file can be used to (for example):

* add a 'Bugs' page on which bugs are documented
* add a 'Trivia' page on which interesting facts are documented
* add a 'Pokes' page on which useful POKEs are listed
* add a 'Changelog' page
* add a 'Glossary' page
* add a 'Graphic glitches' page
* add any other kind of custom page
* change the title of the disassembly
* define the layout of the disassembly index page
* define the link text and titles for the various pages in the disassembly
* define the location of the files and directories in the disassembly
* define the colours used when creating images

A `ref` file must be formatted into sections separated by section names inside
square brackets, like this::

  [SectionName]

The contents of each section that may be found in a `ref` file are described
below.

.. _ref-Bug:

[Bug:\*:\*]
-----------
Each ``Bug:*:*`` section defines an entry on the 'Bugs' page. The section names
and contents take the form::

  [Bug:anchor:title]
  First paragraph.

  Second paragraph.

  ...

where:

* ``anchor`` is the name of the HTML anchor for the entry
* ``title`` is the title of the entry

To ensure that an entry can be linked to by the :ref:`bug` macro, the anchor
name must be limited to the characters '$', '#', 0-9, A-Z and a-z.

Paragraphs must be separated by blank lines, and may contain HTML markup and
:ref:`skool macros <skoolMacros>`.

.. _ref-Changelog:

[Changelog:\*]
--------------
Each ``Changelog:*`` section defines an entry on the 'Changelog' page. The
section names and contents take the form::

  [Changelog:title]
  Intro text.

  First top-level item.
    First subitem.
    Second subitem.
      First subsubitem.

  Second top-level item.
  ...

where ``title`` is the title of the entry, and the intro text and top-level
items are separated by blank lines. Lower-level items are created by using
indentation, as shown.

If the intro text is a single hyphen (``-``), it will not be included in the
final HTML rendering.

The intro text and changelog items may contain HTML markup and
:ref:`skool macros <skoolMacros>`.

+---------+---------+
| Version | Changes |
+=========+=========+
| 2.2.5   | New     |
+---------+---------+

.. _ref-Colours:

[Colours]
---------
The ``Colours`` section contains colour definitions that will be used when
creating images. Each line has the form::

  name=R,G,B

or::

  name=#RGB

where:

*  ``name`` is the colour name
* ``R,G,B`` is a decimal RGB triplet
* ``#RGB`` is a hexadecimal RGB triplet (in the usual 6-digit form, or in the
  short 3-digit form)

Recognised colour names and their default RGB values are:

* ``TRANSPARENT``: 0,254,0 (#00fe00)
* ``BLACK``: 0,0,0 (#000000)
* ``BLUE``: 0,0,197 (#0000c5)
* ``RED``: 197,0,0 (#c50000)
* ``MAGENTA``: 197,0,197 (#c500c5)
* ``GREEN``: 0,198,0 (#00c600)
* ``CYAN``: 0,198,197 (#00c6c5)
* ``YELLOW``: 197,198,0 (#c5c600)
* ``WHITE``: 205,198,205 (#cdc6cd)
* ``BRIGHT_BLUE``: 0,0,255 (#0000ff)
* ``BRIGHT_RED``: 255,0,0 (#ff0000)
* ``BRIGHT_MAGENTA``: 255,0,255 (#ff00ff)
* ``BRIGHT_GREEN``: 0,255,0 (#00ff00)
* ``BRIGHT_CYAN``: 0,255,255 (#00ffff)
* ``BRIGHT_YELLOW``: 255,255,0 (#ffff00)
* ``BRIGHT_WHITE``: 255,255,255 (#ffffff)

+---------+--------------------------------------------+
| Version | Changes                                    |
+=========+============================================+
| 3.4     | Added support for hexadecimal RGB triplets |
+---------+--------------------------------------------+
| 2.0.5   | New                                        |
+---------+--------------------------------------------+


.. _ref-Config:

[Config]
--------
The ``Config`` section contains configuration parameters in the format::

  name=value

Recognised parameters are:

* ``GameDir`` - the root directory of the game's HTML disassembly; if not
  specified, the base name of the `skool` or `ref` file given on the
  :ref:`skool2html.py <skool2html.py>` command line will be used
* ``HtmlWriterClass`` - the name of the Python class to use for writing the
  HTML disassembly of the game (default: ``skoolkit.skoolhtml.HtmlWriter``); if
  the class is in a module that is not in the module search path (e.g. a
  standalone module that is not part of an installed package), the module's
  location may be specified thus: ``/path/to/moduledir:module.classname``
* ``RefFiles`` - a semicolon-separated list of extra `ref` files to use (in
  addition to the one named on the :ref:`skool2html.py` command line, and any
  others with the same filename prefix)
* ``SkoolFile`` - the name of the main `skool` file to use if not given on the
  :ref:`skool2html.py <skool2html.py>` command line; if not specified, the
  `skool` file with the same base name as the `ref` file will be used

For information on how to create your own Python class for writing an HTML
disassembly, see the documentation on
:ref:`extending SkoolKit <extendingSkoolKit>`.

+---------+-------------------------------------------------------------------+
| Version | Changes                                                           |
+=========+===================================================================+
| 5.0     | Added the ``RefFiles`` parameter                                  |
+---------+-------------------------------------------------------------------+
| 3.3.1   | Added support to the ``HtmlWriterClass`` parameter for specifying |
|         | a module outside the module search path                           |
+---------+-------------------------------------------------------------------+
| 2.2.3   | Added the ``HtmlWriterClass`` parameter                           |
+---------+-------------------------------------------------------------------+
| 2.0     | New                                                               |
+---------+-------------------------------------------------------------------+

.. _ref-Fact:

[Fact:\*:\*]
------------
Each ``Fact:*:*`` section defines an entry on the 'Trivia' page. The section
names and contents take the form::

  [Fact:anchor:title]
  First paragraph.

  Second paragraph.

  ...

where:

* ``anchor`` is the name of the HTML anchor for the entry
* ``title`` is the title of the entry

To ensure that an entry can be linked to by the :ref:`fact` macro, the anchor
name must be limited to the characters '$', '#', 0-9, A-Z and a-z.

Paragraphs must be separated by blank lines, and may contain HTML markup and
:ref:`skool macros <skoolMacros>`.

.. _ref-Game:

[Game]
------
The ``Game`` section contains configuration parameters that control certain
aspects of the HTML output. The parameters are in the format::

  name=value

Recognised parameters are:

* ``AddressAnchor`` - the format of the anchors attached to instructions on
  disassembly pages and entries on memory map pages (default: ``{address}``)
* ``Copyright`` - the copyright message that appears in the footer of every
  page (default: '')
* ``Created`` - the message indicating the software used to create the
  disassembly that appears in the footer of every page (default: 'Created using
  SkoolKit $VERSION.'; the string ``$VERSION`` is replaced by the version
  number of SkoolKit)
* ``Font`` - the base name of the font file to use (default: None); multiple
  font files can be declared by separating their names with semicolons
* ``Game`` - the name of the game, which appears in the title of every page,
  and also in the header of every page (if no logo is defined); if not
  specified, the base name of the `skool` file is used
* ``GameStatusBufferIncludes`` - a comma-separated list of addresses of entries
  to include on the 'Game status buffer' page in addition to those that are
  marked with a ``g`` (see the
  :ref:`skool file format reference <skoolFileFormat>`)
* ``InputRegisterTableHeader`` - the text displayed in the header of input
  register tables on routine disassembly pages (default: 'Input')
* ``JavaScript`` - the base name of the JavaScript file to include in every
  page (default: None); multiple JavaScript files can be declared by separating
  their names with semicolons
* ``LinkInternalOperands`` - ``1`` to hyperlink instruction operands that refer
  to an address in the same entry as the instruction, or ``0`` to leave them
  unlinked (default: ``0``)
* ``LinkOperands`` - a comma-separated list of instruction types whose operands
  will be hyperlinked when possible (default: ``CALL,DEFW,DJNZ,JP,JR``); add
  ``LD`` to the list to enable the address operands of LD instructions to be
  hyperlinked as well
* ``Logo`` - the text/HTML that will serve as the game logo in the header of
  every page (typically a skool macro that creates a suitable image); if not
  specified, ``LogoImage`` is used
* ``LogoImage`` - the path to the game logo image, which appears in the header
  of every page; if the specified file does not exist, the name of the game is
  used in place of an image
* ``OutputRegisterTableHeader`` - the text displayed in the header of output
  register tables on routine disassembly pages (default: 'Output')
* ``Release`` - the message indicating the release name and version number of
  the disassembly that appears in the footer of every page (default: '')
* ``StyleSheet`` - the base name of the CSS file to use (default:
  `skoolkit.css`); multiple CSS files can be declared by separating their names
  with semicolons
* ``TitlePrefix`` - the prefix to use before the game name or logo in the
  header of the main index page (default: 'The complete')
* ``TitleSuffix`` - the suffix to use after the game name or logo in the header
  of the main index page (default: 'RAM disassembly')

The ``AddressAnchor`` parameter contains a standard Python format string that
specifies the format of the anchors attached to instructions on disassembly
pages and entries on memory map pages. The default format string is
``{address}``, which produces decimal addresses (e.g. ``#65280``); to produce
4-digit, lower case hexadecimal addresses instead (e.g. ``#ff00``), change
``AddressAnchor`` to ``{address:04x}``.

Note that an address anchor that starts with an upper case letter (e.g.
``#FF00``) will be interpreted as a skool macro, and so any format string that
could produce such an anchor should be avoided.

+---------+-------------------------------------------------------------------+
| Version | Changes                                                           |
+=========+===================================================================+
| 4.3     | Added the ``AddressAnchor`` parameter                             |
+---------+-------------------------------------------------------------------+
| 4.1     | Added the ``LinkInternalOperands`` parameter                      |
+---------+-------------------------------------------------------------------+
| 4.0     | Set default values for the ``InputRegisterTableHeader`` and       |
|         | ``OutputRegisterTableHeader`` parameters; added the               |
|         | ``Copyright``, ``Created`` and ``Release`` parameters (which used |
|         | to live in the ``[Info]`` section in SkoolKit 3)                  |
+---------+-------------------------------------------------------------------+
| 3.7     | Added the ``JavaScript`` parameter                                |
+---------+-------------------------------------------------------------------+
| 3.5     | Added the ``Font``, ``LogoImage`` and ``StyleSheet`` parameters   |
|         | (all of which used to live in the :ref:`Paths` section,           |
|         | ``LogoImage`` by the name ``Logo``)                               |
+---------+-------------------------------------------------------------------+
| 3.4     | Added the ``LinkOperands`` parameter                              |
+---------+-------------------------------------------------------------------+
| 3.1.2   | Added the ``InputRegisterTableHeader`` and                        |
|         | ``OutputRegisterTableHeader`` parameters                          |
+---------+-------------------------------------------------------------------+
| 2.0.5   | Added the ``Logo`` parameter                                      |
+---------+-------------------------------------------------------------------+
| 2.0.3   | Added the ``GameStatusBufferIncludes`` parameter                  |
+---------+-------------------------------------------------------------------+

.. _ref-Glossary:

[Glossary:\*]
-------------
Each ``Glossary:*`` section defines an entry on the 'Glossary' page. The
section names and contents take the form::

  [Glossary:term]
  First paragraph.

  Second paragraph.

  ...

where ``term`` is the term being defined in the entry.

Paragraphs must be separated by blank lines, and may contain HTML markup and
:ref:`skool macros <skoolMacros>`.

+---------+---------------------------------------+
| Version | Changes                               |
+=========+=======================================+
| 3.1.3   | Added support for multiple paragraphs |
+---------+---------------------------------------+

.. _ref-GraphicGlitch:

[GraphicGlitch:\*:\*]
---------------------
Each ``GraphicGlitch:*:*`` section defines an entry on the 'Graphic glitches'
page. The section names and contents take the form::

  [GraphicGlitch:anchor:title]
  First paragraph.

  Second paragraph.

  ...

where:

* ``anchor`` is the name of the HTML anchor for the entry
* ``title`` is the title of the entry

Paragraphs must be separated by blank lines, and may contain HTML markup and
:ref:`skool macros <skoolMacros>`.

.. _ref-ImageWriter:

[ImageWriter]
-------------
The ``ImageWriter`` section contains configuration parameters that control
SkoolKit's image creation library. The parameters are in the format::

  name=value

Recognised parameters are:

* ``DefaultFormat`` - the default image format; valid values are ``png`` (the
  default) and ``gif``
* ``GIFEnableAnimation`` - ``1`` to create animated GIFs for images that
  contain flashing cells, or ``0`` to create plain (unanimated) GIFs for such
  images (default: ``1``)
* ``GIFTransparency`` - ``1`` to make the ``TRANSPARENT`` colour (see
  :ref:`ref-Colours`) in GIF images transparent, or ``0`` to make it opaque
  (default: ``0``)
* ``PNGAlpha`` - the alpha value to use for the ``TRANSPARENT`` colour (see
  :ref:`ref-Colours`) in PNG images; valid values are in the range 0-255, where
  0 means fully transparent, and 255 means fully opaque (default: ``255``)
* ``PNGCompressionLevel`` - the compression level to use for PNG image data;
  valid values are in the range 0-9, where 0 means no compression, 1 is the
  lowest compression level, and 9 is the highest (default: ``9``)
* ``PNGEnableAnimation`` - ``1`` to create animated PNGs (in APNG format) for
  images that contain flashing cells, or ``0`` to create plain (unanimated) PNG
  files for such images (default: ``1``)

The image-creating skool macros will create a file in the default image format
if the filename is unspecified, or its suffix is omitted, or its suffix is
neither ``.png`` nor ``.gif``. For example, if ``DefaultFormat`` is ``png``,
then::

  #FONT32768,26

will create an image file named ``font.png``. To create a GIF instead
(regardless of the default image format)::

  #FONT32768,26(font.gif)

For images that contain flashing cells, animated GIFs are recommended over
animated PNGs in APNG format, because they are more widely supported in web
browsers.

+---------+--------------------------------------------------------------+
| Version | Changes                                                      |
+=========+==============================================================+
| 3.0.1   | Added the ``DefaultFormat``, ``GIFEnableAnimation``,         |
|         | ``GIFTransparency``, ``PNGAlpha`` and ``PNGEnableAnimation`` |
|         | parameters                                                   |
+---------+--------------------------------------------------------------+
| 3.0     | New                                                          |
+---------+--------------------------------------------------------------+

.. _index:

[Index]
-------
The ``Index`` section contains a list of link group IDs in the order in which
the link groups will appear on the disassembly index page. The link groups
themselves - with the exception of ``OtherCode`` - are defined in
``[Index:*:*]`` sections (see below); ``OtherCode`` is a special built-in link
group that contains links to the index pages of secondary disassemblies defined
by :ref:`otherCode` sections.

To see the default ``Index`` section, run the following command::

  $ skool2html.py -r Index$

+---------+---------+
| Version | Changes |
+=========+=========+
| 2.0.5   | New     |
+---------+---------+

.. _indexGroup:

[Index:\*:\*]
-------------
Each ``Index:*:*`` section defines a link group (a group of links on the
disassembly home page). The section names and contents take the form::

  [Index:groupID:text]
  Page1ID
  Page2ID
  ...

where:

* ``groupID`` is the link group ID (as may be declared in the :ref:`index`
  section)
* ``text`` is the text of the link group header
* ``Page1ID``, ``Page2ID`` etc. are the IDs of the pages that will appear in
  the link group

To see the default link groups and their contents, run the following command::

  $ skool2html.py -r Index:

+---------+---------+
| Version | Changes |
+=========+=========+
| 2.0.5   | New     |
+---------+---------+

.. _links:

[Links]
-------
The ``Links`` section defines the link text for the various pages in the HTML
disassembly (as displayed on the disassembly index page). Each line has the
form::

  PageID=text

where:

* ``PageID`` is the ID of the page
* ``text`` is the link text

Recognised page IDs are:

* ``Bugs`` - the 'Bugs' page
* ``Changelog`` - the 'Changelog' page
* ``DataMap`` - the 'Data' memory map page
* ``Facts`` - the 'Trivia' page
* ``GameStatusBuffer`` - the 'Game status buffer' page
* ``Glossary`` - the 'Glossary' page
* ``GraphicGlitches`` - the 'Graphic glitches' page
* ``MemoryMap`` - the 'Everything' memory map page (default: 'Everything')
* ``MessagesMap`` - the 'Messages' memory map page
* ``Pokes`` - the 'Pokes' page
* ``RoutinesMap`` - the 'Routines' memory map page
* ``UnusedMap`` - the 'Unused addresses' memory map page

The default link text for a page is the same as the header defined in the
:ref:`pageHeaders` section, except where indicated above.

The link text for a page defined by a :ref:`memoryMap`, :ref:`otherCode`,
:ref:`page` or :ref:`pageContent` section also defaults to the page header
text, but can be overridden in this section.

If the link text starts with some text in square brackets, that text alone is
used as the link text, and the remaining text is displayed alongside the
hyperlink. For example::

  MemoryMap=[Everything] (routines, data, text and unused addresses)

This declares that the link text for the 'Everything' memory map page will be
'Everything', and '(routines, data, text and unused addresses)' will be
displayed alongside it.

+---------+---------------------------------+
| Version | Changes                         |
+=========+=================================+
| 2.5     | Added the ``UnusedMap`` page ID |
+---------+---------------------------------+
| 2.2.5   | Added the ``Changelog`` page ID |
+---------+---------------------------------+
| 2.0.5   | New                             |
+---------+---------------------------------+

.. _memoryMap:

[MemoryMap:\*]
--------------
Each ``MemoryMap:*`` section defines the properties of a memory map page. The
section names take the form::

  [MemoryMap:PageID]

where ``PageID`` is the unique ID of the memory map page.

Each ``MemoryMap:*`` section contains parameters in the form::

  name=value

Recognised parameters and their default values are:

* ``EntryDescriptions`` - ``1`` to display entry descriptions, or ``0`` not to
  (default: ``0``)
* ``EntryTypes`` - the types of entries to show in the map (by default, every
  type is shown); entry types are identified as follows:

  * ``b`` - DEFB blocks
  * ``c`` - routines
  * ``g`` - game status buffer entries
  * ``G`` - entries whose address appears in the ``GameStatusBufferIncludes``
    parameter in the :ref:`ref-Game` section
  * ``s`` - blocks containing bytes that are all the same value
  * ``t`` - messages
  * ``u`` - unused addresses
  * ``w`` - DEFW blocks

* ``Intro`` - the text (which may contain HTML markup and
  :ref:`skool macros <skoolMacros>`) displayed at the top of the memory map
  page (default: '')
* ``LengthColumn`` - ``1`` to display the 'Length' column, or ``0`` not to
  (default: ``0``)
* ``PageByteColumns`` - ``1`` to display 'Page' and 'Byte' columns, or ``0``
  not to (default: ``0``)
* ``Write`` - ``1`` to write the memory map page, or ``0`` not to (default:
  ``1``)

To see the default memory map pages and their properties, run the following
command::

  $ skool2html.py -r MemoryMap

A custom memory map page can be defined by creating a ``MemoryMap:*`` section
for it. By default, the page will be written to `maps/PageID.html`; to change
this, add a line to the :ref:`paths` section. The title, page header and link
text for the custom memory map page can be defined in the :ref:`titles`,
:ref:`pageHeaders` and :ref:`links` sections.

Every memory map page is built using the :ref:`HTML template <template>` whose
name matches the page ID, if one exists; otherwise, the stock
:ref:`t_MemoryMap` template is used.

+---------+------------------------------------------------------------------+
| Version | Changes                                                          |
+=========+==================================================================+
| 4.0     | Added the ``EntryDescriptions`` and ``LengthColumn`` parameters, |
|         | and support for the ``G`` identifier in the ``EntryTypes``       |
|         | parameter                                                        |
+---------+------------------------------------------------------------------+
| 2.5     | New                                                              |
+---------+------------------------------------------------------------------+

.. _otherCode:

[OtherCode:\*]
--------------
An ``OtherCode:*`` section defines a secondary disassembly that will appear
under 'Other code' on the main disassembly home page. The section name takes
the form::

  [OtherCode:CodeID]

where ``CodeID`` is a unique ID for the secondary disassembly; it must be
limited to the characters '$', '#', 0-9, A-Z and a-z. The unique ID may be used
by the :ref:`R` macro when referring to routines or data blocks in the
secondary disassembly from another disassembly.

An ``OtherCode:*`` section may either be empty or contain a single parameter
named ``Source`` in the form::

  Source=fname

where ``fname`` is the path to the `skool` file from which to generate the
secondary disassembly. If the ``Source`` parameter is not provided, its value
defaults to `CodeID.skool`.

When a secondary disassembly named ``CodeID`` is defined, the following page
and directory IDs become available for use in the :ref:`paths`, :ref:`titles`,
:ref:`pageHeaders` and :ref:`links` sections:

* ``CodeID-Index`` - the ID of the index page
* ``CodeID-Asm-*`` - the IDs of the disassembly pages (``*`` is one of
  ``bcgstuw``, depending on the entry type)
* ``CodeID-CodePath`` - the ID of the directory in which the disassembly pages
  are written

By default, the index page is written to `CodeID/CodeID.html`, and the
disassembly pages are written in a directory named `CodeID`.

Note that the index page is a memory map page, and as such can be configured by
creating a :ref:`memoryMap` section (``MemoryMap:CodeID-Index``) for it.

+---------+----------------------------------------+
| Version | Changes                                |
+=========+========================================+
| 5.0     | Made the ``Source`` parameter optional |
+---------+----------------------------------------+
| 2.0     | New                                    |
+---------+----------------------------------------+

.. _page:

[Page:\*]
---------
A ``Page:*`` section may be used to either declare a page that already exists,
or define a custom page in the HTML disassembly (in conjunction with a
corresponding :ref:`pageContent` section). The section name takes the form::

  [Page:PageID]

where ``PageID`` is a unique ID for the page. The unique ID may be used in an
:ref:`indexGroup` section to create a link to the page in the disassembly
index.

A ``Page:*`` section contains parameters in the form::

  name=value

Recognised parameters are:

* ``Content`` - the path (directory and filename) of a page that already
  exists; when this parameter is supplied, no others are required
* ``JavaScript`` - the base name of the JavaScript file to use in addition to
  any declared by the ``JavaScript`` parameter in the :ref:`ref-Game` section
  (default: None); multiple JavaScript files can be declared by separating
  their names with semicolons
* ``PageContent`` - the HTML source of the body of the page; this defaults to
  the contents of the corresponding :ref:`pageContent` section, but may be
  specified here if the source can be written on a single line

By default, the custom page is written to a file named `PageID.html` in the
root directory of the disassembly; to change this, add a line to the
:ref:`Paths` section. The title, page header and link text for the custom page
can be defined in the :ref:`titles`, :ref:`pageHeaders` and :ref:`links`
sections.

Every custom page is built using the :ref:`HTML template <template>` whose name
matches the page ID, if one exists; otherwise, the stock :ref:`t_Page` template
is used.

Note that a ``Page:*`` section may be empty; if so, it may be omitted from the
`ref` file.

+---------+------------------------------------------------------------------+
| Version | Changes                                                          |
+=========+==================================================================+
| 3.5     | The ``JavaScript`` parameter specifies the JavaScript file(s) to |
|         | use                                                              |
+---------+------------------------------------------------------------------+
| 2.1     | New                                                              |
+---------+------------------------------------------------------------------+

.. _pageContent:

[PageContent:\*]
----------------
A ``PageContent:*`` section contains the HTML source of the body of a custom
page (optionally defined in a :ref:`page` section). The section name takes the
form::

  [PageContent:PageID]

where ``PageID`` is the unique ID of the page.

The HTML source may contain :ref:`skool macros <skoolMacros>`.

+---------+---------+
| Version | Changes |
+=========+=========+
| 2.1     | New     |
+---------+---------+

.. _pageHeaders:

[PageHeaders]
-------------
The ``PageHeaders`` section defines the header text for every page in the HTML
disassembly. Each line has the form::

  PageID=header

where:

* ``PageID`` is the ID of the page
* ``header`` is the header text

Recognised page IDs are:

* ``Asm-b`` - disassembly pages for 'b' blocks (default: 'Data')
* ``Asm-c`` - disassembly pages for 'c' blocks (default: 'Routines')
* ``Asm-g`` - disassembly pages for 'g' blocks (default: 'Game status buffer')
* ``Asm-s`` - disassembly pages for 's' blocks (default: 'Unused')
* ``Asm-t`` - disassembly pages for 't' blocks (default: 'Data')
* ``Asm-u`` - disassembly pages for 'u' blocks (default: 'Unused')
* ``Asm-w`` - disassembly pages for 'w' blocks (default: 'Data')
* ``Bugs`` - the 'Bugs' page
* ``Changelog`` - the 'Changelog' page
* ``DataMap`` - the 'Data' memory map page
* ``Facts`` - the 'Trivia' page
* ``GameStatusBuffer`` - the 'Game status buffer' page
* ``Glossary`` - the 'Glossary' page
* ``GraphicGlitches`` - the 'Graphic glitches' page
* ``MemoryMap`` - the 'Everything' memory map page
* ``MessagesMap`` - the 'Messages' memory map page
* ``Pokes`` - the 'Pokes' page
* ``RoutinesMap`` - the 'Routines' memory map page
* ``UnusedMap`` - the 'Unused addresses' memory map page

The default header text for a page is the same as the title defined in the
:ref:`titles` section, except where indicated above.

The header text for a page defined by a :ref:`memoryMap`, :ref:`otherCode`,
:ref:`page` or :ref:`pageContent` section also defaults to the title, but can
be overridden in this section.

Note that the header of the disassembly index page (``GameIndex``) is not
defined in this section; it is composed from the values of the ``TitlePrefix``
and ``TitleSuffix`` parameters in the :ref:`ref-Game` section.

+---------+---------+
| Version | Changes |
+=========+=========+
| 4.0     | New     |
+---------+---------+

.. _paths:

[Paths]
-------
The ``Paths`` section defines the locations of the files and directories in the
HTML disassembly. Each line has the form::

  ID=path

where:

* ``ID`` is the ID of the file or directory
* ``path`` is the path of the file or directory relative to the root directory
  of the disassembly

Recognised file IDs and their default paths are:

* ``Bugs`` - the 'Bugs' page (default: ``reference/bugs.html``)
* ``Changelog`` - the 'Changelog' page (default: ``reference/changelog.html``)
* ``CodeFiles`` - the format of the disassembly page filenames (default:
  ``{address}.html``)
* ``DataMap`` - the 'Data' memory map page (default: ``maps/data.html``)
* ``Facts`` - the 'Trivia' page (default: ``reference/facts.html``)
* ``GameIndex`` - the home page (default: ``index.html``)
* ``GameStatusBuffer`` - the 'Game status buffer' page (default:
  ``buffers/gbuffer.html``)
* ``Glossary`` - the 'Glossary' page (default: ``reference/glossary.html``)
* ``GraphicGlitches`` - the 'Graphic glitches' page (default:
  ``graphics/glitches.html``)
* ``MemoryMap`` - the 'Everything' memory map page (default: ``maps/all.html``)
* ``MessagesMap`` - the 'Messages' memory map page (default:
  ``maps/messages.html``)
* ``Pokes`` - the 'Pokes' page (default: ``reference/pokes.html``)
* ``RoutinesMap`` - the 'Routines' memory map page (default:
  ``maps/routines.html``)
* ``UnusedMap`` - the 'Unused addresses' memory map page (default:
  ``maps/unused.html``)

Recognised directory IDs and their default paths are:

* ``CodePath`` - the directory in which the disassembly pages are written
  (default: ``asm``)
* ``FontImagePath`` - the directory in which font images (created by the
  :ref:`#FONT <FONT>` macro) are placed (default: ``images/font``)
* ``FontPath`` - the directory in which font files specified by the ``Font``
  parameter in the :ref:`ref-Game` section are placed (default: ``.``)
* ``JavaScriptPath`` - the directory in which JavaScript files specified by the
  ``JavaScript`` parameter in the :ref:`ref-Game` section and :ref:`Page`
  sections are placed (default: ``.``)
* ``ScreenshotImagePath`` - the directory in which screenshot images (created
  by the :ref:`#SCR <SCR>` macro) are placed (default: ``images/scr``)
* ``StyleSheetPath`` - the directory in which CSS files specified by the
  ``StyleSheet`` parameter in the :ref:`ref-Game` section are placed (default:
  ``.``)
* ``UDGImagePath`` - the directory in which UDG images (created by the
  :ref:`#UDG <UDG>` or :ref:`#UDGARRAY <UDGARRAY>` macro) are placed (default:
  ``images/udgs``)

The ``CodeFiles`` parameter contains a standard Python format string that
specifies the format of a disassembly page filename based on the address of the
routine or data block. The default format string is ``{address}.html``, which
produces decimal addresses (e.g. ``65280.html``); to produce 4-digit, upper
case hexadecimal addresses instead (e.g. ``FF00.html``), change ``CodeFiles``
to ``{address:04X}.html``.

+---------+-------------------------------------------------------------------+
| Version | Changes                                                           |
+=========+===================================================================+
| 4.3     | Added the ``CodeFiles`` file ID                                   |
+---------+-------------------------------------------------------------------+
| 3.1.1   | Added the ``FontPath`` directory ID                               |
+---------+-------------------------------------------------------------------+
| 2.5     | Added the ``UnusedMap`` file ID                                   |
+---------+-------------------------------------------------------------------+
| 2.2.5   | Added the ``Changelog`` file ID                                   |
+---------+-------------------------------------------------------------------+
| 2.1.1   | Added the ``CodePath`` directory ID                               |
+---------+-------------------------------------------------------------------+
| 2.0.5   | Added the ``FontImagePath`` directory ID                          |
+---------+-------------------------------------------------------------------+
| 2.0     | New                                                               |
+---------+-------------------------------------------------------------------+

.. _ref-Poke:

[Poke:\*:\*]
------------
Each ``Poke:*:*`` section defines an entry on the 'Pokes' page. The section
names and contents take the form::

  [Poke:anchor:title]
  First paragraph.

  Second paragraph.

  ...

where:

* ``anchor`` is the name of the HTML anchor for the entry
* ``title`` is the title of the entry

To ensure that an entry can be linked to by the :ref:`poke` macro, the anchor
name must be limited to the characters '$', '#', 0-9, A-Z and a-z.

Paragraphs must be separated by blank lines, and may contain HTML markup and
:ref:`skool macros <skoolMacros>`.

.. _resources:

[Resources]
-----------
The ``Resources`` section lists files that will be copied into the disassembly
build directory when :ref:`skool2html.py` is run. Each line has the form::

  fname=destDir

where:

* ``fname`` is the name of the file to copy
* ``destDir`` is the destination directory, relative to the root directory of
  the disassembly; the directory will be created if it doesn't already exist

The files to be copied must be present in `skool2html.py`'s search path in
order for it to find them; to see the search path, run ``skool2html.py -s``.

If your disassembly requires pre-built images or other resources that SkoolKit
does not build, listing them in this section ensures that they will be copied
into place whenever the disassembly is built.

+---------+---------+
| Version | Changes |
+=========+=========+
| 3.6     | New     |
+---------+---------+

.. _template:

[Template:\*]
-------------
Each ``Template:*`` section defines a template used to build an HTML page (or
part of one).

To see the contents of the default templates, run the following command::

  $ skool2html.py -r Template:

For more information, see :ref:`htmlTemplates`.

+---------+---------+
| Version | Changes |
+=========+=========+
| 4.0     | New     |
+---------+---------+

.. _titles:

[Titles]
--------
The ``Titles`` section defines the title (i.e. text used to compose the
``<title>`` element) for every page in the HTML disassembly. Each line has the
form::

  PageID=title

where:

* ``PageID`` is the ID of the page
* ``title`` is the page title

Recognised page IDs and their default titles are:

* ``Asm-b`` - disassembly pages for 'b' blocks (default: 'Data at')
* ``Asm-c`` - disassembly pages for 'c' blocks (default: 'Routine at')
* ``Asm-g`` - disassembly pages for 'g' blocks (default: 'Game status buffer
  entry at')
* ``Asm-s`` - disassembly pages for 's' blocks (default: 'Unused RAM at')
* ``Asm-t`` - disassembly pages for 't' blocks (default: 'Data at')
* ``Asm-u`` - disassembly pages for 'u' blocks (default: 'Unused RAM at')
* ``Asm-w`` - disassembly pages for 'w' blocks (default: 'Data at')
* ``Bugs`` - the 'Bugs' page (default: 'Bugs')
* ``Changelog`` - the 'Changelog' page (default: 'Changelog')
* ``DataMap`` - the 'Data' memory map page (default: 'Data')
* ``Facts`` - the 'Trivia' page (default: 'Trivia')
* ``GameIndex`` - the disassembly index page (default: 'Index')
* ``GameStatusBuffer`` - the 'Game status buffer' page (default: 'Game status
  buffer')
* ``Glossary`` - the 'Glossary' page (default: 'Glossary')
* ``GraphicGlitches`` - the 'Graphic glitches' page (default: 'Graphic
  glitches')
* ``MemoryMap`` - the 'Everything' memory map page (default: 'Memory map')
* ``MessagesMap`` - the 'Messages' memory map page (default: 'Messages')
* ``Pokes`` - the 'Pokes' page (default: 'Pokes')
* ``RoutinesMap`` - the 'Routines' memory map page (default: 'Routines')
* ``UnusedMap`` - the 'Unused addresses' memory map page (default: 'Unused
  addresses')

The title of a page defined by a :ref:`memoryMap`, :ref:`otherCode`,
:ref:`page` or :ref:`pageContent` section defaults to the page ID, but can be
overridden in this section.

+---------+---------------------------------+
| Version | Changes                         |
+=========+=================================+
| 4.0     | Added the ``Asm-*`` page IDs    |
+---------+---------------------------------+
| 2.5     | Added the ``UnusedMap`` page ID |
+---------+---------------------------------+
| 2.2.5   | Added the ``Changelog`` page ID |
+---------+---------------------------------+
| 2.0.5   | New                             |
+---------+---------------------------------+

Ref file comments
-----------------
A comment may be added to a `ref` file by starting a line with a semicolon. For
example::

  ; This is a comment

If a non-comment line in a `ref` file section needs to start with a semicolon,
it can be escaped by doubling it::

  [PageContent:Custom]
  <code>
  ;; This is not a ref file comment
  </code>

The content of this section will be rendered thus::

  <code>
  ; This is not a ref file comment
  </code>

Square brackets
---------------
If a `ref` file section needs to contain a line that looks like a section
header (i.e. like ``[SectionName]``), then to prevent that line from being
parsed as a section header it can be escaped by doubling the opening square
bracket::

  [PageContent:Custom]
  <code>
  [[This is not a section header]
  </code>

The content of this section will be rendered thus::

  <code>
  [This is not a section header]
  </code>

In fact, any line that starts with two opening square brackets will be rendered
with the first one removed.
