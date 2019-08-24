.. _components:

SkoolKit components
===================

SkoolKit relies on several components in order to function:

* :ref:`assembler`
* :ref:`ctlgenerator`
* :ref:`disassembler`

The objects that are used for these components can be specified in the
``[skoolkit]`` section of a file named `skoolkit.ini` either in the current
working directory or in `~/.skoolkit`. The default contents of the
``[skoolkit]`` section are as follows::

  Assembler=skoolkit.z80
  ControlFileGenerator=skoolkit.snactl
  Disassembler=skoolkit.disassembler.Disassembler

.. _assembler:

Assembler
---------
This object is responsible for converting assembly language instructions and
DEFB/DEFM/DEFS/DEFW statements into byte values, or computing their size. It
must supply the following API functions, in common with skoolkit.z80:

.. automodule:: skoolkit.z80
   :members: assemble, get_size

.. _ctlgenerator:

Control file generator
----------------------
This object is reponsible for generating a dictionary of control directives
from a snapshot. Each key in the dictionary is an address, and the associated
value is the control directive (e.g. ``b`` or ``c``) for that address. The
control file generator object must supply the following API function, in common
with skoolkit.snactl:

.. automodule:: skoolkit.snactl
   :members: generate_ctls

.. _disassembler:

Disassembler
------------
This class is responsible for converting byte values into assembly language
instructions and DEFB/DEFM/DEFS/DEFW statements. It must supply the following
API methods, in common with skoolkit.disassembler.Disassembler:

.. autoclass:: skoolkit.disassembler.Disassembler
   :members: disassemble, defb_range, defm_range, defs_range, defw_range, ignore

The *sublengths* argument of the :meth:`defb_range`, :meth:`defm_range`,
:meth:`defs_range` and :meth:`defw_range` methods is a sequence of 2-element
tuples, each of which specifies the desired size and number base for an
instruction in the given address range::

  (size, base)

``size`` is the number of bytes in the instruction or DEFB/DEFM/DEFS/DEFW
statement. ``base`` is the number base indicator for any numeric operand:

* `None` - default base
* 'B' - byte (in a DEFB/DEFM statement)
* 'T' - character (in a DEFB/DEFM statement)
* 'b' - binary
* 'c' - character
* 'd' - decimal
* 'h' - hexadecimal
* 'm' - negative
* 'n' - default base

For instructions with two numeric operands (e.g. 'LD (IX+d),n'), ``base`` may
consist of two letters, one for each operand (e.g. 'dh').

If *sublengths* contains a single element whose ``size`` value is `None`, then
the method should produce a list of instructions with default sizes (as
determined by `defb_size`, `defb_mod` and `defm_size`), using the default
number base.
