.. _skoolFiles:

Skool files
===========
A skool file contains the list of Z80 instructions that make up the routines
and data blocks of the program being disassembled, with accompanying comments
(if any).

.. _skoolFileFormat:

Skool file format
-----------------
A skool file must be in a certain format to ensure that it is processed
correctly by :ref:`skool2html.py`, :ref:`skool2asm.py`, :ref:`skool2ctl.py` and
:ref:`skool2sft.py`. The rules are as follows:

* entries (an 'entry' being a routine or data block) must be separated by
  blank lines, and an entry must not contain any blank lines

* an entry header is a sequence of comment lines broken into four sections;
  see :ref:`entryHeaderFormat`

* each line in an entry may start with one of the following characters:
  ``;* @bcdgirstuw``; see :ref:`entryLineFormat`

* tables (grids) have their own markup syntax; see :ref:`TABLE` for details

.. _entryHeaderFormat:

Entry header format
^^^^^^^^^^^^^^^^^^^
An entry header is a sequence of comment lines broken into four sections:

* entry title
* entry description (optional)
* registers (optional)
* start comment (optional)

The sections are separated by an empty comment line, and paragraphs within
the entry description and start comment must be separated by a comment line
containing a dot (``.``) on its own. For example::

  ; This is the entry title
  ;
  ; This is the first paragraph of the entry description.
  ; .
  ; This is the second paragraph of the entry description.
  ;
  ; A An important parameter
  ; B Another important parameter
  ;
  ; This is the start comment above the first instruction in the entry.

If a start comment is required but a register section is not, either append the
start comment to the entry description, or specify a blank register section by
using a dot (``.``) thus::

  ; This entry has a start comment but no register section
  ;
  ; This is the entry description.
  ;
  ; .
  ;
  ; This is the start comment above the first instruction in the entry.

Likewise, if a register section is required but an entry description is not, a
blank entry description may be specified by using a dot (``.``) thus::

  ; This entry has a register section but no description
  ;
  ; .
  ;
  ; A An important parameter
  ; B Another important parameter

Registers may be listed as shown above, or with colon-terminated prefixes
(such as 'Input:' and 'Output:', or simply 'I:' and 'O:') to distinguish
input values from output values::

  ;  Input:A An important parameter
  ;        B Another important parameter
  ; Output:C The result

In the HTML version of the disassembly, input values and output values are
shown in separate tables. If a register's prefix begins with the letter 'O',
it is regarded as an output value; if it begins with any other letter, it is
regarded as an input value. If a register has no prefix, it will be placed in
the same table as the previous register; if there is no previous register, it
will be placed in the table of input values.

If a register description is very long, it may be split over two or more lines
by starting the second and subsequent lines with a dot (``.``) thus::

  ; HL The description for this register is quite long, so it is split over two
  ; .  lines for improved readability

.. _entryLineFormat:

Entry line format
^^^^^^^^^^^^^^^^^
Each line in an entry may start with one of ``;* @bcdgirstuw``, where:

* ``;`` begins a comment line
* ``*`` denotes an entry point in a routine
* ``@`` begins an :ref:`ASM directive <asm>`
* ``b`` denotes the first instruction in a data block
* ``c`` denotes the first instruction in a code block (routine)
* ``d`` denotes the first instruction in a
  :ref:`data definition entry <dEntry>`
* ``g`` denotes the first instruction in a game status buffer entry
* ``i`` denotes an ignored entry
* ``r`` denotes the first instruction in a :ref:`remote entry <rEntry>`
* ``s`` denotes the first instruction in a data block containing bytes that
  are all the same value (typically unused zeroes)
* ``t`` denotes the first instruction in a data block that contains text
* ``u`` denotes the first instruction in an unused code or data block
* ``w`` denotes the first instruction in a data block that contains two-byte
  values (words)
* a space begins a line that does not require any of the markers listed above

The format of a line containing an instruction is::

  C##### INSTRUCTION[ ; comment]

where:

* ``C`` is one of the characters listed above: ``* bcdgirstuw``
* ``#####`` is an address (e.g. ``24576``, or ``$6000`` if you prefer
  hexadecimal notation)
* ``INSTRUCTION`` is an instruction (e.g. ``LD A,(HL)``)
* ``comment`` is a comment (which may be blank)

The comment for a single instruction may span multiple lines thus::

  c24296 CALL 57935    ; This comment is too long to fit on a single line, so
                       ; we use two lines

A comment may also be associated with more than one instruction by the use of
braces (``{`` and ``}``) to indicate the start and end points, thus::

  *24372 SUB D         ; {This comment applies to the two instructions at
   24373 JR NZ,24378   ; 24372 and 24373}

The opening and closing braces are removed before the comment is rendered in
ASM or HTML mode. (See :ref:`bracesInComments`.)

Comments may appear between instructions, or after the last instruction in an
entry; paragraphs in such comments must be separated by a comment line
containing a dot (``.``) on its own. For example::

  *28975 JR 28902
  ; This is a mid-block comment between two instructions.
  ; .
  ; This is the second paragraph of the comment.
   28977 XOR A

Lines that start with ``*`` will have their addresses shown in bold in the
HTML version of the disassembly (generated by :ref:`skool2html.py`), and will
have labels generated for them in the ASM version (generated by
:ref:`skool2asm.py`).

.. _asm:

ASM directives
--------------
To write an ASM directive in a skool file, start a line with ``@``; for
example::

  ; Start the game
  @label=START
  c24576 XOR A

See :ref:`asmModesAndDirectives` for more details.

Escaping characters
-------------------
Backslash (``\``) and double quote (``"``) characters in string and character
operands must be escaped by preceding them with a backslash. For example::

  c32768 LD A,"\""     ; LD A,34
   32770 LD B,"\\"     ; LD B,92

This ensures that SkoolKit or an assembler can parse such operands correctly.

.. _bracesInComments:

Braces in comments
------------------
As noted above, opening and closing braces (``{``, ``}``) are used to mark the
start and end points of an instruction-level comment that is associated with
more than one instruction, and the braces are removed before the comment is
rendered. This means that if the comment requires an opening or closing brace
`when rendered`, some care must be taken to get the syntax correct.

The rules regarding an instruction-level comment that starts with an opening
brace are as follows:

* The comment terminates on the line where the total number of closing braces
  in the comment becomes equal to or greater than the total number of opening
  braces
* Adjacent opening braces at the start of the comment are removed before
  rendering
* Adjacent closing braces at the end of the comment are removed before
  rendering

By these rules, it is possible to craft an instruction-level comment that
contains matched or unmatched opening and closing braces when rendered.

For example::

  b50000 DEFB 0  ; {{This comment (which spans two instructions) has an
   50001 DEFB 0  ; unmatched closing brace} }

will render in ASM mode as::

  DEFB 0                  ; This comment (which spans two instructions) has an
  DEFB 0                  ; unmatched closing brace}

And::

  b50002 DEFB 0  ; { {{Matched opening and closing braces}} }

will render as::

  DEFB 0                  ; {{Matched opening and closing braces}}

Finally::

  b50003 DEFB 0  ; { {Unmatched opening brace}}

will render as::

  DEFB 0                  ; {Unmatched opening brace

.. _dEntry:

Data definition entries
-----------------------
If the first instruction line in an entry starts with ``d``, the entry is
regarded as a data definition entry. Such entries do not appear in the memory
map generated by `skool2html.py`, but may contain ``DEFB``, ``DEFM``, ``DEFS``
and ``DEFW`` statements that will be used to insert data into the memory
snapshot.

For example::

  ; The eight bytes of code in this routine are also used as UDG data.
  ; .
  ; #HTML(#UDG44919)
  c44919 LD DE,46572   ;
   44922 CP 200        ;
   44924 JP 45429      ;

  d44919 DEFB 17,236,181,254,200,195,117,177

If this data definition entry were not present, the memory snapshot would
contain zeroes at addresses 44919-44926, and the image created by the ``#UDG``
macro would be blank. The reason for this is that by default, the skool file
parser does not convert assembly language instructions into byte values.
However, this behaviour can be changed by using the :ref:`assemble` directive.

.. _rEntry:

Remote entries
--------------
If the first instruction line in an entry starts with ``r``, the entry is
regarded as a remote entry. Such entries do not appear in the memory map
generated by `skool2html.py`, but they enable ``JR``, ``JP`` and ``CALL``
instructions to be hyperlinked to entries defined in other skool files.

For example::

  r26880 main

This entry, if it were present in a secondary skool file, would enable any
``JR``, ``JP`` and ``CALL`` instruction with 26880 as the operand to be
hyperlinked to that routine in the main disassembly (the entry for which should
be defined in the main skool file).

If the desired target of the hyperlink is an entry point within a routine that
is defined in another skool file (as opposed to the address of the routine
itself), both the routine address and the entry point address should be
declared in the remote entry. For example::

  r29012 main
   29015

This enables hyperlinks to 29015 in the main disassembly, which is an entry
point in the routine at 29012. It also enables the :ref:`r` macro to create
hyperlinks to remote entry points using the short form::

  #R29015@main

instead of the longer form (which would be required if the remote entry were
not defined)::

  #R29012@main#29015(29015)

Revision history
----------------
+---------+-----------------------------------------------------------------+
| Version | Changes                                                         |
+=========+=================================================================+
| 4.3     | Added support for the start comment in entry headers; an ASM    |
|         | directive can be declared by starting a line with ``@``         |
+---------+-----------------------------------------------------------------+
| 4.2     | Added support for splitting register descriptions over multiple |
|         | lines                                                           |
+---------+-----------------------------------------------------------------+
| 3.7     | Added support for binary numbers; added the ``s`` block type    |
+---------+-----------------------------------------------------------------+
| 3.1.2   | Added support for 'Input' and 'Output' prefixes in register     |
|         | sections                                                        |
+---------+-----------------------------------------------------------------+
| 2.4     | Added the ability to separate paragraphs and specify a blank    |
|         | entry description by using a dot (``.``) on a line of its own   |
+---------+-----------------------------------------------------------------+
| 2.1     | Added support for hexadecimal numbers                           |
+---------+-----------------------------------------------------------------+
| 2.0     | Added support for data definition entries and remote entries    |
+---------+-----------------------------------------------------------------+
