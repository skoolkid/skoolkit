.. _asmTemplates:

ASM templates
=============
Each line of output produced by :ref:`skool2asm.py` is built from a template. A
template contains 'replacement fields' - identifiers enclosed by braces
(``{`` and ``}``) - that are replaced by appropriate content (such as a label
or register name) when the template is formatted.

The default templates can be overridden by custom templates read from a file by
setting the ``Templates`` configuration parameter of
:ref:`skool2asm.py <skool2asm-conf>`. To define a custom template, specify its
name in square brackets on a line of its own, and follow it with the content of
the template. For example::

  [org]
  .{org} {address}

.. _t_comment:

comment
-------
The ``comment`` template is used to format a line in an entry title, entry
description, block start comment, mid-block comment, or block end comment. ::

  ; {text}

The following identifier is available:

* ``text`` - the text of the comment line

This template is also used to used to format lines between paragraphs in
comments, with ``text`` set to an empty string.

.. _t_equ:

equ
---
The ``equ`` template is used to format an EQU directive produced by :ref:`equ`.
::

  {label} {equ} {value}

The following identifiers are available:

* ``equ`` - 'EQU' or 'equ' (depending on the case)
* ``label`` - the label
* ``value`` - the value

.. _t_instruction:

instruction
-----------
The ``instruction`` template is used to format an instruction line or
instruction comment continuation line. ::

  {indent}{operation:{width}} {sep} {text}

The following identifiers are available:

* ``indent`` - the instruction indent (as defined by the ``indent`` property)
* ``operation`` - either the operation (e.g. 'XOR A'), or an empty string (if
  formatting a comment continuation line)
* ``sep`` - the comment separator (';' if there is a comment, an empty string
  otherwise)
* ``text`` - the text of the comment line
* ``width`` - the width of the instruction field (as defined by the
  ``instruction-width`` property)

The ``indent`` and ``instruction-width`` properties can be set by either the
:ref:`set` directive, or the ``Set-indent`` and ``Set-instruction-width``
configuration parameters of :ref:`skool2asm.py <skool2asm-conf>`.

.. _t_label:

label
-----
The ``label`` template is used to format an instruction label. ::

  {label}{suffix}

The following identifiers are available:

* ``label`` - the instruction label
* ``suffix`` - ':' or an empty string (as defined by the ``label-colons``
  property)

The ``label-colons`` property can be set by either the :ref:`set` directive, or
the ``Set-label-colons`` configuration parameter of
:ref:`skool2asm.py <skool2asm-conf>`.

.. _t_org:

org
---
The ``org`` template is used to format an ORG directive produced by :ref:`org`.
::

  {indent}{org} {address}

The following identifiers are available:

* ``address`` - the ORG address (as a string)
* ``indent`` - the instruction indent (as defined by the ``indent`` property)
* ``org`` - 'ORG' or 'org' (depending on the case)

The ``indent`` property can be set by either the :ref:`set` directive, or the
``Set-indent`` configuration parameter of :ref:`skool2asm.py <skool2asm-conf>`.

.. _t_register:

register
--------
The ``register`` template is used to format lines in the register section of an
entry header. ::

  ; {prefix:>{prefix_len}}{reg:{reg_len}} {text}

The following identifiers are available:

* ``prefix`` - the register prefix (e.g. 'In:' or 'O:'), or an empty string (if
  formatting a register description continuation line)
* ``prefix_len`` - the maximum length of all register prefixes in the register
  section
* ``reg`` - the register name (e.g. 'HL'), or an empty string (if formatting a
  register description continuation line)
* ``reg_len`` - the length of the register name
* ``text`` - the text of a line of the register description
