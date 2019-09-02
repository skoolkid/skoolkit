.. _components:

SkoolKit components
===================

SkoolKit relies on several components in order to function:

* :ref:`assembler`
* :ref:`ctlcomposer`
* :ref:`ctlgenerator`
* :ref:`disassembler`
* :ref:`instructionConverter`
* :ref:`labeller`
* :ref:`skoolRefCalc`
* :ref:`snapshotReader`
* :ref:`snapshotRefCalc`

The objects that are used for these components can be specified in the
``[skoolkit]`` section of a file named `skoolkit.ini` either in the current
working directory or in `~/.skoolkit`. The default contents of the
``[skoolkit]`` section are as follows::

  Assembler=skoolkit.z80
  ControlDirectiveComposer=skoolkit.skoolctl
  ControlFileGenerator=skoolkit.snactl
  Disassembler=skoolkit.disassembler.Disassembler
  InstructionConverter=skoolkit.skoolparser.InstructionConverter
  Labeller=skoolkit.skoolparser.Labeller
  SkoolReferenceCalculator=skoolkit.skoolparser
  SnapshotReader=skoolkit.snapshot
  SnapshotReferenceCalculator=skoolkit.snaskool

.. _assembler:

Assembler
---------
This object is responsible for converting assembly language instructions and
DEFB/DEFM/DEFS/DEFW statements into byte values, or computing their size. It
must supply the following API functions, in common with skoolkit.z80:

.. automodule:: skoolkit.z80
   :members: assemble, get_size

.. _ctlComposer:

Control directive composer
--------------------------
This object is responsible for computing the type, length and sublengths of a
DEFB/DEFM/DEFS/DEFW statement, or the operand bases of a regular instruction,
for the purpose of composing a control directive. It must supply the following
API function, in common with skoolkit.skoolctl:

.. automodule:: skoolkit.skoolctl
   :members: compose

.. _ctlgenerator:

Control file generator
----------------------
This object is reponsible for generating a dictionary of control directives
from a snapshot. Each key in the dictionary is an address, and the associated
value is the control directive (e.g. 'b' or 'c') for that address. The control
file generator object must supply the following API function, in common with
skoolkit.snactl:

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

.. _instructionConverter:

Instruction converter
---------------------
This class is responsible for converting the base and case of instructions in a
skool file. It must supply the following API methods, in common with
skoolkit.skoolparser.InstructionConverter:

.. autoclass:: skoolkit.skoolparser.InstructionConverter
   :members: convert

.. _labeller:

Labeller
--------
This object is responsible for replacing addresses with labels in instruction
operands. It must supply the following API function, in common with
skoolkit.skoolparser.Labeller:

.. automethod:: skoolkit.skoolparser.Labeller.substitute_labels

Memory map entries and remote entries have the following attributes:

* *ctl* - the entry's control directive ('b', 'c', 'g', 'i', 's', 't', 'u' or
  'w' for a memory map entry; `None` for a remote entry)
* *instructions* - a collection of instruction objects

Each instruction object has the following attributes:

* *address* - the address of the instruction
* *keep* - `None` if the instruction has no :ref:`keep` directive; an empty
  collection if it has a bare :ref:`keep` directive; or a collection of
  addresses if it has a :ref:`keep` directive with one or more values
* *operation* - the operation (e.g. 'XOR A'), or an empty string if the
  instruction is in a remote entry

.. _skoolRefCalc:

Skool reference calculator
--------------------------
This object is responsible for generating a dictionary of references (for
each instruction that refers to another instruction) and a dictionary of
referrers (for each instruction that is referred to by other instructions) from
the instructions in a skool file.

Each key in the references dictionary is an instruction object, and the
corresponding value is a 3-element tuple, ``(entry, address, address_s)``,
where ``entry`` is the entry containing the instruction referred to,
``address`` is the address of the instruction referred to, and ``address_s`` is
the corresponding address string in the operand of the referring instruction.

Each key in the referrers dictionary is an instruction object, and the
corresponding value is a list of the entries that refer to that instruction.

The skool reference calculator must supply the following API function, in
common with skoolkit.skoolparser:

.. automodule:: skoolkit.skoolparser
   :members: calculate_references

Memory map entries and remote entries have the following attributes:

* *ctl* - the entry's control directive ('b', 'c', 'g', 'i', 's', 't', 'u' or
  'w' for a memory map entry; `None` for a remote entry)
* *instructions* - a collection of instruction objects

Each instruction object has the following attributes:

* *address* - the address of the instruction
* *keep* - `None` if the instruction has no :ref:`keep` directive; an empty
  collection if it has a bare :ref:`keep` directive; or a collection of
  addresses if it has a :ref:`keep` directive with one or more values
* *operation* - the operation (e.g. 'XOR A'), or an empty string if the
  instruction is in a remote entry

.. _snapshotReader:

Snapshot reader
---------------
This object is responsible for producing a 65536-element list of byte values
from a snapshot file. It must supply the following API functions, in common
with skoolkit.snapshot:

.. automodule:: skoolkit.snapshot
   :members: can_read, get_snapshot

.. _snapshotRefCalc:

Snapshot reference calculator
-----------------------------
This object is responsible for generating a dictionary of entry point addresses
from a snapshot. Each key in the dictionary is an entry point address, and the
associated value is a collection of addresses of routines that jump to or call
that entry point. The snapshot reference calculator must supply the following
API function, in common with skoolkit.snaskool:

.. automodule:: skoolkit.snaskool
   :members: calculate_references

Each memory map entry has the following attributes:

* *ctl* - the entry's control directive ('b', 'c', 'g', 'i', 's', 't', 'u' or
  'w')
* *instructions* - a collection of instruction objects

Each instruction object has the following attributes:

* *address* - the address of the instruction
* *bytes* - the byte values of the instruction
* *label* - the instruction's label, as defined by a :ref:`label` directive
* *operation* - the operation (e.g. 'XOR A')
