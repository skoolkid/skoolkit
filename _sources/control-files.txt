.. _controlFiles:

Control files
=============
A control file contains a list of start addresses of code and data blocks. This
information can be used by :ref:`sna2skool.py <sna2skool.py>` to organise a
skool file into corresponding code and data blocks.

Each block address in a control file is marked with a 'control directive',
which is a single letter that indicates what the block contains:

* ``b`` indicates a data block
* ``c`` indicates a code block
* ``g`` indicates a game status buffer entry
* ``i`` indicates a block that will be ignored
* ``s`` indicates a block containing bytes that are all the same value
  (typically unused zeroes)
* ``t`` indicates a block containing text
* ``u`` indicates an unused block of memory
* ``w`` indicates a block containing words (two-byte values)

(If these letters remind you of the valid characters that may appear in the
first column of each line of a :ref:`skool file <skoolFileFormat>`, that is no
coincidence.)

For example::

  c 24576 Do stuff
  b 24832 Important data
  t 25088 Interesting messages
  u 25344 Unused

This control file declares that:

* Everything before 24576 will be ignored
* There is a routine at 24576-24831 titled 'Do stuff'
* There is data at 24832-25087
* There is text at 25088-25343
* Everything from 25344 onwards is unused (but will still be disassembled as
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
* Block start comments
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

If the description consists of two or more paragraphs, declare each one with a
separate ``D`` directive::

  D 24576 This is the first paragraph of the description of the routine at 24576.
  D 24576 This is the second paragraph of the description of the routine at 24576.

Register values
---------------
To declare the values of the registers upon entry to the routine at 24576, add
one line per register with the ``R`` directive thus::

  R 24576 A An important value in the accumulator
  R 24576 DE Display file address

Block start comments
--------------------
To declare a block start comment that will appear above the instruction at
24576, use the ``N`` directive thus::

  N 24576 And so this routine begins.

If the start comment consists of two or more paragraphs, declare each one with
a separate ``N`` directive::

  N 24576 This is the first paragraph of the start comment.
  N 24576 This is the second paragraph of the start comment.

Mid-block comments
------------------
To declare a mid-block comment that will appear above the instruction at 24592,
use the ``N`` directive thus::

  N 24592 The next section of code does something really important.

If the mid-block comment consists of two or more paragraphs, declare each one
with a separate ``N`` directive::

  N 24592 This is the first paragraph of the mid-block comment.
  N 24592 This is the second paragraph of the mid-block comment.

Block end comments
------------------
To declare a comment that will appear at the end of the routine at 24576, use
the ``E`` directive thus::

  E 24576 And so the work of this routine is done.

If the block end comment consists of two or more paragraphs, declare each one
with a separate ``E`` directive::

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
  C 32821,10 And 10 bytes of code at 32821
  S 32831,17 Followed by 17 zeroes at 32831

The directives (``B``, ``T``, ``C`` and ``S``) used here to mark the sub-blocks
are the upper case equivalents of the directives used to mark top-level blocks
(``b``, ``t``, ``c`` and ``s``). The comments at the end of these sub-block
declarations are taken as instruction-level comments and will appear as such in
the resultant skool file.

If an instruction-level comment spans a group of two or more sub-blocks, it
must be declared with an ``M`` directive::

  M 40000,21 This comment covers the following 3 sub-blocks
  B 40000,3
  W 40003,10
  T 40013,8

An ``M`` directive with no length parameter covers all sub-blocks from the
given start address to either the next mid-block comment or the end of the
containing block (whichever is closer).

If a sub-block directive is left blank, then it is assumed to be of the same
type as the containing block. So in::

  c 24576 A great routine
    24580,8 A great section of code at 24580

the sub-block at 24580 is assumed to be of type ``C``.

If the length parameter is omitted from a sub-block directive, then it is
assumed to end where the next sub-block starts. So in::

  c 24576 A great routine
    24580 A great section of code at 24580
    24588,10 Another great section of code at 24588

the sub-block at 24580 has length 8, because it is implicitly terminated by the
following sub-block at 24588.

Sub-block lengths
-----------------
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
as a comma-separated list of "sublengths" following the main length parameter,
and the final sublength in the list is used for all remaining data in the
block. So, for example::

  B 24580,12,1,2,3 Interesting data

would give::

  24580 DEFB 1        ; {Interesting data
  24581 DEFB 2,3
  24583 DEFB 4,5,6
  24586 DEFB 7,8,9
  24589 DEFB 10,11,12 ; }

Note that even if sublengths are specified, the main length parameter can be
omitted (by leaving it blank) if the sub-block is implicitly terminated by the
next sub-block. For example::

  B 24580,,1,2,3 No need to specify the main length parameter here...
  B 24592,10 ...because this sub-block implies that it must be 12

If the sublength list contains sequences of two or more identical lengths, as
in::

  B 24580,21,2,2,2,2,2,2,1,1,1,3

then it may be abbreviated thus::

  B 24580,21,2*6,1*3,3

Sublengths can be used on ``C``, ``S``, ``T`` and ``W`` directives too (though
on ``C`` directives they are really only useful for specifying
:ref:`number bases <numberBases>`). For example::

  S 32768,100,25 Four 25-byte chunks of zeroes

would give::

  32768 DEFS 25 ; {Four 25-byte chunks of zeroes
  32793 DEFS 25
  32818 DEFS 25
  32843 DEFS 25 ; }

DEFB and DEFM statements may contain both bytes and strings; for example::

  40000 DEFM "Hi ",5
  40004 DEFB 4,"go"

Such statements can be encoded in a control file thus::

  T 40000,,3:B1
  B 40004,3,1:T2

That is, the length of a string in a DEFB statement is prefixed by ``T``, the
length of a sequence of bytes in a DEFM statement is prefixed by ``B``, and the
lengths of all strings and byte sequences are separated by colons. This
notation can also be combined with the '*' notation; for example::

  T 50000,8,2:B2*2

which is equivalent to::

  T 50000,8,2:B2,2:B2

A character code may be 'inverted' (i.e. have bit 7 set), typically to indicate
the end of a string::

  49152 DEFM "Hell","o"+128

This can be encoded thus::

  T 49152,5,4:1

and the terminal character will be restored in the same format.

.. _dotDirective:

The dot and colon directives
----------------------------
The dot (``.``) directive provides an alternative method of specifying a
comment for a top-level or sub-block directive. For example, instead of::

  c 30000 This is the title of the entry

you could write::

  c 30000
  . This is the title of the entry

At first glance this does not appear to be an improvement. But one advantage of
the dot directive is that a comment can be split over multiple lines, and the
line breaks are preserved when restored. This makes it much easier to read and
write a long comment, especially if it contains a ``#LIST`` or ``#TABLE``
macro. For example::

  D 30000 #TABLE(default) { =h Header 1 | =h Header 2 } { Cell 1      | Cell 2 } TABLE#

can be recast like this::

  D 30000
  . #TABLE(default)
  . { =h Header 1 | =h Header 2 }
  . { Cell 1      | Cell 2 }
  . TABLE#

In addition, a sequence of ``D``, ``N``, ``E`` or ``R`` directives at the same
address (one for each paragraph or register description) can be reduced to just
one of those directives followed by a sequence of dot directives::

  N 30000
  . Paragraph 1.
  . .
  . Paragraph 2.

In fact, the dot directive can be used instead of ``D``, ``R`` and ``N``
directives when specifying an entry header. For example::

  c 30000
  . This is the title of the entry.
  .
  . This is the description.
  .
  .   A Input
  . O:B Output
  .
  . This is the start comment.

Note, however, that this works only if the entry header contains no ASM
directives.

The dot directive also makes it simpler to preserve ``@*sub`` and ``@*fix``
directives that replace part of an instruction-level comment. For example,
consider the following skool file snippet::

   49155 LD A,(HL)     ; {Increase the sprite's x-coordinate by
  @bfix=ADD A,3        ; three}
   49156 ADD A,2       ; two (which is a bug)}

When preserved without dot directives, this becomes::

  @ 49156 bfix=ADD A,3        ; three}
  C 49155,3 Increase the sprite's x-coordinate by two (which is a bug)

which is restored incorrectly by `sna2skool.py` (using the default line width
of 79 characters) as::

   49155 LD A,(HL)     ; {Increase the sprite's x-coordinate by two (which is a
  @bfix=ADD A,3        ; three}
   49156 ADD A,2       ; bug)}

This problem could be addressed by recasting the comment lines in the skool
file and adding a ``@bfix`` directive for 'LD A,(HL)'::

  @bfix=               ; {Increase the sprite's x-coordinate by three
   49155 LD A,(HL)     ; {Increase the sprite's x-coordinate by two (which is a
  @bfix=ADD A,3        ; }
   49156 ADD A,2       ; bug)}

which would be preserved without dot directives as::

  @ 49155 bfix=               ; {Increase the sprite's x-coordinate by three
  @ 49156 bfix=ADD A,3        ; }
  C 49155,3 Increase the sprite's x-coordinate by two (which is a bug)

But this solution requires two ``@bfix`` directives instead of one, repeats the
part of the comment that doesn't change, and could still be restored
incorrectly if `sna2skool.py` is used with a line width other than the default.

It is much easier and more robust to use dot directives to preserve the
original form in a way that will always be restored correctly::

  @ 49156 bfix=ADD A,3        ; three}
  C 49155,3
  . Increase the sprite's x-coordinate by
  . two (which is a bug)

Finally, the colon (``:``) directive can be used alongside the dot directive to
force an instruction comment continuation line where there would not otherwise
be one. For example::

  B 31995,2,1
  . The first two comment lines
  : belong to the first DEFB.
  . And this comment line belongs to the second DEFB.

would be restored as::

  b31995 DEFB 0        ; {The first two comment lines
                       ; belong to the first DEFB.
   31996 DEFB 0        ; And this comment line belongs to the second DEFB.}

The colon directive is rarely needed, but it is useful in cases like the one
above where an ``@*sub`` or ``@*fix`` directive is used to replace all or part
of the comment of the second instruction only::

   49155 LD A,(HL)     ; {Having adjusted the sprite's y-coordinate, we now
                       ; increase its x-coordinate by
  @bfix=ADD A,3        ; three}
   49156 ADD A,2       ; two (which is a bug)}

This can be preserved as::

  @ 49156 bfix=ADD A,3        ; three}
  C 49155,3
  . Having adjusted the sprite's y-coordinate, we now
  : increase its x-coordinate by
  . two (which is a bug)

If a dot directive were used instead of the colon directive here, it would
restore incorrectly as::

   49155 LD A,(HL)     ; {Having adjusted the sprite's y-coordinate, we now
  @bfix=ADD A,3        ; three}
   49156 ADD A,2       ; increase its x-coordinate by
                       ; two (which is a bug)}

.. _ctlLoops:

Loops
-----
Sometimes the instructions and statements in a code or data block follow a
repeating pattern. For example::

  b 30000 Two bytes and one word, times ten
  B 30000,2
  W 30002
  B 30004,2
  W 30004
  ...
  B 30036,2
  W 30038

Repeating patterns like this can be expressed more succinctly as a loop by
using the ``L`` directive, which has the following format::

  L start,length,count[,blocks]

where:

* ``start`` is the loop start address
* ``length`` is the length of the loop (the size of the address range to
  repeat)
* ``count`` is the number of times to repeat the loop (only values of 2 or more
  make sense)
* ``blocks`` is ``1`` to repeat block-level elements, or ``0`` to repeat only
  sub-block elements (default: ``0``)

So using the ``L`` directive, the body of the data block above can be expressed
in three lines instead of 20::

  b 30000 Two bytes and one word, times ten
  B 30000,2
  W 30002
  L 30000,4,10

The ``L`` directive can also be used to repeat entire blocks, by setting the
``blocks`` argument to ``1``. For example::

  b 40000 A block of five pairs of bytes
  B 40000,10,2
  L 40000,10,3,1

is equivalent to::

  b 40000 A block of five pairs of bytes
  B 40000,10,2
  b 40010 A block of five pairs of bytes
  B 40010,10,2
  b 40020 A block of five pairs of bytes
  B 40020,10,2

Note that ASM directives in the address range of an ``L`` directive loop are
*not* repeated.

.. _numberBases:

Number bases
------------
Numeric values in instruction operands and DEFB, DEFM, DEFS and DEFW statements
are normally rendered in either decimal or hexadecimal, depending on the
options passed to :ref:`sna2skool.py`. To render a numeric value in a specific
base, as a negative number, or as a character, attach a ``b`` (binary), ``c``
(character), ``d`` (decimal), ``h`` (hexadecimal) or ``m`` (minus) prefix to
the relevant length or sublength parameter on the ``B``, ``C``, ``S``, ``T``
or ``W`` directive.

For example::

  C 30000,b
  C 30002,c

will result in something like this::

  30000 LD A,%10001111
  30002 LD B,"?"

and::

  B 40000,8,b1:d2:h1,m1,b1,h2
  S 40008,8,8:c

will result in something like this::

  40000 DEFB %10101010,23,43,$5F
  40004 DEFB -1
  40005 DEFB %11110000
  40006 DEFB $2B,$80
  40008 DEFS 8,"!"

Note that attaching a prefix to the main length parameter sets the default base
for any sublength parameters that follow. So::

  B 40000,b,1:d2,1
  B 40004,h4,1:b1:d1,1

will result in something like this::

  40000 DEFB %01010101,32,57
  40003 DEFB %00001111
  40004 DEFB $0F,%11110000,93
  40007 DEFB $A0

Some instructions have two numeric operands. To specify a different base for
each one, use two prefixes::

  C 30000,hb4

which will result in something like this::

  30000 LD (IX+$0A),%10000001

To use the default base for one operand, and a specific base for the other, use
the ``n`` (none) prefix to denote the default base. So if the default base is
decimal, then::

  C 30000,,nb4,hn4

will result in something like this::

  30000 LD (IX+10),%10000001
  30004 LD (IX+$0B),130

ASM directives
--------------
To declare an ASM directive for a block or an individual instruction, use the
``@`` directive thus::

  @ address directive[=value]

where:

* ``directive`` is the directive name
* ``address`` is the address of the block or instruction to which the directive
  applies
* ``value`` is the value of the directive (if it requires one)

For example, to declare a :ref:`label` directive for the instruction at 32768::

  @ 32768 label=LOOP

When declaring an :ref:`ignoreua` directive for anything other than an
instruction-level comment, a suffix must be appended to the directive to
specify the type of comment it applies to::

  @ address ignoreua:X

where ``X`` is one of:

* ``d`` - entry description
* ``e`` - block end comment
* ``i`` - instruction-level comment (default)
* ``m`` - block start comment or mid-block comment
* ``r`` - register description section
* ``t`` - entry title

For example, to declare an :ref:`ignoreua` directive for the description of the
routine at 49152::

  @ 49152 ignoreua:d
  D 49152 This is the description of the routine at 49152.

Instruction-level comments
--------------------------
One limitation of storing instruction-level comments as shown so far is that
there is no way to distinguish between a blank comment that spans two or more
instructions and no comment at all. For example, both::

  30000 DEFB 0 ; {
  30001 DEFB 0 ; }

and::

  30000 DEFB 0 ;
  30001 DEFB 0 ;

would be preserved thus::

  B 30000,2,1

To solve this problem, a special syntax is used to preserve blank
multi-instruction comments::

  B 30000,2,1 .

When restored, this comment is reduced to an empty string.

But how then to preserve a multi-instruction comment consisting of a single dot
(``.``), or a sequence of two or more dots? In that case, another dot is
prefixed to the comment. So::

  30000 DEFB 0 ; {...
  30001 DEFB 0 ; }

is preserved thus::

  B 30000,2,1 ....

Note that this scheme does not apply to multi-instruction comments that contain
at least one character other than a dot; such comments are preserved verbatim
(that is, without a dot prefix).

.. _nonEntryBlocks-ctl:

Non-entry blocks
----------------
In addition to regular entries (routines and data blocks), a skool file may
also contain blocks of lines that do not match the format of an entry, such as
a header comment that appears before the first entry and contains copyright
information. Blocks like this can be preserved by the ``>`` directive. For
example, the copyright header in this skool file::

  ; Copyright 2018 J Smith

  ; Start
  c24576 JP 32768

is preserved thus::

  > 24576 ; Copyright 2018 J Smith

Note that the address of the ``>`` directive is the address of the next regular
entry.

A non-entry block may also appear at the end of the skool file, after the
last regular entry::

  ; The end
  c65535 RET

  ; And that was the disassembly.

In this case the block is preserved by the ``>`` directive with the parameter
``1`` (indicating a 'footer') following the address of the last entry::

  > 65535,1 ; And that was the disassembly.

Control file comments
---------------------
A comment may be added to a control file by starting a line with a hash
character (``#``), a per cent sign (``%``), or a semicolon (``;``). For
example::

  # This is a comment
  % This is another comment
  ; This is yet another comment

Control file comments are ignored by `sna2skool.py`, and will not show up in
the skool file.

Limitations
-----------
Control files cannot preserve ASM block directives that occur inside a regular
entry. If your skool file contains any such ASM block directives, they should
be replaced before using :ref:`skool2ctl.py`.

An ASM block directive that adds, removes or modifies a sequence of
instructions and their associated comments can be replaced by one or more plain
:ref:`isub`, :ref:`ssub`, :ref:`rsub`, :ref:`ofix`, :ref:`bfix` or :ref:`rfix`
directives.

An ASM block directive that modifies part of an entry header, mid-block comment
or block end comment can be replaced by an :ref:`IF` macro that checks the
relevant substitution mode (``asm``) or fix mode (``fix``). For example::

  @bfix-begin
  ; This is a bug.
  @bfix+else
  ; This bug is fixed.
  @bfix+end

could be replaced by::

  ; This #IF({fix}<2)(is a bug,bug is fixed).

Revision history
----------------
+---------+-------------------------------------------------------------------+
| Version | Changes                                                           |
+=========+===================================================================+
| 7.2     | Added the dot (``.``) and colon (``:``) directives for specifying |
|         | comments over multiple lines                                      |
+---------+-------------------------------------------------------------------+
| 7.1     | Added support for specifying that numeric values in instruction   |
|         | operands and DEFB, DEFM, DEFS and DEFW statements be rendered as  |
|         | negative decimal numbers                                          |
+---------+-------------------------------------------------------------------+
| 7.0     | Added the ``>`` directive for preserving non-entry blocks; added  |
|         | support for preserving 'inverted' characters (with bit 7 set);    |
|         | the byte value in an ``S`` directive may be left blank            |
+---------+-------------------------------------------------------------------+
| 4.5     | Added support for specifying character values in DEFS statements  |
+---------+-------------------------------------------------------------------+
| 4.4     | Added support for specifying that numeric values in instruction   |
|         | operands be rendered as characters or in a specific base; added   |
|         | support for specifying character values in DEFW statements        |
+---------+-------------------------------------------------------------------+
| 4.3     | Added the ``@`` directive, the ``N`` directive and support for    |
|         | block start comments                                              |
+---------+-------------------------------------------------------------------+
| 4.2     | Added the ``L`` directive and support for preserving the location |
|         | of :ref:`ignoreua` directives                                     |
+---------+-------------------------------------------------------------------+
| 3.7     | Added support for binary numbers; added support for specifying    |
|         | the base of numeric values in DEFB, DEFM, DEFS and DEFW           |
|         | statements; added the ``s`` and ``S`` directives and support for  |
|         | DEFS statements with non-zero byte values                         |
+---------+-------------------------------------------------------------------+
| 3.6     | Added support for preserving blank comments that span two or more |
|         | instructions                                                      |
+---------+-------------------------------------------------------------------+
| 3.1.4   | Added support for DEFB and DEFM statements that contain both      |
|         | strings and bytes                                                 |
+---------+-------------------------------------------------------------------+
| 2.4     | Added support for non-block ASM directives                        |
+---------+-------------------------------------------------------------------+
| 2.2     | Added support for the ``*`` notation in DEFB, DEFM, DEFS and DEFW |
|         | statement length lists                                            |
+---------+-------------------------------------------------------------------+
| 2.1.2   | Added support for DEFM, DEFS and DEFW statement lengths           |
+---------+-------------------------------------------------------------------+
| 2.1.1   | Added the ``M`` directive                                         |
+---------+-------------------------------------------------------------------+
| 2.1     | Added support for DEFB statement lengths                          |
+---------+-------------------------------------------------------------------+
| 2.0.6   | Added support for hexadecimal numbers                             |
+---------+-------------------------------------------------------------------+
| 1.0.7   | Added support for block titles, block descriptions, register      |
|         | values, mid-block comments, block end comments, sub-block types   |
|         | and instruction-level comments                                    |
+---------+-------------------------------------------------------------------+
