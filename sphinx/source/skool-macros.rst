.. _skoolMacros:

Skool macros
============
Skool files and ref files may contain skool macros that are 'expanded' to an
appropriate piece of HTML markup (when rendering in HTML mode), or to an
appropriate piece of plain text (when rendering in ASM mode).

Syntax
^^^^^^
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

  #UDG39144,56,4,1,0,0,0,1

and::

  #UDG30115,,2

is equivalent to::

  #UDG30115,56,2

.. _numericParameters:

Numeric parameters
^^^^^^^^^^^^^^^^^^
Numeric parameters may be written in decimal notation::

  #UDG51673,17

or in hexadecimal notation (prefixed by ``$``)::

  #UDG$C9D9,$11

Wherever a sequence of numeric parameters appears in a macro, that sequence
may optionally be enclosed in parentheses: ``(`` and ``)``. Parentheses are
`required` if any numeric parameter is written as an expression containing
arithmetic operations or skool macros::

  #UDG(51672+1,#PEEK51672)

The following operators are permitted in an arithmetic expression:

* arithmetic operators: ``+``, ``-``, ``*``, ``/``, ``%`` (modulo), ``**``
  (power)
* bitwise operators: ``&`` (AND), ``|`` (OR), ``^`` (XOR)
* bit shift operators: ``>>``, ``<<``
* Boolean operators: ``&&`` (and), ``||`` (or)
* comparison operators: ``==``, ``!=``, ``>``, ``<``, ``>=``, ``<=``

Parentheses and spaces are also permitted in an arithmetic expression::

  #IF(1 == 2 || (1 <= 2 && 2 < 3))(Yes,No)

The ``expr`` parameter of the :ref:`asm-if` directive and the :ref:`IF` macro,
and the ``key`` parameter of the :ref:`MAP` macro also recognise some
replacement fields:

* ``asm`` - 1 if in :ref:`isubMode`, 2 if in :ref:`ssubMode`, 3 if in
  :ref:`rsubMode`, or 0 otherwise
* ``base`` - 10 if the ``--decimal`` option is used with :ref:`skool2asm.py`
  or :ref:`skool2html.py`, 16 if the ``--hex`` option is used, or 0 if neither
  option is used
* ``case`` - 1 if the ``--lower`` option is used with :ref:`skool2asm.py`
  or :ref:`skool2html.py`, 2 if the ``--upper`` option is used, or 0 if neither
  option is used
* ``fix`` - 1 if in :ref:`ofixMode`, 2 if in :ref:`bfixMode`, 3 if in
  :ref:`rfixMode`, or 0 otherwise
* ``html`` - 1 if in HTML mode, 0 otherwise
* ``vars`` - a dictionary of variables defined by the ``--var`` option of
  :ref:`skool2asm.py` or :ref:`skool2html.py`; accessing an undefined variable
  in this dictionary yields the value '0'

For example::

  #IF({case}==1)(hl,HL)

expands to ``hl`` if in lower case mode, or ``HL`` otherwise.

Note that if a replacement field is used, the numeric parameter must be
enclosed in parentheses.

.. versionchanged:: 6.4
   The ``asm`` replacement field indicates the exact ASM mode; added the
   ``fix`` and ``vars`` replacement fields.

.. _stringParameters:

String parameters
^^^^^^^^^^^^^^^^^
Where a macro requires a single string parameter consisting of arbitrary text,
it must be enclosed in parentheses, square brackets or braces::

  (text)
  [text]
  {text}

If ``text`` contains unbalanced brackets, a non-whitespace character that is
not present in ``text`` may be used as an alternative delimiter. For example::

  /text/
  |text|

Where a macro requires multiple string parameters consisting of arbitrary text,
they must be enclosed in parentheses, square brackets or braces and be
separated by commas::

  (string1,string2)
  [string1,string2]
  {string1,string2}

When a comma-separated sequence of string parameters is split, any commas that
appear between parentheses are retained. For example, the string parameters
of the outer ``#FOR`` macro in::

  #FOR0,1(n,#FOR(0,1)(m,(n,m),;),;)

are split into ``n``, ``#FOR(0,1)(m,(n,m),;)`` and ``;``, and the string
parameters of the inner ``#FOR`` macro are split into ``m``, ``(n,m)``, and
``;``.

Alternatively, an arbitrary delimiter - ``d``, which cannot be whitespace - and
separator - ``s``, which can be whitespace - may be used. (They can be the same
character.) The string parameters must open with ``ds``, be separated by ``s``,
and close with ``sd``. For example::

  //same/delimiter/and/separator//
  | different delimiter and separator |

Note that if an alternative delimiter or separator is used, it must not be '&',
'<' or '>'.

.. versionchanged:: 6.4
   When a comma-separated sequence of string parameters is split, any commas
   that appear between parentheses are retained.

SMPL macros
^^^^^^^^^^^
The macros described in this section constitute the Skool Macro Programming
Language (SMPL). They can be used to programmatically specify values in the
parameter string of any macro.

.. _hash:

#()
---
The ``#()`` macro expands the skool macros in its sole string parameter. ::

  #(text)

It takes effect only when it immediately follows the opening token of another
skool macro, and is expanded `before` that macro. For example::

  #UDGARRAY#(2#FOR37159,37168,9||n|;(n+1),#PEEKn||)(item)

This instance of the ``#()`` macro expands the ``#FOR`` macro first, giving::

  2;(37159+1),#PEEK37159;(37168+1),#PEEK37168

It then expands the ``#PEEK`` macros, ultimately forming the parameters of the
``#UDGARRAY`` macro.

See :ref:`stringParameters` for details on alternative ways to supply the
``text`` parameter. Note that if an alternative delimiter is used, it must not
be an alphanumeric character (A-Z, a-z, 0-9).

.. _EVAL:

#EVAL
-----
The ``#EVAL`` macro expands to the value of an arithmetic expression. ::

  #EVALexpr[,base,width]

* ``expr`` is the arithmetic expression
* ``base`` is the number base in which the value is expressed: ``2``, ``10``
  (the default) or ``16``
* ``width`` is the minimum number of digits in the output (default: ``1``);
  the value will be padded with leading zeroes if necessary

For example::

  ; The following mask byte is #EVAL(#PEEK29435,2,8).
   29435 DEFB 62

This instance of the ``#EVAL`` macro expands to '00111110' (62 in binary).

+---------+--------------------------------------------------------+
| Version | Changes                                                |
+=========+========================================================+
| 6.0     | Hexadecimal values are rendered in lower case when the |
|         | ``--lower`` option is used                             |
+---------+--------------------------------------------------------+
| 5.1     | New                                                    |
+---------+--------------------------------------------------------+

.. _FOR:

#FOR
----
The ``#FOR`` macro expands to a sequence of strings based on a range of
integers. ::

  #FORstart,stop[,step](var,string[,sep,fsep])

* ``start`` is first integer in the range
* ``stop`` is the final integer in the range
* ``step`` is the gap between each integer in the range (default: ``1``)
* ``var`` is the variable name; for each integer in the range, it evaluates to
  that integer
* ``string`` is the output string that is evaluated for each integer in the
  range; wherever the variable name (``var``) appears, its value is substituted
* ``sep`` is the separator placed between each output string (default: the
  empty string)
* ``fsep`` is the separator placed between the final two output strings
  (default: ``sep``)

For example::

  ; The next three bytes (#FOR31734,31736||n|#PEEKn|, | and ||) define the
  ; item locations.
   31734 DEFB 24,17,156

This instance of the ``#FOR`` macro expands to '24, 17 and 156'.

See :ref:`stringParameters` for details on alternative ways to supply the
``var``, ``string``, ``sep`` and ``fsep`` parameters.

+---------+---------+
| Version | Changes |
+=========+=========+
| 5.1     | New     |
+---------+---------+

.. _FOREACH:

#FOREACH
--------

The ``#FOREACH`` macro expands to a sequence of output strings based on a
sequence of input strings. ::

  #FOREACH([s1,s2,...])(var,string[,sep,fsep])

or::

  #FOREACH(svar)(var,string[,sep,fsep])

* ``s1``, ``s2``  etc. are the input strings
* ``svar`` is a special variable that expands to a specific sequence of input
  strings (see below)
* ``var`` is the variable name; for each input string, it evaluates to that
  string
* ``string`` is the output string that is evaluated for each input string;
  wherever the variable name (``var``) appears, its value is substituted
* ``sep`` is the separator placed between each output string (default: the
  empty string)
* ``fsep`` is the separator placed between the final two output strings
  (default: ``sep``)

For example::

  ; The next three bytes (#FOREACH(31734,31735,31736)||n|#PEEKn|, | and ||)
  ; define the item locations.
   31734 DEFB 24,17,156

This instance of the ``#FOREACH`` macro expands to '24, 17 and 156'.

The ``#FOREACH`` macro recognises certain special variables, each one of which
expands to a specific sequence of strings. The special variables are:

* ``ENTRY[types]`` - the addresses of every entry of the specified type(s) in
  the memory map; if ``types`` is not given, every type is included
* ``EREFaddr`` - the addresses of the routines that jump to or call a given
  instruction (at ``addr``)
* ``REFaddr`` - the addresses of the routines that jump to or call a given
  routine (at ``addr``), or jump to or call any entry point within that routine

For example::

  ; The messages can be found at #FOREACH(ENTRYt)||n|n|, | and ||.

This instance of the ``#FOREACH`` macro expands to a list of the addresses of
the entries of type ``t`` (text).

See :ref:`stringParameters` for details on alternative ways to supply the
``var``, ``string``, ``sep`` and ``fsep`` parameters.

+---------+---------+
| Version | Changes |
+=========+=========+
| 5.1     | New     |
+---------+---------+

.. _IF:

#IF
---
The ``#IF`` macro expands to an arbitrary string based on the truth value of an
arithmetic expression. ::

  #IFexpr(true[,false])

* ``expr`` is the arithmetic expression
* ``true`` is the output string when ``expr`` is true
* ``false`` is the output string when ``expr`` is false (default: the empty
  string)

For example::

  ; #FOR0,7||n|#IF(#PEEK47134 & 2**(7-n))(X,O)||
   47134 DEFB 170

This instance of the ``#IF`` macro is used (in combination with a ``#FOR``
macro and a ``#PEEK`` macro) to display the contents of the address 47134 in
the memory snapshot in binary format with 'X' for one and 'O' for zero:
XOXOXOXO.

See :ref:`stringParameters` for details on alternative ways to supply the
``true`` and ``false`` output strings.

See :ref:`numericParameters` for details on the replacement fields that may be
used in the ``expr`` parameter.

+---------+----------------------------------------------------------------+
| Version | Changes                                                        |
+=========+================================================================+
| 6.0     | Added support for replacement fields in the ``expr`` parameter |
+---------+----------------------------------------------------------------+
| 5.1     | New                                                            |
+---------+----------------------------------------------------------------+

.. _MAP:

#MAP
----
The ``#MAP`` macro expands to a value from a map of key-value pairs whose keys
are integers. ::

  #MAPkey(default[,k1:v1,k2:v2...])

* ``key`` is the integer to look up in the map
* ``default`` is the default output string (used when ``key`` is not found in
  the map)
* ``k1:v1``, ``k2:v2`` etc. are the key-value pairs in the map

For example::

  ; The next three bytes specify the directions that are available from here:
  ; #FOR56112,56114||q|#MAP(#PEEKq)(?,0:left,1:right,2:up,3:down)|, | and ||.
   56112 DEFB 0,1,3

This instance of the ``#MAP`` macro is used (in combination with a ``#FOR``
macro and a ``#PEEK`` macro) to display a list of directions available based on
the contents of addresses 56112-56114: 'left, right and down'.

Note that the keys (``k1``, ``k2`` etc.) may be expressed using arithmetic
operations. They may also be expressed using skool macros, but in that case the
*entire* parameter string of the ``#MAP`` macro must be enclosed by a
:ref:`hash` macro.

See :ref:`stringParameters` for details on alternative ways to supply the
default output string and the key-value pairs.

See :ref:`numericParameters` for details on the replacement fields that may be
used in the ``key`` parameter.

+---------+---------------------------------------------------------------+
| Version | Changes                                                       |
+=========+===============================================================+
| 6.0     | Added support for replacement fields in the ``key`` parameter |
+---------+---------------------------------------------------------------+
| 5.1     | New                                                           |
+---------+---------------------------------------------------------------+

.. _PEEK:

#PEEK
-----
The ``#PEEK`` macro expands to the contents of an address in the memory
snapshot. ::

  #PEEKaddr

* ``addr`` is the address

For example::

  ; At the start of the game, the number of lives remaining is #PEEK33879.

This instance of the ``#PEEK`` macro expands to the contents of the address
33879 in the memory snapshot.

See also :ref:`POKES`.

+---------+---------+
| Version | Changes |
+=========+=========+
| 5.1     | New     |
+---------+---------+

General macros
^^^^^^^^^^^^^^

.. _CALL:

#CALL
-----
In HTML mode, the ``#CALL`` macro expands to the return value of a method on
the `HtmlWriter` class or subclass that is being used to create the HTML
disassembly (as defined by the ``HtmlWriterClass`` parameter in the
:ref:`ref-Config` section of the ref file).

In ASM mode, the ``#CALL`` macro expands to the return value of a method on the
`AsmWriter` class or subclass that is being used to generate the ASM output (as
defined by the :ref:`writer` ASM directive in the skool file). ::

  #CALL:methodName(args)

* ``methodName`` is the name of the method to call
* ``args`` is a comma-separated list of arguments to pass to the method

For example::

  ; The word at address 32768 is #CALL:word(32768).

This instance of the ``#CALL`` macro expands to the return value of the `word`
method (on the `HtmlWriter` or `AsmWriter` subclass being used) when called
with the argument ``32768``.

For information on writing methods that may be called by a ``#CALL`` macro, see
the documentation on :ref:`extending SkoolKit <extendingSkoolKit>`.

+---------+--------------------------------------------------------------+
| Version | Changes                                                      |
+=========+==============================================================+
| 5.1     | Added support for arithmetic expressions and skool macros in |
|         | numeric method arguments                                     |
+---------+--------------------------------------------------------------+
| 3.1     | Added support for ASM mode                                   |
+---------+--------------------------------------------------------------+
| 2.1     | New                                                          |
+---------+--------------------------------------------------------------+

.. _CHR:

#CHR
----
In HTML mode, the ``#CHR`` macro expands to a numeric character reference
(``&#num;``). In ASM mode, it expands to a unicode character in the UTF-8
encoding. ::

  #CHRnum

For example:

.. parsed-literal::
   :class: nonexistent

    26751 DEFB 127   ; This is the copyright symbol: #CHR169

In HTML mode, this instance of the ``#CHR`` macro expands to ``&#169;``. In ASM
mode, it expands to the copyright symbol.

+---------+------------------------------------------------------------------+
| Version | Changes                                                          |
+=========+==================================================================+
| 5.1     | Added support for arithmetic expressions and skool macros in the |
|         | ``num`` parameter                                                |
+---------+------------------------------------------------------------------+
| 3.1     | New                                                              |
+---------+------------------------------------------------------------------+

.. _D:

#D
--
The ``#D`` macro expands to the title of an entry (a routine or data block) in
the memory map. ::

  #Daddr

* ``addr`` is the address of the entry.

For example::

  ; Now we make an indirect jump to one of the following routines:
  ; .
  ; #TABLE(default,centre)
  ; { =h Address | =h Description }
  ; { #R27126    | #D27126 }

This instance of the ``#D`` macro expands to the title of the routine at 27126.

+---------+------------------------------------------------------------------+
| Version | Changes                                                          |
+=========+==================================================================+
| 5.1     | Added support for arithmetic expressions and skool macros in the |
|         | ``addr`` parameter                                               |
+---------+------------------------------------------------------------------+

.. _HTML:

#HTML
-----
The ``#HTML`` macro expands to arbitrary text (in HTML mode) or to an empty
string (in ASM mode). ::

  #HTML(text)

The ``#HTML`` macro may be used to render HTML (which would otherwise be
escaped) from a skool file. For example::

  ; #HTML(For more information, go <a href="http://example.com/">here</a>.)

``text`` may contain other skool macros, which will be expanded before
rendering. For example::

  ; #HTML[The UDG defined here (32768) looks like this: #UDG32768,4,1]

See :ref:`stringParameters` for details on alternative ways to supply the
``text`` parameter. Note that if an alternative delimiter is used, it must not
be an upper case letter.

See also :ref:`UDGTABLE`.

+---------+---------+
| Version | Changes |
+=========+=========+
| 3.1.2   | New     |
+---------+---------+

.. _INCLUDE:

#INCLUDE
--------
In HTML mode, the ``#INCLUDE`` macro expands to the contents of a ref file
section; in ASM mode, it expands to an empty string. ::

  #INCLUDE[paragraphs](section)

* ``paragraphs`` specifies how to format the contents of the ref file section:
  verbatim (``0`` - the default), or into paragraphs (``1``)
* ``section`` is the name of the ref file section

The ``#INCLUDE`` macro can be used to insert the contents of one ref file
section into another. For example::

  [MemoryMap:RoutinesMap]
  Intro=#INCLUDE(RoutinesMapIntro)

  [RoutinesMapIntro]
  This is the intro to the 'Routines' map page.

See :ref:`stringParameters` for details on alternative ways to supply the
``section`` parameter.

+---------+---------+
| Version | Changes |
+=========+=========+
| 5.3     | New     |
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

In HTML mode, if the link text is blank, it defaults either to the title of the
entry being linked to (if the page is a :ref:`box page <boxpages>` and contains
an entry with the specified anchor), or to the page's link text.

In ASM mode, the ``#LINK`` macro expands to the link text.

The page IDs that may be used are the same as the file IDs that may be used in
the :ref:`paths` section of a ref file, or the page IDs defined by :ref:`page`
sections.

For example::

  ; See the #LINK:Glossary(glossary) for a definition of 'chuntey'.

In HTML mode, this instance of the ``#LINK`` macro expands to a hyperlink to
the 'Glossary' page, with link text 'glossary'.

In ASM mode, this instance of the ``#LINK`` macro expands to 'glossary'.

To create a hyperlink to an entry on a memory map page, use the address of the
entry as the anchor. For example::

  ; Now we update the #LINK:GameStatusBuffer#40000(number of lives).

In HTML mode, the anchor of this ``#LINK`` macro (40000) is converted to the
format specified by the ``AddressAnchor`` parameter in the :ref:`ref-Game`
section.

+---------+------------------------------------------------------------------+
| Version | Changes                                                          |
+=========+==================================================================+
| 5.4     | When linking to an entry on a :ref:`box page <boxpages>`, the    |
|         | link text, if left blank, defaults to the title of the entry (in |
|         | HTML mode)                                                       |
+---------+------------------------------------------------------------------+
| 5.2     | An entry address anchor in a link to a memory map page is        |
|         | converted to the format specified by the ``AddressAnchor``       |
|         | parameter                                                        |
+---------+------------------------------------------------------------------+
| 3.1.3   | If left blank, the link text defaults to the page's link text in |
|         | HTML mode                                                        |
+---------+------------------------------------------------------------------+
| 2.1     | New                                                              |
+---------+------------------------------------------------------------------+

.. _LIST:

#LIST
-----
The ``#LIST`` macro marks the beginning of a list of bulleted items; ``LIST#``
is used to mark the end. Between these markers, the list items are defined. ::

  #LIST[(class[,bullet])][<flag>][items]LIST#

* ``class`` is the CSS class to use for the ``<ul>`` element
* ``bullet`` is the bullet character to use in ASM mode
* ``flag`` is the wrap flag (see below)

Each item in a list must start with ``{`` followed by a space, and end with
``}`` preceded by a space.

For example::

  ; #LIST(data)
  ; { Item 1 }
  ; { Item 2 }
  ; LIST#

This list has two items, and will have the CSS class 'data'.

In ASM mode, lists are rendered as plain text, with each item on its own line,
and an asterisk as the bullet character. The bullet character can be changed
for all lists by using a :ref:`set` directive to set the ``bullet`` property,
or it can be changed for a specific list by setting the ``bullet`` parameter.

The wrap flag (``flag``), if present, determines how :ref:`sna2skool.py` will
write list items when reading from a control file. Supported values are:

* ``nowrap`` - write each list item on a single line
* ``wrapalign`` - wrap each list item with an indent at the start of the second
  and subsequent lines to maintain text alignment with the first line

By default, each list item is wrapped over multiple lines with no indent.

+---------+-------------------------------------------------------------------+
| Version | Changes                                                           |
+=========+===================================================================+
| 7.2     | ``#LIST`` can be used in register descriptions in ASM mode        |
+---------+-------------------------------------------------------------------+
| 7.0     | Added the ``nowrap`` and ``wrapalign`` flags                      |
+---------+-------------------------------------------------------------------+
| 6.4     | In ASM mode: ``#LIST`` can be used in an instruction-level        |
|         | comment and as a parameter of another macro; if the bullet        |
|         | character is an empty string, list items are no longer indented   |
|         | by one space; added the ``bullet`` parameter                      |
+---------+-------------------------------------------------------------------+
| 3.2     | New                                                               |
+---------+-------------------------------------------------------------------+

.. _N:

#N
--
The ``#N`` macro renders a numeric value in either decimal or hexadecimal
format depending on the options used with :ref:`skool2asm.py` or
:ref:`skool2html.py`. A hexadecimal number is rendered in lower case when the
``--lower`` option is used, or in upper case otherwise. ::

  #Nvalue[,hwidth,dwidth,affix,hex][(prefix[,suffix])]

* ``value`` is the numeric value
* ``hwidth`` is the minimum number of digits printed in hexadecimal output
  (default: 2 for values < 256, or 4 otherwise)
* ``dwidth`` is the minimum number of digits printed in decimal output
  (default: 1)
* ``affix`` is 1 if ``prefix`` or ``suffix`` is specified, 0 if not (default:
  0)
* ``hex`` is 1 to render the value in hexadecimal format unless the
  ``--decimal`` option is used, or 0 to render it in decimal format unless the
  ``--hex`` option is used (default: 0)
* ``prefix`` is the prefix for a hexadecimal number (default: empty string)
* ``suffix`` is the suffix for a hexadecimal number (default: empty string)

For example::

  #N15,4,5,1(0x)

This instance of the ``#N`` macro expands to one of the following:

* ``00015`` (when ``--hex`` is not used)
* ``0x000F`` (when ``--hex`` is used without ``--lower``)
* ``0x000f`` (when both ``--hex`` and ``--lower`` are used)

See :ref:`stringParameters` for details on alternative ways to supply the
``prefix`` and ``suffix`` parameters.

+---------+-------------------------------------------------------------------+
| Version | Changes                                                           |
+=========+===================================================================+
| 6.2     | Added the ``hex`` parameter                                       |
+---------+-------------------------------------------------------------------+
| 5.2     | New                                                               |
+---------+-------------------------------------------------------------------+

.. _R:

#R
--
In HTML mode, the ``#R`` macro expands to a hyperlink (``<a>`` element) to the
disassembly page for a routine or data block, or to a line at a given address
within that page. ::

  #Raddr[@code][#name][(link text)]

* ``addr`` is the address of the routine or data block (or entry point
  thereof)
* ``code`` is the ID of the disassembly that contains the routine or data block
  (if not given, the current disassembly is assumed; otherwise this must be an
  ID defined in an :ref:`otherCode` section of the ref file)
* ``#name`` is the named anchor of an item on the disassembly page
* ``link text`` is the link text to use (default: ``addr``)

The disassembly ID (``code``) and anchor name (``name``) must be limited to the
characters '$', '#', 0-9, A-Z and a-z.

In ASM mode, the ``#R`` macro expands to the link text if it is specified, or
to the label for ``addr``, or to ``addr`` (converted to decimal or hexadecimal
as appropriate) if no label is found.

For example::

  ; Prepare for a new game
  ;
  ; Used by the routine at #R25820.

In HTML mode, this instance of the ``#R`` macro expands to a hyperlink to the
disassembly page for the routine at 25820.

In ASM mode, this instance of the ``#R`` macro expands to the label for the
routine at 25820 (or simply ``25820`` if that routine has no label).

To create a hyperlink to the first instruction in a routine or data block, use
an anchor that evaluates to the address of that instruction. For example::

  ; See the #R40000#40000(first item) in the data table at 40000.

In HTML mode, the anchor of this ``#R`` macro (40000) is converted to the
format specified by the ``AddressAnchor`` parameter in the :ref:`ref-Game`
section.

+---------+-----------------------------------------------------------------+
| Version | Changes                                                         |
+=========+=================================================================+
| 6.1     | In ASM mode, ``addr`` is converted to decimal or hexadecimal as |
|         | appropriate even when it refers to an unavailable instruction   |
+---------+-----------------------------------------------------------------+
| 5.1     | An anchor that matches the entry address is converted to the    |
|         | format specified by the ``AddressAnchor`` parameter; added      |
|         | support for arithmetic expressions and skool macros in the      |
|         | ``addr`` parameter                                              |
+---------+-----------------------------------------------------------------+
| 3.5     | Added the ability to resolve (in HTML mode) the address of an   |
|         | entry point in another disassembly when an appropriate          |
|         | :ref:`remote entry <remote>` is defined                         |
+---------+-----------------------------------------------------------------+
| 2.0     | Added support for the ``@code`` notation                        |
+---------+-----------------------------------------------------------------+

.. _RAW:

#RAW
----
The ``#RAW`` macro expands to the exact value of its sole string argument,
leaving any other macros (or macro-like tokens) it contains unexpanded. ::

  #RAW(text)

For example::

  ; See the routine at #RAW(#BEEF).

This instance of the ``#RAW`` macro expands to '#BEEF'.

See :ref:`stringParameters` for details on alternative ways to supply the
``text`` parameter. Note that if an alternative delimiter is used, it must not
be an upper case letter.

+---------+---------+
| Version | Changes |
+=========+=========+
| 6.4     | New     |
+---------+---------+

.. _REG:

#REG
----
In HTML mode, the ``#REG`` macro expands to a styled ``<span>`` element
containing a register name or arbitrary text (with case adjusted as
appropriate). ::

  #REGreg

where ``reg`` is the name of the register, or::

  #REG(text)

where ``text`` is arbitrary text (e.g. ``hlh'l'``).

See :ref:`stringParameters` for details on alternative ways to supply the
``text`` parameter. Note that if an alternative delimiter is used, it must not
be a letter.

In ASM mode, the ``#REG`` macro expands to either ``reg`` or ``text`` (with
case adjusted as appropriate).

The register name (``reg``) must be one of the following::

  a b c d e f h l
  a' b' c' d' e' f' h' l'
  af bc de hl
  af' bc' de' hl'
  ix iy ixh iyh ixl iyl
  i r sp pc

For example:

.. parsed-literal::
   :class: nonexistent

    24623 LD C,31       ; #REGbc'=31

+---------+-----------------------------------------------------+
| Version | Changes                                             |
+=========+=====================================================+
| 5.4     | Added support for an arbitrary text parameter       |
+---------+-----------------------------------------------------+
| 5.3     | Added support for the F and F' registers            |
+---------+-----------------------------------------------------+
| 5.1     | The ``reg`` parameter must be a valid register name |
+---------+-----------------------------------------------------+

.. _SPACE:

#SPACE
------
The ``#SPACE`` macro expands to one or more ``&#160;`` expressions (in HTML
mode) or spaces (in ASM mode). ::

  #SPACE[num]

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

+---------+------------------------------------------------------------------+
| Version | Changes                                                          |
+=========+==================================================================+
| 5.1     | Added support for arithmetic expressions and skool macros in the |
|         | ``num`` parameter                                                |
+---------+------------------------------------------------------------------+
| 2.4.1   | Added support for the ``#SPACE([num])`` syntax                   |
+---------+------------------------------------------------------------------+

.. _TABLE:

#TABLE
------
The ``#TABLE`` macro marks the beginning of a table; ``TABLE#`` is used to mark
the end. Between these markers, the rows of the table are defined. ::

  #TABLE[([class[,class1[:w][,class2[:w]...]]])][<flag>][rows]TABLE#

* ``class`` is the CSS class to use for the ``<table>`` element
* ``class1``, ``class2`` etc. are the CSS classes to use for the ``<td>``
  elements in columns 1, 2 etc.
* ``flag`` is the wrap flag (see below)

Each row in a table must start with ``{`` followed by a space, and end with
``}`` preceded by a space. The cells in a row must be separated by ``|`` with a
space on each side.

For example::

  ; #TABLE(default,centre)
  ; { 0 | Off }
  ; { 1 | On }
  ; TABLE#

This table has two rows and two columns, and will have the CSS class 'default'.
The cells in the first column will have the CSS class 'centre'.

By default, cells will be rendered as ``<td>`` elements. To render a cell as a
``<th>`` element, use the ``=h`` indicator before the cell contents::

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

Finally, the ``=t`` indicator makes a cell transparent (i.e. gives it the same
background colour as the page body).

If a cell requires more than one indicator, separate the indicators by commas::

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

The wrap flag (``flag``), if present, determines how :ref:`sna2skool.py` will
write table rows when reading from a control file. Supported values are:

* ``nowrap`` - write each table row on a single line
* ``wrapalign`` - wrap each table row with an indent at the start of the second
  and subsequent lines to maintain text alignment with the rightmost column on
  the first line

By default, each table row is wrapped over multiple lines with no indent.

See also :ref:`UDGTABLE`.

+---------+-------------------------------------------------------------------+
| Version | Changes                                                           |
+=========+===================================================================+
| 7.2     | ``#TABLE`` can be used in register descriptions in ASM mode       |
+---------+-------------------------------------------------------------------+
| 7.0     | Added the ``nowrap`` and ``wrapalign`` flags                      |
+---------+-------------------------------------------------------------------+
| 6.4     | In ASM mode, ``#TABLE`` can be used in an instruction-level       |
|         | comment and as a parameter of another macro                       |
+---------+-------------------------------------------------------------------+

.. _UDGTABLE:

#UDGTABLE
---------
The ``#UDGTABLE`` macro behaves in exactly the same way as the ``#TABLE``
macro, except that the resulting table will not be rendered in ASM mode. Its
intended use is to contain images that will be rendered in HTML mode only.

See :ref:`TABLE`, and also :ref:`HTML`.

.. _VERSION:

#VERSION
--------
The ``#VERSION`` macro expands to the version of SkoolKit. ::

  #VERSION

+---------+---------+
| Version | Changes |
+=========+=========+
| 6.0     | New     |
+---------+---------+

.. _imageMacros:

Image macros
^^^^^^^^^^^^
The :ref:`FONT`, :ref:`SCR`, :ref:`UDG` and :ref:`UDGARRAY` macros (described
in the following sections) may be used to create images based on graphic data
in the memory snapshot. They are not supported in ASM mode.

These macros have several numeric parameters, most of which are optional. This
can give rise to a long sequence of commas in a macro parameter string, making
it hard to read (and write); for example::

  #UDG32768,,,,,,1

To alleviate this problem, the image macros accept keyword arguments at any
position in the parameter string; the ``#UDG`` macro above could be rewritten
as follows::

  #UDG32768,rotate=1

.. _FONT:

#FONT
-----
In HTML mode, the ``#FONT`` macro expands to an ``<img>`` element for an image
of text rendered in the game font. ::

  #FONT[:(text)]addr[,chars,attr,scale][{CROP}][(fname)]

* ``text`` is the text to render (default: the 96 characters from code 32 to
  code 127)
* ``addr`` is the base address of the font graphic data
* ``chars`` is the number of characters to render (default: the length of
  ``text``)
* ``attr`` is the attribute byte to use (default: 56)
* ``scale`` is the scale of the image (default: 2)
* ``CROP`` is the cropping specification (see :ref:`cropping`)
* ``fname`` is the name of the image file (default: '`font`')

If ``fname`` contains an image path ID replacement field (e.g.
``{ScreenshotImagePath}/font``), the corresponding parameter value from the
:ref:`Paths` section will be substituted.

If ``fname`` starts with a '/', the filename is taken to be relative to the
root of the HTML disassembly.

If ``fname`` contains no image path ID replacement fields and does not start
with a '/', the filename is taken to be relative to the directory defined by
the ``FontImagePath`` parameter in the :ref:`paths` section.

If ``fname`` does not end with '`.png`' or '`.gif`', that suffix (depending on
the default image format specified in the :ref:`ref-ImageWriter` section of the
ref file) will be appended.

If an image with the given filename doesn't already exist, it will be created.

For example::

  ; Font graphic data
  ;
  ; #HTML[#FONT:(0123456789)49152]

In HTML mode, this instance of the ``#FONT`` macro expands to an ``<img>``
element for the image of the digits 0-9 in the 8x8 font whose graphic data
starts at 49152.

See :ref:`stringParameters` for details on alternative ways to supply the
``text`` parameter.

.. note::
   Support for GIF images is deprecated since version 7.2. Use PNG images
   instead.

+---------+------------------------------------------------------------------+
| Version | Changes                                                          |
+=========+==================================================================+
| 6.3     | Added support for image path ID replacement fields in the        |
|         | ``fname`` parameter                                              |
+---------+------------------------------------------------------------------+
| 5.1     | Added support for arithmetic expressions and skool macros in the |
|         | numeric parameters                                               |
+---------+------------------------------------------------------------------+
| 4.3     | Added the ability to create frames                               |
+---------+------------------------------------------------------------------+
| 4.2     | Added the ability to specify alt text for the ``<img>`` element  |
+---------+------------------------------------------------------------------+
| 4.0     | Added support for keyword arguments                              |
+---------+------------------------------------------------------------------+
| 3.6     | Added the ``text`` parameter, and made the ``chars`` parameter   |
|         | optional                                                         |
+---------+------------------------------------------------------------------+
| 3.0     | Added image-cropping capabilities                                |
+---------+------------------------------------------------------------------+
| 2.0.5   | Added the ``fname`` parameter and support for regular 8x8 fonts  |
+---------+------------------------------------------------------------------+

.. _SCR:

#SCR
----
In HTML mode, the ``#SCR`` macro expands to an ``<img>`` element for an image
constructed from the display file and attribute file (or suitably arranged
graphic data and attribute bytes elsewhere in memory) of the current memory
snapshot (in turn constructed from the contents of the skool file). ::

  #SCR[scale,x,y,w,h,df,af][{CROP}][(fname)]

* ``scale`` is the scale of the image (default: 1)
* ``x`` is the x-coordinate of the top-left tile of the screen to include in
  the screenshot (default: 0)
* ``y`` is the y-coordinate of the top-left tile of the screen to include in
  the screenshot (default: 0)
* ``w`` is the width of the screenshot in tiles (default: 32)
* ``h`` is the height of the screenshot in tiles (default: 24)
* ``df`` is the base address of the display file (default: 16384)
* ``af`` is the base address of the attribute file (default: 22528)
* ``CROP`` is the cropping specification (see :ref:`cropping`)
* ``fname`` is the name of the image file (default: '`scr`')

If ``fname`` contains an image path ID replacement field (e.g.
``{UDGImagePath}/scr``), the corresponding parameter value from the
:ref:`Paths` section will be substituted.

If ``fname`` starts with a '/', the filename is taken to be relative to the
root of the HTML disassembly.

If ``fname`` contains no image path ID replacement fields and does not start
with a '/', the filename is taken to be relative to the directory defined by
the ``ScreenshotImagePath`` parameter in the :ref:`paths` section.

If ``fname`` does not end with '`.png`' or '`.gif`', that suffix (depending on
the default image format specified in the :ref:`ref-ImageWriter` section of the
ref file) will be appended.

If an image with the given filename doesn't already exist, it will be created.

For example::

  ; #UDGTABLE
  ; { #SCR(loading) | This is the loading screen. }
  ; TABLE#

.. note::
   Support for GIF images is deprecated since version 7.2. Use PNG images
   instead.

+---------+------------------------------------------------------------------+
| Version | Changes                                                          |
+=========+==================================================================+
| 6.3     | Added support for image path ID replacement fields in the        |
|         | ``fname`` parameter                                              |
+---------+------------------------------------------------------------------+
| 5.1     | Added support for arithmetic expressions and skool macros in the |
|         | numeric parameters                                               |
+---------+------------------------------------------------------------------+
| 4.3     | Added the ability to create frames                               |
+---------+------------------------------------------------------------------+
| 4.2     | Added the ability to specify alt text for the ``<img>`` element  |
+---------+------------------------------------------------------------------+
| 4.0     | Added support for keyword arguments                              |
+---------+------------------------------------------------------------------+
| 3.0     | Added image-cropping capabilities and the ``df`` and ``af``      |
|         | parameters                                                       |
+---------+------------------------------------------------------------------+
| 2.0.5   | Added the ``scale``, ``x``, ``y``, ``w``, ``h`` and ``fname``    |
|         | parameters                                                       |
+---------+------------------------------------------------------------------+

.. _UDG:

#UDG
----
In HTML mode, the ``#UDG`` macro expands to an ``<img>`` element for the image
of a UDG (an 8x8 block of pixels). ::

  #UDGaddr[,attr,scale,step,inc,flip,rotate,mask][:MASK][{CROP}][(fname)]

* ``addr`` is the base address of the UDG bytes
* ``attr`` is the attribute byte to use (default: 56)
* ``scale`` is the scale of the image (default: 4)
* ``step`` is the interval between successive bytes of the UDG (default: 1)
* ``inc`` is added to each UDG byte before constructing the image (default: 0)
* ``flip`` is 1 to flip the UDG horizontally, 2 to flip it vertically, 3 to
  flip it both ways, or 0 to leave it as it is (default: 0)
* ``rotate`` is 1 to rotate the UDG 90 degrees clockwise, 2 to rotate it 180
  degrees, 3 to rotate it 90 degrees anticlockwise, or 0 to leave it as it is
  (default: 0)
* ``mask`` is the type of mask to apply (see :ref:`masks`)
* ``MASK`` is the mask specification (see below)
* ``CROP`` is the cropping specification (see :ref:`cropping`)
* ``fname`` is the name of the image file (if not given, a name specified by
  the ``UDGFilename`` parameter in the :ref:`Paths` section will be used)

The mask specification (``MASK``) takes the form::

  addr[,step]

* ``addr`` is the base address of the mask bytes to use for the UDG
* ``step`` is the interval between successive mask bytes (defaults to the value
  of ``step`` for the UDG)

Note that if any of the parameters in the mask specification is expressed using
arithmetic operations or skool macros, then the entire specification must be
enclosed in parentheses.

If ``fname`` contains an image path ID replacement field (e.g.
``{ScreenshotImagePath}/udg``), the corresponding parameter value from the
:ref:`Paths` section will be substituted.

If ``fname`` starts with a '/', the filename is taken to be relative to the
root of the HTML disassembly.

If ``fname`` contains no image path ID replacement fields and does not start
with a '/', the filename is taken to be relative to the directory defined by
the ``UDGImagePath`` parameter in the :ref:`paths` section.

If ``fname`` does not end with '`.png`' or '`.gif`', that suffix (depending on
the default image format specified in the :ref:`ref-ImageWriter` section of the
ref file) will be appended.

If an image with the given filename doesn't already exist, it will be created.

For example::

  ; Safe key UDG
  ;
  ; #HTML[#UDG39144,6(safe_key)]

In HTML mode, this instance of the ``#UDG`` macro expands to an ``<img>``
element for the image of the UDG at 39144 (which will be named `safe_key.png`
or `safe_key.gif`), with attribute byte 6 (INK 6: PAPER 0).

.. note::
   Support for GIF images is deprecated since version 7.2. Use PNG images
   instead.

+---------+------------------------------------------------------------------+
| Version | Changes                                                          |
+=========+==================================================================+
| 6.3     | Added support for image path ID replacement fields in the        |
|         | ``fname`` parameter                                              |
+---------+------------------------------------------------------------------+
| 5.1     | Added support for arithmetic expressions and skool macros in the |
|         | numeric parameters                                               |
+---------+------------------------------------------------------------------+
| 4.3     | Added the ability to create frames                               |
+---------+------------------------------------------------------------------+
| 4.2     | Added the ability to specify alt text for the ``<img>`` element  |
+---------+------------------------------------------------------------------+
| 4.0     | Added the ``mask`` parameter and support for AND-OR masking;     |
|         | added support for keyword arguments                              |
+---------+------------------------------------------------------------------+
| 3.1.2   | Made the ``attr`` parameter optional                             |
+---------+------------------------------------------------------------------+
| 3.0     | Added image-cropping capabilities                                |
+---------+------------------------------------------------------------------+
| 2.4     | Added the ``rotate`` parameter                                   |
+---------+------------------------------------------------------------------+
| 2.3.1   | Added the ``flip`` parameter                                     |
+---------+------------------------------------------------------------------+
| 2.1     | Added support for masks                                          |
+---------+------------------------------------------------------------------+
| 2.0.5   | Added the ``fname`` parameter                                    |
+---------+------------------------------------------------------------------+

.. _UDGARRAY:

#UDGARRAY
---------
In HTML mode, the ``#UDGARRAY`` macro expands to an ``<img>`` element for the
image of an array of UDGs (8x8 blocks of pixels). ::

  #UDGARRAYwidth[,attr,scale,step,inc,flip,rotate,mask];SPEC1[;SPEC2;...][@ATTRS1[;ATTRS2;...]][{CROP}](fname)

* ``width`` is the width of the image (in UDGs)
* ``attr`` is the default attribute byte of each UDG (default: 56)
* ``scale`` is the scale of the image (default: 2)
* ``step`` is the default interval between successive bytes of each UDG
  (default: 1)
* ``inc`` is added to each UDG byte before constructing the image (default: 0)
* ``flip`` is 1 to flip the array of UDGs horizontally, 2 to flip it
  vertically, 3 to flip it both ways, or 0 to leave it as it is (default: 0)
* ``rotate`` is 1 to rotate the array of UDGs 90 degrees clockwise, 2 to rotate
  it 180 degrees, 3 to rotate it 90 degrees anticlockwise, or 0 to leave it as
  it is (default: 0)
* ``mask`` is the type of mask to apply (see :ref:`masks`)
* ``CROP`` is the cropping specification (see :ref:`cropping`)
* ``fname`` is the name of the image file

``SPEC1``, ``SPEC2`` etc. are UDG specifications for the sets of UDGs that make
up the array. Each UDG specification has the form::

  addr[,attr,step,inc][:MASK]

* ``addr`` is the address range specification for the set of UDGs (see below)
* ``attr`` is the attribute byte of each UDG in the set (defaults to the value
  of ``attr`` for the UDG array)
* ``step`` is the interval between successive bytes of each UDG in the set
  (defaults to the value of ``step`` for the UDG array)
* ``inc`` is added to each byte of every UDG in the set before constructing the
  image (defaults to the value of ``inc`` for the UDG array)
* ``MASK`` is the mask specification

The mask specification (``MASK``) takes the form::

  addr[,step]

* ``addr`` is the address range specification for the set of mask UDGs (see
  below)
* ``step`` is the interval between successive bytes of each mask UDG in the set
  (defaults to the value of ``step`` for the set of UDGs)

``ATTRS1``, ``ATTRS2`` etc. are attribute address range specifications (see
below). If supplied, attribute values are taken from the specified addresses
instead of the ``attr`` parameter values.

Address range specifications (for both UDGs and attributes) may be given in one
of the following forms:

* a single address (e.g. ``39144``)
* a simple address range (e.g. ``33008-33015``)
* an address range with a step (e.g. ``32768-33792-256``)
* an address range with a horizontal and a vertical step (e.g.
  ``63476-63525-1-16``; this form specifies the step between the base addresses
  of adjacent items in each row as 1, and the step between the base addresses
  of adjacent items in each column as 16)

Any of these forms of address ranges can be repeated by appending ``xN``, where
``N`` is the desired number of repetitions. For example:

* ``39648x3`` is equivalent to ``39648;39648;39648``
* ``32768-32769x2`` is equivalent to ``32768;32769;32768;32769``

As many UDG specifications as required may be supplied, separated by
semicolons; the UDGs will be arranged in a rectangular array with the given
width.

Note that, like the main parameters of a ``#UDGARRAY`` macro (up to but not
including the first semicolon), if any of the following parts of the parameter
string is expressed using arithmetic operations or skool macros, then that part
must be enclosed in parentheses:

* any of the 1-5 parts of a UDG, mask or attribute address range specification
  (separated by ``-`` and ``x``)
* the part of a UDG or mask specification after the comma that follows the
  address range

If ``fname`` contains an image path ID replacement field (e.g.
``{ScreenshotImagePath}/udgs``), the corresponding parameter value from the
:ref:`Paths` section will be substituted.

If ``fname`` starts with a '/', the filename is taken to be relative to the
root of the HTML disassembly.

If ``fname`` contains no image path ID replacement fields and does not start
with a '/', the filename is taken to be relative to the directory defined by
the ``UDGImagePath`` parameter in the :ref:`paths` section.

If ``fname`` does not end with '`.png`' or '`.gif`', that suffix (depending on
the default image format specified in the :ref:`ref-ImageWriter` section of the
ref file) will be appended.

If an image with the given filename doesn't already exist, it will be created.

For example::

  ; Base sprite
  ;
  ; #HTML[#UDGARRAY4;32768-32888-8(base_sprite.png)]

In HTML mode, this instance of the ``#UDGARRAY`` macro expands to an ``<img>``
element for the image of the 4x4 sprite formed by the 16 UDGs with base
addresses 32768, 32776, 32784 and so on up to 32888; the image file will be
named `base_sprite.png`.

.. note::
   Support for GIF images is deprecated since version 7.2. Use PNG images
   instead.

+---------+-------------------------------------------------------------------+
| Version | Changes                                                           |
+=========+===================================================================+
| 7.1     | Added the ability to specify attribute addresses                  |
+---------+-------------------------------------------------------------------+
| 6.3     | Added support for image path ID replacement fields in the         |
|         | ``fname`` parameter                                               |
+---------+-------------------------------------------------------------------+
| 5.1     | Added support for arithmetic expressions and skool macros in the  |
|         | numeric parameters                                                |
+---------+-------------------------------------------------------------------+
| 4.2     | Added the ability to specify alt text for the ``<img>`` element   |
+---------+-------------------------------------------------------------------+
| 4.0     | Added the ``mask`` parameter and support for AND-OR masking;      |
|         | added support for keyword arguments                               |
+---------+-------------------------------------------------------------------+
| 3.6     | Added support for creating an animated image from an arbitrary    |
|         | sequence of frames                                                |
+---------+-------------------------------------------------------------------+
| 3.1.1   | Added support for UDG address ranges with horizontal and vertical |
|         | steps                                                             |
+---------+-------------------------------------------------------------------+
| 3.0     | Added image-cropping capabilities                                 |
+---------+-------------------------------------------------------------------+
| 2.4     | Added the ``rotate`` parameter                                    |
+---------+-------------------------------------------------------------------+
| 2.3.1   | Added the ``flip`` parameter                                      |
+---------+-------------------------------------------------------------------+
| 2.2.5   | Added support for masks                                           |
+---------+-------------------------------------------------------------------+
| 2.0.5   | New                                                               |
+---------+-------------------------------------------------------------------+

Alt text
--------
The value of the ``alt`` attribute in the ``<img>`` element created by an image
macro can be specified by appending a ``|`` character and the required text to
the filename. For example::

  #SCR(screenshot1|Screenshot 1)

This ``#SCR`` macro creates an image named `screenshot1.png` with alt text
'Screenshot 1'.

Animation
---------
The image macros may be used to create the frames of an animated image. To
create a frame, the ``fname`` parameter must have one of the following forms:

* ``name*`` - writes an image file with this name, and also creates a frame
  with the same name
* ``name1*name2`` - writes an image file named `name1`, and also creates a
  frame named `name2`
* ``*name`` - writes no image file, but creates a frame with this name

Then a special form of the ``#UDGARRAY`` macro creates the animated image from
a set of frames::

  #UDGARRAY*FRAME1[;FRAME2;...](fname)

``FRAME1``, ``FRAME2`` etc. are frame specifications; each one has the form::

  name[,delay]

* ``name`` is the name of the frame
* ``delay`` is the delay between this frame and the next in 1/100ths of a
  second; it also sets the default delay for any frames that follow (default:
  32)

For example::

  ; #UDGTABLE {
  ; #FONT:(hello)$3D00(hello*) |
  ; #FONT:(there)$3D00(there*) |
  ; #FONT:(peeps)$3D00(peeps*) |
  ; #UDGARRAY*hello,50;there;peeps(hello_there_peeps.gif)
  ; } TABLE#

The ``#FONT`` macros create the required frames (and write images of them); the
``#UDGARRAY`` macro combines the three frames into a single animated image,
with a delay of 0.5s between each frame.

.. _cropping:

Cropping
--------
Each image macro accepts a cropping specification (``CROP``) which takes the
form::

  x,y,width,height

* ``x`` is the x-coordinate of the leftmost pixel column of the constructed
  image to include in the final image (default: 0); if greater than 0, the
  image will be cropped on the left
* ``y`` is the y-coordinate of the topmost pixel row of the constructed image
  to include in the final image (default: 0); if greater than 0, the image will
  be cropped on the top
* ``width`` is the width of the final image in pixels (default: width of the
  constructed image)
* ``height`` is the height of the final image in pixels (default: height of the
  constructed image)

For example::

  #UDG40000,scale=2{2,2,12,12}

This ``#UDG`` macro creates an image of the UDG at 40000, at scale 2, with the
top two rows and bottom two rows of pixels removed, and the leftmost two
columns and rightmost two columns of pixels removed.

.. _masks:

Masks
-----
The :ref:`UDG` and :ref:`UDGARRAY` macros accept a ``mask`` parameter that
determines what kind of mask to apply to each UDG. The supported values are:

* ``0`` - no mask
* ``1`` - OR-AND mask (this is the default)
* ``2`` - AND-OR mask

Given a 'background' bit (B), a UDG bit (U), and a mask bit (M), the OR-AND
mask works as follows:

* OR the UDG bit (U) onto the background bit (B)
* AND the mask bit (M) onto the result

=  =  ===============
U  M  Result
=  =  ===============
0  0  0 (paper)
0  1  B (transparent)
1  0  0 (paper)
1  1  1 (ink)
=  =  ===============

The AND-OR mask works as follows:

* AND the mask bit (M) onto the background bit (B)
* OR the UDG bit (U) onto the result

=  =  ===============
U  M  Result
=  =  ===============
0  0  0 (paper)
0  1  B (transparent)
1  0  1 (ink)
1  1  1 (ink)
=  =  ===============

By default, transparent bits in masked images are rendered in bright green
(#00fe00); this colour can be changed by modifying the ``TRANSPARENT``
parameter in the :ref:`ref-Colours` section. To make the transparent bits in
masked images actually transparent, set ``GIFTransparency=1`` or ``PNGAlpha=0``
in the :ref:`ref-ImageWriter` section.

Snapshot macros
^^^^^^^^^^^^^^^
The :ref:`POKES`, :ref:`POPS` and :ref:`PUSHS` macros (described in the
following sections) may be used to manipulate the memory snapshot that is built
from the ``DEFB``, ``DEFM``, ``DEFS`` and ``DEFW`` statements in the skool
file. Each macro expands to an empty string.

.. _POKES:

#POKES
------
The ``#POKES`` macro POKEs values into the current memory snapshot. ::

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

See also :ref:`PEEK`.

+---------+------------------------------------------------------------------+
| Version | Changes                                                          |
+=========+==================================================================+
| 5.1     | Added support for arithmetic expressions and skool macros in the |
|         | numeric parameters                                               |
+---------+------------------------------------------------------------------+
| 3.1     | Added support for ASM mode                                       |
+---------+------------------------------------------------------------------+
| 2.3.1   | Added support for multiple addresses                             |
+---------+------------------------------------------------------------------+

.. _POPS:

#POPS
-----
The ``#POPS`` macro removes the current memory snapshot and replaces it with
the one that was previously saved by a ``#PUSHS`` macro. ::

  #POPS

+---------+----------------------------+
| Version | Changes                    |
+=========+============================+
| 3.1     | Added support for ASM mode |
+---------+----------------------------+

.. _PUSHS:

#PUSHS
------
The ``#PUSHS`` macro saves the current memory snapshot, and replaces it with an
identical copy with a given name. ::

  #PUSHS[name]

* ``name`` is the snapshot name (defaults to an empty string)

The snapshot name must be limited to the characters '$', '#', 0-9, A-Z and a-z;
it must not start with a capital letter. The name can be retrieved by using the
:meth:`~skoolkit.skoolhtml.HtmlWriter.get_snapshot_name` method on HtmlWriter.

+---------+----------------------------+
| Version | Changes                    |
+=========+============================+
| 3.1     | Added support for ASM mode |
+---------+----------------------------+

.. _definingMacrosWithReplace:

Defining macros with @replace
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
By using the :ref:`replace` directive, it is possible to define new macros
based on existing ones without writing any Python code. Some examples are given
below.

#asm
----
There is the :ref:`HTML` macro for inserting content in HTML mode only, but
there is no corresponding macro for inserting content in ASM mode only. The
following ``@replace`` directive defines an ``#asm`` macro to fill that gap::

  @replace=/#asm(\(.*\))/#IF({asm})\1

For example::

  #asm(This text appears only in ASM mode.)

#tile
-----
Suppose the game you're disassembling arranges tiles in groups of nine bytes:
the attribute byte first, followed by the eight graphic bytes. If there is a
tile at 32768, then::

  #UDG(32769,#PEEK32768)

will create an image of it. If you want to create several tile images, this
syntax can get cumbersome; it would be easier if you could supply just the
address of the attribute byte. The following ``@replace`` directive defines a
``#tile`` macro that creates a tile image given an attribute byte address::

  @replace=/#tile\i/#UDG(\1+1,#PEEK\1)

Now you can create an image of the tile at 32768 like this::

  #tile32768

#tiles
------
If you have several nine-byte tiles arranged one after the other, you might
want to create images of all of them in a single row of a ``#UDGTABLE``. The
following ``@replace`` directive defines a ``#tiles`` macro for this purpose::

  @replace=/#tiles\i,\i/#FOR(\1,\1+9*(\2-1),9)(n,#UDG(n+1,#PEEKn), | )

Now you can create a ``#UDGTABLE`` of images of a series of 10 tiles starting
at 32768 like this::

  #UDGTABLE { #tiles32768,10 } TABLE#

#udg
----
The :ref:`UDG` macro is not supported in ASM mode, but ``@replace`` can define
a ``#udg`` macro that is::

  @replace=/#udg\i/#IF({asm})(#LIST(,) #FOR(\1,\1+7)(u,{ |#FOR(7,0,-1)(n,#IF(#PEEKu&2**n)(*, ))| }) LIST#)

For example::

  ; #udg30000
   30000 DEFB 48,72,136,144,104,4,10,4

If conversion of DEFB statements has been switched on in ASM mode by the
:ref:`assemble` directive (e.g. ``@assemble=,1``), this ``#udg`` macro produces
the following output::

  ; |  **    |
  ; | *  *   |
  ; |*   *   |
  ; |*  *    |
  ; | ** *   |
  ; |     *  |
  ; |    * * |
  ; |     *  |
