.. _components:

SkoolKit components
===================

SkoolKit relies on several components in order to function:

* :ref:`assembler`
* :ref:`ctlComposer`
* :ref:`ctlGenerator`
* :ref:`disassembler`
* :ref:`htmlTemplateFormatter`
* :ref:`imageWriter`
* :ref:`instructionUtility`
* :ref:`operandEvaluator`
* :ref:`operandFormatter`
* :ref:`snapshotReader`
* :ref:`snapshotRefCalc`

The objects that are used for these components can be specified in the
:ref:`skoolkit` section of `skoolkit.ini`.

.. _skoolkit:

[skoolkit]
----------
Global configuration for SkoolKit can be specified in the ``[skoolkit]``
section of a file named `skoolkit.ini` either in the current working directory
or in `~/.skoolkit`. The default contents of this section are as follows::

  [skoolkit]
  Assembler=skoolkit.z80.Assembler
  ControlDirectiveComposer=skoolkit.skoolctl.ControlDirectiveComposer
  ControlFileGenerator=skoolkit.snactl
  DefaultDisassemblyStartAddress=16384
  Disassembler=skoolkit.disassembler.Disassembler
  HtmlTemplateFormatter=skoolkit.skoolhtml.TemplateFormatter
  ImageWriter=skoolkit.image.ImageWriter
  InstructionUtility=skoolkit.skoolparser.InstructionUtility
  OperandEvaluator=skoolkit.z80
  OperandFormatter=skoolkit.disassembler.OperandFormatter
  SnapshotReader=skoolkit.snapshot
  SnapshotReferenceCalculator=skoolkit.snaskool
  SnapshotReferenceOperations=DJ,JR,JP,CA,RS

Most of the parameters in the ``[skoolkit]`` section specify the objects to use
for SkoolKit's pluggable components. The other recognised parameters are:

* ``DefaultDisassemblyStartAddress`` - the address at which to start
  disassembling a snapshot when no control file is provided; this is used by
  :ref:`sna2ctl.py` and :ref:`sna2skool.py`, and also by :ref:`snapinfo.py`
  when generating a call graph
* ``SnapshotReferenceOperations`` - the instructions whose address operands are
  used by the :ref:`snapshot reference calculator <snapshotRefCalc>` to
  identify entry points in routines and data blocks

.. _assembler:

Assembler
---------
This object is responsible for converting assembly language instructions and
DEFB/DEFM/DEFS/DEFW statements into byte values, or computing their size. It
must supply the following API functions, in common with skoolkit.z80.Assembler:

.. autoclass:: skoolkit.z80.Assembler
   :members: assemble, get_size

.. _ctlComposer:

Control directive composer
--------------------------
This class is responsible for computing the type, length and sublengths of a
DEFB/DEFM/DEFS/DEFW statement, or the operand bases of a regular instruction,
for the purpose of composing a control directive. It must supply the following
API methods, in common with skoolkit.skoolctl.ControlDirectiveComposer:

.. autoclass:: skoolkit.skoolctl.ControlDirectiveComposer
   :members: compose

If **compose()** encounters an error while parsing an operation and cannot
recover, it should raise a SkoolParsingError:

.. autoclass:: skoolkit.SkoolParsingError

.. _ctlGenerator:

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

If the first element of *sublengths* has a ``size`` value of 0, then the method
should produce a list of statements with default sizes (as determined by
`defb_size`, `defm_size` and `defw_size`), using the specified base.

.. versionchanged:: 8.5
   Added the ability to disassemble an instruction that wraps around the 64K
   boundary, along with the *wrap* attribute on the disassembler configuration
   object to control this behaviour.

.. _htmlTemplateFormatter:

HTML template formatter
-----------------------
This class is responsible for formatting HTML templates. It must supply the
following API methods, in common with skoolkit.skoolhtml.TemplateFormatter:

.. autoclass:: skoolkit.skoolhtml.TemplateFormatter
   :members: format_template

.. _imageWriter:

Image writer
------------
This class is responsible for constructing images and writing them to files. It
must supply the following API methods, in common with
skoolkit.image.ImageWriter:

.. autoclass:: skoolkit.image.ImageWriter
   :members: image_fname, write_image

.. _instructionUtility:

Instruction utility
-------------------
This object is responsible for performing various operations on the
instructions in a skool file:

* converting base and case
* replacing addresses with labels (or other addresses) in instruction operands;
  this is required both for ASM output and for binary output
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

* *address* - the address of the instruction as stated in the skool file; note
  that this will not be the same as the actual address of the instruction if it
  has been moved by the insertion, removal or replacement of other instructions
  by ``@*sub`` or ``@*fix`` directives
* *keep* - `None` if the instruction has no :ref:`keep` directive; an empty
  collection if it has a bare :ref:`keep` directive; or a collection of
  addresses if it has a :ref:`keep` directive with one or more values
* *nowarn* - `None` if the instruction has no :ref:`nowarn` directive; an empty
  collection if it has a bare :ref:`nowarn` directive; or a collection of
  addresses if it has a :ref:`nowarn` directive with one or more values
* *operation* - the operation (e.g. 'XOR A') after any ``@*sub`` or ``@*fix``
  directives have been applied; for an instruction in a remote entry, this is
  an empty string
* *refs* - the addresses of the instruction's indirect referrers, as declared
  by a :ref:`refs` directive
* *rrefs* - the addresses of the instruction's direct referrers to be removed,
  as declared by a :ref:`refs` directive
* *sub* - `True` if the operation was supplied by ``@*sub`` or ``@*fix``
  directive, `False` otherwise

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

.. versionchanged:: 8.2
   Added the *refs* and *rrefs* attributes to instruction objects.

.. versionchanged:: 8.1
   Added the *mode* parameter to the :meth:`substitute_labels` method, and
   changed the required signature of the *warn* function. Added the *nowarn*
   and *sub* attributes to instruction objects.

.. _operandEvaluator:

Operand evaluator
-----------------
This object is used by the :ref:`assembler <assembler>` to evaluate instruction
operands, and by the :ref:`control directive composer <ctlcomposer>` to
determine the length and sublengths of DEFB, DEFM and DEFS statements. It must
supply the following API functions, in common with skoolkit.z80:

.. automodule:: skoolkit.z80
   :members: eval_int, eval_string, split_operands
   :noindex:

.. _operandFormatter:

Operand formatter
-----------------
This class is used by the :ref:`disassembler <disassembler>` to format numeric
instruction operands. It must supply the following API methods, in common with
skoolkit.disassembler.OperandFormatter:

.. autoclass:: skoolkit.disassembler.OperandFormatter
   :members: format_byte, format_word, is_char

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
associated value is a collection of entries that jump to, call or otherwise
refer to that entry point. This dictionary is needed by :ref:`sna2skool.py` for
marking each entry point in a skool file with an asterisk, and listing its
referrers.

The snapshot reference calculator must supply the following API function, in
common with skoolkit.snaskool:

.. automodule:: skoolkit.snaskool
   :members: calculate_references

The value of the *operations* argument is derived from the
``SnapshotReferenceOperations`` parameter in the ``[skoolkit]`` section of
`skoolkit.ini`. In its default form, this parameter is a comma-separated list
of regular expression patterns that designates 'DJNZ', 'JR', 'JP', 'CALL' and
'RST' operations as those whose address operands will be used to identify entry
points in the skool file::

  SnapshotReferenceOperations=DJ,JR,JP,CA,RS

To use a pattern that contains a comma, an alternative (non-alphabetic)
separator can be specified in the first character of the parameter value. For
example::

  SnapshotReferenceOperations=;DJ;JR;JP;CA;RS;LD A,\(\i\);LD \(\i\),A

This would additionally designate the 'LD A,(nn)' and 'LD (nn),A' operations
as identifying entry points. As a convenience for dealing with decimal and
hexadecimal numbers, wherever ``\i`` appears in a pattern, it is replaced by a
pattern that matches a decimal number or a hexadecimal number preceded by
``$``.

Each memory map entry has the following attributes:

* *ctl* - the entry's control directive ('b', 'c', 'g', 'i', 's', 't', 'u' or
  'w')
* *instructions* - a collection of instruction objects

Each instruction object has the following attributes:

* *address* - the address of the instruction
* *bytes* - the byte values of the instruction
* *label* - the instruction's label, as defined by a :ref:`label` directive
* *operation* - the operation (e.g. 'XOR A')
* *refs* - the addresses of the instruction's indirect referrers, as declared
  by a :ref:`refs` directive
* *rrefs* - the addresses of the instruction's direct referrers to be removed,
  as declared by a :ref:`refs` directive

.. versionchanged:: 8.5
   The ``SnapshotReferenceOperations`` parameter defines a list of regular
   expression patterns.

.. versionchanged:: 8.2
   Added the *refs* and *rrefs* attributes to instruction objects.

Component API
-------------
The following functions are provided to facilitate access to the components and
other values declared in the ``[skoolkit]`` section of `skoolkit.ini`.

.. automodule:: skoolkit.components
   :members: get_component, get_value
