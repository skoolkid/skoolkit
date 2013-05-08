.. _controlFiles:

Control files
=============
A control file contains a list of start addresses of code and data blocks. This
information can be used by :ref:`sna2skool.py <sna2skool.py>` to organise a
`skool` file into corresponding code and data blocks.

Each block address in a control file is marked with a 'control directive',
which is a single letter that indicates what the block contains:

* ``b`` indicates a data block
* ``c`` indicates a code block
* ``g`` indicates a game status buffer entry
* ``i`` indicates a block that should be ignored
* ``t`` indicates a block containing text
* ``u`` indicates an unused block of memory
* ``w`` indicates a block containing words (two-byte values)
* ``z`` indicates an unused block containing all zeroes

(If these letters remind you of the valid characters that may appear in the
first column of each line of a :ref:`skool file <skoolFileFormat>`, that is no
coincidence.)

For example::

  c 24576 Do stuff
  b 24832 Important data
  t 25088 Interesting messages
  u 25344 Unused

This control file declares that:

* Everything before 24576 should be ignored
* There is a routine at 24576-24831 which should be titled 'Do stuff'
* There is data at 24832-25087
* There is text at 25088-25343
* Everything from 25344 onwards is unused (but should still be disassembled as
  data)

Addresses may be written as hexadecimal numbers, too; the equivalent example
control file using hexadecimal notation would be::

  c $6000 Do stuff
  b $6100 Important data
  t $6200 Interesting messages
  u $6300 Unused

Besides the declaration of block types, addresses and titles, the control file
syntax also supports the declaration of the following things:

* Block descriptions
* Register values
* Mid-block comments
* Block end comments
* Sub-block types and comments
* DEFB/DEFM/DEFW/DEFS statement lengths in data, text and unused sub-blocks
* ASM directives (except block directives)

The syntax for declaring these things is described in the following sections.

Block descriptions
------------------
To provide a description for a code block at 24576 (for example), use the ``D``
directive thus::

  c 24576 This is the title of the routine at 24576
  D 24576 This is the description of the routine at 24576.

If the description consists of two or more paragraphs, each one should be
declared with a separate ``D`` directive::

  D 24576 This is the first paragraph of the description of the routine at 24576.
  D 24576 This is the second paragraph of the description of the routine at 24576.

Register values
---------------
To declare the values of the registers upon entry to the routine at 24576, add
one line per register with the ``R`` directive thus::

  R 24576 A An important value in the accumulator
  R 24576 DE Display file address

Mid-block comments
------------------
To declare a mid-block comment that will appear above the instruction at 24592,
use the ``D`` directive thus::

  D 24592 The next section of code does something really important.

If the mid-block comment consists of two or more paragraphs, each one should be
declared with a separate ``D`` directive::

  D 24592 This is the first paragraph of the mid-block comment.
  D 24592 This is the second paragraph of the mid-block comment.

Block end comments
------------------
To declare a comment that will appear at the end of the routine at 24576, use
the ``E`` directive thus::

  E 24576 And so the work of this routine is done.

If the block end comment consists of two or more paragraphs, each one should be
declared with a separate ``E`` directive::

  E 24576 This is the first paragraph of the end comment for the routine at 24576.
  E 24576 This is the second paragraph of the end comment for the routine at 24576.

Sub-block syntax
----------------
Sometimes a block marked as one type (code, data, text, or whatever) may
contain instructions or statements of another type. For example, a word (``w``)
block may contain the odd non-word here and there. To declare such sub-blocks
whose type does not match that of the containing block, use the following
syntax::

  w 32768 A block containing mostly words
  B 32800,3 But here's a sub-block of 3 bytes at 32800
  T 32809,8 And an 8-byte text string at 32809
  C 32821,10 And 10 bytes of code at 32821 too?

The directives (``B``, ``T`` and ``C``) used here to mark the sub-blocks are
the upper case equivalents of the directives used to mark top-level blocks
(``b``, ``t`` and ``c``). The comments at the end of these sub-block
declarations are taken as instruction-level comments and will appear as such in
the resultant `skool` file.

If an instruction-level comment spans a group of two or more sub-blocks of
different types, it must be declared with an ``M`` directive::

  M 40000,21 This comment covers the following 3 sub-blocks
  B 40000,3
  W 40003,10
  T 40013,8

If the length parameter is omitted from an ``M`` directive, the comment is
assumed to cover all sub-blocks from the given start address to the end of the
top-level block.

Three bits of sub-block syntax left. First,  the blank sub-block directive::

  c 24576 A great routine
    24580,11 A great section of code at 24580

This is equivalent to::

  c 24576 A great routine
  C 24580,11 A great section of code at 24580

That is, the the type of a blank sub-block directive is taken to be the same as
that of the parent block.

Next, the address range::

  c 24576 A great routine
    24580-24590 A great section of code at 24580

This is equivalent to::

  c 24576 A great routine
    24580,11 A great section of code at 24580

That is, you can specify the extent of a sub-block using either an address
range, or an address and a length.

Finally, the implicit sub-block extent::

  c 24576 A great routine
    24580 A great section of code at 24580
    24588,10 Another great section of code at 24590

This is equivalent to::

  c 24576 A great routine
    24580,8 A great section of code at 24580
    24588,10 Another great section of code at 24588

But the declaration of the length (8) of the sub-block at 24580 is redundant,
because the sub-block is implicitly terminated by the declaration of the
sub-block at 24588 that follows. This is exactly how top-level block
declarations work: each top-level block is implicitly terminated by the
declaration of the next one.

Statement lengths in 'B', 'T', 'W' and 'Z' sub-blocks
-----------------------------------------------------
Normally, a ``B`` sub-block declared thus::

  B 24580,12 Interesting data

would result in something like this in the corresponding skool file::

  24580 DEFB 1,2,3,4,5,6,7,8 ; {Interesting data
  24588 DEFB 9,10,11,12      ; }

But what if you wanted to split the data in this sub-block into groups of 3
bytes each? That can be achieved with::

  B 24580,12,3 Interesting data

which would give::

  24580 DEFB 1,2,3    ; {Interesting data
  24583 DEFB 4,5,6
  24586 DEFB 7,8,9
  24589 DEFB 10,11,12 ; }

That is, in a ``B`` directive, the desired DEFB statement lengths may be given
as a comma-separated list of numbers following the sub-block length parameter,
and the final number in the list is used for all remaining data in the block.
So, for example::

  B 24580,12,1,2,3 Interesting data

would give::

  24580 DEFB 1        ; {Interesting data
  24581 DEFB 2,3
  24583 DEFB 4,5,6
  24586 DEFB 7,8,9
  24589 DEFB 10,11,12 ; }

If the statement length list contains sequences of two or more identical
lengths, as in::

  B 24580,21,2,2,2,2,2,2,1,1,1,3

then it may be abbreviated thus::

  B 24580,21,2*6,1*3,3

The same syntax can be used for ``T``, ``W`` and ``Z`` sub-blocks too. For
example::

  Z 32768,100,25 Four 25-byte chunks of zeroes

would give::

  32768 DEFS 25 ; {Four 25-byte chunks of zeroes
  32793 DEFS 25
  32818 DEFS 25
  32843 DEFS 25 ; }

DEFB and DEFM statements may contain both bytes and strings; for example::

  40000 DEFM "Hi ",5
  40004 DEFB 4,"go"

Such statements can be encoded in a control file thus::

  T 40000,4,3:B1
  B 40004,3,1:T2

That is, the length of a string in a DEFB statement is prefixed by ``T``, the
length of a sequence of bytes in a DEFM statement is prefixed by ``B``, and the
lengths of all strings and byte sequences are separated by colons. This
notation can also be combined with the '*' notation; for example::

  T 50000,8,2:B2*2

which is equivalent to::

  T 50000,8,2:B2,2:B2

ASM directives
--------------
To declare an ASM directive for a block or an individual instruction, use the
following syntax::

  ; @directive:address[=value]

where:

* ``directive`` is the directive name
* ``address`` is the address of the block or instruction to which the directive
  applies
* ``value`` is the value of the directive (if it requires one)

For example, to declare a :ref:`label` directive for the instruction at 32768::

  ; @label:32768=LOOP

Note that neither ASM block directives (such as the :ref:`bfixBlockDirectives`)
nor the exact location of :ref:`org`, :ref:`writer`, :ref:`start`, :ref:`end`,
:ref:`ignoreua` and :ref:`set` ASM directives can be preserved using this
syntax.

Control file comments
---------------------
A comment may be added to a control file by starting a line with something
other than a space, a control directive, or ``; @``. For example::

  ; This is a comment
  # This is another comment
  % This is yet another comment

Limitations
-----------
A control file can be useful in the early stages of developing a `skool` file
for reorganising code and data blocks, but it cannot preserve the following
elements:

* ASM block directives
* the exact locations of `@org`, `@writer`, `@start`, `@end`, `@ignoreua` and
  `@set` ASM directives
* data definition entries ('d' blocks) and remote entries ('r' blocks)
* comments that are not part of a code or data block

:ref:`skoolFileTemplates`, however, can preserve all of these elements, and so
may be a better choice for `skool` files that contain any of them.

Revision history
----------------
+---------+-------------------------------------------------------------------+
| Version | Changes                                                           |
+=========+===================================================================+
| 1.0.7   | Added support for block titles, block descriptions, register      |
|         | values, mid-block comments, block end comments, sub-block types   |
|         | and instruction-level comments                                    |
+---------+-------------------------------------------------------------------+
| 2.0.6   | Added support for hexadecimal numbers                             |
+---------+-------------------------------------------------------------------+
| 2.1     | Added support for DEFB statement lengths in ``B`` sub-blocks      |
+---------+-------------------------------------------------------------------+
| 2.1.1   | Added the ``M`` directive                                         |
+---------+-------------------------------------------------------------------+
| 2.1.2   | Added support for DEFM, DEFW and DEFS statement lengths in ``T``, |
|         | ``W`` and ``Z`` sub-blocks                                        |
+---------+-------------------------------------------------------------------+
| 2.2     | Added support for the ``*`` notation in DEFB, DEFM, DEFW and DEFS |
|         | statement length lists in ``B``, ``T``, ``W`` and ``Z``           |
|         | sub-blocks                                                        |
+---------+-------------------------------------------------------------------+
| 2.4     | Added support for non-block ASM directives                        |
+---------+-------------------------------------------------------------------+
| 3.1.4   | Added support for DEFB and DEFM statements that contain both      |
|         | strings and bytes                                                 |
+---------+-------------------------------------------------------------------+
