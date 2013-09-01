.. _skoolMacros:

Skool macros
============
`skool` files and `ref` files may contain skool macros that are 'expanded' to
an appropriate piece of HTML markup (when rendering in HTML mode), or to an
appropriate piece of plain text (when rendering in ASM mode).

Skool macros have the following general form::

  #MACROrparam1,rparam2,...[,oparam1,oparam2,...]

where:

* ``MACRO`` is the macro name
* ``rparam1``, ``rparam2`` etc. are required parameters
* ``oparam1``, ``oparam2`` etc. are optional parameters

If an optional parameter is left blank or omitted entirely, it assumes its
default value. So, for example::

  #UDG39144

is equivalent to::

  #UDG39144,56,4,1,0,0,0

and::

  #UDG30115,23,,2,1

is equivalent to::

  #UDG30115,23,4,2,1

Numeric parameters may be given in decimal notation (as already shown in the
examples above), or in hexadecimal notation (prefixed by ``$``)::

  #UDG$98E8,$06

The skool macros recognised by SkoolKit are described in the following
subsections.

.. _BUG:

#BUG
----
In HTML mode, the ``#BUG`` macro expands to a hyperlink (``<a>`` element) to
the 'Bugs' page, or to a specific entry on that page. ::

  #BUG[#name][(link text)]

* ``#name`` is the named anchor of a bug (if linking to a specific one)
* ``link text`` is the link text to use

In HTML mode, if the link text is blank, the title of the bug entry (if linking
to a specific one) is substituted; if the link text is omitted entirely, 'bug'
is substituted.

In ASM mode, the ``#BUG`` macro expands to the link text, or 'bug' if the link
text is blank or omitted.

For example:

.. parsed-literal::
   :class: nonexistent

    42726 DEFB 130 ; This is a #BUG#bug1; it should be 188

In HTML mode, this instance of the ``#BUG`` macro expands to a hyperlink to an
entry on the 'Bugs' page.

In ASM mode, this instance of the ``#BUG`` macro expands to 'bug'.

See also :ref:`FACT` and :ref:`POKE`.

+---------+-----------------------------------------------------------------+
| Version | Changes                                                         |
+=========+=================================================================+
| 2.3.1   | If left blank, the link text defaults to the bug entry title in |
|         | HTML mode                                                       |
+---------+-----------------------------------------------------------------+

.. _CALL:

#CALL
-----
In HTML mode, the ``#CALL`` macro expands to the return value of a method on
the `HtmlWriter` class or subclass that is being used to create the HTML
disassembly (as defined by the ``HtmlWriterClass`` parameter in the
:ref:`ref-Config` section of the `ref` file).

In ASM mode, the ``#CALL`` macro expands to the return value of a method on the
`AsmWriter` class or subclass that is being used to generate the ASM output (as
defined by the :ref:`writer` ASM directive in the `skool` file). ::

  #CALL:methodName(args)

* ``methodName`` is the name of the method to call
* ``args`` is a comma-separated list of arguments to pass to the method

For example::

  ; The byte at address 32768 is #CALL:peek(32768).

This instance of the ``#CALL`` macro expands to the return value of the `peek`
method (on the `HtmlWriter` or `AsmWriter` subclass being used) when called
with the argument ``32768``.

For information on writing methods that may be called by a ``#CALL`` macro, see
the documentation on :ref:`extending SkoolKit <extendingSkoolKit>`.

+---------+----------------------------+
| Version | Changes                    |
+=========+============================+
| 2.1     | New                        |
+---------+----------------------------+
| 3.1     | Added support for ASM mode |
+---------+----------------------------+

.. _CHR:

#CHR
----
In HTML mode, the ``#CHR`` macro expands to a numeric character reference
(``&#num;``). In ASM mode, it expands to a unicode character in the UTF-8
encoding. ::

  #CHRnum

or::

  #CHR(num)

For example:

.. parsed-literal::
   :class: nonexistent

    26751 DEFB 127   ; This is the copyright symbol: #CHR169

In HTML mode, this instance of the ``#CHR`` macro expands to ``&#169;``. In ASM
mode, it expands to the copyright symbol.

+---------+---------+
| Version | Changes |
+=========+=========+
| 3.1     | New     |
+---------+---------+

.. _D:

#D
--
The ``#D`` (Description) macro expands to the title of an entry (a routine or
data block) in the memory map. ::

  #Daddr

* ``addr`` is the address of the entry.

For example::

  ; Now we make an indirect jump to one of the following routines:
  ; .
  ; #TABLE(default,centre)
  ; { =h Address | =h Description }
  ; { #R27126    | #D27126 }

This instance of the ``#D`` macro expands to the title of the routine at 27126.

.. _EREFS:

#EREFS
------
The ``#EREFS`` (Entry point REFerenceS) macro expands to a comma-separated
sequence of hyperlinks to (in HTML mode) or addresses of (in ASM mode) the
routines that jump to or call a given address. ::

  #EREFSaddr

* ``addr`` is the address to search for references to

See also :ref:`m-REFS`.

+---------+----------------------------+
| Version | Changes                    |
+=========+============================+
| 3.1     | Added support for ASM mode |
+---------+----------------------------+

.. _FACT:

#FACT
-----
In HTML mode, the ``#FACT`` macro expands to a hyperlink (``<a>`` element) to
the 'Trivia' page, or to a specific entry on that page. ::

  #FACT[#name][(link text)]

* ``#name`` is the named anchor of a trivia entry (if linking to a specific
  one)
* ``link text`` is the link text to use

In HTML mode, if the link text is blank, the title of the trivia entry (if
linking to a specific one) is substituted; if the link text is omitted
entirely, 'fact' is substituted.

In ASM mode, the ``#FACT`` macro expands to the link text, or 'fact' if the
link text is blank or omitted.

For example::

  See the trivia entry #FACT#interestingFact() for details.

In HTML mode, this instance of the ``#FACT`` macro expands to a hyperlink to
an entry on the 'Trivia' page, with link text equal to the title of the entry.

See also :ref:`BUG` and :ref:`POKE`.

+---------+-----------------------------------------------------------------+
| Version | Changes                                                         |
+=========+=================================================================+
| 2.3.1   | If left blank, the link text defaults to the trivia entry title |
|         | in HTML mode; added support for ASM mode                        |
+---------+-----------------------------------------------------------------+

.. _FONT:

#FONT
-----
In HTML mode, the ``#FONT`` macro expands to an ``<img>`` element for an image
of the game font. ::

  #FONTaddr,chars[,attr,scale][{X,Y,W,H}][(fname)]

* ``addr`` is the base address of the font graphic data
* ``chars`` is the number of characters in the font
* ``attr`` is the attribute byte to use (default: 56)
* ``scale`` is the required scale of the image (default: 2)
* ``X`` is the x-coordinate of the leftmost pixel column of the constructed
  image to include in the final image (if greater than 0, the image will be
  cropped on the left)
* ``Y`` is the y-coordinate of the topmost pixel row of the constructed image
  to include in the final image (if greater than 0, the image will be cropped
  on the top)
* ``W`` is the width of the final image (if less than the full width of the
  constructed image, the image will be cropped on the right)
* ``H`` is the height of the final image (if less than the full height of the
  constructed image, the image will be cropped on the bottom)
* ``fname`` is the name of the image file (default: '`font`'); '`.png`' or
  '`.gif`' will be appended (depending on the default image format specified in
  the :ref:`ref-ImageWriter` section of the `ref` file) if not present

The ``#FONT`` macro is not supported in ASM mode.

If an image with the given filename doesn't already exist, it will be created.
If ``fname`` starts with a '/', the filename is taken to be relative to the
root of the HTML disassembly; otherwise the filename is taken to be relative to
the directory defined by the ``FontImagePath`` parameter in the :ref:`paths`
section of the `ref` file.

For example::

  ; Font graphic data
  ;
  ; #HTML(#FONT49152,32)

In HTML mode, this instance of the ``#FONT`` macro expands to an ``<img>``
element for the image of the 32 characters in the 8*8 font whose graphic data
starts at 49152.

+---------+-----------------------------------------------------------------+
| Version | Changes                                                         |
+=========+=================================================================+
| 2.0.5   | Added the ``fname`` parameter and support for regular 8x8 fonts |
+---------+-----------------------------------------------------------------+
| 3.0     | Added image-cropping capabilities                               |
+---------+-----------------------------------------------------------------+

.. _HTML:

#HTML
-----
The ``#HTML`` macro expands to arbitrary text (in HTML mode) or to an empty
string (in ASM mode). ::

  #HTML(text)

The ``#HTML`` macro may be used to render HTML (which would otherwise be
escaped) from a `skool` file. For example::

  ; #HTML(For more information, go <a href="http://example.com/">here</a>.)

If ``text`` contains a closing bracket - ``)`` - then the macro will not expand
as required. In that case, square brackets, braces or any character that does
not appear in ``text`` (except for an upper case letter) may be used as
delimiters::

  #HTML[text]
  #HTML{text}
  #HTML@text@

``text`` may contain other skool macros, which will be expanded before
rendering. For example::

  ; #HTML[The UDG defined here (32768) looks like this: #UDG32768,4,1]

See also :ref:`UDGTABLE`.

+---------+---------+
| Version | Changes |
+=========+=========+
| 3.1.2   | New     |
+---------+---------+

.. _LINK:

#LINK
-----
In HTML mode, the ``#LINK`` macro expands to a hyperlink (``<a>`` element) to
another page. ::

  #LINK:PageId[#name](link text)

* ``PageId`` is the ID of the page to link to
* ``name`` is the name of an anchor on the page to link to
* ``link text`` is the link text to use

In HTML mode, if the link text is blank, the page's link text (as defined in
the :ref:`links` section or the relevant :ref:`page` section of the `ref` file)
is substituted.

In ASM mode, the ``#LINK`` macro expands to the link text.

The page IDs that may be used are the same as the file IDs that may be used in
the :ref:`paths` section of a `ref` file, or the page IDs defined by
:ref:`page` sections.

For example::

  ; See the #LINK:Glossary(glossary) for a definition of 'chuntey'.

In HTML mode, this instance of the ``#LINK`` macro expands to a hyperlink to
the 'Glossary' page, with link text 'glossary'.

In ASM mode, this instance of the ``#LINK`` macro expands to 'glossary'.

+---------+------------------------------------------------------------------+
| Version | Changes                                                          |
+=========+==================================================================+
| 2.1     | New                                                              |
+---------+------------------------------------------------------------------+
| 3.1.3   | If left blank, the link text defaults to the page's link text in |
|         | HTML mode                                                        |
+---------+------------------------------------------------------------------+

.. _LIST:

#LIST
-----
The ``#LIST`` macro marks the beginning of a list of bulleted items; ``LIST#``
is used to mark the end. Between these markers, the list items are defined. ::

  #LIST[(class)]<items>LIST#

* ``class`` is the CSS class to use for the ``<ul>`` element

Each item in a list must start with ``{`` followed by a whitespace character,
and end with ``}`` preceded by a whitespace character.

For example::

  ; #LIST(data)
  ; { Item 1 }
  ; { Item 2 }
  ; LIST#

This list has two items, and will have the CSS class 'data'.

In ASM mode, lists are rendered as plain text, with each item on its own line,
and an asterisk as the bullet character. The bullet character can be changed by
using a :ref:`set` directive to set the ``bullet`` property on the ASM writer.

+---------+---------+
| Version | Changes |
+=========+=========+
| 3.2     | New     |
+---------+---------+

.. _POKE:

#POKE
-----
In HTML mode, the ``#POKE`` macro expands to a hyperlink (``<a>`` element) to
the 'Pokes' page, or to a specific entry on that page. ::

  #POKE[#name][(link text)]

* ``#name`` is the named anchor of a poke (if linking to a specific one)
* ``link text`` is the link text to use

In HTML mode, if the link text is blank, the title of the poke entry (if
linking to a specific one) is substituted; if the link text is omitted
entirely, 'poke' is substituted.

In ASM mode, the ``#POKE`` macro expands to the link text, or 'poke' if the
link text is blank or omitted.

For example::

  ; Of course, if you feel like cheating, you can always give yourself
  ; #POKE#infiniteLives(infinite lives).

In HTML mode, this instance of the ``#POKE`` macro expands to a hyperlink to
an entry on the 'Pokes' page, with link text 'infinite lives'.

In ASM mode, this instance of the ``#POKE`` macro expands to 'infinite lives'.

See also :ref:`BUG` and :ref:`FACT`.

+---------+------------------------------------------------------------------+
| Version | Changes                                                          |
+=========+==================================================================+
| 2.3.1   | If left blank, the link text defaults to the poke entry title in |
|         | HTML mode; added support for ASM mode                            |
+---------+------------------------------------------------------------------+

.. _POKES:

#POKES
------
The ``#POKES`` (POKE Snapshot) macro POKEs values into the current memory
snapshot. ::

  #POKESaddr,byte[,length,step][;addr,byte[,length,step];...]

* ``addr`` is the address to POKE
* ``byte`` is the value to POKE ``addr`` with
* ``length`` is the number of addresses to POKE (default: 1)
* ``step`` is the address increment to use after each POKE (if ``length``>1;
  default: 1)

For example::

  The UDG looks like this:

  #UDG32768(udg_orig)

  But it's supposed to look like this:

  #PUSHS
  #POKES32772,254;32775,136
  #UDG32768(udg_fixed)
  #POPS

This instance of the ``#POKES`` macro does ``POKE 32772,254`` and
``POKE 32775,136``, which fixes a graphic glitch in the UDG at 32768.

The ``#POKES`` macro expands to an empty string.

See also :ref:`PUSHS` and :ref:`POPS`.

+---------+--------------------------------------+
| Version | Changes                              |
+=========+======================================+
| 2.3.1   | Added support for multiple addresses |
+---------+--------------------------------------+
| 3.1     | Added support for ASM mode           |
+---------+--------------------------------------+

.. _POPS:

#POPS
-----
The ``#POPS`` (POP Snapshot) macro removes the current memory snapshot and
replaces it with the one that was previously saved by a ``#PUSHS`` macro. ::

  #POPS

The ``#POPS`` macro expands to an empty string.

See also :ref:`PUSHS` and :ref:`POKES`.

+---------+----------------------------+
| Version | Changes                    |
+=========+============================+
| 3.1     | Added support for ASM mode |
+---------+----------------------------+

.. _PUSHS:

#PUSHS
------
As a `skool` file is being parsed, a memory snapshot is built up from all the
``DEFB``, ``DEFW``, ``DEFM`` and ``DEFS`` instructions. After the file has been
parsed, the memory snapshot may be used to build images of the game's graphic
elements (for example).

The ``#PUSHS`` (PUSH Snapshot) macro saves the current snapshot, and replaces
it with an identical copy with a given name. ::

  #PUSHS[name]

* ``name`` is the snapshot name (defaults to an empty string)

The new snapshot may then be modified by using the ``#POKES`` macro.

For example::

  The UDG at 32768 is supposed to look like this:

  #PUSHS
  #POKES32772,254
  #UDG32768
  #POPS

The ``#PUSHS`` macro expands to an empty string.

See also :ref:`POKES` and :ref:`POPS`.

+---------+----------------------------+
| Version | Changes                    |
+=========+============================+
| 3.1     | Added support for ASM mode |
+---------+----------------------------+

.. _R:

#R
--
In HTML mode, the ``#R`` (Reference) macro expands to a hyperlink (``<a>``
element) to the disassembly page for a routine or data block, or to a line at a
given address within that page. ::

  #Raddr[@code][#name][(link text)]

* ``addr`` is the address of the routine or data block (or entry point
  thereof)
* ``code`` is the ID of the disassembly that contains the routine or data block
  (if not given, the current disassembly is assumed; otherwise this should be
  an ID defined in an ``[OtherCode:*]`` section of the ref file)
* ``#name`` is the named anchor of an item on the disassembly page
* ``link text`` is the link text to use (default: ``addr``)

In ASM mode, the ``#R`` macro expands to the link text if it is specified, or
to the label for ``addr``, or to ``addr`` if no label is found.

For example::

  ; Prepare for a new game
  ;
  ; Used by the routine at #R25820.

In HTML mode, this instance of the ``#R`` macro expands to a hyperlink to the
disassembly page for the routine at 25820.

In ASM mode, this instance of the ``#R`` macro expands to the label for the
routine at 25820 (or simply ``25820`` if that routine has no label).

+---------+------------------------------------------------------------------+
| Version | Changes                                                          |
+=========+==================================================================+
| 2.0     | Added support for the ``@code`` notation                         |
+---------+------------------------------------------------------------------+
| 3.5     | Added the ability to resolve (in HTML mode) the address of an    |
|         | entry point in another disassembly when an appropriate           |
|         | :ref:`remote entry <rEntry>` is defined                          |
+---------+------------------------------------------------------------------+

.. _m-REFS:

#REFS
-----
The ``#REFS`` (REFerenceS) macro expands to a comma-separated sequence of
hyperlinks to (in HTML mode) or addresses of (in ASM mode) the routines that
jump to or call a given routine, or jump to or call any entry point within that
routine. ::

  #REFSaddr[(prefix)]

* ``addr`` is the address of the routine to search for references to
* ``prefix`` is the text to display before the sequence of hyperlinks or
  addresses if there is at least one reference (default: no text)

If there are no references, the macro expands to the following text::

  Not used directly by any other routines

See also :ref:`EREFS`.

+---------+--------------------------------+
| Version | Changes                        |
+=========+================================+
| 1.0.6   | Added the ``prefix`` parameter |
+---------+--------------------------------+
| 3.1     | Added support for ASM mode     |
+---------+--------------------------------+

.. _REG:

#REG
----
In HTML mode, the ``#REG`` (REGister) macro expands to a styled ``<span>``
element containing a register name. ::

  #REGreg

* ``reg`` is the name of the register (e.g. 'a', 'bc')

In ASM mode, the ``#REG`` macro expands to the name of the register.

The register name must contain 1, 2 or 3 of the following characters::

  abcdefhlirspxy'

For example:

.. parsed-literal::
   :class: nonexistent

    24623 LD C,31       ; #REGbc'=31

.. _SCR:

#SCR
----
In HTML mode, the ``#SCR`` (SCReenshot) macro expands to an ``<img>`` element
for an image constructed from the display file and attribute file (or suitably
arranged graphic data and attribute bytes elsewhere in memory) of the current
memory snapshot (in turn constructed from the contents of the `skool` file). ::

  #SCR[scale,x,y,w,h,dfAddr,afAddr][{X,Y,W,H}][(fname)]

* ``scale`` is the required scale of the image (default: 1)
* ``x`` is the x-coordinate of the top-left tile of the screen to include in
  the screenshot (default: 0)
* ``y`` is the y-coordinate of the top-left tile of the screen to include in
  the screenshot (default: 0)
* ``w`` is the width of the screenshot in tiles (default: 32)
* ``h`` is the height of the screenshot in tiles (default: 24)
* ``dfAddr`` is the base address of the display file (default: 16384)
* ``afAddr`` is the base address of the attribute file (default: 22528)
* ``X`` is the x-coordinate of the leftmost pixel column of the constructed
  image to include in the final image (if greater than 0, the image will be
  cropped on the left)
* ``Y`` is the y-coordinate of the topmost pixel row of the constructed image
  to include in the final image (if greater than 0, the image will be cropped
  on the top)
* ``W`` is the width of the final image (if less than the full width of the
  constructed image, the image will be cropped on the right)
* ``H`` is the height of the final image (if less than the full height of the
  constructed image, the image will be cropped on the bottom)
* ``fname`` is the name of the image file (default: '`scr`'); '`.png`' or
  '`.gif`' will be appended (depending on the default image format specified in
  the :ref:`ref-ImageWriter` section of the `ref` file) if not present

The ``#SCR`` macro is not supported in ASM mode.

If an image with the given filename doesn't already exist, it will be created.
If ``fname`` starts with a '/', the filename is taken to be relative to the
root of the HTML disassembly; otherwise the filename is taken to be relative to
the directory defined by the ``ScreenshotImagePath`` parameter in the
:ref:`paths` section of the `ref` file.

For example::

  ; #UDGTABLE
  ; { #SCR(loading) | This is the loading screen. }
  ; TABLE#

+---------+---------------------------------------------------------------+
| Version | Changes                                                       |
+=========+===============================================================+
| 2.0.5   | Added the ``scale``, ``x``, ``y``, ``w``, ``h`` and ``fname`` |
|         | parameters                                                    |
+---------+---------------------------------------------------------------+
| 3.0     | Added image-cropping capabilities and the ``dfAddr`` and      |
|         | ``afAddr`` parameters                                         |
+---------+---------------------------------------------------------------+

.. _SPACE:

#SPACE
------
The ``#SPACE`` macro expands to one or more ``&#160;`` expressions (in HTML
mode) or spaces (in ASM mode). ::

  #SPACE[num]

or::

  #SPACE([num])

* ``num`` is the number of spaces required (default: 1)

For example::

  ; '#SPACE8' (8 spaces)
  t56832 DEFM "        "

In HTML mode, this instance of the ``#SPACE`` macro expands to::

  &#160;&#160;&#160;&#160;&#160;&#160;&#160;&#160;

In ASM mode, this instance of the ``#SPACE`` macro expands to a string
containing 8 spaces.

The form ``SPACE([num])`` may be used to distinguish the macro from adjacent
text where necessary. For example::

  ; 'Score:#SPACE(5)0'
  t49152 DEFM "Score:     0"

+---------+------------------------------------------------+
| Version | Changes                                        |
+=========+================================================+
| 2.4.1   | Added support for the ``#SPACE([num])`` syntax |
+---------+------------------------------------------------+

.. _TABLE:

#TABLE
------
The ``#TABLE`` macro marks the beginning of a table; ``TABLE#`` is used to mark
the end. Between these markers, the rows of the table are defined. ::

  #TABLE[([class[,class1[:w][,class2[:w]...]]])]<rows>TABLE#

* ``class`` is the CSS class to use for the ``<table>`` element
* ``class1``, ``class2`` etc. are the CSS classes to use for the ``<td>``
  elements in columns 1, 2 etc.

Each row in a table must start with ``{`` followed by a whitespace character,
and end with ``}`` preceded by a whitespace character. The cells in a row must
be separated by ``|`` with a whitespace character on each side.

For example::

  ; #TABLE(default,centre)
  ; { 0 | Off }
  ; { 1 | On }
  ; TABLE#

This table has two rows and two columns, and will have the CSS class 'default'.
The cells in the first column will have the CSS class 'centre'.

By default, cells will be rendered as ``<td>`` elements. To specify that a
``<th>`` element should be used instead, use the ``=h`` indicator before the
cell contents::

  ; #TABLE
  ; { =h Header 1  | =h Header 2 }
  ; { Regular cell | Another one }
  ; TABLE#

It is also possible to specify ``colspan`` and ``rowspan`` attributes using the
``=c`` and ``=r`` indicators::

  ; #TABLE
  ; { =r2 2 rows  | X | Y }
  ; { =c2           2 columns }
  ; TABLE#

Finally, the ``=t`` indicator specifies that a cell should be transparent (i.e.
have the same background colour as the page body).

If a cell requires more than one indicator, the indicators should be separated
by commas::

  ; #TABLE
  ; { =h,c2 Wide header }
  ; { Column 1 | Column 2 }
  ; TABLE#

The CSS files included in SkoolKit provide two classes that may be used when
defining tables:

* ``default`` - a class for ``<table>`` elements that provides a background
  colour to make the table stand out from the page body
* ``centre`` - a class for ``<td>`` elements that centres their contents

In ASM mode, tables are rendered as plain text, using dashes (``-``) and pipes
(``|``) for the borders, and plus signs (``+``) where a horizontal border meets
a vertical border.

ASM mode also supports the ``:w`` indicator in the ``#TABLE`` macro's
parameters. The ``:w`` indicator marks a column as a candidate for having its
width reduced (by wrapping the text it contains) so that the table will be no
more than 79 characters wide when rendered. For example::

  ; #TABLE(default,centre,:w)
  ; { =h X | =h Description }
  ; { 0    | Text in this column will be wrapped in ASM mode to make the table less than 80 characters wide }
  ; TABLE#

See also :ref:`UDGTABLE`.

.. _UDG:

#UDG
----
In HTML mode, the ``#UDG`` macro expands to an ``<img>`` element for the image
of a UDG (an 8x8 block of pixels). ::

  #UDGaddr[,attr,scale,step,inc,flip,rotate][:maskAddr[,maskStep]][{X,Y,W,H}][(fname)]

* ``addr`` is the base address of the UDG bytes
* ``attr`` is the attribute byte to use (default: 56)
* ``scale`` is the required scale of the image (default: 4)
* ``step`` is the interval between successive bytes of the UDG (default: 1)
* ``inc`` will be added to each UDG byte before constructing the image
  (default: 0)
* ``flip`` is 1 to flip the UDG horizontally, 2 to flip it vertically, 3 to
  flip it both ways, or 0 to leave it as it is (default: 0)
* ``rotate`` is 1 to rotate the UDG 90 degrees clockwise, 2 to rotate it 180
  degrees, 3 to rotate it 90 degrees anticlockwise, or 0 to leave it as it is
  (default: 0)
* ``maskAddr`` is the base address of the mask bytes to use for the UDG
* ``maskStep`` is the interval between successive mask bytes (default:
  ``step``)
* ``X`` is the x-coordinate of the leftmost pixel column of the constructed
  image to include in the final image (if greater than 0, the image will be
  cropped on the left)
* ``Y`` is the y-coordinate of the topmost pixel row of the constructed image
  to include in the final image (if greater than 0, the image will be cropped
  on the top)
* ``W`` is the width of the final image (if less than the full width of the
  constructed image, the image will be cropped on the right)
* ``H`` is the height of the final image (if less than the full height of the
  constructed image, the image will be cropped on the bottom)
* ``fname`` is the name of the image file (if not given, a name based on
  ``addr``, ``attr`` and ``scale`` will be generated); '`.png`' or '`.gif`'
  will be appended (depending on the default image format specified in the
  :ref:`ref-ImageWriter` section of the `ref` file) if not present

The ``#UDG`` macro is not supported in ASM mode.

If an image with the given filename doesn't already exist, it will be created.
If ``fname`` starts with a '/', the filename is taken to be relative to the
root of the HTML disassembly; otherwise the filename is taken to be relative to
the directory defined by the ``UDGImagePath`` parameter in the :ref:`paths`
section of the `ref` file.

For example::

  ; Safe key UDG
  ;
  ; #HTML[#UDG39144,6(safe_key)]

In HTML mode, this instance of the ``#UDG`` macro expands to an ``<img>``
element for the image of the UDG at 39144 (which will be named `safe_key.png`
or `safe_key.gif`), with attribute byte 6 (INK 6: PAPER 0).

+---------+--------------------------------------+
| Version | Changes                              |
+=========+======================================+
| 2.0.5   | Added the ``fname`` parameter        |
+---------+--------------------------------------+
| 2.1     | Added support for masks              |
+---------+--------------------------------------+
| 2.3.1   | Added the ``flip`` parameter         |
+---------+--------------------------------------+
| 2.4     | Added the ``rotate`` parameter       |
+---------+--------------------------------------+
| 3.0     | Added image-cropping capabilities    |
+---------+--------------------------------------+
| 3.1.2   | Made the ``attr`` parameter optional |
+---------+--------------------------------------+

.. _UDGARRAY:

#UDGARRAY
---------
In HTML mode, the ``#UDGARRAY`` macro expands to an ``<img>`` element for the
image of an array of UDGs (8x8 blocks of pixels). ::

  #UDGARRAYwidth[,attr,scale,step,inc,flip,rotate];addr1[,attr1,step1,inc1][:maskAddr1[,maskStep1]];...[{X,Y,W,H}](fname)

* ``width`` is the width of the image (in UDGs)
* ``attr`` is the default attribute byte to use for each UDG (default: 56)
* ``scale`` is the required scale of the image (default: 2)
* ``step`` is the default interval between successive bytes of each UDG
  (default: 1)
* ``inc`` will be added to each UDG byte before constructing the image
  (default: 0)
* ``flip`` is 1 to flip the array of UDGs horizontally, 2 to flip it
  vertically, 3 to flip it both ways, or 0 to leave it as it is (default: 0)
* ``rotate`` is 1 to rotate the array of UDGs 90 degrees clockwise, 2 to rotate
  it 180 degrees, 3 to rotate it 90 degrees anticlockwise, or 0 to leave it as
  it is (default: 0)
* ``addr1`` is the address range specification for the first set of UDGs (see
  below)
* ``attr1`` is the attribute byte to use for each UDG in the set (overrides
  ``attr`` if specified)
* ``step1`` is the interval between successive bytes of each UDG in the set
  (overrides ``step`` if specified)
* ``inc1`` will be added to each byte of every UDG in the set before
  constructing the image (overrides ``inc`` if specified)
* ``maskAddr1`` is the address range specification for the first set of mask
  UDGs (see below)
* ``maskStep1`` is the interval between successive bytes of each mask UDG in
  the set (default: ``step1``)
* ``X`` is the x-coordinate of the leftmost pixel column of the constructed
  image to include in the final image (if greater than 0, the image will be
  cropped on the left)
* ``Y`` is the y-coordinate of the topmost pixel row of the constructed image
  to include in the final image (if greater than 0, the image will be cropped
  on the top)
* ``W`` is the width of the final image (if less than the full width of the
  constructed image, the image will be cropped on the right)
* ``H`` is the height of the final image (if less than the full height of the
  constructed image, the image will be cropped on the bottom)
* ``fname`` is the name of the image file; '`.png`' or '`.gif`' will be
  appended (depending on the default image format specified in the
  :ref:`ref-ImageWriter` section of the `ref` file) if not present

Address range specifications (``addr1``, ``maskAddr1`` etc.) may be given in
one of the following forms:

* a single address (e.g. ``39144``)
* a simple address range (e.g. ``33008-33015``)
* an address range with a step (e.g. ``32768-33792-256``)
* an address range with a horizontal and a vertical step (e.g.
  ``63476-63525-1-16``; this form specifies the step between the base addresses
  of adjacent UDGs in each row as 1, and the step between the base addresses of
  adjacent UDGs in each column as 16)

Any of these forms of address ranges can be repeated by appending ``xN``, where
``N`` is the desired number of repetitions. For example:

* ``39648x3`` is equivalent to ``39648;39648;39648``
* ``32768-32769x2`` is equivalent to ``32768;32769;32768;32769``

As many sets of UDGs as required may be specified, separated by semicolons;
the UDGs will be arranged in a rectangular array with the given width.

The ``#UDGARRAY`` macro is not supported in ASM mode.

If an image with the given filename doesn't already exist, it will be created.
If ``fname`` starts with a '/', the filename is taken to be relative to the
root of the HTML disassembly; otherwise the filename is taken to be relative to
the directory defined by the ``UDGImagePath`` parameter in the :ref:`paths`
section of the `ref` file.

For example::

  ; Base sprite
  ;
  ; #HTML[#UDGARRAY4;32768-32888-8(base_sprite.png)]

In HTML mode, this instance of the ``#UDGARRAY`` macro expands to an ``<img>``
element for the image of the 4x4 sprite formed by the 16 UDGs with base
addresses 32768, 32776, 32784 and so on up to 32888; the image file will be
named `base_sprite.png`.

+---------+-------------------------------------------------------------------+
| Version | Changes                                                           |
+=========+===================================================================+
| 2.0.5   | New                                                               |
+---------+-------------------------------------------------------------------+
| 2.2.5   | Added support for masks                                           |
+---------+-------------------------------------------------------------------+
| 2.3.1   | Added the ``flip`` parameter                                      |
+---------+-------------------------------------------------------------------+
| 2.4     | Added the ``rotate`` parameter                                    |
+---------+-------------------------------------------------------------------+
| 3.0     | Added image-cropping capabilities                                 |
+---------+-------------------------------------------------------------------+
| 3.1.1   | Added support for UDG address ranges with horizontal and vertical |
|         | steps                                                             |
+---------+-------------------------------------------------------------------+

.. _UDGTABLE:

#UDGTABLE
---------
The ``#UDGTABLE`` macro behaves in exactly the same way as the ``#TABLE``
macro, except that the resulting table will not be rendered in ASM mode. Its
intended use is to contain images that should be rendered in HTML mode only.

See :ref:`TABLE`, and also :ref:`HTML`.
