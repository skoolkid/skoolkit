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

Paragraphs should be separated by blank lines, and may contain HTML markup and
:ref:`skool macros <skoolMacros>`.

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
| 2.0.5   | New                                        |
+---------+--------------------------------------------+
| 3.4     | Added support for hexadecimal RGB triplets |
+---------+--------------------------------------------+


.. _ref-Config:

[Config]
--------
The ``Config`` section contains configuration parameters in the format::

  name=value

Recognised parameters are:

* ``SkoolFile`` - the name of the main `skool` file to use if not given on the
  :ref:`skool2html.py <skool2html.py>` command line; if not specified, the
  `skool` file with the same base name as the `ref` file will be used
* ``HtmlWriterClass`` - the name of the Python class to use for writing the
  HTML disassembly of the game (default: ``skoolkit.skoolhtml.HtmlWriter``); if
  the class is in a module that is not in the module search path (e.g. a
  standalone module that is not part of an installed package), the module's
  location may be specified thus: ``/path/to/moduledir:module.classname``
* ``GameDir`` - the root directory of the game's HTML disassembly; if not
  specified, the base name of the `skool` or `ref` file given on the
  :ref:`skool2html.py <skool2html.py>` command line will be used

For information on how to create your own Python class for writing an HTML
disassembly, see the documentation on
:ref:`extending SkoolKit <extendingSkoolKit>`.

+---------+-------------------------------------------------------------------+
| Version | Changes                                                           |
+=========+===================================================================+
| 2.0     | New                                                               |
+---------+-------------------------------------------------------------------+
| 2.2.3   | Added the ``HtmlWriterClass`` parameter                           |
+---------+-------------------------------------------------------------------+
| 3.3.1   | Added support to the ``HtmlWriterClass`` parameter for specifying |
|         | a module outside the module search path                           |
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

Paragraphs should be separated by blank lines, and may contain HTML markup and
:ref:`skool macros <skoolMacros>`.

.. _ref-Game:

[Game]
------
The ``Game`` section contains configuration parameters that control certain
aspects of the HTML output. The parameters are in the format::

  name=value

Recognised parameters are:

* ``Font`` - the base name of the font file to use (default: None); multiple
  font files can be declared by separating their names with semicolons
* ``Game`` - the name of the game, which appears in the title of every page,
  and also in the header of every page (if no logo is defined); if not
  specified, the base name of the `skool` file is used
* ``GameStatusBufferIncludes`` - a comma-separated list of addresses of entries
  to include on the 'Game status buffer' page in addition to those that are
  marked with a ``g`` (see the
  :ref:`skool file format reference <skoolFileFormat>`)
* ``InputRegisterTableHeader`` - the text to use in the header of input
  register tables on routine disassembly pages; if not specified, no header is
  displayed
* ``LinkOperands`` - a comma-separated list of instruction types whose operands
  should be hyperlinked when possible (default: ``CALL,DEFW,DJNZ,JP,JR``); add
  ``LD`` to the list to enable the address operands of LD instructions to be
  hyperlinked as well
* ``Logo`` - the text/HTML that will serve as the game logo in the header of
  every page (typically a skool macro that creates a suitable image); if not
  specified, ``LogoImage`` is used
* ``LogoImage`` - the path to the game logo image, which appears in the header
  of every page; if the specified file does not exist, the name of the game is
  used in place of an image
* ``OutputRegisterTableHeader`` - the text to use in the header of output
  register tables on routine disassembly pages; if not specified, no header is
  displayed
* ``StyleSheet`` - the base name of the CSS file to use (default:
  `skoolkit.css`); multiple CSS files can be declared by separating their names
  with semicolons
* ``TitlePrefix`` - the prefix to use before the game name or logo in the
  header of the main index page (default: 'The complete')
* ``TitleSuffix`` - the suffix to use after the game name or logo in the header
  of the main index page (default: 'RAM disassembly')

+---------+-----------------------------------------------------------------+
| Version | Changes                                                         |
+=========+=================================================================+
| 2.0.3   | Added the ``GameStatusBufferIncludes`` parameter                |
+---------+-----------------------------------------------------------------+
| 2.0.5   | Added the ``Logo`` parameter                                    |
+---------+-----------------------------------------------------------------+
| 3.1.2   | Added the ``InputRegisterTableHeader`` and                      |
|         | ``OutputRegisterTableHeader`` parameters                        |
+---------+-----------------------------------------------------------------+
| 3.4     | Added the ``LinkOperands`` parameter                            |
+---------+-----------------------------------------------------------------+
| 3.5     | Added the ``Font``, ``LogoImage`` and ``StyleSheet`` parameters |
|         | (all of which used to live in the :ref:`Paths` section,         |
|         | ``LogoImage`` by the name ``Logo``)                             |
+---------+-----------------------------------------------------------------+

[Glossary:\*]
-------------
Each ``Glossary:*`` section defines an entry on the 'Glossary' page. The
section names and contents take the form::

  [Glossary:term]
  First paragraph.

  Second paragraph.

  ...

where ``term`` is the term being defined in the entry.

Paragraphs should be separated by blank lines, and may contain HTML markup and
:ref:`skool macros <skoolMacros>`.

+---------+---------------------------------------+
| Version | Changes                               |
+=========+=======================================+
| 3.1.3   | Added support for multiple paragraphs |
+---------+---------------------------------------+

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

Paragraphs should be separated by blank lines, and may contain HTML markup and
:ref:`skool macros <skoolMacros>`.

.. _graphics:

[Graphics]
----------
The ``Graphics`` section, if present, defines the body of the 'Other graphics'
page; it may contain HTML markup and :ref:`skool macros <skoolMacros>`.

+---------+---------+
| Version | Changes |
+=========+=========+
| 2.0.5   | New     |
+---------+---------+

.. _ref-ImageWriter:

[ImageWriter]
-------------
The ``ImageWriter`` section contains configuration parameters that control
SkoolKit's image creation library. The parameters are in the format::

  name=value

Recognised parameters are:

* ``DefaultFormat`` - the default image format; valid values are ``png`` (the
  default) and ``gif``
* ``GIFCompression`` - ``1`` to create compressed GIFs (which is slower but
  produces much smaller files), or ``0`` to create uncompressed GIFs (default:
  ``1``); 
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

+---------+---------------------------------------------------------------+
| Version | Changes                                                       |
+=========+===============================================================+
| 3.0     | New                                                           |
+---------+---------------------------------------------------------------+
| 3.0.1   | Added the ``DefaultFormat``, ``GIFCompression``,              |
|         | ``GIFEnableAnimation``, ``GIFTransparency``, ``PNGAlpha`` and |
|         | ``PNGEnableAnimation`` parameters                             |
+---------+---------------------------------------------------------------+

.. _index:

[Index]
-------
The ``Index`` section contains a list of link group IDs in the order in which
the link groups should appear on the disassembly index page. The link groups
themselves are defined in ``[Index:*:*]`` sections (see below).

By default, SkoolKit defines the following list of link groups::

  [Index]
  MemoryMaps
  Graphics
  DataTables
  OtherCode
  Reference

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

The page IDs that may be used in an ``[Index:*:*]`` section are the same as the
file IDs that may be used in the :ref:`paths` section, or the IDs defined by
:ref:`page` sections.

By default, SkoolKit defines four link groups with the following names and
contents::

  [Index:MemoryMaps:Memory maps]
  MemoryMap
  RoutinesMap
  DataMap
  MessagesMap
  UnusedMap

  [Index:Graphics:Graphics]
  Graphics
  GraphicGlitches

  [Index:DataTables:Data tables and buffers]
  GameStatusBuffer

  [Index:Reference:Reference]
  Changelog
  Glossary
  Facts
  Bugs
  Pokes

+---------+---------+
| Version | Changes |
+=========+=========+
| 2.0.5   | New     |
+---------+---------+

[Info]
------
The ``Info`` section contains parameters that define the release and copyright
information that appears in the footer of every page of the HTML disassembly.
Each line has the form::

  name=text

Recognised parameters are:

* ``Copyright`` - copyright message (default: '')
* ``Created`` - message indicating the software used to create the disassembly
  (default: 'Created using SkoolKit $VERSION.')
* ``Release`` - message indicating the release name and version number of the
  disassembly (default: '')

If the string ``$VERSION`` appears anywhere in the ``Created`` message, it is
replaced by the version number of SkoolKit.

Each of these messages may contain HTML markup.

+---------+-----------------------------------------------------+
| Version | Changes                                             |
+=========+=====================================================+
| 2.0     | New                                                 |
+---------+-----------------------------------------------------+
| 2.0.3   | Added the ``Created`` parameter                     |
+---------+-----------------------------------------------------+
| 2.2.5   | Set the default value for the ``Created`` parameter |
+---------+-----------------------------------------------------+

.. _links:

[Links]
-------
The ``Links`` section defines the link text for the various pages in the HTML
disassembly (as displayed on the disassembly index page). Each line has the
form::

  ID=text

where:

* ``ID`` is the ID of the page
* ``text`` is the link text

Recognised page IDs are:

* ``Bugs`` - the 'Bugs' page
* ``Changelog`` - the 'Changelog' page
* ``DataMap`` - the 'Data' memory map page
* ``Facts`` - the 'Trivia' page
* ``GameStatusBuffer`` - the 'Game status buffer' page
* ``Glossary`` - the 'Glossary' page
* ``GraphicGlitches`` - the 'Graphic glitches' page
* ``Graphics`` - the 'Other graphics' page
* ``MemoryMap`` - the 'Everything' memory map page (default: 'Everything')
* ``MessagesMap`` - the 'Messages' memory map page
* ``Pokes`` - the 'Pokes' page
* ``RoutinesMap`` - the 'Routines' memory map page
* ``UnusedMap`` - the 'Unused addresses' memory map page

The default link text for a page is the same as the page title (see
:ref:`titles`) except where indicated above.

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
| 2.0.5   | New                             |
+---------+---------------------------------+
| 2.2.5   | Added the ``Changelog`` page ID |
+---------+---------------------------------+
| 2.5     | Added the ``UnusedMap`` page ID |
+---------+---------------------------------+

.. _memoryMap:

[MemoryMap:\*]
--------------
Each ``MemoryMap:*`` section defines the properties of a memory map page. The
section names take the form::

  [MemoryMap:PageID]

where ``PageID`` is the unique ID of the memory map page (which should be the
same as the corresponding page ID that appears in the :ref:`Paths` section).

Each ``MemoryMap:*`` section contains parameters in the form::

  name=value

Recognised parameters and their default values are:

* ``EntryTypes`` - the types of entries to show in the map (by default, every
  type is shown); entry types are identified by their control directives as
  follows:

  * ``b`` - DEFB blocks
  * ``c`` - routines
  * ``g`` - game status buffer entries
  * ``t`` - messages
  * ``u`` - unused addresses
  * ``w`` - DEFW blocks
  * ``z`` - blocks containing all zeroes

* ``Intro`` - the text (HTML) to display at the top of the memory map page
  (default: '')
* ``PageByteColumns`` - ``1`` if the memory map page should include 'Page' and
  'Byte' columns, ``0`` otherwise (default: ``0``)
* ``Write`` - ``1`` if the memory map page should be written, ``0`` otherwise
  (default: ``1``)

By default, SkoolKit defines five memory maps whose property values differ from
the defaults as follows::

  [MemoryMap:MemoryMap]
  PageByteColumns=1

  [MemoryMap:RoutinesMap]
  EntryTypes=c

  [MemoryMap:DataMap]
  EntryTypes=bw
  PageByteColumns=1

  [MemoryMap:MessagesMap]
  EntryTypes=t

  [MemoryMap:UnusedMap]
  EntryTypes=uz
  PageByteColumns=1

+---------+---------+
| Version | Changes |
+=========+=========+
| 2.5     | New     |
+---------+---------+

[OtherCode:\*]
--------------
Each ``OtherCode:*`` section defines a secondary disassembly that will appear
under 'Other code' on the main disassembly home page. The section names take
the form::

  [OtherCode:asm_id]

where ``asm_id`` is a unique ID for the secondary disassembly. The unique ID
may be used by the :ref:`#R macro <R>` when referring to routines or data
blocks in the secondary disassembly from another disassembly.

Each ``OtherCode:*`` section contains parameters in the form::

  name=value

The following parameters are required:

* ``Header`` - the header text that will appear on each routine or data block
  disassembly page in the secondary disassembly
* ``Index`` - the filename of the home page of the secondary disassembly
* ``Path`` - the directory to which the secondary disassembly files will be
  written
* ``Source`` - the `skool` file from which to generate the secondary
  disassembly
* ``Title`` - the header text that will appear on the the secondary disassembly
  index page

The following parameters are optional:

* ``IndexPageId`` - the ID of the secondary disassembly index page; if defined,
  it can be used by the :ref:`link` macro to create a hyperlink to the page
* ``Link`` - the link text to use on the main disassembly index page for the
  hyperlink to the secondary disassembly index page (defaults to the value of
  the ``Title`` parameter)

+---------+---------------------------------------------------+
| Version | Changes                                           |
+=========+===================================================+
| 2.0     | New                                               |
+---------+---------------------------------------------------+
| 2.2.5   | Added the ``IndexPageId`` and ``Link`` parameters |
+---------+---------------------------------------------------+

.. _page:

[Page:\*]
---------
Each ``Page:*`` section is used to either declare a page that already exists,
or define a custom page in the HTML disassembly (in conjunction with a
corresponding :ref:`pageContent` section). The section names take the form::

  [Page:PageId]

where ``PageId`` is a unique ID for the page. The unique ID may be used in an
:ref:`indexGroup` section to create a link to the page in the disassembly
index.

Each ``Page:*`` section contains parameters in the form::

  name=value

One of the following two parameters is required:

* ``Content`` - the path (directory and filename) of a page that already exists
* ``Path`` - the path (directory and filename) where the custom page will be
  created

The following parameters are optional:

* ``BodyClass`` - the CSS class to use for the ``<body>`` element of the page
  (default: no CSS class is used)
* ``JavaScript`` - the base name of the JavaScript file to use (default: None);
  multiple JavaScript files can be declared by separating their names with
  semicolons
* ``Link`` - the link text for the page (defaults to the title)
* ``PageContent`` - the HTML source of the body of the page; this may contain
  :ref:`skool macros <skoolMacros>`, and can be used instead of a
  :ref:`pageContent` section if the source can be written on a single line
* ``Title`` - the title of the page (defaults to the page ID)

+---------+------------------------------------------------------------------+
| Version | Changes                                                          |
+=========+==================================================================+
| 2.1     | New                                                              |
+---------+------------------------------------------------------------------+
| 3.5     | The ``JavaScript`` parameter specifies the JavaScript file(s) to |
|         | use                                                              |
+---------+------------------------------------------------------------------+

.. _pageContent:

[PageContent:\*]
----------------
Each ``PageContent:*`` section contains the HTML source of the body of a custom
page defined in a :ref:`page` section. The section names take the form::

  [PageContent:PageId]

where ``PageId`` is the unique ID of the page (as previously declared in the
name of the corresponding :ref:`page` section).

The HTML source may contain :ref:`skool macros <skoolMacros>`.

+---------+---------+
| Version | Changes |
+=========+=========+
| 2.1     | New     |
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

* ``Bugs`` - the 'Bugs' page (default: `reference/bugs.html`)
* ``Changelog`` - the 'Changelog' page (default: `reference/changelog.html`)
* ``DataMap`` - the 'Data' memory map page (default: `maps/data.html`)
* ``Facts`` - the 'Trivia' page (default: `reference/facts.html`)
* ``GameIndex`` - the disassembly home page (default: `index.html`)
* ``GameStatusBuffer`` - the 'Game status buffer' page (default:
  `buffers/gbuffer.html`)
* ``Glossary`` - the 'Glossary' page (default: `reference/glossary.html`)
* ``GraphicGlitches`` - the 'Graphic glitches' page (default:
  `graphics/glitches.html`)
* ``Graphics`` - the 'Other graphics' page (default: `graphics/graphics.html`)
* ``MemoryMap`` - the 'Everything' memory map page (default: `maps/all.html`)
* ``MessagesMap`` - the 'Messages' memory map page (default:
  `maps/messages.html`)
* ``Pokes`` - the 'Pokes' page (default: `reference/pokes.html`)
* ``RoutinesMap`` - the 'Routines' memory map page (default:
  `maps/routines.html`)
* ``UnusedMap`` - the 'Unused addresses' memory map page (default:
  `maps/unused.html`)

Recognised directory IDs and their default paths are:

* ``CodePath`` - the directory in which the disassembly files will be written
  (default: `asm`)
* ``FontPath`` - the directory in which to store font files specified by the
  ``Font`` parameter in the :ref:`ref-Game` section (default: `.`)
* ``FontImagePath`` - the directory in which font images (created by the
  :ref:`#FONT <FONT>` macro) will be placed (default: `images/font`)
* ``JavaScriptPath`` - the directory in which to store JavaScript files
  specified by the ``JavaScript`` parameter in :ref:`Page` sections (default:
  `.`)
* ``ScreenshotImagePath`` - the directory in which screenshot images (created
  by the :ref:`#SCR <SCR>` macro) will be placed (default: `images/scr`)
* ``StyleSheetPath`` - the directory in which to store CSS files specified by
  the ``StyleSheet`` parameter in the :ref:`ref-Game` section (default: `.`)
* ``UDGImagePath`` - the directory in which UDG images (created by the
  :ref:`#UDG <UDG>` or :ref:`#UDGARRAY <UDGARRAY>` macro) will be placed
  (default: `images/udgs`)

+---------+-------------------------------------------------------------------+
| Version | Changes                                                           |
+=========+===================================================================+
| 2.0     | New                                                               |
+---------+-------------------------------------------------------------------+
| 2.0.5   | Added the ``FontImagePath`` directory ID                          |
+---------+-------------------------------------------------------------------+
| 2.1.1   | Added the ``CodePath`` directory ID                               |
+---------+-------------------------------------------------------------------+
| 2.2.5   | Added the ``Changelog`` file ID                                   |
+---------+-------------------------------------------------------------------+
| 2.5     | Added the ``UnusedMap`` file ID                                   |
+---------+-------------------------------------------------------------------+
| 3.1.1   | Added the ``FontPath`` directory ID                               |
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

Paragraphs should be separated by blank lines, and may contain HTML markup and
:ref:`skool macros <skoolMacros>`.

.. _titles:

[Titles]
--------
The ``Titles`` section defines the titles of the various pages in the HTML
disassembly. Each line has the form::

  ID=title

where:

* ``ID`` is the ID of the page
* ``title`` is the page title

Recognised page IDs and their default titles are:

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
* ``Graphics`` - the 'Other graphics' page (default: 'Graphics')
* ``MemoryMap`` - the 'Everything' memory map page (default: 'Memory map')
* ``MessagesMap`` - the 'Messages' memory map page (default: 'Messages')
* ``Pokes`` - the 'Pokes' page (default: 'Pokes')
* ``RoutinesMap`` - the 'Routines' memory map page (default: 'Routines')
* ``UnusedMap`` - the 'Unused addresses' memory map page (default: 'Unused
  addresses')

+---------+---------------------------------+
| Version | Changes                         |
+=========+=================================+
| 2.0.5   | New                             |
+---------+---------------------------------+
| 2.2.5   | Added the ``Changelog`` page ID |
+---------+---------------------------------+
| 2.5     | Added the ``UnusedMap`` page ID |
+---------+---------------------------------+
