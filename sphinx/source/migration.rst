.. _migrating:

Migrating from SkoolKit 6
=========================
SkoolKit 7 includes some changes that make it incompatible with SkoolKit 6. If
you have developed a disassembly using SkoolKit 6 and find that the SkoolKit
commands no longer work with your skool files or ref files, or produce broken
output, look through the following sections for tips on how to migrate your
disassembly to SkoolKit 7.

@nolabel
--------
The ``@nolabel`` directive is not supported in SkoolKit 7. Instead you should
use the :ref:`label` directive with a blank label: ``@label=``.

skoolkit6to7.py
---------------
The `skoolkit6to7.py`_ script may be used to convert a skool file or ref file
that is compatible with SkoolKit 6 into a file that will work with SkoolKit 7.
For example, to convert `game.ref`::

  $ skoolkit6to7.py game.ref > game7.ref

.. _skoolkit6to7.py: https://github.com/skoolkid/skoolkit/raw/master/utils/skoolkit6to7.py
