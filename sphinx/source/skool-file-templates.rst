.. _skoolFileTemplates:

Skool file templates
====================
A skool file template defines the basic structure of a `skool` file, but,
unlike a `skool` file, contains directives on how to disassemble a program into
Z80 instructions instead of the Z80 instructions themselves. The directives are
similar to those that may appear in a control file.

The :ref:`skool2sft.py` command can generate a skool file template from an
existing `skool` file; the :ref:`sna2skool.py` command can then generate a
`skool` file from the template and an appropriate snapshot.

.. _skoolFileTemplateFormat:

Skool file template format
--------------------------
A skool file template has the same layout as a `skool` file, except that the
lines in 'b', 'c', 'g', 't', 'u', 'w' and 'z' blocks that correspond to Z80
instructions look like this::

  xX#####,n[;c[ comment]]

where:

* ``x`` is one of the characters ``* bcgtuwz`` (with the same meaning as in a
  :ref:`skool file <skoolFiles>`)
* ``X`` is one of the characters ``BCTWZ`` (with the same meaning as in a
  :ref:`control file <controlFiles>`)
* ``#####`` is the address at which to start disassembling
* ``n`` is the number of bytes to disassemble
* ``c`` is the index of the column in which the comment marker (``;``) appears
  in the line (if it does appear)
* ``comment``, if present, is the instruction-level comment for the line on
  which the instruction occurs

If a comment for a single instruction spans two or more lines in a `skool`
file, as in::

  c24296 CALL 57935    ; This comment is too long to fit on a single line, so
                       ; we use two lines

then it will be rendered in the skool file template thus::

  cC24296,3;21 This comment is too long to fit on a single line, so
   ;21 we use two lines

Sequences of DEFB statements can be declared on a single line thus::

  bB40960,8*2,5

which is equivalent to::

  bB40960,8
   B40968,8
   B40976,5

The same syntax also applies for declaring sequences of DEFM, DEFW and DEFS
statements.

DEFB and DEFM statements may contain both strings and bytes; for example::

  b30000 DEFB 1,2,3,4,"Hello!"
   30010 DEFM "A",5,6
   30013 DEFM "B",7,8

Such statements will be rendered in the skool file template thus::

  bB30000,4:T6
   T30010,1:B2*2

Finally, any line that begins with a hash character (``#``) is ignored by
`sna2skool.py`, and will not show up in the `skool` file.

Data definition entries
-----------------------
In the same way as `skool2html.py` uses data definition entries ('d' blocks) in
a `skool` file to insert data into the memory snapshot it constructs,
`sna2skool.py` uses data definition entries in a skool file template to replace
data in the snapshot given on the command line. This feature can be used to
make sure that a 'volatile' part of memory is set to a specific value before
being disassembled.

For example, if address 32400 holds the number of lives, you could make sure
that its contents are set to 0 so that it will disassemble to ``DEFB 0``
(whatever the contents may be in the snapshot itself) thus::

  d32400 DEFB 0

  ; Number of lives
  bB32400,1

Revision history
----------------
+---------+--------------------------------------------------------------+
| Version | Changes                                                      |
+=========+==============================================================+
| 2.4     | New                                                          |
+---------+--------------------------------------------------------------+
| 3.1.4   | Added support for DEFB and DEFM statements that contain both |
|         | strings and bytes                                            |
+---------+--------------------------------------------------------------+
