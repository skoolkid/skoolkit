.. _refFiles:

Ref files
=========
If you want to configure or augment an HTML disassembly, you will need one or
more ref files. A ref file can be used to (for example):

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

A ref file must be formatted into sections separated by section names inside
square brackets, like this::

  [SectionName]

The contents of each section that may be found in a ref file are described
below.

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
  specified, the base name of the skool file given on the :ref:`skool2html.py`
  command line will be used
* ``HtmlWriterClass`` - the name of the Python class to use for writing the
  HTML disassembly of the game (default: ``skoolkit.skoolhtml.HtmlWriter``); if
  the class is in a module that is not in the module search path (e.g. a
  standalone module that is not part of an installed package), the module's
  location may be specified thus: ``/path/to/moduledir:module.classname``
* ``RefFiles`` - a semicolon-separated list of extra ref files to use (after
  any that are automatically read by virtue of having the same filename prefix
  as the skool file, and before any others named on the :ref:`skool2html.py`
  command line)

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

.. _ref-Game:

[Game]
------
The ``Game`` section contains configuration parameters that control certain
aspects of the HTML output. The parameters are in the format::

  name=value

Recognised parameters are:

* ``AddressAnchor`` - the format of the anchors attached to instructions on
  disassembly pages and entries on memory map pages (default: ``{address}``)
* ``AsmSinglePageTemplate`` - the name of the HTML template used to build the
  disassembly on a single page, as opposed to a separate page for each routine
  and data block (default: None); set this to 'AsmAllInOne' to use the
  :ref:`t_AsmAllInOne` template
* ``Bytes`` - the format specification for the ``bytes`` replacement field in
  the :ref:`t_asm_instruction` template (default: ''); if not blank, assembled
  instruction byte values are displayed on disassembly pages
* ``Copyright`` - the copyright message that appears in the footer of every
  page (default: '')
* ``Created`` - the message indicating the software used to create the
  disassembly that appears in the footer of every page (default: 'Created using
  SkoolKit #VERSION.')
* ``DisassemblyTableNumCols`` - the number of columns in the disassembly table
  on disassembly pages (default: the number of occurrences of '</td>' in the
  :ref:`t_asm_instruction` template); this value is used by the :ref:`t_Asm`,
  :ref:`t_asm_comment` and :ref:`t_asm_entry` templates
* ``Font`` - the base name of the font file to use (default: None); multiple
  font files can be declared by separating their names with semicolons
* ``Game`` - the name of the game, which appears in the title of every page,
  and also in the header of every page (if no logo is defined); if not
  specified, the base name of the skool file is used
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

Every parameter in this section may contain :ref:`skool macros <skoolMacros>`.

The ``AddressAnchor`` parameter contains a standard Python format string that
specifies the format of the anchors attached to instructions on disassembly
pages and entries on memory map pages. The default format string is
``{address}``, which produces decimal addresses (e.g. ``#65280``). To produce
4-digit, lower case hexadecimal addresses instead (e.g. ``#ff00``), change
``AddressAnchor`` to ``{address:04x}``. Or to produce 4-digit, upper case
hexadecimal addresses if the ``--hex`` option is used with
:ref:`skool2html.py`, and decimal addresses otherwise:
``{address#IF({base}==16)(:04X)}``.

+---------+-------------------------------------------------------------------+
| Version | Changes                                                           |
+=========+===================================================================+
| 7.2     | Added the ``Bytes`` and ``DisassemblyTableNumCols`` parameters    |
+---------+-------------------------------------------------------------------+
| 6.0     | Every parameter (not just ``Logo``) may contain                   |
|         | :ref:`skool macros <skoolMacros>`                                 |
+---------+-------------------------------------------------------------------+
| 5.3     | Added the ``AsmSinglePageTemplate`` parameter                     |
+---------+-------------------------------------------------------------------+
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

.. _ref-ImageWriter:

[ImageWriter]
-------------
The ``ImageWriter`` section contains configuration parameters that control
SkoolKit's image creation library. The parameters are in the format::

  name=value

Recognised parameters are:

* ``DefaultAnimationFormat`` - the default format for animated images: ``gif``
  (the default) or ``png``
* ``DefaultFormat`` - the default image format: ``png`` (the default) or
  ``gif``
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

.. note::
   Support for GIF images is deprecated since version 7.2. Use PNG images
   instead.

+---------+--------------------------------------------------------------+
| Version | Changes                                                      |
+=========+==============================================================+
| 6.0     | ``DefaultAnimationFormat`` defaults to ``gif``               |
+---------+--------------------------------------------------------------+
| 5.1     | Added the ``DefaultAnimationFormat`` parameter               |
+---------+--------------------------------------------------------------+
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
:ref:`indexGroup` sections. ``OtherCode`` is a special built-in link group that
contains links to the index pages of secondary disassemblies defined by
:ref:`otherCode` sections.

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

* ``AsmSinglePage`` - the disassembly page (when a single-page template is
  specified by the ``AsmSinglePageTemplate`` parameter in the :ref:`ref-Game`
  section)
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

The link text for a page defined by a :ref:`memoryMap`, :ref:`otherCode` or
:ref:`page` section also defaults to the page header text, but can be
overridden in this section.

If the link text starts with some text in square brackets, that text alone is
used as the link text, and the remaining text is displayed alongside the
hyperlink. For example::

  MemoryMap=[Everything] (routines, data, text and unused addresses)

This declares that the link text for the 'Everything' memory map page will be
'Everything', and '(routines, data, text and unused addresses)' will be
displayed alongside it.

+---------+-------------------------------------+
| Version | Changes                             |
+=========+=====================================+
| 5.3     | Added the ``AsmSinglePage`` page ID |
+---------+-------------------------------------+
| 2.5     | Added the ``UnusedMap`` page ID     |
+---------+-------------------------------------+
| 2.2.5   | Added the ``Changelog`` page ID     |
+---------+-------------------------------------+
| 2.0.5   | New                                 |
+---------+-------------------------------------+

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
  * ``s`` - blocks containing bytes that are all the same value
  * ``t`` - messages
  * ``u`` - unused addresses
  * ``w`` - DEFW blocks

* ``Includes`` - a comma-separated list of addresses of entries to include on
  the memory map page in addition to those specified by the ``EntryTypes``
  parameter
* ``Intro`` - the text (which may contain HTML markup) displayed at the top of
  the memory map page (default: '')
* ``LengthColumn`` - ``1`` to display the 'Length' column, or ``0`` not to
  (default: ``0``)
* ``PageByteColumns`` - ``1`` to display 'Page' and 'Byte' columns, or ``0``
  not to (default: ``0``)
* ``Write`` - ``1`` to write the memory map page, or ``0`` not to (default:
  ``1``)

Every parameter in this section may contain :ref:`skool macros <skoolMacros>`.

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
| 6.2     | Added the ``Includes`` parameter                                 |
+---------+------------------------------------------------------------------+
| 6.0     | Every parameter (not just ``Intro``) may contain                 |
|         | :ref:`skool macros <skoolMacros>`                                |
+---------+------------------------------------------------------------------+
| 4.0     | Added the ``EntryDescriptions`` and ``LengthColumn`` parameters  |
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

where ``fname`` is the path to the skool file from which to generate the
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
* ``CodeID-AsmSinglePage`` - the ID of the disassembly page (when a single-page
  template is specified by the ``AsmSinglePageTemplate`` parameter in the
  :ref:`ref-Game` section)

By default, the index page is written to `CodeID/CodeID.html`, and the
disassembly pages are written in a directory named `CodeID`; if a single-page
template is used, the disassembly page is written to `CodeID/asm.html`.

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
A ``Page:*`` section either declares a page that already exists, or defines a
custom page in the HTML disassembly. The section name takes the form::

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
* ``PageContent`` - the HTML source of the body of the page; the :ref:`INCLUDE`
  macro may be used here to include the contents of a separate ref file section
* ``SectionPrefix`` - the prefix of the names of the ref file sections from
  which to build the entries on a :ref:`box page <boxpages>`
* ``SectionType`` - how to parse and render :ref:`box page <boxpages>` entry
  sections (when ``SectionPrefix`` is defined): as single-line list items with
  indentation (``ListItems``), as multi-line list items prefixed by '-'
  (``BulletPoints``), or as paragraphs (the default)

Every parameter in this section may contain :ref:`skool macros <skoolMacros>`.

Note that the ``Content``, ``SectionPrefix`` and ``PageContent`` parameters are
mutually exclusive (and that is their order of precedence); one of them must be
present.

By default, the custom page is written to a file named `PageID.html` in the
root directory of the disassembly; to change this, add a line to the
:ref:`Paths` section. The title, page header and link text for the custom page
default to 'PageID', but can be overridden in the :ref:`titles`,
:ref:`pageHeaders` and :ref:`links` sections.

Every custom page is built using the :ref:`HTML template <template>` whose name
matches the page ID, if one exists; otherwise, either the :ref:`t_Reference`
template is used (when ``SectionPrefix`` is defined), or the :ref:`t_Page`
template is used.

+---------+------------------------------------------------------------------+
| Version | Changes                                                          |
+=========+==================================================================+
| 6.0     | Added support for ``SectionType=BulletPoints``; every parameter  |
|         | (not just ``PageContent``) may contain                           |
|         | :ref:`skool macros <skoolMacros>`                                |
+---------+------------------------------------------------------------------+
| 5.4     | Added the ``SectionType`` parameter                              |
+---------+------------------------------------------------------------------+
| 5.3     | Added the ``SectionPrefix`` parameter                            |
+---------+------------------------------------------------------------------+
| 3.5     | The ``JavaScript`` parameter specifies the JavaScript file(s) to |
|         | use                                                              |
+---------+------------------------------------------------------------------+
| 2.1     | New                                                              |
+---------+------------------------------------------------------------------+

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
* ``Asm-t`` - disassembly pages for 't' blocks (default: 'Messages')
* ``Asm-u`` - disassembly pages for 'u' blocks (default: 'Unused')
* ``Asm-w`` - disassembly pages for 'w' blocks (default: 'Data')
* ``AsmSinglePage`` - the disassembly page (when a single-page template is
  specified by the ``AsmSinglePageTemplate`` parameter in the :ref:`ref-Game`
  section)
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

Every parameter in this section may contain :ref:`skool macros <skoolMacros>`.

The default header text for a page is the same as the title defined in the
:ref:`titles` section, except where indicated above.

The header text for a page defined by a :ref:`memoryMap`, :ref:`otherCode` or
:ref:`page` section also defaults to the title, but can be overridden in this
section.

Note that the header of the disassembly index page (``GameIndex``) is not
defined in this section; it is composed from the values of the ``TitlePrefix``
and ``TitleSuffix`` parameters in the :ref:`ref-Game` section.

+---------+------------------------------------------------------------+
| Version | Changes                                                    |
+=========+============================================================+
| 6.0     | The default header for ``Asm-t`` pages is 'Messages'; page |
|         | headers may contain :ref:`skool macros <skoolMacros>`      |
+---------+------------------------------------------------------------+
| 5.3     | Added the ``AsmSinglePage`` page ID                        |
+---------+------------------------------------------------------------+
| 4.0     | New                                                        |
+---------+------------------------------------------------------------+

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

* ``AsmSinglePage`` - the disassembly page (when a single-page template is
  specified by the ``AsmSinglePageTemplate`` parameter in the :ref:`ref-Game`
  section; default: ``asm.html``)
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
* ``UDGFilename`` - the format of the default filename for images created by
  the :ref:`UDG` macro (default: ``udg{addr}_{attr}x{scale}``); this is a
  standard Python format string that recognises the macro parameters ``addr``,
  ``attr`` and ``scale``
* ``UnusedMap`` - the 'Unused addresses' memory map page (default:
  ``maps/unused.html``)

Recognised directory IDs and their default paths are:

* ``CodePath`` - the directory in which the disassembly pages are written
  (default: ``asm``)
* ``FontImagePath`` - the directory in which font images (created by the
  :ref:`#FONT <FONT>` macro) are placed (default: ``{ImagePath}/font``)
* ``FontPath`` - the directory in which font files specified by the ``Font``
  parameter in the :ref:`ref-Game` section are placed (default: ``.``)
* ``ImagePath`` - the base directory in which images are placed (default:
  ``images``)
* ``JavaScriptPath`` - the directory in which JavaScript files specified by the
  ``JavaScript`` parameter in the :ref:`ref-Game` section and :ref:`Page`
  sections are placed (default: ``.``)
* ``ScreenshotImagePath`` - the directory in which screenshot images (created
  by the :ref:`#SCR <SCR>` macro) are placed (default: ``{ImagePath}/scr``)
* ``StyleSheetPath`` - the directory in which CSS files specified by the
  ``StyleSheet`` parameter in the :ref:`ref-Game` section are placed (default:
  ``.``)
* ``UDGImagePath`` - the directory in which UDG images (created by the
  :ref:`#UDG <UDG>` or :ref:`#UDGARRAY <UDGARRAY>` macro) are placed (default:
  ``{ImagePath}/udgs``)

Every parameter in this section may contain :ref:`skool macros <skoolMacros>`.

The ``CodeFiles`` parameter contains a standard Python format string that
specifies the format of a disassembly page filename based on the address of the
routine or data block. The default format string is ``{address}.html``, which
produces decimal addresses (e.g. ``65280.html``). To produce 4-digit, upper
case hexadecimal addresses instead (e.g. ``FF00.html``), change ``CodeFiles``
to ``{address:04X}.html``. Or to produce 4-digit, upper case hexadecimal
addresses if the ``--hex`` option is used with :ref:`skool2html.py`, and
decimal addresses otherwise: ``{address#IF({base}==16)(:04X)}.html``.

+---------+-------------------------------------------------------------------+
| Version | Changes                                                           |
+=========+===================================================================+
| 6.3     | Added the ``ImagePath`` directory ID and the ability to define    |
|         | one image path ID in terms of another                             |
+---------+-------------------------------------------------------------------+
| 6.0     | Paths may contain :ref:`skool macros <skoolMacros>`; added the    |
|         | ``UDGFilename`` parameter (which used to live in the              |
|         | :ref:`ref-Game` section)                                          |
+---------+-------------------------------------------------------------------+
| 5.3     | Added the ``AsmSinglePage`` file ID                               |
+---------+-------------------------------------------------------------------+
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
order for it to find them. To see the search path, run::

  $ skool2html.py -s

``fname`` may contain the special wildcard characters ``*``, ``?`` and ``[]``,
which are expanded as follows:

* ``*`` - matches any number of characters
* ``?`` - matches any single character
* ``[seq]`` - matches any character in ``seq``; ``seq`` may be a simple
  sequence of characters (e.g. ``abcde``) or a range (e.g. ``a-e``)
* ``[!seq]`` - matches any character not in ``seq``

If your disassembly requires pre-built images or other resources that SkoolKit
does not build, listing them in this section ensures that they will be copied
into place whenever the disassembly is built.

+---------+-------------------------------------------------------------------+
| Version | Changes                                                           |
+=========+===================================================================+
| 6.3     | Added support for pathname pattern expansion using wildcard       |
|         | characters                                                        |
+---------+-------------------------------------------------------------------+
| 3.6     | New                                                               |
+---------+-------------------------------------------------------------------+

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
* ``Asm-t`` - disassembly pages for 't' blocks (default: 'Text at')
* ``Asm-u`` - disassembly pages for 'u' blocks (default: 'Unused RAM at')
* ``Asm-w`` - disassembly pages for 'w' blocks (default: 'Data at')
* ``AsmSinglePage`` - the disassembly page (when a single-page template is
  specified by the ``AsmSinglePageTemplate`` parameter in the :ref:`ref-Game`
  section; default: 'Disassembly')
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

Every parameter in this section may contain :ref:`skool macros <skoolMacros>`.

The title of a page defined by a :ref:`memoryMap`, :ref:`otherCode` or
:ref:`page` section defaults to the page ID, but can be overridden in this
section.

+---------+----------------------------------------------------------------+
| Version | Changes                                                        |
+=========+================================================================+
| 6.0     | The default title for ``Asm-t`` pages is 'Text at'; titles may |
|         | contain :ref:`skool macros <skoolMacros>`                      |
+---------+----------------------------------------------------------------+
| 5.3     | Added the ``AsmSinglePage`` page ID                            |
+---------+----------------------------------------------------------------+
| 4.0     | Added the ``Asm-*`` page IDs                                   |
+---------+----------------------------------------------------------------+
| 2.5     | Added the ``UnusedMap`` page ID                                |
+---------+----------------------------------------------------------------+
| 2.2.5   | Added the ``Changelog`` page ID                                |
+---------+----------------------------------------------------------------+
| 2.0.5   | New                                                            |
+---------+----------------------------------------------------------------+

.. _boxpages:

Box pages
---------
A 'box page' is an HTML page that contains entries (blocks of arbitrary text)
distinguished by alternating background colours, and a table of contents (links
to each entry). It is defined by a :ref:`Page` section that contains a
``SectionPrefix`` parameter, which determines the prefix of the ref file
sections from which the entries are built.

SkoolKit defines some box pages by default. Their names and the ref file
sections that can be used to define their entries are as follows:

* ``Bugs`` - ``[Bug:title]`` or ``[Bug:anchor:title]``
* ``Changelog`` - ``[Changelog:title]`` or ``[Changelog:anchor:title]``
* ``Facts`` - ``[Fact:title]`` or ``[Fact:anchor:title]``
* ``Glossary`` - ``[Glossary:title]`` or ``[Glossary:anchor:title]``
* ``GraphicGlitches`` - ``[GraphicGlitch:title]`` or
  ``[GraphicGlitch:anchor:title]``
* ``Pokes`` - ``[Poke:title]`` or ``[Poke:anchor:title]``

To see the contents of the default :ref:`Page` sections, run the following
command::

  $ skool2html.py -r Page:

If ``anchor`` is omitted from an entry section name, it defaults to the title
converted to lower case with parentheses and whitespace characters replaced by
underscores.

By default, a box page entry section is parsed as a sequence of paragraphs
separated by blank lines. For example::

  [Bug:anchor:title]
  First paragraph.

  Second paragraph.

  ...

However, if the ``SectionType`` parameter in the :ref:`Page` section is set to
``ListItems``, each entry section is parsed as a sequence of single-line list
items with indentation. For example::

  [Changelog:title]
  Intro text.

  First top-level item.
    First subitem.
    Second subitem.
      First subsubitem.

  Second top-level item.
  ...

The intro text and the first top-level item must be separated by a blank line.
Lower-level items are created by using indentation, as shown. Blank lines
between items are optional and are ignored. If the intro text is a single
hyphen (``-``), it is not included in the final HTML rendering.

If your list items are long, you might prefer to set the ``SectionType``
parameter to ``BulletPoints``; in that case, each entry section is parsed as a
sequence of multi-line list items prefixed by '-'. For example::

  [Changes:title]
  Intro text.

  - First top-level item,
    split over two lines.
    - First subitem, also
      split over two lines.
    - Second subitem, on one line this time.
      - First subsubitem,
        this time split
        over three lines.

  - Second top-level item.
  ...

An entry section's ``anchor``, ``title`` and contents may contain HTML markup
and :ref:`skool macros <skoolMacros>`.

+---------+-----------------------------------------------------------------+
| Version | Changes                                                         |
+=========+=================================================================+
| 6.0     | Added support for parsing an entry section as a sequence of     |
|         | multi-line list items prefixed by '-'                           |
|         | (``SectionType=BulletPoints``); the ``anchor`` and ``title`` of |
|         | an entry section name may contain                               |
|         | :ref:`skool macros <skoolMacros>`                               |
+---------+-----------------------------------------------------------------+
| 5.4     | The ``anchor`` part of an entry section name is optional        |
+---------+-----------------------------------------------------------------+

Appending content
-----------------
Content may be appended to an existing ref file section defined elsewhere by
adding a '+' suffix to the section name. For example, to add a line to the
:ref:`ref-Game` section::

  [Game+]
  AddressAnchor={address:04x}

Ref file comments
-----------------
A comment may be added to a ref file by starting a line with a semicolon. For
example::

  ; This is a comment

If a non-comment line in a ref file section needs to start with a semicolon, it
can be escaped by doubling it::

  [Glossary:term]
  <code>
  ;; This is not a ref file comment
  </code>

The content of this section will be rendered thus::

  <code>
  ; This is not a ref file comment
  </code>

Square brackets
---------------
If a ref file section needs to contain a line that looks like a section header
(i.e. like ``[SectionName]``), then to prevent that line from being parsed as a
section header it can be escaped by doubling the opening square bracket::

  [Glossary:term]
  <code>
  [[This is not a section header]
  </code>

The content of this section will be rendered thus::

  <code>
  [This is not a section header]
  </code>

In fact, any line that starts with two opening square brackets will be rendered
with the first one removed.
