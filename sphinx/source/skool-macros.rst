.. _skoolMacros:

Skool macros
============
Skool files and ref files may contain skool macros that are 'expanded' to an
appropriate piece of HTML markup (when rendering in HTML mode), or to an
appropriate piece of plain text (when rendering in ASM mode).

Syntax
^^^^^^
Skool macros have the following general form::

  #MACROri1,ri2,...[,oi1,oi2,...](rs1,rs2,...[,os1,os2,...])

where:

* ``MACRO`` is the macro name
* ``ri1``, ``ri2`` etc. are required integer parameters
* ``oi1``, ``oi2`` etc. are optional integer parameters
* ``rs1``, ``rs2`` etc. are required string parameters
* ``os1``, ``os2`` etc. are optional string parameters

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
generally recommended - especially when there are two or more parameters - in
order to unambiguously separate the numeric parameters from any content that
follows them. Parentheses are `required` if any numeric parameter is written as
an expression containing arithmetic operations, skool macros or replacement
fields::

  #UDG(51672+{offset},#PEEK51672)

The following operators are permitted in an arithmetic expression:

* arithmetic operators: ``+``, ``-``, ``*``, ``/``, ``%`` (modulo), ``**``
  (power)
* bitwise operators: ``&`` (AND), ``|`` (OR), ``^`` (XOR)
* bit shift operators: ``>>``, ``<<``
* Boolean operators: ``&&`` (and), ``||`` (or)
* comparison operators: ``==``, ``!=``, ``>``, ``<``, ``>=``, ``<=``

Parentheses and spaces are also permitted in an arithmetic expression::

  #IF(1 == 2 || (1 <= 2 && 2 < 3))(Yes,No)

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

.. _replacementFields:

Replacement fields
^^^^^^^^^^^^^^^^^^
The following replacement fields are available for use in the integer
parameters of the :ref:`asm-if` directive and every skool macro (including
macros defined by :ref:`DEF` or :ref:`DEFINE`), and also in the string
parameters of some macros:

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
* ``mode`` - a dictionary containing a copy of the ``asm``, ``base``, ``case``,
  ``fix`` and ``html`` fields
* ``sim`` - a dictionary of register values populated by the :ref:`SIM` macro
* ``vars`` - a dictionary of variables defined by the ``--var`` option of
  :ref:`skool2asm.py` or :ref:`skool2html.py`; accessing an undefined variable
  in this dictionary yields the integer value '0'

Replacement fields for the variables defined by the :ref:`LET` macro are also
available. Note that the ``#LET`` macro can change the values of the ``asm``,
``base``, ``case``, ``fix`` and ``html`` fields, but their original values are
always available in the ``mode`` dictionary.

For example::

  #IF({mode[case]}==1)(hl,HL)

expands to ``hl`` if in lower case mode, or ``HL`` otherwise.

Note that if a replacement field is used, the parameter string must be
enclosed in parentheses.

.. versionchanged:: 8.7
   Added the ``sim`` dictionary.

.. versionchanged:: 8.2
   Added the ``mode`` dictionary.

.. versionchanged:: 6.4
   The ``asm`` replacement field indicates the exact ASM mode; added the
   ``fix`` and ``vars`` replacement fields.

.. _SMPLmacros:

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

  #UDGARRAY#(2(#FOR37159,37168,9||n|(n+1),#PEEKn|;||))(item)

This instance of the ``#()`` macro expands the ``#FOR`` macro first, giving::

  2((37159+1),#PEEK37159;(37168+1),#PEEK37168)

It then expands the ``#PEEK`` macros, ultimately forming the parameters of the
``#UDGARRAY`` macro.

See :ref:`stringParameters` for details on alternative ways to supply the
``text`` parameter. Note that if an alternative delimiter is used, it must not
be an alphanumeric character (A-Z, a-z, 0-9).

.. _DEF:

#DEF
----
The ``#DEF`` macro defines a new skool macro. ::

  #DEF[flags](#MACRO[(ia[=i0],ib[=i1]...)[(sa[=s0],sb[=s1]...)]] body)

* ``flags`` controls various options (see below)
* ``MACRO`` is the macro name (which must be all upper case letters)
* ``ia[=i0]``, ``ib[=i1]`` etc. are the integer parameter names and optional
  default values; the parameter names must consist of lower case letters only
* ``sa[=s0]``, ``sb[=s1]`` etc. are the string parameter names and optional
  default values
* ``body`` is the body of the macro definition, which may contain placeholders
  (``$var``, ``${var}`` - when ``flags`` is 0) or replacement fields
  (``{var}`` - when ``flags`` is 1) representing the integer and string
  argument values

``flags`` is the sum of the following values, chosen according to the desired
outcome:

* 1 - use replacement fields (e.g. ``{var}``) instead of $-placeholders
  (``$var``, ``${var}``) to represent the defined macro's argument values
* 2 - strip leading and trailing whitespace from the output of the defined
  macro whenever it is expanded

For example::

  #DEF(#MIN(a,b) #IF($a<$b)($a,$b))

This defines a ``#MIN`` macro that accepts two integer arguments and expands to
the value of the smaller argument.

Default values for the defined macro's optional integer parameters can be
specified in the macro's signature. For example::

  #DEF(#PROD(a,b=1,c=1) #EVAL($a*$b*$c))

This defines a ``#PROD`` macro that accepts one, two or three integer
arguments, the second and third of which default to 1, and expands to the
product of all three arguments.

Default values for the defined macro's optional string parameters can also be
specified in the macro's signature, and their default values may refer to the
integer argument values. For example::

  #DEF(#NUM(a)(s=$a) $s)

This defines a ``#NUM`` macro that accepts one integer argument and an optional
string argument. It expands either to the integer argument, or to the string
argument if provided. So ``#NUM15`` expands to '15', and ``#NUM15($0F)``
expands to '$0F'.

If ``flags`` is odd (bit 0 set), replacement fields are used instead of
$-placeholders to represent the defined macro's argument values. The main
advantage of using replacement fields is that Python string formatting options
can be used on the argument values. For example::

  #DEF1(#HEX(n) {n:04X})

This defines a ``#HEX`` macro that formats its sole integer argument as a
4-digit upper case hexadecimal number.

However, when using replacement fields, care must be taken to escape any field
that doesn't represent an argument value. For example::

  #LET(count=0)
  #DEF1(#ADD(amount) #LET(count={{count}}+{amount}))

This defines a variable named ``count``, and an ``#ADD`` macro that increases
its value by a given amount. Note how the replacement field for the ``count``
variable in the body of the macro definition is escaped: ``{{count}}``.

If bit 1 of ``flags`` is set, the defined macro will be expanded, in isolation
from any surrounding content, as soon as it is encountered. For that to work,
the macro definition must be entirely self-contained, i.e. it must not depend
on any surrounding content in order to be syntactically correct. For example,
if the ``#IFZERO`` macro is defined thus::

  #DEF2(#IFZERO(n) #IF($n==0))

then any attempt to expand an ``#IFZERO`` macro will lead to an error message
about the ``#IF`` macro having no output strings. To fix this, either reset
bit 1 of ``flags``, or redefine ``#IFZERO`` with the output strings included in
the definition::

  #DEF2(#IFZERO(n)(a,b) #IF($n==0)($a,$b))

For more examples, see :ref:`definingMacrosWithDEF`.

Note that if a string parameter of a defined macro is optional, that argument
will take its default value only if it is omitted; if instead it is left blank,
it takes the value of the empty string.

In general, the string arguments of a defined macro may be supplied between
alternative delimiters (see :ref:`stringParameters`) if desired. However, if
every string parameter of the defined macro is optional, the string arguments
must be either omitted entirely or provided between parentheses (and therefore
separated by commas). This allows a macro with all of its optional string
arguments omitted to be immediately followed by some character other than an
opening parenthesis without that character being interpreted as an alternative
delimiter.

To define a macro that will be available for use immediately anywhere in the
skool file or ref files, consider using the :ref:`expand` directive, or the
``Expand`` parameter in the :ref:`ref-Config` section.

The ``flags`` parameter of the ``#DEF`` macro may contain
:ref:`replacement fields <replacementFields>`.

The integer parameters of a macro defined by ``#DEF`` may contain
:ref:`replacement fields <replacementFields>`, and may also be supplied via
keyword arguments.

+---------+------------------------------------------------------------------+
| Version | Changes                                                          |
+=========+==================================================================+
| 8.6     | Added the ``flags`` parameter, the ability to use replacement    |
|         | fields to represent the defined macro's argument values, and the |
|         | ability to strip whitespace from the defined macro's output      |
+---------+------------------------------------------------------------------+
| 8.5     | New                                                              |
+---------+------------------------------------------------------------------+

.. _DEFINE:

#DEFINE
-------
The ``#DEFINE`` macro defines a new skool macro. ::

  #DEFINEiparams[,sparams](name,value)

* ``iparams`` is the number of integer parameters the macro expects
* ``sparams`` is the number of string parameters the macro expects (default:
  ``0``)
* ``name`` is the macro name (which must be all upper case letters)
* ``value`` is the macro's output value (a standard Python format string
  containing replacement fields for the integer and string arguments)

For example::

  #DEFINE2(MIN,#IF({0}<{1})({0},{1}))

This defines a ``#MIN`` macro that accepts two integer arguments and expands to
the value of the smaller argument.

To define a macro that will be available for use immediately anywhere in the
skool file or ref files, consider using the :ref:`expand` directive, or the
``Expand`` parameter in the :ref:`ref-Config` section.

The integer parameters of a macro defined by ``#DEFINE`` may contain
:ref:`replacement fields <replacementFields>`.

See :ref:`stringParameters` for details on alternative ways to supply the
``name`` and ``value`` parameters.

.. note::
   The ``#DEFINE`` macro is deprecated since version 8.5. Use the more powerful
   :ref:`DEF` macro instead.

+---------+---------+
| Version | Changes |
+=========+=========+
| 8.2     | New     |
+---------+---------+

.. _EVAL:

#EVAL
-----
The ``#EVAL`` macro expands to the value of an arithmetic expression. ::

  #EVALexpr[,base,width]

* ``expr`` is the arithmetic expression
* ``base`` is the number base in which the value is expressed: 2, 10 (the
  default) or 16
* ``width`` is the minimum number of digits in the output (default: 1); the
  value will be padded with leading zeroes if necessary

For example::

  ; The following mask byte is #EVAL(#PEEK29435,2,8).
   29435 DEFB 62

This instance of the ``#EVAL`` macro expands to '00111110' (62 in binary).

The parameter string of the ``#EVAL`` macro may contain
:ref:`replacement fields <replacementFields>`.

+---------+-------------------------------------------------------------------+
| Version | Changes                                                           |
+=========+===================================================================+
| 8.0     | Added support for replacement fields in the parameter string      |
+---------+-------------------------------------------------------------------+
| 6.0     | Hexadecimal values are rendered in lower case when the            |
|         | ``--lower`` option is used                                        |
+---------+-------------------------------------------------------------------+
| 5.1     | New                                                               |
+---------+-------------------------------------------------------------------+

.. _FOR:

#FOR
----
The ``#FOR`` macro expands to a sequence of strings based on a range of
integers. ::

  #FORstart,stop[,step,flags](var,string[,sep,fsep])

* ``start`` is first integer in the range
* ``stop`` is the final integer in the range
* ``step`` is the gap between each integer in the range (default: 1)
* ``flags`` controls whether to affix commas to or replace variable names in
  each separator (see below)
* ``var`` is the variable name; for each integer in the range, it evaluates to
  that integer
* ``string`` is the output string that is evaluated for each integer in the
  range; wherever the variable name (``var``) appears, its value is substituted
* ``sep`` is the separator placed between each output string (default: the
  empty string); this may be modified depending on the value of ``flags``
* ``fsep`` is the separator placed between the final two output strings
  (default: ``sep``)

``flags`` is the sum of the following values, chosen according to the desired
outcome:

* 1 - prefix each separator (``sep``) with a comma
* 2 - suffix each separator (``sep``) with a comma
* 4 - replace any variable name (``var``) in each separator (``sep``) with the
  variable value

For example::

  ; The next three bytes (#FOR31734,31736,,1(n,#PEEKn, , and )) define the
  ; item locations.
   31734 DEFB 24,17,156

This instance of the ``#FOR`` macro expands to '24, 17 and 156'.

The integer parameters of the ``#FOR`` macro (``start``, ``stop``, ``step``,
``flags``) may contain :ref:`replacement fields <replacementFields>`.

See :ref:`stringParameters` for details on alternative ways to supply the
``var``, ``string``, ``sep`` and ``fsep`` parameters.

+---------+-------------------------------------------------------------------+
| Version | Changes                                                           |
+=========+===================================================================+
| 8.7     | Added the ``flags`` parameter                                     |
+---------+-------------------------------------------------------------------+
| 8.2     | Added support for replacement fields in the integer parameters    |
+---------+-------------------------------------------------------------------+
| 5.1     | New                                                               |
+---------+-------------------------------------------------------------------+

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
``s1,s2,...`` and ``var,string[,sep,fsep]`` parameter strings.

+---------+---------+
| Version | Changes |
+=========+=========+
| 5.1     | New     |
+---------+---------+

.. _FORMAT:

#FORMAT
-------
The ``#FORMAT`` macro performs a Python-style `string formatting operation`_ on
its string argument. ::

  #FORMAT[case](text)

* ``case`` is 1 to convert the formatted string to lower case, 2 to convert it
  to upper case, or 0 to leave it alone (the default)
* ``text`` is the string to format

For example::

  #FORMAT(0x{count:04X})

This instance of the ``#FORMAT`` macro formats the value of the ``count``
variable (assuming it has already been defined by the :ref:`LET` macro) as a
4-digit upper case hexadecimal number prefixed by '0x'.

Note that if ``text`` could be read as an integer parameter, ``case`` should be
explicitly specified in order to prevent ``text`` from being interpreted as the
``case`` parameter. For example::

  #FORMAT0({count})

Alternatively, the :ref:`EVAL` macro may be a better option for formatting a
pure numeric value.

The parameters of the ``#FORMAT`` macro may contain
:ref:`replacement fields <replacementFields>`.

See :ref:`stringParameters` for details on alternative ways to supply the
``text`` parameter.

+---------+-------------------------------------------------------------------+
| Version | Changes                                                           |
+=========+===================================================================+
| 8.5     | Added the ``case`` parameter                                      |
+---------+-------------------------------------------------------------------+
| 8.2     | New                                                               |
+---------+-------------------------------------------------------------------+

.. _string formatting operation: https://docs.python.org/3/library/string.html#format-string-syntax

.. _IF:

#IF
---
The ``#IF`` macro expands to an arbitrary string based on the truth value of an
arithmetic expression. ::

  #IFexpr(true[,false])

* ``expr`` is the arithmetic expression, which may contain
  :ref:`replacement fields <replacementFields>`
* ``true`` is the output string when ``expr`` is true
* ``false`` is the output string when ``expr`` is false (default: the empty
  string)

For example::

  ; #FOR0,7(n,#IF(#PEEK47134 & 2**(7-n))(X,O))
   47134 DEFB 170

This instance of the ``#IF`` macro is used (in combination with a ``#FOR``
macro and a ``#PEEK`` macro) to display the contents of the address 47134 in
the memory snapshot in binary format with 'X' for one and 'O' for zero:
XOXOXOXO.

See :ref:`stringParameters` for details on alternative ways to supply the
``true`` and ``false`` output strings.

+---------+----------------------------------------------------------------+
| Version | Changes                                                        |
+=========+================================================================+
| 6.0     | Added support for replacement fields in the ``expr`` parameter |
+---------+----------------------------------------------------------------+
| 5.1     | New                                                            |
+---------+----------------------------------------------------------------+

.. _LET:

#LET
----
The ``#LET`` macro defines an integer, string or dictionary variable.

The syntax for defining an integer or string variable is::

  #LET(name=value)

* ``name`` is the variable name
* ``value`` is the value to assign; this may contain skool macros (which are
  expanded immediately) and :ref:`replacement fields <replacementFields>`
  (which are replaced after any skool macros have been expanded)

If ``name`` ends with a dollar sign (``$``), ``value`` is interpreted as a
string. Otherwise ``value`` is evaluated as an arithmetic expression.

For example::

  #LET(count=2*2)
  #LET(count$=2*2)

These ``#LET`` macros assign the integer value '4' to the variable ``count`` and
the string value '2*2' to the variable ``count$``. The variables are then
accessible to other macros via the replacement fields ``{count}`` and
``{count$}``.

The syntax for defining a dictionary variable is::

  #LET(name[]=(default[,k1[:v1],k2[:v2]...]))

* ``name`` is the dictionary variable name
* ``default`` is the default value (used when a key is not found in the
  dictionary)
* ``k1:v1``, ``k2:v2`` etc. are the key-value pairs in the dictionary

The keys in a dictionary are integers, and the associated values are strings if
``name`` ends with a dollar sign, or integers otherwise. If the value part of a
key-value pair is omitted, it defaults to the key.

For example::

  #LET(n[]=(0,1:10,2:20))
  #LET(d$[]=(?,1:a,2:b))

The first ``#LET`` macro defines the dictionary variable ``n`` with default
integer value 0, and keys '1' and '2' mapping to the integer values 10 and 20.
The values in this dictionary are accessible to other macros via the replacement
fields ``{n[1]}`` and ``{n[2]}``.

The second ``#LET`` macro defines the dictionary variable ``d$`` with default
string value '?', and keys '1' and '2' mapping to the string values 'a' and
'b'. The values in this dictionary are accessible to other macros via the
replacement fields ``{d$[1]}`` and ``{d$[2]}``.

To define a variable that will be available for use immediately anywhere in the
skool file or ref files, consider using the :ref:`expand` directive.

See :ref:`stringParameters` for details on alternative ways to supply the
entire ``name=value`` parameter string, or the part after the equals sign when
defining a dictionary variable.

+---------+--------------------------------------------------+
| Version | Changes                                          |
+=========+==================================================+
| 8.6     | Added the ability to define dictionary variables |
+---------+--------------------------------------------------+
| 8.2     | New                                              |
+---------+--------------------------------------------------+

.. _MAP:

#MAP
----
The ``#MAP`` macro expands to a value from a map of key-value pairs whose keys
are integers. ::

  #MAPkey(default[,k1:v1,k2:v2...])

* ``key`` is the integer to look up in the map; this parameter may contain
  :ref:`replacement fields <replacementFields>`
* ``default`` is the default output string (used when ``key`` is not found in
  the map)
* ``k1:v1``, ``k2:v2`` etc. are the key-value pairs in the map

For example::

  ; The next three bytes specify the directions that are available from here:
  ; #FOR56112,56114,,1(q,#MAP(#PEEKq)(?,0:left,1:right,2:up,3:down), , and ).
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

+---------+---------------------------------------------------------------+
| Version | Changes                                                       |
+=========+===============================================================+
| 6.0     | Added support for replacement fields in the ``key`` parameter |
+---------+---------------------------------------------------------------+
| 5.1     | New                                                           |
+---------+---------------------------------------------------------------+

.. _PC:

#PC
---
The ``#PC`` macro expands to the address of the closest instruction in the
current entry. ::

  #PC

For example::

  c32768 XOR A ; This instruction is at #PC.

This instance of the ``#PC`` macro expands to '32768'.

In an entry header (i.e. title, description, register description or start
comment), the ``#PC`` macro expands to the address of the first instruction in
the entry. In a mid-block comment, the ``#PC`` macro expands to the address of
the following instruction. In an instruction-level comment, the ``#PC`` macro
expands to the address of the instruction. In a block end comment, the ``#PC``
macro expands to the address of the last instruction in the entry.

+---------+---------+
| Version | Changes |
+=========+=========+
| 8.0     | New     |
+---------+---------+

.. _PEEK:

#PEEK
-----
The ``#PEEK`` macro expands to the contents of an address in the internal
memory snapshot constructed from the contents of the skool file. ::

  #PEEKaddr

* ``addr`` is the address, which may contain
  :ref:`replacement fields <replacementFields>`

For example::

  ; At the start of the game, the number of lives remaining is #PEEK33879.

This instance of the ``#PEEK`` macro expands to the contents of the address
33879 in the internal memory snapshot.

Note that, by default, the internal memory snapshot constructed by
:ref:`skool2asm.py` is entirely blank (all zeroes), and the snapshot
constructed by :ref:`skool2html.py` is populated only by ``DEFB``, ``DEFM``,
``DEFS`` and ``DEFW`` statements, and by :ref:`defb`, :ref:`defs` and
:ref:`defw` directives. To change this behaviour, use the :ref:`assemble`
directive.

See also :ref:`POKES`.

+---------+-------------------------------------------------------------------+
| Version | Changes                                                           |
+=========+===================================================================+
| 8.2     | Added support for replacement fields in the ``addr`` parameter    |
+---------+-------------------------------------------------------------------+
| 5.1     | New                                                               |
+---------+-------------------------------------------------------------------+

.. _STR:

#STR
----
The ``#STR`` macro expands to the text string at a given address in the memory
snapshot. ::

  #STRaddr[,flags,length][(end)]

* ``addr`` is the address of the first character in the string
* ``flags`` indicates operations to be performed on the string (default: 0)
* ``length`` is the number of characters in the string; if -1 (the default),
  the string ends immediately before the first zero byte, or on the first byte
  that has bit 7 set (bit 7 of that byte will be reset before converting it to
  a character), or when ``end`` evaluates to true
* ``end`` is an arithmetic expression that identifies the end marker byte for
  the string (when bit 3 of ``flags`` is set)

``flags`` is the sum of the following values, chosen according to the desired
outcome:

* 1 - strip trailing whitespace from the string
* 2 - strip leading whitespace from the string
* 4 - replace each sequence of N>=2 spaces in the string with ``#SPACE(N)``
  (see :ref:`SPACE`)
* 8 - use the ``end`` parameter to determine where the string ends

When bit 3 of ``flags`` is set, ``end`` is evaluated for each byte encountered,
and if the result is true, the string is terminated. ``end`` may contain the
placeholder ``$b`` for the current byte value.

For example::

  ; The messages here are '#STR47154', '#STR47158' and '#STR47161,8($b==255)'.
   47154 DEFM "One",0
   47158 DEFM "Tw","o"+128
   47161 DEFM "Three",255

These instances of the ``#STR`` macro expand to 'One', 'Two' and 'Three'.

The parameters of the ``#STR`` macro may contain
:ref:`replacement fields <replacementFields>`.

+---------+---------+
| Version | Changes |
+=========+=========+
| 8.6     | New     |
+---------+---------+

.. _WHILE:

#WHILE
------
The ``#WHILE`` macro repeatedly expands macros while a conditional expression
is true. ::

  #WHILE(expr)(body)

* ``expr`` is the conditional expression
* ``body`` is the text to repeatedly expand; leading and trailing whitespace
  are stripped from the expanded value

For example::

  #LET(a=3)
  #WHILE({a}>0)(
    #EVAL({a})
    #LET(a={a}-1)
  )

This instance of the ``#WHILE`` macro expands to '321'.

The ``expr`` parameter of the ``#WHILE`` macro may contain
:ref:`replacement fields <replacementFields>`.

See :ref:`stringParameters` for details on alternative ways to supply the
``body`` parameter.

+---------+---------+
| Version | Changes |
+=========+=========+
| 8.6     | New     |
+---------+---------+

General macros
^^^^^^^^^^^^^^

.. _AUDIO:

#AUDIO
------
In HTML mode, the ``#AUDIO`` macro expands to an HTML5 ``<audio>`` element. ::

  #AUDIO[flags,offset](fname)[(delays)]

Or, when bit 2 of ``flags`` is set::

  #AUDIO[flags,offset](fname)(start,stop)

* ``flags`` controls various options (see below)
* ``offset`` is the initial offset in T-states from the start of a frame
  (default: 0); this value affects when contention and interrupt delays (if
  enabled) first take effect
* ``fname`` is the name of the audio file
* ``delays`` is a comma-separated list of delays (in T-states) between speaker
  state changes; this parameter may contain skool macros (which are expanded
  first) and :ref:`replacement fields <replacementFields>` (which are replaced
  after any skool macros have been expanded)
* ``start`` is the address at which to start executing code in a simulator
  (when bit 2 of ``flags`` is set)
* ``stop`` is the address at which to stop executing code in a simulator (when
  bit 2 of ``flags`` is set)

``flags`` is the sum of the following values, chosen according to the desired
outcome:

* 1 (bit 0) - modify delays to approximate the effect of running in contended
  memory; this increases any delays that occur during the contended period of a
  frame by a given factor (as specified by the ``ContentionBegin``,
  ``ContentionEnd`` and ``ContentionFactor`` parameters in the
  :ref:`ref-AudioWriter` section)
* 2 (bit 1) - modify delays as if interrupts were enabled; this increases any
  delays that occur over a frame boundary by a given number of T-states (as
  specified by the ``InterruptDelay`` parameter in the :ref:`ref-AudioWriter`
  section)
* 4 (bit 2) - execute instructions from ``start`` to ``stop`` in a simulator to
  obtain the delays between speaker state changes

If ``fname`` starts with a '/', the filename is taken to be relative to the
root of the HTML disassembly. Otherwise the filename is taken to be relative to
the audio directory (as defined by the ``AudioPath`` parameter in the
:ref:`paths` section).

If ``delays`` is specified and ``fname`` ends with '.wav', a corresponding
audio file in WAV format is created. Each element in ``delays`` can be an
integer, a list or tuple of integers, or a list/tuple of lists/tuples of
integers etc. nested to arbitrary depth, expressed as Python literals. For
example::

  1000, [1500]*100, [(800, 1200)*2, 900]*200

This would be flattened into a list of integers, as follows:

* a single instance of '1000'
* 100 instances of '1500'
* 200 instances of the sequence '800, 1200, 800, 1200, 900'

The sum of this list of integers being 1131000, this would result in an audio
file of duration 1131000 / 3500000 = 0.323s (assuming that no memory contention
is simulated and interrupts are disabled, i.e. bits 0 and 1 of ``flags`` are
reset).

The characters allowed in the ``delays`` parameter are ' ' (space), newline,
the digits 0-9, and any of ``,*+-%()[]``.

An alternative to supplying the delay values manually is to execute the code
that produces the sound effect in a simulator, and let the simulator compute
the delays. This can be done by setting bit 2 of ``flags`` and specifying the
code to execute via the ``start`` and ``stop`` address parameters. For
example::

  ; #AUDIO4(beep.wav)(32768,32782)
  @assemble=2
  c32768 LD L,0
  *32771 OUT (254),A
   32773 XOR 16
   32775 LD B,200
   32777 DJNZ 32777
   32779 DEC L
   32780 JR NZ,32771
   32782 RET

.. note::
   The simulator does not simulate memory contention, I/O contention, or
   interrupts. Use bits 0 and 1 of ``flags`` to approximate memory contention
   effects and interrupt delays if desired.

Note also that, by default, the internal memory snapshot constructed by
:ref:`skool2asm.py` is entirely blank (all zeroes), and the snapshot
constructed by :ref:`skool2html.py` is populated only by ``DEFB``, ``DEFM``,
``DEFS`` and ``DEFW`` statements, and by :ref:`defb`, :ref:`defs` and
:ref:`defw` directives. To make sure that the internal memory snapshot actually
contains the code to be executed, use the :ref:`assemble` directive (as shown
in the example above).

If ``delays`` or ``start`` and ``stop`` parameters are specified, but ``fname``
does not end with '.wav', no audio file is written. This enables the parameters
to be kept in place as a reminder of how an original WAV file was created by
the ``#AUDIO`` macro before it was converted to another format.

If neither ``delays`` nor ``start`` and ``stop`` parameters are specified, or
``fname`` does not end with '.wav', the named audio file must already exist in
the specified location, otherwise the ``<audio>`` element controls will not
work. To make sure that a pre-built audio file is copied into the desired
location when :ref:`skool2html.py` is run, it can be declared in the
:ref:`resources` section.

By default, if ``fname`` ends with '.wav', but a '.flac', '.mp3' or '.ogg' file
with the same basename already exists, that file is used and no WAV file is
written. This enables an original WAV file to be replaced by an alternative
(compressed) version without having to modify the ``fname`` parameter of the
``#AUDIO`` macro. The alternative audio file types that the ``#AUDIO`` macro
looks for before writing a WAV file are specified by the ``AudioFormats``
parameter in the :ref:`ref-game` section.

The ``flags``, ``offset``, ``start`` and ``stop`` parameters of the ``#AUDIO``
macro may contain :ref:`replacement fields <replacementFields>`.

The :ref:`t_audio` template is used to format the ``<audio>`` element.

Audio file creation can be configured via the :ref:`ref-AudioWriter` section.

+---------+---------+
| Version | Changes |
+=========+=========+
| 8.7     | New     |
+---------+---------+

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
* ``args`` is a comma-separated list of arguments to pass to the method, which
  may contain :ref:`replacement fields <replacementFields>`

Each argument can be expressed either as a plain value (e.g. ``32768``) or as a
keyword argument (e.g. ``address=32768``).

For example::

  ; The word at address 32768 is #CALL:word(32768).

This instance of the ``#CALL`` macro expands to the return value of the `word`
method (on the `HtmlWriter` or `AsmWriter` subclass being used) when called
with the argument ``32768``.

For information on writing methods that may be called by a ``#CALL`` macro, see
the documentation on :ref:`extending SkoolKit <extendingSkoolKit>`.

+---------+-------------------------------------------------------------------+
| Version | Changes                                                           |
+=========+===================================================================+
| 8.3     | Added support for replacement fields in the ``args`` parameter    |
+---------+-------------------------------------------------------------------+
| 8.1     | Added support for keyword arguments                               |
+---------+-------------------------------------------------------------------+
| 5.1     | Added support for arithmetic expressions and skool macros in the  |
|         | ``args`` parameter                                                |
+---------+-------------------------------------------------------------------+
| 3.1     | Added support for ASM mode                                        |
+---------+-------------------------------------------------------------------+
| 2.1     | New                                                               |
+---------+-------------------------------------------------------------------+

.. _CHR:

#CHR
----
In HTML mode, the ``#CHR`` macro expands either to a numeric character
reference, or to a unicode character in the UTF-8 encoding. In ASM mode, it
always expands to a unicode character in the UTF-8 encoding. ::

  #CHRnum[,flags]

* ``num`` is the character code
* ``flags`` enables options that control the output (default: 0)

``flags`` is the sum of the following values, chosen according to the desired
outcome:

* 1 - produce a character in the UTF-8 encoding instead of a numeric character
  reference in HTML mode
* 2 - map character code 94 to 8593 ('↑'), 96 to 163 ('£'), and 127 to 169
  ('©'), in accordance with the ZX Spectrum character set

For example:

.. parsed-literal::
   :class: nonexistent

    26751 DEFB 127   ; This is the copyright symbol: #CHR169
    26572 DEFB 127   ; This is also the copyright symbol: #CHR127,2

In HTML mode, these instances of the ``#CHR`` macro expand to '&#169;'. In ASM
mode, they both expand to '©'.

The parameter string of the ``#CHR`` macro may contain
:ref:`replacement fields <replacementFields>`.

+---------+------------------------------------------------------------------+
| Version | Changes                                                          |
+=========+==================================================================+
| 8.6     | Added the ``flags`` parameter, the ability to use UTF-8 encoding |
|         | in HTML mode, and support for mapping character codes 94, 96 and |
|         | 127 to '↑', '£'  and '©'                                         |
+---------+------------------------------------------------------------------+
| 8.3     | Added support for replacement fields in the parameter string     |
+---------+------------------------------------------------------------------+
| 5.1     | Added support for arithmetic expressions and skool macros in the |
|         | parameter string                                                 |
+---------+------------------------------------------------------------------+
| 3.1     | New                                                              |
+---------+------------------------------------------------------------------+

.. _D:

#D
--
The ``#D`` macro expands to the title of an entry (a routine or data block) in
the memory map. ::

  #Daddr

* ``addr`` is the address of the entry, which may contain
  :ref:`replacement fields <replacementFields>`

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
| 8.3     | Added support for replacement fields in the ``addr`` parameter   |
+---------+------------------------------------------------------------------+
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
In HTML mode, the ``#INCLUDE`` macro expands to the contents of one or more ref
file sections. In ASM mode, it expands to an empty string. ::

  #INCLUDE[paragraphs](pattern)

* ``paragraphs`` specifies how to format the contents of the ref file sections:
  verbatim (0 - the default), or into paragraphs (1)
* ``pattern`` is a regular expression pattern that identifies the names of the
  ref file sections to include

The ``#INCLUDE`` macro can be used to insert the contents of one ref file
section into another. For example::

  [MemoryMap:RoutinesMap]
  Intro=#INCLUDE(RoutinesMapIntro)

  [RoutinesMapIntro]
  This is the intro to the 'Routines' map page.

If ``pattern`` identifies multiple ref file sections, they are concatenated in
the order in which they appear in the ref file.

The ``paragraphs`` parameter of the ``#INCLUDE`` macro may contain
:ref:`replacement fields <replacementFields>`.

See :ref:`stringParameters` for details on alternative ways to supply the
``pattern`` parameter.

+---------+-------------------------------------------------------------------+
| Version | Changes                                                           |
+=========+===================================================================+
| 8.6     | Added the ability to combine multiple ref file sections           |
+---------+-------------------------------------------------------------------+
| 8.3     | Added support for replacement fields in the ``paragraphs``        |
|         | parameter                                                         |
+---------+-------------------------------------------------------------------+
| 5.3     | New                                                               |
+---------+-------------------------------------------------------------------+

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

The integer parameters of the ``#N`` macro may contain
:ref:`replacement fields <replacementFields>`.

See :ref:`stringParameters` for details on alternative ways to supply the
``prefix`` and ``suffix`` parameters.

+---------+-------------------------------------------------------------------+
| Version | Changes                                                           |
+=========+===================================================================+
| 8.3     | Added support for replacement fields in the integer parameters    |
+---------+-------------------------------------------------------------------+
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
  thereof), which may contain :ref:`replacement fields <replacementFields>`
* ``code`` is the ID of the disassembly that contains the routine or data block
  (if not given, the current disassembly is assumed; otherwise this must be
  either an ID defined in an :ref:`otherCode` section of the ref file, or
  ``main`` to identify the main disassembly)
* ``#name`` is the named anchor of an item on the disassembly page
* ``link text`` is the link text to use

The disassembly ID (``code``) and anchor name (``name``) must be limited to the
characters '$', '#', 0-9, A-Z and a-z.

If ``link_text`` is not provided, it defaults to the label for ``addr`` if one
is defined, or to the address formatted according to the ``Address`` parameter
in the :ref:`ref-Game` section.

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
| 8.4     | In HTML mode, the link text defaults to the address formatted   |
|         | according to the ``Address`` parameter                          |
+---------+-----------------------------------------------------------------+
| 8.3     | Added support for replacement fields in the ``addr`` parameter  |
+---------+-----------------------------------------------------------------+
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

.. _SIM:

#SIM
----
The ``#SIM`` macro simulates the execution of machine code in the internal
memory snapshot constructed from the contents of the skool file. ::

  #SIMstop[,start,clear,a,f,bc,de,hl,xa,xf,xbc,xde,xhl,ix,iy,i,r,sp]

* ``stop`` is the address at which to stop execution
* ``start`` is the address at which to start execution (default: ``stop`` from
  the previous invocation of the ``#SIM`` macro, or 0 if this is the first run)
* ``clear`` is 0 to use the register values that resulted from the previous
  invocation of the ``#SIM`` macro (the default), or 1 to reset them to their
  default values (shown below)
* ``a`` sets the value of the A (accumulator) register (default: 0)
* ``f`` sets the value of the F (flags) register (default: 0)
* ``bc`` sets the value of the BC register pair (default: 0)
* ``de`` sets the value of the DE register pair (default: 0)
* ``hl`` sets the value of the HL register pair (default: 0)
* ``xa`` sets the value of the A' (shadow accumulator) register (default: 0)
* ``xf`` sets the value of the F' (shadow flags) register (default: 0)
* ``xbc`` sets the value of the shadow BC register pair (default: 0)
* ``xde`` sets the value of the shadow DE register pair (default: 0)
* ``xhl`` sets the value of the shadow HL register pair (default: 0)
* ``ix`` sets the value of the IX register (default: 0)
* ``iy`` sets the value of the IY register (default: 23610)
* ``i`` sets the value of the I register (default: 63)
* ``r`` sets the value of the R register (default: 0)
* ``sp`` sets the value of the stack pointer (default: 23552)

The parameters of the ``#SIM`` macro may contain
:ref:`replacement fields <replacementFields>` and may also be given as keyword arguments.

When execution stops, the simulator's register and clock values are copied to
the ``sim`` dictionary, where they are accessible via replacement fields with
the following names:

* ``sim[A]``
* ``sim[F]``
* ``sim[BC]``
* ``sim[DE]``
* ``sim[HL]``
* ``sim[^A]`` - the shadow A register
* ``sim[^F]`` - the shadow flags register
* ``sim[^BC]`` - the shadow BC register pair
* ``sim[^DE]`` - the shadow DE register pair
* ``sim[^HL]`` - the shadow HL register pair
* ``sim[IX]``
* ``sim[IY]``
* ``sim[I]``
* ``sim[R]``
* ``sim[SP]``
* ``sim[PC]`` - the program counter (equal to ``stop``); this is used as the
  default value of ``start`` for the next invocation of the ``#SIM`` macro
* ``sim[tstates]`` - the number of T-states elapsed

For example::

  @assemble=2,2
  ; #SIM(start=32768,stop=32772,bc=13256,de=672)
   32768 LD HL,443
   32771 ADD HL,BC
  ; At this point HL=#EVAL({sim[HL]}).
  ; #SIM(32773)
   32772 ADD HL,DE
  ; And now HL=#EVAL({sim[HL]}).
   32773 RET

The first ``#SIM`` macro initialises the BC and DE register pairs to 13256 and
672 respectively, starts executing code at 32768, and stops when it reaches the
'ADD HL,DE' instruction at 32772. The second ``#SIM`` macro picks up execution
where the first left off, and stops when it reaches the 'RET' instruction
at 32773.

After the ``#EVAL`` macros have been expanded, the second mid-block comment
here is rendered as 'At this point HL=13699', and the third is rendered as 'And
now HL=14371'.

.. note::
   The simulator does not simulate memory contention, I/O contention, or
   interrupts. This means that ``sim[tstates]`` may not be accurate if the code
   being simulated runs in or accesses contended memory, or performs I/O
   operations, or runs while interrupts are enabled.

Note that, by default, the internal memory snapshot constructed by
:ref:`skool2asm.py` is entirely blank (all zeroes), and the snapshot
constructed by :ref:`skool2html.py` is populated only by ``DEFB``, ``DEFM``,
``DEFS`` and ``DEFW`` statements, and by :ref:`defb`, :ref:`defs` and
:ref:`defw` directives. To make sure that the internal memory snapshot actually
contains the code to be executed, use the :ref:`assemble` directive (as shown
in the example above).

Note also that code executed by the ``#SIM`` macro operates directly on the
internal memory snapshot, and therefore can modify it. To avoid that, use the
:ref:`PUSHS` and :ref:`POPS` macros to operate on a copy of the snapshot.

+---------+---------+
| Version | Changes |
+=========+=========+
| 8.7     | New     |
+---------+---------+

.. _SPACE:

#SPACE
------
The ``#SPACE`` macro expands to one or more ``&#160;`` expressions (in HTML
mode) or spaces (in ASM mode). ::

  #SPACE[num]

* ``num`` is the number of spaces required (default: 1), which may contain
  :ref:`replacement fields <replacementFields>`

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
| 8.3     | Added support for replacement fields in the ``num`` parameter    |
+---------+------------------------------------------------------------------+
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

.. _TSTATES:

#TSTATES
--------
The ``#TSTATES`` macro expands to the time taken, in T-states, to execute one
or more instructions. ::

  #TSTATESstart[,stop,flags(text)]

* ``start`` is the address of the instruction at which to start the clock
* ``stop`` is the address of the instruction at which to stop the clock
* ``flags`` controls various options (see below)
* ``text`` is the text to expand to (when bit 1 of ``flags`` is set); this may
  contain the placeholders ``$min`` and ``$max`` for the sums of the smaller
  and larger timing values of the instructions in the given range, or
  ``$tstates`` for the actual timing value when bit 2 of ``flags`` is set

``flags`` is the sum of the following values, chosen according to the desired
outcome:

* 1 (bit 0) - use the larger timing value for an instruction whose timing is
  variable
* 2 (bit 1) - expand to ``text``
* 4 (bit 2) - execute instructions in a simulator to get the actual timing

For example::

  c30000 LD A,1   ; This instruction takes #TSTATES30000 T-states

This instance of the ``#TSTATES`` macros expands to '7'.

For any instruction in the range ``start`` to ``stop`` whose timing is variable
(e.g. a conditional call, return or relative jump), the smaller timing value is
used by default::

  c40000 RET Z    ; This instruction takes at least #TSTATES40000 T-states

This instance of the ``#TSTATES`` macros expands to '5'.

To use the larger timing values, set bit 0 of ``flags``. If both smaller and
larger timing values are required, set bit 1 of ``flags`` and use the ``text``
parameter::

  c50000 LD B,100    ; Set the delay parameter
   50002 DJNZ 50002  ; Delay for #TSTATES50002,,2(#EVAL(99*$max+$min)) T-states

This instance of the ``#TSTATES`` macro expands to ``#EVAL(99*13+8)``, which in
turn expands to '1295'.

Note that an instruction's timing can be determined only if it has been
assembled. To make sure that it is assembled, use the :ref:`assemble`
directive. In addition, unless bit 2 of ``flags`` is set, only true
instructions (i.e. not ``DEFB``, ``DEFM``, ``DEFS`` and ``DEFW`` statements)
can be timed.

If bit 2 of ``flags`` is set, the ``stop`` address must be specified, and the
instructions are executed in a simulator to determine their actual timing. This
is useful for computing the time taken by conditional operations and operations
that are repeated in a loop. For example::

  c32768 LD DE,0     ; {This creates a delay of #TSTATES(32768,32776,4)
  *32771 DEC DE      ; T-states
   32772 LD A,D      ;
   32773 OR E        ;
   32774 JR NZ,32771 ; }
   32776 RET

This instance of the ``#TSTATES`` macro expands to '1703941'.

.. note::
   The simulator does not simulate memory contention, I/O contention, or
   interrupts. This means that ``#TSTATES`` may not provide accurate timing if
   the code being timed runs in or accesses contended memory, or performs I/O
   operations, or runs while interrupts are enabled.

The integer parameters of the ``#TSTATES`` macro may contain
:ref:`replacement fields <replacementFields>`.

See :ref:`stringParameters` for details on alternative ways to supply the
``text`` parameter.

See also the :ref:`SIM` macro, which can not only time instructions, but also
track changes to register values as code is executed.

See also the ``Timings`` configuration parameter for
:ref:`sna2skool.py <sna2skool-conf>`, which can be used to show instruction
timings in comment fields when disassembling a snapshot.

+---------+---------+
| Version | Changes |
+=========+=========+
| 8.7     | New     |
+---------+---------+

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
The :ref:`COPY`, :ref:`FONT`, :ref:`OVER`, :ref:`PLOT`, :ref:`SCR`, :ref:`UDG`,
:ref:`UDGARRAY` and :ref:`UDGS` macros (described in the following sections)
may be used to create images based on graphic data in the memory snapshot. They
are not supported in ASM mode.

Some of these macros have several numeric parameters, most of which are
optional. This can give rise to a long sequence of commas in a macro parameter
string, making it hard to read (and write); for example::

  #UDG32768,,,,,,1

To alleviate this problem, the image macros accept keyword arguments at any
position in the parameter string; the ``#UDG`` macro above could be rewritten
as follows::

  #UDG32768,rotate=1

.. _COPY:

#COPY
-----
In HTML mode, the ``#COPY`` macro copies all or part of an existing frame into
a new frame. ::

  #COPY[x,y,width,height,scale,mask,tindex,alpha][{CROP}](old,new)

* ``x`` and ``y`` are the coordinates of the top left tile of the existing
  frame to include in the new frame (default: (0, 0))
* ``width`` and ``height`` are the width and height (in tiles) of the portion
  of the existing frame to copy (by default, the portion extends to the right
  and bottom edges of the existing frame)
* ``scale`` is the scale of the new frame; if omitted, the scale of the
  existing frame is used
* ``mask`` is the mask type of the new frame (see :ref:`masks`); if omitted,
  the mask type of the existing frame is used
* ``tindex`` is the index (0-15) of the entry in the palette to use as the
  transparent colour for the new frame (see :ref:`palette`); if omitted, the
  transparency index of the existing frame is used
* ``alpha`` is the alpha value (0-255) to use for the transparent colour in the
  new frame; if omitted, the alpha value of the existing frame is used
* ``CROP`` is the cropping specification for the new frame (see
  :ref:`cropping`); if omitted, the cropping specification of the existing
  frame is used
* ``old`` is the name of the existing frame
* ``new`` is the name of the new frame

For example::

  ; #UDGARRAY4(30000-30120-8)(*original)
  ; #COPY1,1,2,2(original,centre)
  ; #UDGARRAY*centre(img)

This instance of the ``#COPY`` macro creates a new frame from a copy of the
central 2x2 portion of the 4x4 frame created by the ``#UDGARRAY`` macro.  The
``#UDGARRAY*`` macro then creates an image of the new frame.

The integer parameters and the cropping specification of the ``#COPY`` macro
may contain :ref:`replacement fields <replacementFields>`.

See :ref:`stringParameters` for details on alternative ways to supply the
``old`` and ``new`` parameters.

+---------+-----------------------------------------------+
| Version | Changes                                       |
+=========+===============================================+
| 8.6     | Added the ``tindex`` and ``alpha`` parameters |
+---------+-----------------------------------------------+
| 8.5     | New                                           |
+---------+-----------------------------------------------+

.. _FONT:

#FONT
-----
In HTML mode, the ``#FONT`` macro expands to an ``<img>`` element for an image
of text rendered in the game font. ::

  #FONT[:(text)]addr[,chars,attr,scale,tindex,alpha][{CROP}][(fname)]

* ``text`` is the text to render (default: the 96 characters from code 32 to
  code 127)
* ``addr`` is the base address of the font graphic data
* ``chars`` is the number of characters to render (default: the length of
  ``text``)
* ``attr`` is the attribute byte to use (default: 56)
* ``scale`` is the scale of the image (default: 2)
* ``tindex`` is the index (0-15) of the entry in the palette to use as the
  transparent colour (default: 0; see :ref:`palette`)
* ``alpha`` is the alpha value (0-255) to use for the transparent colour
  (default: the value of the ``PNGAlpha`` parameter in the
  :ref:`ref-ImageWriter` section)
* ``CROP`` is the cropping specification (see :ref:`cropping`)
* ``fname`` is the name of the image file (see :ref:`Filenames`; default:
  '`font`')

For example::

  ; Font graphic data
  ;
  ; #HTML[#FONT:(0123456789)49152]

In HTML mode, this instance of the ``#FONT`` macro expands to an ``<img>``
element for the image of the digits 0-9 in the 8x8 font whose graphic data
starts at 49152.

The integer parameters and the cropping specification of the ``#FONT`` macro
may contain :ref:`replacement fields <replacementFields>`.

See :ref:`stringParameters` for details on alternative ways to supply the
``text`` parameter.

+---------+------------------------------------------------------------------+
| Version | Changes                                                          |
+=========+==================================================================+
| 8.3     | Added support for replacement fields in the integer parameters   |
|         | and the cropping specification                                   |
+---------+------------------------------------------------------------------+
| 8.2     | Added the ``tindex`` and ``alpha`` parameters                    |
+---------+------------------------------------------------------------------+
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

.. _OVER:

#OVER
-----
In HTML mode, the ``#OVER`` macro superimposes one frame (the foreground frame)
on another (the background frame). ::

  #OVERx,y[,xoffset,yoffset,rmode][(attr)][(byte)](bg,fg)

* ``x`` and ``y`` are the tile coordinates on the background frame at which to
  superimpose the foreground frame; negative coordinates are allowed
* ``xoffset`` and ``yoffset`` are the pixel offsets by which to shift the
  foreground frame from the given tile coordinates (default: (0, 0))
* ``rmode`` is the attribute and graphic byte replacement mode (see below)
* ``attr`` is the replacement attribute byte for any background UDG over which
  a foreground UDG is superimposed (when ``rmode`` is 1 or 3)
* ``byte`` is the replacement graphic byte for any background UDG over which
  a foreground UDG is superimposed (when ``rmode`` is 2 or 3)
* ``bg`` is the name of the background frame
* ``fg`` is the name of the foreground frame

``rmode`` specifies whether and how to replace the attribute and graphic bytes
of each background UDG over which a foreground UDG is superimposed:

* 0 - leave the attribute byte unchanged and apply the foreground frame's mask
* 1 - replace the attribute byte with the value of ``attr`` and apply the
  foreground frame's mask
* 2 - leave the attribute byte unchanged and replace the graphic bytes with the
  value of ``byte``
* 3 - replace the attribute byte with the value of ``attr`` and replace the
  graphic bytes with the value of ``byte``

``attr`` is an expression that is evaluated once for each background UDG over
which a foreground UDG is superimposed. ``attr`` may contain skool macros, and
recognises the following placeholders:

* ``$b`` - the background UDG attribute value
* ``$f`` - the foreground UDG attribute value

``byte`` is an expression that is evaluated once for each of the 8 graphic
bytes in a background UDG over which a foreground UDG is superimposed. ``byte``
may contain skool macros, and recognises the following placeholders:

* ``$b`` - the background UDG graphic byte value
* ``$f`` - the foreground UDG graphic byte value
* ``$m`` - the foreground UDG mask byte value (or 0 if the foreground UDG has
  no mask)

If the foreground frame has no mask, its contents are combined with those of
the background frame by OR operations.

For example::

  ; #UDGARRAY2(30000-30024-8)(*background)
  ; #UDG30032:30040(*object)
  ; #OVER0,1(background,object)
  ; #UDGARRAY*background(image)

This instance of the ``#OVER`` macro superimposes the frame created by the
``#UDG`` macro at tile coordinates (0, 1) on the background frame created by
the ``#UDGARRAY`` macro. The ``#UDGARRAY*`` macro then creates an image of the
modified background frame.

The integer parameters of the ``#OVER`` macro may contain
:ref:`replacement fields <replacementFields>`.

See :ref:`stringParameters` for details on alternative ways to supply the
``bg`` and ``fg`` parameters.

+---------+---------+
| Version | Changes |
+=========+=========+
| 8.5     | New     |
+---------+---------+

.. _PLOT:

#PLOT
-----
In HTML mode, the ``#PLOT`` macro sets, resets or flips a pixel in a frame
already created by one of the other image macros. ::

  #PLOTx,y[,value](frame)

* ``x`` and ``y`` are the coordinates of the pixel, relative to the top-left
  corner of the frame
* ``value`` is 0 to reset the pixel, 1 to set it (the default), or 2 to flip it
* ``frame`` is the name of the frame

For example::

  ; #UDG30000(*tile)
  ; #PLOT1,2(tile)
  ; #UDGARRAY*tile(tile)

This instance of the ``#PLOT`` macro sets the second pixel from the left in the
third row from the top in the frame created by the ``#UDG`` macro. The
``#UDGARRAY*`` macro then creates an image of the modified frame.

The integer parameters of the ``#PLOT`` macro may contain
:ref:`replacement fields <replacementFields>`.

+---------+---------+
| Version | Changes |
+=========+=========+
| 8.3     | New     |
+---------+---------+

.. _SCR:

#SCR
----
In HTML mode, the ``#SCR`` macro expands to an ``<img>`` element for an image
constructed from the display file and attribute file (or suitably arranged
graphic data and attribute bytes elsewhere in memory) of the current memory
snapshot (in turn constructed from the contents of the skool file). ::

  #SCR[scale,x,y,w,h,df,af,tindex,alpha][{CROP}][(fname)]

* ``scale`` is the scale of the image (default: 1)
* ``x`` is the x-coordinate of the top-left tile of the screen to include in
  the screenshot (default: 0)
* ``y`` is the y-coordinate of the top-left tile of the screen to include in
  the screenshot (default: 0)
* ``w`` is the width of the screenshot in tiles (default: 32)
* ``h`` is the height of the screenshot in tiles (default: 24)
* ``df`` is the base address of the display file (default: 16384)
* ``af`` is the base address of the attribute file (default: 22528)
* ``tindex`` is the index (0-15) of the entry in the palette to use as the
  transparent colour (default: 0; see :ref:`palette`)
* ``alpha`` is the alpha value (0-255) to use for the transparent colour
  (default: the value of the ``PNGAlpha`` parameter in the
  :ref:`ref-ImageWriter` section)
* ``CROP`` is the cropping specification (see :ref:`cropping`)
* ``fname`` is the name of the image file (see :ref:`Filenames`; default:
  '`scr`')

For example::

  ; #UDGTABLE
  ; { #SCR(loading) | This is the loading screen. }
  ; TABLE#

The integer parameters and the cropping specification of the ``#SCR`` macro
may contain :ref:`replacement fields <replacementFields>`.

+---------+------------------------------------------------------------------+
| Version | Changes                                                          |
+=========+==================================================================+
| 8.3     | Added support for replacement fields in the integer parameters   |
|         | and the cropping specification                                   |
+---------+------------------------------------------------------------------+
| 8.2     | Added the ``tindex`` and ``alpha`` parameters                    |
+---------+------------------------------------------------------------------+
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

  #UDGaddr[,attr,scale,step,inc,flip,rotate,mask,tindex,alpha][:MASK][{CROP}][(fname)]

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
* ``tindex`` is the index (0-15) of the entry in the palette to use as the
  transparent colour (default: 0; see :ref:`palette`)
* ``alpha`` is the alpha value (0-255) to use for the transparent colour
  (default: the value of the ``PNGAlpha`` parameter in the
  :ref:`ref-ImageWriter` section)
* ``MASK`` is the mask specification (see below)
* ``CROP`` is the cropping specification (see :ref:`cropping`)
* ``fname`` is the name of the image file (see :ref:`Filenames`); if not given,
  a name specified by the ``UDGFilename`` parameter in the :ref:`Paths` section
  will be used

The mask specification (``MASK``) takes the form::

  addr[,step]

* ``addr`` is the base address of the mask bytes to use for the UDG
* ``step`` is the interval between successive mask bytes (defaults to the value
  of ``step`` for the UDG)

Note that if any of the parameters in the mask specification is expressed using
arithmetic operations or skool macros, then the entire specification must be
enclosed in parentheses.

For example::

  ; Safe key UDG
  ;
  ; #HTML[#UDG39144,6(safe_key)]

In HTML mode, this instance of the ``#UDG`` macro expands to an ``<img>``
element for the image of the UDG at 39144 (which will be named `safe_key.png`),
with attribute byte 6 (INK 6: PAPER 0).

The integer parameters, mask specification and cropping specification of the
``#UDG`` macro may contain :ref:`replacement fields <replacementFields>`.

+---------+------------------------------------------------------------------+
| Version | Changes                                                          |
+=========+==================================================================+
| 8.3     | Added support for replacement fields in the integer parameters,  |
|         | mask specification and cropping specification                    |
+---------+------------------------------------------------------------------+
| 8.2     | Added the ``tindex`` and ``alpha`` parameters                    |
+---------+------------------------------------------------------------------+
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

  #UDGARRAYwidth[,attr,scale,step,inc,flip,rotate,mask,tindex,alpha](SPEC1[;SPEC2;...])[@ATTRS1[;ATTRS2;...]][{CROP}](fname)

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
* ``tindex`` is the index (0-15) of the entry in the palette to use as the
  transparent colour (default: 0; see :ref:`palette`)
* ``alpha`` is the alpha value (0-255) to use for the transparent colour
  (default: the value of the ``PNGAlpha`` parameter in the
  :ref:`ref-ImageWriter` section)
* ``CROP`` is the cropping specification (see :ref:`cropping`)
* ``fname`` is the name of the image file (see :ref:`Filenames`)

``SPEC1``, ``SPEC2`` etc. are UDG specifications for the sets of UDGs that make
up the array. The parentheses around them are optional, but recommended. If the
parentheses are omitted, ``SPEC1`` must be prefixed by a semicolon to separate
it from the main parameters. Each UDG specification has the form::

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

For example::

  ; Base sprite
  ;
  ; #HTML[#UDGARRAY4(32768-32888-8)(base_sprite.png)]

In HTML mode, this instance of the ``#UDGARRAY`` macro expands to an ``<img>``
element for the image of the 4x4 sprite formed by the 16 UDGs with base
addresses 32768, 32776, 32784 and so on up to 32888; the image file will be
named `base_sprite.png`.

The integer parameters, UDG specifications, attribute address range
specification and cropping specification of the ``#UDGARRAY`` macro may contain
:ref:`replacement fields <replacementFields>`.

See also :ref:`UDGS`.

+---------+-------------------------------------------------------------------+
| Version | Changes                                                           |
+=========+===================================================================+
| 8.6     | The UDG specifications may be enclosed in parentheses             |
+---------+-------------------------------------------------------------------+
| 8.3     | Added support for replacement fields in the integer parameters    |
|         | and the UDG, attribute address range and cropping specifications  |
+---------+-------------------------------------------------------------------+
| 8.2     | Added the ``tindex`` and ``alpha`` parameters                     |
+---------+-------------------------------------------------------------------+
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

.. _UDGS:

#UDGS
-----
In HTML mode, the ``#UDGS`` macro expands to an ``<img>`` element for the image
of a rectangular array of UDGs (8x8 blocks of pixels). ::

  #UDGSwidth,height[,scale,flip,rotate,mask,tindex,alpha][{CROP}](fname)(uframe)

* ``width`` is the width of the array
* ``height`` is the height of the array
* ``scale`` is the scale of the image
* ``flip`` is 1 to flip the array of UDGs horizontally, 2 to flip it
  vertically, 3 to flip it both ways, or 0 to leave it as it is (default: 0)
* ``rotate`` is 1 to rotate the array of UDGs 90 degrees clockwise, 2 to rotate
  it 180 degrees, 3 to rotate it 90 degrees anticlockwise, or 0 to leave it as
  it is (default: 0)
* ``mask`` is the type of mask to apply (see :ref:`masks`)
* ``tindex`` is the index (0-15) of the entry in the palette to use as the
  transparent colour (see :ref:`palette`)
* ``alpha`` is the alpha value (0-255) to use for the transparent colour
* ``CROP`` is the cropping specification (see :ref:`cropping`)
* ``fname`` is the name of the image file (see :ref:`Filenames`)
* ``uframe`` is expanded once for each slot in the array, and may contain the
  placeholders ``$x`` and ``$y`` for the coordinates of the slot; the resulting
  text is interpreted as the name of the frame whose top-left UDG should be
  placed into the slot

For example::

  #UDGS2,2(sprite)(
    #LET(a=30000+9*(2*$y+$x))
    #UDG({a}+1,#PEEK({a}))(*udg)
    udg
  )

This instance of the ``#UDGS`` macro expands to an ``<img>`` element for the
image of the 2x2 sprite formed by the four 9-byte UDG definitions (where the
first byte is the attribute value, and the next eight bytes are the graphic
data) with base addresses 30000, 30009, 30018 and 30027. The image file is
named `sprite.png`.

Unless specified by macro arguments, the scale, mask type, transparency index
and alpha value of the image created by the ``#UDGS`` macro are copied from the
last frame used to populate the array (corresponding to the bottom-right UDG).

The integer parameters and the ``uframe`` parameter of the ``#UDGS`` macro may
contain :ref:`replacement fields <replacementFields>`.

See :ref:`stringParameters` for details on alternative ways to supply the
``uframe`` parameter.

See also :ref:`UDGARRAY`.

+---------+---------+
| Version | Changes |
+=========+=========+
| 8.6     | New     |
+---------+---------+

.. _Filenames:

Filenames
---------
The ``fname`` parameter of the :ref:`FONT`, :ref:`SCR`, :ref:`UDG`,
:ref:`UDGARRAY` and :ref:`UDGS` macros can be used to specify not only an image
filename, but also its exact location, the ``alt`` attribute of the ``<img>``
element, and a frame name (see :ref:`Animation`).

If ``fname`` contains an image path ID replacement field (e.g.
``{ScreenshotImagePath}/udgs``), the corresponding parameter value from the
:ref:`Paths` section will be substituted.

If ``fname`` starts with a '/', the filename is taken to be relative to the
root of the HTML disassembly.

If ``fname`` contains no image path ID replacement fields and does not start
with a '/', the filename is taken to be relative to the directory defined by
one of the following parameters in the :ref:`paths` section, depending on the
macro being used:

* ``FontImagePath`` - :ref:`FONT`
* ``ScreenshotImagePath`` - :ref:`SCR`
* ``UdgImagePath`` - :ref:`UDG`, :ref:`UDGARRAY` and :ref:`UDGS`

If ``fname`` does not end with '`.png`', that suffix will be appended.

If an image with the given filename doesn't already exist, it will be created.

The value of the ``alt`` attribute in the ``<img>`` element can be specified by
appending a ``|`` character and the required text to the filename. For
example::

  #SCR(screenshot1|Screenshot 1)

This ``#SCR`` macro creates an image named `screenshot1.png` with alt text
'Screenshot 1'.

.. _Animation:

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

  #UDGARRAY*(FRAME1[;FRAME2;...])(fname)

``FRAME1``, ``FRAME2`` etc. are frame specifications. The parentheses around
them are optional, but recommended. Each frame specification has the form::

  name[,delay,x,y]

* ``name`` is the name of the frame
* ``delay`` is the delay between this frame and the next in 1/100ths of a
  second; it also sets the default delay for any frames that follow (default:
  32)
* ``x`` and ``y`` are the coordinates at which to render the frame, relative to
  the top-left corner of the first frame (default: (0,0))

For example::

  ; #UDGTABLE {
  ; #FONT:(hello)$3D00(hello*) |
  ; #FONT:(there)$3D00(there*) |
  ; #FONT:(peeps)$3D00(peeps*) |
  ; #UDGARRAY*(hello,50;there;peeps)(hello_there_peeps)
  ; } TABLE#

The ``#FONT`` macros create the required frames (and write images of them); the
``#UDGARRAY`` macro combines the three frames into a single animated image,
with a delay of 0.5s between each frame.

The integer parameters of a frame specification may contain
:ref:`replacement fields <replacementFields>`.

Note that the first frame of an animated image determines the size of the image
as a whole. Therefore, the region defined by the width, height and coordinates
of any subsequent frame must fall entirely inside the first frame.

+---------+-------------------------------------------------------------------+
| Version | Changes                                                           |
+=========+===================================================================+
| 8.6     | The frame specifications may be enclosed in parentheses           |
+---------+-------------------------------------------------------------------+
| 8.3     | Added the ``x`` and ``y`` parameters to the frame specification;  |
|         | added support for replacement fields in the integer parameters of |
|         | a frame specification                                             |
+---------+-------------------------------------------------------------------+
| 3.6     | New                                                               |
+---------+-------------------------------------------------------------------+

.. _cropping:

Cropping
--------
The :ref:`COPY`, :ref:`FONT`, :ref:`SCR`, :ref:`UDG`, :ref:`UDGARRAY` and
:ref:`UDGS` macros accept a cropping specification (``CROP``) which takes the
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

The parameters of the cropping specification may contain
:ref:`replacement fields <replacementFields>`.

.. _masks:

Masks
-----
The :ref:`COPY`, :ref:`UDG`, :ref:`UDGARRAY` and :ref:`UDGS` macros accept a
``mask`` parameter that determines what kind of mask to apply to each UDG. The
supported values are:

* 0 - no mask
* 1 - OR-AND mask (this is the default)
* 2 - AND-OR mask

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
masked images actually transparent, set ``PNGAlpha=0`` in the
:ref:`ref-ImageWriter` section.

.. _palette:

Palette
-------
Images created by the image macros use colours drawn from a palette of 16
entries:

* 0 - transparent
* 1 - black
* 2 - blue
* 3 - red
* 4 - magenta
* 5 - green
* 6 - cyan
* 7 - yellow
* 8 - white
* 9 - bright blue
* 10 - bright red
* 11 - bright magenta
* 12 - bright green
* 13 - bright cyan
* 14 - bright yellow
* 15 - bright white

The RGB values for these colours are defined in the :ref:`ref-Colours` section.

The index values (0-15) may be used by an image macro's ``tindex`` parameter to
specify a transparent colour to use other than the default (0). The palette
entry specified by ``tindex``, if not 0, will be used as the transparent colour
only if the image does not already contain any transparent bits produced by a
:ref:`mask <masks>`. In an animated image, the ``tindex`` and ``alpha`` values
on the first frame take effect; any ``tindex`` and ``alpha`` values on the
second or subsequent frames are ignored.

For example::

  #UDG30000,attr=2,tindex=1,alpha=0

This ``#UDG`` macro creates an image of the UDG at 30000 with red INK and black
PAPER (``attr=2``), black as the transparent colour (``tindex=1``), and full
transparency (``alpha=0``).

Snapshot macros
^^^^^^^^^^^^^^^
The :ref:`POKES`, :ref:`POPS` and :ref:`PUSHS` macros (described in the
following sections) may be used to manipulate the memory snapshot that is built
from the skool file. Each macro expands to an empty string.

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

The parameter string of the ``#POKES`` macro may contain
:ref:`replacement fields <replacementFields>`.

See also :ref:`PEEK`.

+---------+------------------------------------------------------------------+
| Version | Changes                                                          |
+=========+==================================================================+
| 8.3     | Added support for replacement fields in the parameter string     |
+---------+------------------------------------------------------------------+
| 5.1     | Added support for arithmetic expressions and skool macros in the |
|         | parameter string                                                 |
+---------+------------------------------------------------------------------+
| 3.1     | Added support for ASM mode                                       |
+---------+------------------------------------------------------------------+
| 2.3.1   | Added support for multiple addresses                             |
+---------+------------------------------------------------------------------+

.. _POPS:

#POPS
-----
The ``#POPS`` macro removes the current internal memory snapshot and replaces
it with the one that was previously saved by a ``#PUSHS`` macro. ::

  #POPS

+---------+----------------------------+
| Version | Changes                    |
+=========+============================+
| 3.1     | Added support for ASM mode |
+---------+----------------------------+

.. _PUSHS:

#PUSHS
------
The ``#PUSHS`` macro saves the current internal memory snapshot, and replaces
it with an identical copy with a given name. ::

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

.. _definingMacrosWithDEF:

Defining macros with #DEF
^^^^^^^^^^^^^^^^^^^^^^^^^
By using the :ref:`DEF` macro, it is possible to define new macros based on
existing ones without writing any Python code. Some examples are given below.

#ASM
----
There is the :ref:`HTML` macro for inserting content in HTML mode only, but
there is no corresponding macro for inserting content in ASM mode only. The
following ``#DEF`` macro defines an ``#ASM`` macro to fill that gap::

  #DEF(#ASM #IF({mode[asm]}))

For example::

  #ASM(This text appears only in ASM mode.)

#ASMUDG
-------
The :ref:`UDG` macro is not supported in ASM mode, but ``#DEF`` can define an
``#ASMUDG`` macro (based on the ``#ASM`` macro defined above) that is::

  #DEF(#ASMUDG(a) #ASM(#LIST(,) #FOR($a,$a+7)(u,{ |#FOR(7,0,-1)(n,#IF(#PEEKu&2**n)(*, ))| }) LIST#))

For example::

  ; #ASMUDG30000
   30000 DEFB 48,72,136,144,104,4,10,4

If conversion of DEFB statements has been switched on in ASM mode by the
:ref:`assemble` directive (e.g. ``@assemble=,1``), this ``#ASMUDG`` macro
produces the following output::

  ; |  **    |
  ; | *  *   |
  ; |*   *   |
  ; |*  *    |
  ; | ** *   |
  ; |     *  |
  ; |    * * |
  ; |     *  |

#TILE, #TILES
-------------
Suppose the game you're disassembling arranges tiles in groups of nine bytes:
the attribute byte first, followed by the eight graphic bytes. If there is a
tile at 32768, then::

  #UDG(32769,#PEEK32768)

will create an image of it. If you want to create several tile images, this
syntax can get cumbersome; it would be easier if you could supply just the
address of the attribute byte. The following ``#DEF`` macro defines a ``#TILE``
macro that creates a tile image given an attribute byte address::

  #DEF(#TILE(a) #UDG($a+1,#PEEK$a))

Now you can create an image of the tile at 32768 like this::

  #TILE32768

If you have several nine-byte tiles arranged one after the other, you might
want to create images of all of them in a single row of a ``#UDGTABLE``. The
following ``#DEF`` macro defines a ``#TILES`` macro (based on the ``#TILE``
macro already defined) for this purpose::

  #DEF(#TILES(a,m) #FOR($a,$a+9*($m-1),9)(n,#TILEn, | ))

Now you can create a ``#UDGTABLE`` of images of a series of 10 tiles starting
at 32768 like this::

  #UDGTABLE { #TILES32768,10 } TABLE#
