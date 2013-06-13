.. _asmModesAndDirectives:

ASM modes and directives
========================
A `skool` file may contain directives that are processed during the parsing
phase. Exactly how a directive is processed (and whether it is executed)
depends on the 'substitution mode' and 'bugfix mode' in which the `skool` file
is being parsed.

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

  ; @isub=LD A,(32512)
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

  ; @ssub=LD (27015+1),A
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
  ; @ssub=LD (HL),24002%256
   24000 LD (HL),194
  ; @rsub+begin
         INC L
         LD (HL),24002/256
  ; @rsub+end
   24002 XOR A

This ``@rsub`` block directive inserts two instructions that ensure that the
address stored at 32766 will have the correct MSB as well as the correct LSB,
regardless of where the code originally at 24002 now lives.

``@rsub`` mode is invoked by passing the ``-r`` option to
:ref:`skool2asm.py <skool2asm.py>`. ``@rsub`` mode also implies ``@ofix`` mode;
see below for a description of ``@ofix`` mode and the other bugfix modes.

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

  ; @ofix-begin
   27872 CALL 27633    ; This should be CALL 27634
  ; @ofix+else
         CALL 27634
  ; @ofix+end

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

  ; @bfix-begin
   32205 JR Z,32232    ; This should be JR NZ,32232
  ; @bfix+else
         JR NZ,32232   ;
  ; @bfix+end

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
  ; @rsub+begin
         LD A,H
         OR L
  ; @rsub+end
   28433 JP Z,29712

These ``@rfix`` block directives insert some instructions to fix the faulty
check on whether HL holds 0.

``@rfix`` mode is invoked by passing the ``-f 3`` option to
:ref:`skool2asm.py <skool2asm.py>`. ``@rfix`` mode implies ``@rsub`` mode (see
:ref:`rsubMode`).

.. _asmDirectives:

ASM directives
--------------
The ASM directives recognised by SkoolKit are described in the following
subsections.

.. _bfix:

@bfix
^^^^^
The ``@bfix`` directive makes an instruction substitution in ``@bfix`` mode. ::

  ; @bfix=INSTRUCTION

* ``INSTRUCTION`` is the replacement instruction

For example::

  ; @bfix=DEFM "Phosphorus"
  t57532 DEFM "Phosphorous"

.. _bfixBlockDirectives:

@bfix block directives
^^^^^^^^^^^^^^^^^^^^^^
The ``@bfix`` block directives define a block of lines that will be inserted or
removed in ``@bfix`` mode.

The syntax for defining a block that will be inserted in ``@bfix`` mode (but
left out otherwise) is::

  ; @bfix+begin
  ...                  ; Lines to be inserted
  ; @bfix+end

The syntax for defining a block that will be removed in ``@bfix`` mode (but
left in otherwise) is::

  ; @bfix-begin
  ...                  ; Lines to be removed
  ; @bfix-end

Typically, though, it is desirable to define a block that will be removed in
``@bfix`` mode right next to the block that should be inserted in its place.
That may be done thus::

  ; @bfix-begin
  ...                  ; Instructions to be removed
  ; @bfix+else
  ...                  ; Instructions to be inserted
  ; @bfix+end

which is equivalent to::

  ; @bfix-begin
  ...                  ; Instructions to be removed
  ; @bfix-end
  ; @bfix+begin
  ...                  ; Instructions to be inserted
  ; @bfix+end

For example::

  ; @bfix-begin
   32205 JR Z,32232    ; This should be JR NZ,32232
  ; @bfix+else
         JR NZ,32232   ;
  ; @bfix+end

.. _end:

@end
^^^^
The ``@end`` directive may be used to indicate where to stop parsing the
`skool` file for the purpose of generating ASM output. Everything after the
``@end`` directive is ignored. ::

  ; @end

See also :ref:`start`.

+---------+---------+
| Version | Changes |
+=========+=========+
| 2.2.2   | New     |
+---------+---------+

.. _ignoreua:

@ignoreua
^^^^^^^^^
The ``@ignoreua`` directive suppresses any warnings that would otherwise be
reported concerning addresses not converted to labels in the comment that
follows; the comment may be an entry title, an entry description, a mid-block
comment, a block end comment, or an instruction-level comment. ::

  ; @ignoreua

To apply the directive to an entry title::

  ; @ignoreua
  ; Prepare data at 32768
  ;
  ; This routine operates on the data in page 128.

If the ``@ignoreua`` directive were not present, a warning would be printed
(during the rendering phase) about the entry title containing an address
(32768) that has not been converted to a label.

To apply the directive to an entry description::

  ; Prepare data in page 128
  ;
  ; @ignoreua
  ; This routine operates on the data at 32768.

If the ``@ignoreua`` directive were not present, a warning would be printed
(during the rendering phase) about the entry description containing an address
(32768) that has not been converted to a label.

To apply the directive to a mid-block comment::

   28913 LD L,A
  ; @ignoreua
  ; #REGhl now holds either 32522 or 32600.
   28914 LD B,(HL)

If the ``@ignoreua`` directive were not present, warnings would be printed
(during the rendering phase) about the comment containing addresses (32522,
32600) that have not been converted to labels.

To apply the directive to a block end comment::

   44159 JP 63152
  ; @ignoreua
  ; This routine continues at 63152.

If the ``@ignoreua`` directive were not present, warnings would be printed
(during the rendering phase) about the comment containing an address (63152)
that has not been converted to a label.

To apply the directive to an instruction-level comment::

  ; @ignoreua
   60159 LD C,A        ; #REGbc now holds 62818

If the ``@ignoreua`` directive were not present, a warning would be printed
(during the rendering phase) about the comment containing an address (62818)
that has not been converted to a label.

+---------+---------------------------------------------------------------+
| Version | Changes                                                       |
+=========+===============================================================+
| 2.4.1   | Added support for entry titles, entry descriptions, mid-block |
|         | comments and block end comments                               |
+---------+---------------------------------------------------------------+

.. _isub:

@isub
^^^^^
The ``@isub`` directive makes an instruction substitution in ``@isub`` mode. ::

  ; @isub=INSTRUCTION

* ``INSTRUCTION`` is the replacement instruction

For example::

  ; @isub=LD A,(32512)
   25396 LD A,(m)

This ``@isub`` directive ensures that ``LD A,(m)`` is replaced by the valid
instruction ``LD A,(32512)`` when rendering in ASM mode.

.. _isubBlockDirectives:

@isub block directives
^^^^^^^^^^^^^^^^^^^^^^
The ``@isub`` block directives define a block of lines that will be inserted or
removed in ``@isub`` mode.

The syntax is equivalent to that for the :ref:`bfixBlockDirectives`.

.. _keep:

@keep
^^^^^
The ``@keep`` directive prevents the substitution of a label for the operand in
the next instruction (but only when the instruction has not been replaced using
an ``@isub`` or ``@ssub`` directive). ::

  ; @keep

For example::

  ; @keep
   28328 LD BC,24576   ; #REGb=96, #REGc=0

If the ``@keep`` directive were not present, the operand (24576) of the
``LD BC`` instruction would be replaced with the label of the routine at 24576
(if there is a routine at that address); however, the operand is meant to be a
pure data value, not a variable or routine address.

.. _label:

@label
^^^^^^
The ``@label`` directive sets the label for the next instruction. ::

  ; @label=LABEL

* ``LABEL`` is the label to apply

For example::

  ; @label=ENDGAME
  c24576 XOR A

This sets the label for the routine at 24576 to ``ENDGAME``.

.. _nolabel:

@nolabel
^^^^^^^^
The ``@nolabel`` directive prevents the next instruction from having a label
automatically generated. ::

  ; @nolabel

For example::

  ; @label=TOGGLE
  c48998 LD HL,32769
  ; @bfix+begin
  ; @label=LOOP
  ; @bfix+end
   49001 LD A,(HL)
  ; @bfix+begin
  ; @nolabel
  ; @bfix+end
  *49002 XOR L
   49003 LD (HL),A
   49004 INC L
  ; @bfix-begin
   49005 JR NZ,49002
  ; @bfix+else
   49005 JR NZ,49001
  ; @bfix+end

The ``@nolabel`` directive here prevents the instruction at 49002 from being
labelled in ``@bfix`` mode (because no label is required; instead, the previous
instruction at 49001 will be labelled).

The output in ``@bfix`` mode will be::

  TOGGLE:
    LD HL,32769
  LOOP:
    LD A,(HL)
    XOR L
    LD (HL),A
    INC L
    JR NZ,LOOP

And the output when not in ``@bfix`` mode will be::

  TOGGLE:
    LD HL,32769
    LD A,(HL)
  TOGGLE_0:
    XOR L
    LD (HL),A
    INC L
    JR NZ,TOGGLE_0

.. _nowarn:

@nowarn
^^^^^^^
The ``@nowarn`` directive suppresses any warnings that would otherwise be
reported for the next instruction concerning:

* a ``LD`` operand being replaced with a routine label (if the instruction has
  not been replaced using ``@isub`` or ``@ssub``)
* an operand not being replaced with a label (because the operand address has
  no label)

::

  ; @nowarn

For example::

  ; @nowarn
   25560 LD BC,25404   ; Point #REGbc at the routine at #R25404

If this ``@nowarn`` directive were not present, a warning would be printed
(during the parsing phase) about the operand (25404) being replaced with a
routine label (which would be inappropriate if 25404 were intended to be a pure
data value).

For another example::

  ; @ofix-begin
  ; @nowarn
   27872 CALL 27633    ; This should be CALL #R27634
  ; @ofix+else
         CALL 27634    ;
  ; @ofix+end

If this ``@nowarn`` directive were not present, a warning would be printed
(during the parsing phase, if not in ``@ofix`` mode) about the operand (27633)
not being replaced with a label (usually you would want the operand of a CALL
instruction to be replaced with a label, but not in this case).

.. _ofix:

@ofix
^^^^^
The ``@ofix`` directive makes an instruction substitution in ``@ofix`` mode. ::

  ; @ofix=INSTRUCTION

* ``INSTRUCTION`` is the replacement instruction (with a corrected operand)

For example::

  ; @ofix=JR NZ,26067
   25989 JR NZ,26068

This ``@ofix`` directive replaces the operand of the ``JR NZ`` instruction with
26067.

.. _ofixBlockDirectives:

@ofix block directives
^^^^^^^^^^^^^^^^^^^^^^
The ``@ofix`` block directives define a block of lines that will be inserted or
removed in ``@ofix`` mode.

The syntax is equivalent to that for the :ref:`bfixBlockDirectives`.

.. _org:

@org
^^^^
The ``@org`` directive inserts an ``ORG`` assembler directive. ::

  ; @org=ADDRESS

* ``ADDRESS`` is the ``ORG`` address

.. _rem:

@rem
^^^^
The ``@rem`` directive may be used to make an illuminating comment about a
nearby section or other ASM directive in a `skool` file. The directive is
ignored by the parser. ::

  ; @rem=COMMENT

* ``COMMENT`` is a suitably illuminating comment

For example::

  ; @rem=The next section of data MUST start at 64000
  ; @org=64000

+---------+-----------------------+
| Version | Changes               |
+=========+=======================+
| 2.4     | The ``=`` is required |
+---------+-----------------------+

.. _rfixBlockDirectives:

@rfix block directives
^^^^^^^^^^^^^^^^^^^^^^
The ``@rfix`` block directives define a block of lines that will be inserted or
removed in ``@rfix`` mode.

The syntax is equivalent to that for the :ref:`bfixBlockDirectives`.

.. _rsub:

@rsub
^^^^^
The ``@rsub`` directive makes an instruction substitution in ``@rsub`` mode. ::

  ; @rsub=INSTRUCTION

* ``INSTRUCTION`` is the replacement instruction

For example::

  ; @rsub=INC BC
   30143 INC C         ; Point #REGbc at the next byte of data

.. _rsubBlockDirectives:

@rsub block directives
^^^^^^^^^^^^^^^^^^^^^^
The ``@rsub`` block directives define a block of lines that will be inserted or
removed in ``@rsub`` mode.

The syntax is equivalent to that for the :ref:`bfixBlockDirectives`.

.. _set:

@set
^^^^
The ``@set`` directive sets a property on the ASM writer. ::

  ; @set-name=value

* ``name`` is the property name
* ``value`` is the property value

``@set`` directives should be placed somewhere after the ``@start`` directive,
and before the ``@end`` directive (if there is one).

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
  ASM output (after parsing the `skool` file), or ``0`` to suppress them
  (default: ``1``)
* ``wrap-column-width-min`` - the minimum width of a wrappable table column
  (default: ``10``)

For example::

  ; @set-bullet=+

This ``@set`` directive sets the bullet character to '+'.

+---------+---------------------------------------------------------------+
| Version | Changes                                                       |
+=========+===============================================================+
| 3.2     | New                                                           |
+---------+---------------------------------------------------------------+
| 3.3.1   | Added the `comment-width-min`, `indent`, `instruction-width`, |
|         | `label-colons`, `line-width` and `warnings` properties        |
+---------+---------------------------------------------------------------+
| 3.4     | Added the `handle-unsupported-macros` and                     |
|         | `wrap-column-width-min` properties                            |
+---------+---------------------------------------------------------------+

.. _ssub:

@ssub
^^^^^
The ``@ssub`` directive makes an instruction substitution in ``@ssub`` mode. ::

  ; @ssub=INSTRUCTION

* ``INSTRUCTION`` is the replacement instruction

For example::

  ; @ssub=LD (27015+1),A
  *27012 LD (27016),A  ; Change the instruction below from SET 0,B to RES 0,B
                       ; or vice versa
   27015 SET 0,B

This ``@ssub`` directive replaces ``LD (27016),A`` with ``LD (27015+1),A``; the
``27015`` will be replaced by the label for that address before rendering.
(``27016`` cannot be replaced by a label, since it is not the address of an
instruction.)

.. _start:

@start
^^^^^^
The ``@start`` directive must be used to indicate where to start parsing the
`skool` file for the purpose of generating ASM output. Everything before the
``@start`` directive is ignored. ::

  ; @start

See also :ref:`end`.

.. _writer:

@writer
^^^^^^^
The ``@writer`` directive specifies the name of the Python class to use to
generate ASM output. It should be placed somewhere after the ``@start``
directive, and before the ``@end`` directive (if there is one). ::

  ; @writer=package.module.classname

or::

  ; @writer=/path/to/moduledir:module.classname

The second of these forms may be used to specify a class in a module that is
outside the module search path (e.g. a standalone module that is not part of
an installed package).

The default ASM writer class is skoolkit.skoolasm.AsmWriter. For information on
how to create your own Python class for generating ASM output, see the
documentation on :ref:`extending SkoolKit <extendingSkoolKit>`.

+---------+-----------------------------------------------------------------+
| Version | Changes                                                         |
+=========+=================================================================+
| 3.1     | New                                                             |
+---------+-----------------------------------------------------------------+
| 3.3.1   | Added support for specifying a module outside the module search |
|         | path                                                            |
+---------+-----------------------------------------------------------------+
