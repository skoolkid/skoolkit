.. _asmModesAndDirectives:

ASM modes and directives
========================
A skool file may contain directives that are processed during the parsing
phase. Exactly how a directive is processed (and whether it is executed)
depends on the 'substitution mode' and 'bugfix mode' in which the skool file is
being parsed.

.. _substitutionModes:

Substitution modes
------------------
There are three substitution modes: ``@isub``, ``@ssub``, and ``@rsub``. These
modes are described in the following subsections.

.. _isubMode:

@isub mode
^^^^^^^^^^
In ``@isub`` mode, ``@isub`` directives are executed, but ``@ssub``, and
``@rsub`` directives are not. The main purpose of ``@isub`` mode is to make the
minimum number of instruction substitutions necessary to produce an ASM file
that assembles.

For example::

  @isub=LD A,(32512)
   25396 LD A,(m)

This ``@isub`` directive ensures that ``LD A,(m)`` is replaced by the valid
instruction ``LD A,(32512)`` when rendering in ASM mode.

``@isub`` mode is invoked by default when running
:ref:`skool2asm.py <skool2asm.py>`.

.. _ssubMode:

@ssub mode
^^^^^^^^^^
In ``@ssub`` mode, ``@isub`` and ``@ssub`` directives are executed, but
``@rsub`` directives are not. The main purpose of ``@ssub`` mode is to replace
LSBs, MSBs and full addresses in the operands of instructions with labels, to
make the code amenable to some degree of relocation, but without actually
removing or inserting any code.

For example::

  @ssub=LD (27015+1),A
  *27012 LD (27016),A  ; Change the instruction below from SET 0,B to RES 0,B
                       ; or vice versa
   27015 SET 0,B

This ``@ssub`` directive replaces ``LD (27016),A`` with ``LD (27015+1),A``; the
``27015`` will be replaced by the label for that address before rendering.
(``27016`` cannot be replaced by a label, since it is not the address of an
instruction.)

``@ssub`` mode is invoked by passing the ``-s`` option to
:ref:`skool2asm.py <skool2asm.py>`.

.. _rsubMode:

@rsub mode
^^^^^^^^^^
In ``@rsub`` mode, ``@isub``, ``@ssub`` and ``@rsub`` directives are executed.
The main purpose of ``@rsub`` mode is to make code unconditionally relocatable,
even if that requires the removal of existing code or the insertion of new
code.

For example::

   23997 LD HL,32766
  @ssub=LD (HL),24002%256
   24000 LD (HL),194
  @rsub+begin
         INC L
         LD (HL),24002/256
  @rsub+end
   24002 XOR A

This ``@rsub`` block directive inserts two instructions that ensure that the
address stored at 32766 will have the correct MSB as well as the correct LSB,
regardless of where the code originally at 24002 now lives.

``@rsub`` mode is invoked by passing the ``-r`` option to
:ref:`skool2asm.py <skool2asm.py>`. ``@rsub`` mode also implies
:ref:`ofixMode`.

.. _bugfixModes:

Bugfix modes
------------
There are three bugfix modes: ``@ofix``, ``@bfix`` and ``@rfix``. These
modes are described in the following subsections.

.. _ofixMode:

@ofix mode
^^^^^^^^^^
In ``@ofix`` mode, ``@ofix`` directives are executed, but ``@bfix`` and
``@rfix`` directives are not. The main purpose of ``@ofix`` mode is to fix
instructions that have faulty operands.

For example::

  @ofix-begin
   27872 CALL 27633    ; This should be CALL 27634
  @ofix+else
         CALL 27634
  @ofix+end

These ``@ofix`` block directives fix the faulty operand of the CALL
instruction.

``@ofix`` mode is invoked by passing the ``-f 1`` option to
:ref:`skool2asm.py <skool2asm.py>`.

.. _bfixMode:

@bfix mode
^^^^^^^^^^
In ``@bfix`` mode, ``@ofix`` and ``@bfix`` directives are executed, but
``@rfix`` directives are not. The main purpose of ``@bfix`` mode is to fix bugs
by replacing instructions, but without changing the start address of any
routines, routine entry points, or data blocks.

For example::

  @bfix-begin
   32205 JR Z,32232    ; This should be JR NZ,32232
  @bfix+else
         JR NZ,32232   ;
  @bfix+end

``@bfix`` mode is invoked by passing the ``-f 2`` option to
:ref:`skool2asm.py <skool2asm.py>`.

.. _rfixMode:

@rfix mode
^^^^^^^^^^
In ``@rfix`` mode, ``@ofix``, ``@bfix`` and ``@rfix`` directives are executed.
The purpose of ``@rfix`` mode is to fix bugs that cannot be fixed without
moving code around (to make space for the fix).

For example::

   28432 DEC HL
  @rfix+begin
         LD A,H
         OR L
  @rfix+end
   28433 JP Z,29712

These ``@rfix`` block directives insert some instructions to fix the faulty
check on whether HL holds 0.

``@rfix`` mode is invoked by passing the ``-f 3`` option to
:ref:`skool2asm.py <skool2asm.py>`. ``@rfix`` mode implies :ref:`rsubMode`.

.. _asmDirectives:

ASM directives
--------------
The ASM directives recognised by SkoolKit are described in the following
subsections.

.. _assemble:

@assemble
^^^^^^^^^
The ``@assemble`` directive controls whether assembly language instructions,
``DEFB``, ``DEFM``, ``DEFS`` and ``DEFW`` statements, and :ref:`defb`,
:ref:`defs` and :ref:`defw` directives are converted into byte values for the
purpose of populating the memory snapshot. ::

  @assemble=H,A

``H`` is an integer value that determines what is converted in HTML mode, and
``A`` is an integer value that determines what is converted in ASM mode:

* ``0`` - do not convert anything (this is the default in ASM mode)
* ``1`` - convert ``DEFB``, ``DEFM``, ``DEFS`` and ``DEFW`` statements and
  ``@defb``, ``@defs`` and ``@defw`` directives only (this is the default in
  HTML mode)
* ``2`` - convert assembly language instructions as well

If ``H`` or ``A`` is blank or omitted, its value is left unchanged.

For example::

  ; The eight bytes of code in this routine are also used as UDG data.
  ; .
  ; #HTML(#UDG44919)
  @assemble=2
  c44919 LD DE,46572   ;
   44922 CP 200        ;
   44924 JP 45429      ;
  @assemble=1

The ``@assemble=2`` directive is required to define the bytes for addresses
44919-44926. If it were not present, the memory snapshot would contain zeroes
at those addresses, and the image created by the ``#UDG`` macro would be blank.

+---------+-------------------------------------------------------------------+
| Version | Changes                                                           |
+=========+===================================================================+
| 7.0     | The accepted values are 0, 1 and 2 (previously -1, 0 and 1)       |
+---------+-------------------------------------------------------------------+
| 6.3     | Added support for specifying what's converted in HTML mode and    |
|         | ASM mode separately, and for switching off conversion entirely    |
+---------+-------------------------------------------------------------------+
| 6.1     | Added the ability to assemble instructions whose operands contain |
|         | arithmetic expressions                                            |
+---------+-------------------------------------------------------------------+
| 5.0     | New                                                               |
+---------+-------------------------------------------------------------------+

.. _bfix:

@bfix
^^^^^
The ``@bfix`` directive replaces, inserts or removes a label, instruction and
comment in :ref:`bfixMode`. ::

  @bfix=[>][|][+][/][LABEL:][INSTRUCTION][; comment]

or, when removing instructions::

  @bfix=!addr1[-addr2]

* ``>`` - if this marker is present, ``INSTRUCTION`` is inserted before the
  current instruction instead of replacing it
* ``|`` - if this marker is present, ``INSTRUCTION`` overwrites any overlapping
  instructions instead of pushing them aside
* ``+`` - if this marker is present, ``INSTRUCTION`` is inserted after the
  current instruction instead of replacing it
* ``/`` - if this marker is present, any remaining comment lines are removed
* ``LABEL`` is the replacement label; if not given, any existing label is left
  unchanged
* ``INSTRUCTION`` is the replacement instruction; if not given, the existing
  instruction is left unchanged
* ``comment`` is the replacement comment; if not given, the existing comment is
  left unchanged
* ``addr1`` is the address of the first instruction to remove
* ``addr2``, if given, is the address of the last instruction to remove

For example::

  @label=CMASK
  @bfix=BMASK: AND B ; Apply the mask
   29713 AND C       ; This should be 'AND B'

This ``@bfix`` directive replaces the instruction ``AND C`` with ``AND B``,
replaces the label ``CMASK`` with ``BMASK``, and also replaces the comment.

Comment continuation lines can be replaced, removed or added by using
additional ``@bfix`` directives. For example, to replace both comment lines
of an instruction that has two::

  @bfix=AND B  ; This directive replaces the first comment line
  @bfix=       ; and this directive replaces the second comment line
   29713 AND C ; Both of these comment lines
               ; will be replaced

To add a second comment line to an instruction that has only one::

  @bfix=AND B  ; This directive replaces the first comment line
  @bfix=       ; and this directive adds a second comment line
   29713 AND C ; This comment line will be replaced

To replace two comment lines with one::

  @bfix=/AND B ; The '/' in this directive effectively terminates the comment
   29713 AND C ; This comment line will be replaced
               ; and this one will be removed

A single instruction can be replaced with two or more by using the ``|``
(overwrite) marker. For example, to replace ``LD HL,0`` with ``LD L,0`` and
``LD H,L``::

  @bfix=|LD L,0  ; Clear L
  @bfix=|LD H,L  ; Clear H
   36671 LD HL,0 ; Clear HL

Two or more instructions can also be replaced with a single instruction. For
example, to replace ``XOR A`` and ``INC A`` with ``LD A,1``::

  @bfix=|LD A,1
   49912 XOR A
   49913 INC A

A sequence of instructions can be replaced by chaining ``@bfix`` directives.
For example, to swap two ``XOR`` instructions::

  @bfix=|XOR C
  @bfix=|XOR B
   51121 XOR B
   51122 XOR C

This is equivalent to::

  @bfix=XOR C
   51121 XOR B
  @bfix=XOR B
   51122 XOR C

Note that when ``@bfix`` directives are chained like this, the second and
subsequent directives replace instruction comments in their entirety, instead
of line by line. For example::

  @bfix=|LD A,D ; Set A=D
  @bfix=|XOR B  ; Flip the bits
   51121 LD A,B ; Set A=B
   51122 XOR C  ; XOR the contents of the accumulator with the contents of the
                ; C register

replaces both comment lines of the instruction at 51122 with 'Flip the bits'.

A sequence of instructions can be inserted before the current instruction by
using the ``>`` marker. For example::

   47191 EX DE,HL
  ; A mid-block comment.
  @bfix=>LD (HL),C
  @bfix=>INC HL
   47192 LD (HL),B

This will insert ``LD (HL),C`` and ``INC HL`` between ``EX DE,HL`` and
``LD (HL),B``. The mid-block comment that was above ``LD (HL),B`` will now be
above ``LD (HL),C``.

A sequence of instructions can be inserted after the current instruction
(without first specifying a replacement for it) by using the ``+`` marker. For
example::

  @bfix=+LD (HL),C
  @bfix=INC HL
   47191 EX DE,HL
  ; A mid-block comment.
   47192 LD (HL),B

This will insert ``LD (HL),C`` and ``INC HL`` between ``EX DE,HL`` and
``LD (HL),B``. In this case, the mid-block comment above ``LD (HL),B`` will
remain there.

The current instruction can be replaced and a sequence of instructions inserted
after it by chaining ``@bfix`` directives. For example::

  @bfix=LD (HL),B  ; {Save B and C here
  @bfix=INC HL     ;
  @bfix=LD (HL),C  ; }
   61125 LD (HL),A ; Save A here
   61126 RET

This will replace ``LD (HL),A`` with ``LD (HL),B`` and insert ``INC HL`` and
``LD (HL),C`` before the ``RET`` instruction.

An instruction can be removed by using the ``!`` notation. For example::

   51184 XOR A
  @bfix=!51185
   51185 AND A ; This instruction is redundant
   51186 RET

This removes the redundant instruction at 51185.

An entire entry can be removed by specifying an address range that covers every
instruction in the entry::

  ; Unused
  @bfix=!40000-40001
  c40000 NOP
   40001 RET

+---------+-------------------------------------------------------------------+
| Version | Changes                                                           |
+=========+===================================================================+
| 7.1     | Added support for the ``+`` marker (to insert an instruction      |
|         | after the current one)                                            |
+---------+-------------------------------------------------------------------+
| 7.0     | Added support for specifying the replacement comment over         |
|         | multiple lines, replacing the label, and inserting, overwriting   |
|         | and removing instructions                                         |
+---------+-------------------------------------------------------------------+
| 6.4     | Added support for replacing the comment                           |
+---------+-------------------------------------------------------------------+

.. _bfixBlockDirectives:

@bfix block directives
^^^^^^^^^^^^^^^^^^^^^^
The ``@bfix`` block directives define a block of lines that will be inserted or
removed in :ref:`bfixMode`.

The syntax for defining a block that will be inserted in ``@bfix`` mode (but
left out otherwise) is::

  @bfix+begin
  ...                  ; Lines to be inserted
  @bfix+end

The syntax for defining a block that will be removed in ``@bfix`` mode (but
left in otherwise) is::

  @bfix-begin
  ...                  ; Lines to be removed
  @bfix-end

Typically, though, it is desirable to define a block that will be removed in
``@bfix`` mode right next to the block that will be inserted in its place. That
may be done thus::

  @bfix-begin
  ...                  ; Instructions to be removed
  @bfix+else
  ...                  ; Instructions to be inserted
  @bfix+end

which is equivalent to::

  @bfix-begin
  ...                  ; Instructions to be removed
  @bfix-end
  @bfix+begin
  ...                  ; Instructions to be inserted
  @bfix+end

For example::

  @bfix-begin
   32205 JR Z,32232    ; This should be JR NZ,32232
  @bfix+else
         JR NZ,32232   ;
  @bfix+end

.. _defb:

@defb
^^^^^
The ``@defb`` directive inserts byte values into the memory snapshot at a given
address. ::

  @defb=address:value1[,value2...]

* ``address`` is the address
* ``value1``, ``value2`` etc. are the byte values (as might appear in a
  ``DEFB`` statement)

The sequence of comma-separated values may be followed by a semicolon (``;``)
and arbitrary text, which will be ignored.

For example::

  @defb=30000:5,"Hello" ; Welcome message

This will insert the value 5 followed by the ASCII codes of the characters in
"Hello" into the memory snapshot at address 30000.

``@defb`` directives are processed not only when :ref:`skool2asm.py` or
:ref:`skool2html.py` is run, but also when :ref:`sna2skool.py` is run on a
control file or skool file template; thus the ``@defb`` directive can be used
to override the contents of the snapshot that is read by `sna2skool.py`.

+---------+---------+
| Version | Changes |
+=========+=========+
| 6.3     | New     |
+---------+---------+

.. _defs:

@defs
^^^^^
The ``@defs`` directive inserts a sequence of byte values into the memory
snapshot at a given address. ::

  @defs=address:length[,value]

* ``address`` is the address
* ``length`` is the length of the sequence
* ``value`` is the byte value (default: 0)

The directive may be followed by a semicolon (``;``) and arbitrary text, which
will be ignored.

For example::

  @defs=30000:5,$FF ; Five 255s

This will insert the value 255 into the memory snapshot at addresses
30000-30004.

``@defs`` directives are processed not only when :ref:`skool2asm.py` or
:ref:`skool2html.py` is run, but also when :ref:`sna2skool.py` is run on a
control file or skool file template; thus the ``@defs`` directive can be used
to override the contents of the snapshot that is read by `sna2skool.py`.

+---------+---------+
| Version | Changes |
+=========+=========+
| 6.3     | New     |
+---------+---------+

.. _defw:

@defw
^^^^^
The ``@defw`` directive inserts word values into the memory snapshot at a given
address. ::

  @defw=address:value1[,value2...]

* ``address`` is the address
* ``value1``, ``value2`` etc. are the word values (as might appear in a
  ``DEFW`` statement)

The sequence of comma-separated values may be followed by a semicolon (``;``)
and arbitrary text, which will be ignored.

For example::

  @defw=30000:32768,32775 ; Message addresses

This will insert the word values 32768 and 32775 into the memory snapshot at
addresses 30000 and 30002.

``@defw`` directives are processed not only when :ref:`skool2asm.py` or
:ref:`skool2html.py` is run, but also when :ref:`sna2skool.py` is run on a
control file or skool file template; thus the ``@defw`` directive can be used
to override the contents of the snapshot that is read by `sna2skool.py`.

+---------+---------+
| Version | Changes |
+=========+=========+
| 6.3     | New     |
+---------+---------+

.. _end:

@end
^^^^
The ``@end`` directive may be used to indicate where to stop parsing the skool
file for the purpose of generating ASM output. Everything after the ``@end``
directive is ignored by :ref:`skool2asm.py`.

See also :ref:`start`.

+---------+---------+
| Version | Changes |
+=========+=========+
| 2.2.2   | New     |
+---------+---------+

.. _equ:

@equ
^^^^
The ``@equ`` directive defines an EQU directive that will appear in the ASM
output. ::

  @equ=label=value

* ``label`` is the label
* ``value`` is the value assigned to the label

For example::

  @equ=ATTRS=22528
  c32768 LD HL,22528

This will produce an EQU directive (``ATTRS EQU 22528``) in the ASM output, and
replace the operand of the instruction at 32768 with a label: ``LD HL,ATTRS``.

+---------+---------+
| Version | Changes |
+=========+=========+
| 5.4     | New     |
+---------+---------+

.. _asm-if:

@if
^^^
The ``@if`` directive conditionally processes other ASM directives based on the
value of an arithmetic expression. ::

  @if(expr)(true[,false])

* ``expr`` is the arithmetic expression
* ``true`` is processed when ``expr`` is true
* ``false`` (if given) is processed when ``expr`` is false

See :ref:`numericParameters` for details on the operators and replacement
fields that may be used in the ``expr`` parameter.

For example::

  @if({case}==1))(replace=/#hl/hl,replace=/#hl/HL)

would process ``replace=/#hl/hl`` if in lower case mode, or ``replace=/#hl/HL``
otherwise.

The ``true`` and ``false`` parameters may be supplied in the same way as they
are for the :ref:`if` macro. See :ref:`stringParameters` for more details.

+---------+---------+
| Version | Changes |
+=========+=========+
| 6.4     | New     |
+---------+---------+

.. _ignoreua:

@ignoreua
^^^^^^^^^
The ``@ignoreua`` directive suppresses any warnings that would otherwise be
reported concerning addresses not converted to labels in the comment that
follows; the comment may be an entry title, an entry description, a register
description section, a block start comment, a mid-block comment, a block end
comment, or an instruction-level comment.

To apply the directive to an entry title::

  @ignoreua
  ; Prepare data at 32768
  c32768 LD A,(HL)

If the ``@ignoreua`` directive were not present, a warning would be printed
(during the rendering phase) about the entry title containing an address
(32768) that has not been converted to a label.

To apply the directive to an entry description::

  ; Prepare data in page 128
  ;
  @ignoreua
  ; This routine operates on the data at 32768.
  c49152 LD A,(HL)

If the ``@ignoreua`` directive were not present, a warning would be printed
(during the rendering phase) about the entry description containing an address
(32768) that has not been converted to a label.

To apply the directive to a register description section::

  ; Prepare data in page 128
  ;
  ; This routine operates on the data in page 128.
  ;
  @ignoreua
  ; HL 32768
  c49152 LD A,(HL)

If the ``@ignoreua`` directive were not present, a warning would be printed
(during the rendering phase) about the register description containing an
address (32768) that has not been converted to a label.

To apply the directive to a block start comment::

  ; Prepare data in page 128
  ;
  ; This routine operates on the data in page 128.
  ;
  ; HL 128*256
  ;
  @ignoreua
  ; First pick up the byte at 32768.
  c49152 LD A,(HL)

If the ``@ignoreua`` directive were not present, a warning would be printed
(during the rendering phase) about the start comment containing an address
(32768) that has not been converted to a label.

To apply the directive to a mid-block comment::

   28913 LD L,A
  @ignoreua
  ; #REGhl now holds either 32522 or 32600.
   28914 LD B,(HL)

If the ``@ignoreua`` directive were not present, warnings would be printed
(during the rendering phase) about the comment containing addresses (32522,
32600) that have not been converted to labels.

To apply the directive to a block end comment::

   44159 JP 63152
  @ignoreua
  ; This routine continues at 63152.

If the ``@ignoreua`` directive were not present, warnings would be printed
(during the rendering phase) about the comment containing an address (63152)
that has not been converted to a label.

To apply the directive to an instruction-level comment::

  @ignoreua
   60159 LD C,A        ; #REGbc now holds 62818

If the ``@ignoreua`` directive were not present, a warning would be printed
(during the rendering phase) about the comment containing an address (62818)
that has not been converted to a label.

+---------+---------------------------------------------------------------+
| Version | Changes                                                       |
+=========+===============================================================+
| 4.2     | Added support for register description sections               |
+---------+---------------------------------------------------------------+
| 2.4.1   | Added support for entry titles, entry descriptions, mid-block |
|         | comments and block end comments                               |
+---------+---------------------------------------------------------------+

.. _isub:

@isub
^^^^^
The ``@isub`` directive replaces, inserts or removes a label, instruction and
comment in :ref:`isubMode`.

The syntax is equivalent to that for the :ref:`bfix` directive.

+---------+-------------------------------------------------------------------+
| Version | Changes                                                           |
+=========+===================================================================+
| 7.1     | Added support for the ``+`` marker (to insert an instruction      |
|         | after the current one)                                            |
+---------+-------------------------------------------------------------------+
| 7.0     | Added support for specifying the replacement comment over         |
|         | multiple lines, replacing the label, and inserting, overwriting   |
|         | and removing instructions                                         |
+---------+-------------------------------------------------------------------+
| 6.4     | Added support for replacing the comment                           |
+---------+-------------------------------------------------------------------+

.. _isubBlockDirectives:

@isub block directives
^^^^^^^^^^^^^^^^^^^^^^
The ``@isub`` block directives define a block of lines that will be inserted or
removed in :ref:`isubMode`.

The syntax is equivalent to that for the :ref:`bfixBlockDirectives`.

.. _keep:

@keep
^^^^^
The ``@keep`` directive prevents the substitution of labels for numeric values
in the operand of the next instruction::

  @keep[=val1[,val2...]]

* ``val1``, ``val2`` etc. are the values to keep; if none are specified, all
  values are kept

In HTML mode, the ``@keep`` directive also prevents the operand from being
hyperlinked.

For example::

  @keep
   28328 LD BC,24576   ; #REGb=96, #REGc=0

If the ``@keep`` directive were not present, the operand (24576) of the
``LD BC`` instruction would be replaced with the label of the routine at 24576
(if there is a routine at that address); however, the operand is meant to be a
pure data value, not a variable or routine address.

+---------+-------------------------------------------------------------------+
| Version | Changes                                                           |
+=========+===================================================================+
| 6.2     | Added the ability to specify the values to keep; the ``@keep``    |
|         | directive is applied to instructions that have been replaced by   |
|         | an :ref:`isub`, :ref:`ssub` or :ref:`rsub` directive              |
+---------+-------------------------------------------------------------------+

.. _label:

@label
^^^^^^
The ``@label`` directive sets the label for the next instruction. ::

  @label=LABEL

* ``LABEL`` is the label to apply

For example::

  @label=ENDGAME
  c24576 XOR A

This sets the label for the routine at 24576 to ``ENDGAME``.

If ``LABEL`` is blank (``@label=``), the next instruction will have its entry
point marker removed (if it has one), and be prevented from having a label
automatically generated.

If ``LABEL`` starts with ``*`` (e.g. ``@label=*LOOP``), the next instruction
will be marked as an entry point (as if the instruction line in the skool file
started with ``*``), in addition to having its label set.

If ``LABEL`` is just ``*`` (``@label=*``), the next instruction will be marked
as an entry point, and have a label automatically generated.

In addition to being processed when :ref:`skool2asm.py` or :ref:`skool2html.py`
is run, ``@label`` directive values are checked by :ref:`sna2skool.py` while
reading a control file. They can be used to prevent an entry point marker from
being added to an instruction where it otherwise would be (``@label=``), or
force one to be added where it otherwise wouldn't (``@label=*``).

+---------+-------------------------------------------------------------------+
| Version | Changes                                                           |
+=========+===================================================================+
| 7.0     | An entry point marker (``*``) can be added to or removed from the |
|         | next instruction                                                  |
+---------+-------------------------------------------------------------------+
| 6.3     | ``LABEL`` may be blank (to prevent the next instruction from      |
|         | having a label automatically generated)                           |
+---------+-------------------------------------------------------------------+

.. _nowarn:

@nowarn
^^^^^^^
The ``@nowarn`` directive suppresses any warnings that would otherwise be
reported for the next instruction concerning:

* a ``LD`` operand being replaced with a routine label (if the instruction has
  not been replaced using ``@isub`` or ``@ssub``)
* an operand not being replaced with a label (because the operand address has
  no label)

For example::

  @nowarn
   25560 LD BC,25404   ; Point #REGbc at the routine at #R25404

If this ``@nowarn`` directive were not present, a warning would be printed
(during the parsing phase) about the operand (25404) being replaced with a
routine label (which would be inappropriate if 25404 were intended to be a pure
data value).

For another example::

  @ofix-begin
  @nowarn
   27872 CALL 27633    ; This should be CALL #R27634
  @ofix+else
         CALL 27634    ;
  @ofix+end

If this ``@nowarn`` directive were not present, a warning would be printed
(during the parsing phase, if not in :ref:`ofixMode`) about the operand (27633)
not being replaced with a label (usually you would want the operand of a CALL
instruction to be replaced with a label, but not in this case).

.. _ofix:

@ofix
^^^^^
The ``@ofix`` directive replaces, inserts or removes a label, instruction and
comment in :ref:`ofixMode`.

The syntax is equivalent to that for the :ref:`bfix` directive.

+---------+-------------------------------------------------------------------+
| Version | Changes                                                           |
+=========+===================================================================+
| 7.1     | Added support for the ``+`` marker (to insert an instruction      |
|         | after the current one)                                            |
+---------+-------------------------------------------------------------------+
| 7.0     | Added support for specifying the replacement comment over         |
|         | multiple lines, replacing the label, and inserting, overwriting   |
|         | and removing instructions                                         |
+---------+-------------------------------------------------------------------+
| 6.4     | Added support for replacing the comment                           |
+---------+-------------------------------------------------------------------+

.. _ofixBlockDirectives:

@ofix block directives
^^^^^^^^^^^^^^^^^^^^^^
The ``@ofix`` block directives define a block of lines that will be inserted or
removed in :ref:`ofixMode`.

The syntax is equivalent to that for the :ref:`bfixBlockDirectives`.

.. _org:

@org
^^^^
The ``@org`` directive inserts an ``ORG`` assembler directive. ::

  @org[=address]

* ``address`` is the ``ORG`` address; if not specified, it defaults to the
  address of the next instruction

Note that the ``@org`` directive works only on the first instruction in an
entry.

+---------+-------------------------------------------------------------------+
| Version | Changes                                                           |
+=========+===================================================================+
| 6.3     | The ``address`` parameter is optional                             |
+---------+-------------------------------------------------------------------+

.. _rem:

@rem
^^^^
The ``@rem`` directive may be used to make an illuminating comment about a
nearby section or other ASM directive in a skool file. The directive is ignored
by the parser. ::

  @rem=COMMENT

* ``COMMENT`` is a suitably illuminating comment

For example::

  @rem=The next section of data MUST start at 64000
  @org=64000

+---------+-----------------------+
| Version | Changes               |
+=========+=======================+
| 2.4     | The ``=`` is required |
+---------+-----------------------+

.. _remote:

@remote
^^^^^^^
The ``@remote`` directive creates a remote entry in a skool file. A remote
entry enables ``JR``, ``JP`` and ``CALL`` instructions to be hyperlinked to an
entry defined in another skool file. ::

  @remote=code:address[,address2...]

* ``code`` is the ID of the disassembly defined in the other skool file
* ``address`` is the address of the remote entry
* ``address2`` etc. are addresses of other entry points in the remote entry

For example::

  @remote=main:29012,29015

This directive, if it appeared in a secondary skool file, would enable
references to the routine at 29012 and its entry point at 29015 in the main
disassembly. It would also enable the :ref:`R` macro to create a hyperlink to a
remote entry point using the form::

  #R29015@main

+---------+---------+
| Version | Changes |
+=========+=========+
| 6.3     | New     |
+---------+---------+

.. _replace:

@replace
^^^^^^^^
The ``@replace`` directive replaces strings that match a regular expression in
skool file annotations and ref file section names and contents. ::

  @replace=/pattern/repl

or::

  @replace=/pattern/repl/

* ``pattern`` is the regular expression
* ``repl`` is the replacement string

(If the second form is used, any text appearing after the terminating ``/`` is
ignored.)

For example::

  @replace=/#copy/#CHR(169)

This ``@replace`` directive replaces all instances of ``#copy`` with
``#CHR(169)``.

If ``/`` appears anywhere in ``pattern`` or ``repl``, then an alternative
separator should be used; for example::

  @replace=|n/a|not applicable

As a convenience for dealing with decimal and hexadecimal numbers, wherever
``\i`` appears in ``pattern``, it is replaced by a regular expression group
that matches a decimal number or a hexadecimal number preceded by ``$``. For
example::

  @replace=/#udg\i,\i/#UDG(\1,#PEEK\2)

This ``@replace`` directive would replace ``#udg$a001,40960`` with
``#UDG($a001,#PEEK40960)``.

Note that string replacements specified by ``@replace`` directives are made
before skool macros are expanded, and in the order in which the directives
appear in the skool file. For example, if we have::

  @replace=/#foo\i/#bar\1
  @replace=/#bar\i/#EVAL\1,16

then ``#foo31`` would be replaced by ``#EVAL31,16``, but if these directives
were reversed::

  @replace=/#bar\i/#EVAL\1,16
  @replace=/#foo\i/#bar\1

then ``#foo31`` would be replaced by ``#bar31``.

See also :ref:`definingMacrosWithReplace`.

+---------+--------------------------------------------+
| Version | Changes                                    |
+=========+============================================+
| 6.0     | Replaces strings in ref file section names |
+---------+--------------------------------------------+
| 5.1     | New                                        |
+---------+--------------------------------------------+

.. _rfix:

@rfix
^^^^^
The ``@rfix`` directive replaces, inserts or removes a label, instruction and
comment in :ref:`rfixMode`.

The syntax is equivalent to that for the :ref:`bfix` directive.

+---------+-------------------------------------------------------------------+
| Version | Changes                                                           |
+=========+===================================================================+
| 7.1     | Added support for the ``+`` marker (to insert an instruction      |
|         | after the current one)                                            |
+---------+-------------------------------------------------------------------+
| 7.0     | Added support for specifying the replacement comment over         |
|         | multiple lines, replacing the label, and inserting, overwriting   |
|         | and removing instructions                                         |
+---------+-------------------------------------------------------------------+
| 6.4     | Added support for replacing the comment                           |
+---------+-------------------------------------------------------------------+
| 5.2     | New                                                               |
+---------+-------------------------------------------------------------------+

.. _rfixBlockDirectives:

@rfix block directives
^^^^^^^^^^^^^^^^^^^^^^
The ``@rfix`` block directives define a block of lines that will be inserted or
removed in :ref:`rfixMode`.

The syntax is equivalent to that for the :ref:`bfixBlockDirectives`.

.. _rsub:

@rsub
^^^^^
The ``@rsub`` directive replaces, inserts or removes a label, instruction and
comment in :ref:`rsubMode`.

The syntax is equivalent to that for the :ref:`rfix` directive.

+---------+-------------------------------------------------------------------+
| Version | Changes                                                           |
+=========+===================================================================+
| 7.1     | Added support for the ``+`` marker (to insert an instruction      |
|         | after the current one)                                            |
+---------+-------------------------------------------------------------------+
| 7.0     | Added support for specifying the replacement comment over         |
|         | multiple lines, replacing the label, and inserting, overwriting   |
|         | and removing instructions                                         |
+---------+-------------------------------------------------------------------+
| 6.4     | Added support for replacing the comment                           |
+---------+-------------------------------------------------------------------+

.. _rsubBlockDirectives:

@rsub block directives
^^^^^^^^^^^^^^^^^^^^^^
The ``@rsub`` block directives define a block of lines that will be inserted or
removed in :ref:`rsubMode`.

The syntax is equivalent to that for the :ref:`bfixBlockDirectives`.

.. _set:

@set
^^^^
The ``@set`` directive sets a property on the ASM writer. ::

  @set-name=value

* ``name`` is the property name
* ``value`` is the property value

``@set`` directives must be placed somewhere after the :ref:`start` directive,
and before the :ref:`end` directive (if there is one).

Recognised property names and their default values are:

* ``bullet`` - the bullet character(s) to use for list items specified in a
  :ref:`LIST` macro (default: ``*``)
* ``comment-width-min`` - the minimum width of the instruction comment field
  (default: ``10``)
* ``crlf`` - ``1`` to use CR+LF to terminate lines, or ``0`` to use the system
  default (default: ``0``)
* ``handle-unsupported-macros`` - how to handle an unsupported macro: ``1`` to
  expand it to an empty string, or ``0`` to exit with an error (default: ``0``)
* ``indent`` - the number of spaces by which to indent instructions (default:
  ``2``)
* ``instruction-width`` - the width of the instruction field (default: ``23``)
* ``label-colons`` - ``1`` to append a colon to labels, or ``0`` to leave
  labels unadorned (default: ``1``)
* ``line-width`` - the maximum width of each line (default: ``79``)
* ``tab`` - ``1`` to use a tab character to indent instructions, or ``0`` to
  use spaces (default: ``0``)
* ``warnings`` - ``1`` to print any warnings that are produced while writing
  ASM output (after parsing the skool file), or ``0`` to suppress them
  (default: ``1``)
* ``wrap-column-width-min`` - the minimum width of a wrappable table column
  (default: ``10``)

For example::

  @set-bullet=+

This ``@set`` directive sets the bullet character to '+'.

+---------+-------------------------------------------------------------+
| Version | Changes                                                     |
+=========+=============================================================+
| 3.4     | Added the ``handle-unsupported-macros`` and                 |
|         | ``wrap-column-width-min`` properties                        |
+---------+-------------------------------------------------------------+
| 3.3.1   | Added the ``comment-width-min``, ``indent``,                |
|         | ``instruction-width``, ``label-colons``, ``line-width`` and |
|         | ``warnings`` properties                                     |
+---------+-------------------------------------------------------------+
| 3.2     | New                                                         |
+---------+-------------------------------------------------------------+

.. _ssub:

@ssub
^^^^^
The ``@ssub`` directive replaces, inserts or removes a label, instruction and
comment in :ref:`ssubMode`.

The syntax is equivalent to that for the :ref:`bfix` directive.

+---------+-------------------------------------------------------------------+
| Version | Changes                                                           |
+=========+===================================================================+
| 7.1     | Added support for the ``+`` marker (to insert an instruction      |
|         | after the current one)                                            |
+---------+-------------------------------------------------------------------+
| 7.0     | Added support for specifying the replacement comment over         |
|         | multiple lines, replacing the label, and inserting, overwriting   |
|         | and removing instructions                                         |
+---------+-------------------------------------------------------------------+
| 6.4     | Added support for replacing the comment                           |
+---------+-------------------------------------------------------------------+

.. _ssubBlockDirectives:

@ssub block directives
^^^^^^^^^^^^^^^^^^^^^^
The ``@ssub`` block directives define a block of lines that will be inserted or
removed in :ref:`ssubMode`.

The syntax is equivalent to that for the :ref:`bfixBlockDirectives`.

+---------+---------+
| Version | Changes |
+=========+=========+
| 4.4     | New     |
+---------+---------+

.. _start:

@start
^^^^^^
The ``@start`` directive indicates where to start parsing the skool file for
the purpose of generating ASM output. Everything before the ``@start``
directive is ignored by :ref:`skool2asm.py`.

See also :ref:`end`.

.. _writer:

@writer
^^^^^^^
The ``@writer`` directive specifies the name of the Python class to use to
generate ASM output. It must be placed somewhere after the :ref:`start`
directive, and before the :ref:`end` directive (if there is one). ::

  @writer=package.module.classname

or::

  @writer=/path/to/moduledir:module.classname

The second of these forms may be used to specify a class in a module that is
outside the module search path (e.g. a standalone module that is not part of
an installed package).

The default ASM writer class is skoolkit.skoolasm.AsmWriter. For information on
how to create your own Python class for generating ASM output, see the
documentation on :ref:`extending SkoolKit <extendingSkoolKit>`.

+---------+-----------------------------------------------------------------+
| Version | Changes                                                         |
+=========+=================================================================+
| 3.3.1   | Added support for specifying a module outside the module search |
|         | path                                                            |
+---------+-----------------------------------------------------------------+
| 3.1     | New                                                             |
+---------+-----------------------------------------------------------------+
