.. _components:

SkoolKit components
===================

SkoolKit relies on several components in order to function:

* :ref:`assembler`
* :ref:`ctlcomposer`
* :ref:`ctlgenerator`
* :ref:`disassembler`
* :ref:`instructionUtility`
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
  InstructionUtility=skoolkit.skoolparser.InstructionUtility
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
   :members: disassemble, defb_range, defm_range, defs_range, defw_range

The 3-element tuples returned by these methods should have the form
``(address, operation, bytes)``, where:

* ``address`` is the address of the instruction
* ``operation`` is the operation (e.g. 'XOR A', 'DEFB 1')
* ``bytes`` is a sequence of byte values for the instruction (e.g. ``(62, 0)``
  for 'LD A,0')

The *sublengths* argument of the :meth:`defb_range`, :meth:`defm_range`,
:meth:`defs_range` and :meth:`defw_range` methods is a sequence of 2-element
tuples of the form ``(size, base)``, each of which specifies the desired size
(in bytes) and number base for an item in the DEFB/DEFM/DEFS/DEFW statement.
``base`` may have one of the following values:

* 'b' - binary
* 'c' - character
* 'd' - decimal
* 'h' - hexadecimal
* 'm' - negative
* 'n' - default base

If the first element of *sublengths* has a ``size`` value of `None`, then
the method should produce a list of statements with default sizes (as
determined by `defb_size`, `defm_size` and `defw_size`), using the specified
base.

.. _instructionUtility:

Instruction utility
-------------------
This object is responsible for performing various operations on the
instructions in a skool file:

* converting base and case
* replacing addresses with labels in instruction operands; this is required for
  ASM output
* generating a dictionary of references (for each instruction that refers to
  another instruction); this is required for hyperlinking instruction operands
  in HTML output
* generating a dictionary of referrers (for each instruction that is referred
  to by other instructions); this is required by the special ``EREF`` and
  ``REF`` variables of the :ref:`FOREACH` macro
* deciding whether to set byte values; this affects the :ref:`PEEK` macro and
  the :ref:`image macros <imageMacros>`, and instruction byte values in HTML
  output

The object must supply the following API functions, in common with
skoolkit.skoolparser.InstructionUtility:

.. autoclass:: skoolkit.skoolparser.InstructionUtility
   :members: calculate_references, convert, set_byte_values, substitute_labels

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

Each key in the references dictionary should be an instruction object, and the
corresponding value should be a 3-element tuple::

  (ref_instruction, address_s, use_label)

* ``ref_instruction`` - the instruction referred to
* ``address_s`` - the address string in the operand of the referring
  instruction (to be replaced by a hyperlink in HTML output)
* ``use_label`` - whether to use a label as the link text for the hyperlink in
  HTML output; if no label for ``ref_instruction`` is defined, or ``use_label``
  is `False`, the address string (``address_s``) will be used as the link text

Each key in the referrers dictionary should be an instruction object, and the
corresponding value should be a collection of the entries that refer to that
instruction.

.. _snapshotReader:

Snapshot reader
---------------
This object is responsible for producing a 65536-element list of byte values
from a snapshot file. It must supply the following API functions, in common
with skoolkit.snapshot:

.. automodule:: skoolkit.snapshot
   :members: can_read, get_snapshot

If **get_snapshot()** encounters an error while reading a snapshot file, it
should raise a SnapshotError:

.. autoclass:: skoolkit.snapshot.SnapshotError

.. _snapshotRefCalc:

Snapshot reference calculator
-----------------------------
This object is responsible for generating a dictionary of entry point addresses
from a snapshot. Each key in the dictionary is an entry point address, and the
associated value is a collection of entries that jump to or call that entry
point. This dictionary is needed for listing entry point referrers in a skool
file (when the ``ListRefs`` configuration parameter of
:ref:`sna2skool.py <sna2skool-conf>` is 1 or 2).

The snapshot reference calculator must supply the following API function, in
common with skoolkit.snaskool:

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
