.. _migrating:

Migrating from SkoolKit 8
=========================
SkoolKit 9 includes some changes that make it incompatible with SkoolKit 8. If
you have developed a disassembly using SkoolKit 8 and find that the SkoolKit
commands no longer work with your source files, or produce broken output, look
through the following sections for tips on how to migrate your disassembly to
SkoolKit 9.

#DEFINE
-------
The ``#DEFINE`` macro is not supported in SkoolKit 9. Instead, the more
powerful :ref:`DEF` macro should be used.

For example, you might have used ``#DEFINE`` to define a ``#MIN`` macro that
expands to the smaller of its two integer arguments::

  #DEFINE2(MIN,#IF({0}<{1})({0},{1}))

This can be redefined by using the ``#DEF`` macro::

  #DEF(#MIN(a,b) #IF($a<$b)($a,$b))
