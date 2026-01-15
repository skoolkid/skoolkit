.. _migrating:

Migrating from SkoolKit 9
=========================
SkoolKit 10 includes some changes that make it incompatible with SkoolKit 9. If
you have developed a disassembly using SkoolKit 9 and find that the SkoolKit
commands no longer work with your source files, or produce broken output, look
through the following sections for tips on how to migrate your disassembly to
SkoolKit 10.

#CALL
-----
In SkoolKit 9, the :ref:`CALL` macro could be written thus::

  #CALL:method(args)

This is not supported in SkoolKit 10. Instead, use the following syntax::

  #CALL(method(args))

#FONT
-----
In SkoolKit 9, the :ref:`FONT` macro could be written thus::

  #FONT:(text)params[{CROP}][(fname)]

This is not supported in SkoolKit 10. Instead, use the following syntax::

  #FONTparams[(text)][{CROP}][(fname)]

#LINK
-----
In SkoolKit 9, the :ref:`LINK` macro could be written thus::

  #LINK:PageId[#name](link text)

This is not supported in SkoolKit 10. Instead, use the following syntax::

  #LINK(PageId[#name])(link text)

#UDGARRAY
---------
In SkoolKit 9, the UDG specifications of a :ref:`UDGARRAY` macro could be
separated from the main parameters by a semicolon::

  #UDGARRAYparams;SPEC1;SPEC2...

This is not supported in SkoolKit 10. Instead, the UDG specifications must be
enclosed in parentheses::

  #UDGARRAYparams(SPEC1;SPEC2...)...

In SkoolKit 9, the attribute address range specifications of a :ref:`UDGARRAY`
macro could be separated from the preceding UDG specifications by an ``@``
symbol::

  #UDGARRAYparams(SPEC1;SPEC2...)@ATTRS1;ATTRS2...

This is not supported in SkoolKit 10. Instead, the attribute address range
specifications must be enclosed in square brackets::

  #UDGARRAYparams(SPEC1;SPEC2...)[ATTRS1;ATTRS2...]...

#UDGARRAY*
----------
The ``#UDGARRAY*`` macro is not supported in SkoolKit 10. Use the :ref:`FRAMES`
macro instead.

skoolkit9to10.py
----------------
The `skoolkit9to10.py`_ script may be used to convert a skool file, control
file or ref file that is compatible with SkoolKit 9 into a file that will work
with SkoolKit 10. For example, to convert `game.skool`::

  $ skoolkit9to10.py game.skool > game10.skool

.. _skoolkit9to10.py: https://github.com/skoolkid/skoolkit/raw/master/utils/skoolkit9to10.py
