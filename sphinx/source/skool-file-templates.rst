.. _skoolFileTemplates:

Skool file templates
====================
.. note::
   Skool file templates and :ref:`skool2sft.py` are deprecated since version
   7.2. Use :ref:`control files <controlFiles>` and :ref:`skool2ctl.py`
   instead.

A skool file template defines the basic structure of a skool file, but, unlike
a skool file, contains directives on how to disassemble a program into Z80
instructions instead of the Z80 instructions themselves. The directives are
similar to those that may appear in a control file.

The :ref:`skool2sft.py` command can generate a skool file template from an
existing skool file; the :ref:`sna2skool.py` command can then generate a skool
file from the template and an appropriate snapshot.

.. _skoolFileTemplateFormat:

Skool file template format
--------------------------
A skool file template has the same layout as a skool file, except that the
lines in ``b``, ``c``, ``g``, ``i``, ``s``, ``t``, ``u`` and ``w`` blocks that
correspond to Z80 instructions look like this::

  xX#####,N[;c[ comment]]

where:

* ``x`` is one of the characters ``* bcgistuw`` (with the same meaning as in a
  :ref:`skool file <skoolFiles>`)
* ``X`` is one of the characters ``BCSTW`` (with the same meaning as in a
  :ref:`control file <controlFiles>`), or ``I`` (meaning the instruction field
  is blank, as may be the case in the first line of an ``i`` block)
* ``#####`` is the address at which to start disassembling
* ``N`` is the number of bytes to disassemble (or a list of sublengths; see
  :ref:`sftSubblockSyntax`)
* ``c`` is the index of the column in which the comment marker (``;``) appears
  in the line (if it does appear)
* ``comment``, if present, is the instruction-level comment for the line on
  which the instruction occurs

If a comment for a single instruction spans two or more lines in a skool file,
as in::

  c24296 CALL 57935    ; This comment is too long to fit on a single line, so
                       ; we use two lines

then it will be rendered in the skool file template thus::

  cC24296,3;21 This comment is too long to fit on a single line, so
   ;21 we use two lines

.. _sftSubblockSyntax:

Sub-block syntax
----------------
The syntax for specifying ``B``, ``C``, ``S``, ``T`` and ``W`` sub-blocks is
analogous to the syntax used in :ref:`control files <controlFiles>`. A brief
summary of the syntax is given here.

Sequences of DEFB statements can be declared on a single line by a
comma-separated list of sublengths thus::

  bB40960,8*2,5

which is equivalent to::

  bB40960,8
   B40968,8
   B40976,5

The same syntax also applies for declaring sequences of DEFM, DEFS and DEFW
statements.

DEFB and DEFM statements may contain both strings and bytes; for example::

  b30000 DEFB 1,2,3,4,"Hello!"
   30010 DEFM 5,6
   30012 DEFM "B",7,8

Such statements are preserved in a skool file template thus::

  bB30000,4:T6
   T30010,B2,1:B2

DEFB, DEFM, DEFS and DEFW statements may contain numeric values in various
bases or as characters. For example::

  b40000 DEFB %10101010,23,43,$5F
   40004 DEFB -1
   40005 DEFB %11110000
   40006 DEFB $2B,$80
   40008 DEFS 8,"!"

These statements are preserved in a skool file template thus::

  bB40000,b1:d2:h1,m1,b1,h2
   S40008,8:c

Instruction operands may also contain numeric values in various bases or as
characters. For example::

  c50000 LD A,%00011000
   50002 LD B,"!"
   50004 LD (IX+$1A),%00001111

These instructions are preserved in a skool file template by using ``b``
(binary), ``c`` (character), ``d`` (decimal) and ``h`` (hexadecimal) prefixes
on sublength parameters thus::

  cC50000,b2,c2,hb4

Skool file template comments
----------------------------
Any line that begins with a hash character (``#``) is ignored by
`sna2skool.py`, and will not show up in the skool file.

Revision history
----------------
+---------+-------------------------------------------------------------------+
| Version | Changes                                                           |
+=========+===================================================================+
| 7.1     | Added support for specifying that numeric values in instruction   |
|         | operands and DEFB, DEFM, DEFS and DEFW statements be rendered as  |
|         | negative decimal numbers                                          |
+---------+-------------------------------------------------------------------+
| 7.0     | Added support for preserving 'inverted' characters (with bit 7    |
|         | set); the byte value in an ``S`` directive may be left blank      |
+---------+-------------------------------------------------------------------+
| 5.1     | Added support for preserving ``i`` blocks in the same way as code |
|         | and data blocks (instead of verbatim)                             |
+---------+-------------------------------------------------------------------+
| 4.5     | Added support for specifying character values in DEFS statements  |
+---------+-------------------------------------------------------------------+
| 4.4     | Added support for specifying that numeric values in instruction   |
|         | operands be rendered as characters or in a specific base; added   |
|         | support for specifying character values in DEFW statements        |
+---------+-------------------------------------------------------------------+
| 3.7     | Added support for binary numbers; added support for specifying    |
|         | the base of numeric values in DEFB, DEFM, DEFS and DEFW           |
|         | statements; added the ``s`` and ``S`` directives and support for  |
|         | DEFS statements with non-zero byte values                         |
+---------+-------------------------------------------------------------------+
| 3.1.4   | Added support for DEFB and DEFM statements that contain both      |
|         | strings and bytes                                                 |
+---------+-------------------------------------------------------------------+
| 2.4     | New                                                               |
+---------+-------------------------------------------------------------------+
