.. _skoolkit1x:

SkoolKit 1.x changelog
======================
1.4 (2010-11-11)
------------------
* Updated the Skool Daze disassembly
* Updated the Back to Skool disassembly
* Updated the incomplete Contact Sam Cruise disassembly

1.3.1 (2010-10-18)
------------------
* Added documentation on :ref:`supported assemblers <supportedAssemblers>`
* Added the `bin2tap.py` utility
* Documentation sources included in `docs-src`
* When running `skool2asm.py` or `skool2html.py` on Linux/BSD, show elapsed
  time instead of CPU time

1.3 (2010-07-23)
----------------
* Updated the Skool Daze disassembly
* Updated the Back to Skool disassembly
* Updated the incomplete Contact Sam Cruise disassembly

1.2 (2010-05-03)
----------------
Updated the Back to Skool disassembly.

1.1 (2010-02-25)
----------------
* Updated the Skool Daze disassembly
* Updated the Back to Skool disassembly
* Updated `contact_sam_cruise.ctl`
* Added `csc.ref` (to supply extra information to the Contact Sam Cruise
  disassembly)
* Added the `skool2ctl.py` utility

1.0.7 (2010-02-12)
------------------
* Extended the control file syntax to support block titles, descriptions,
  registers and comments, and sub-block types and comments
* Added two example control files: `contact_sam_cruise.ctl` and
  `manic_miner.ctl`
* Fixed the bug in `sna2skool.py` that made it list referrers of entry points
  in non-code blocks
* Added support to `sna2skool.py` for the ``LD IXh,r`` and ``LD IXl,r``
  instructions

1.0.6 (2010-02-04)
------------------
Above each entry point in a code block, `sna2skool.py` will insert a comment
containing a list of the routines that call or jump to that entry point.

1.0.5 (2010-02-03)
------------------
Made the following changes to `sna2skool.py`:

* Added the ``-t`` option (to show ASCII text in the comment fields)
* Set block titles according to the apparent contents (code/text/data) when
  using the ``-g`` option

1.0.4 (2010-02-02)
------------------
Made the following changes to `sna2skool.py`:

* Fixed the bug that caused the last instruction before the 64K boundary to be
  disassembled as a ``DEFB`` statement
* Added the ``-g`` option (to generate a control file using rudimentary static
  code analysis)
* Added the ``-s`` option (to specify the disassembly start address)

1.0.3 (2010-02-01)
------------------
* `sna2skool.py` copes with instructions that cross the 64K boundary
* `skool2html.py` writes the 'Game status buffer', 'Glossary', 'Trivia', 'Bugs'
  and 'Pokes' pages for a skool file specified by the ``-f`` option (in
  addition to the disassembly files and memory maps)

1.0.2 (2010-01-31)
------------------
Modified `sna2skool.py` so that it:

* recognises instructions that are unchanged by a DD or FD prefix
* recognises instructions with a DDCB or FDCB prefix
* produces a 4-byte ``DEFB`` for the ED-prefixed ``LD HL,(nn)`` and
  ``LD (nn),HL`` instructions
* produces a 2-byte ``DEFB`` for a relative jump across the 64K boundary

1.0.1 (2010-01-30)
------------------
Fixed the following bugs in `sna2skool.py`:

* 'X' was replaced by 'Y' instead of 'IX' by 'IY' (leading to nonsense
  mnemonics such as ``YOR IYh``)
* ED72 was disassembled as ``SBC HL,BC`` instead of ``SBC HL,SP``
* ED7A was disassembled as ``ADD HL,SP`` instead of ``ADC HL,SP``
* ED63 and ED6B were disassembled as ``LD (nn),HL`` and ``LD HL,(nn)`` (which
  is correct, but won't assemble back to the same bytes)

1.0 (2010-01-28)
----------------
Initial public release.
