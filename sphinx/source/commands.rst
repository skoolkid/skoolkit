.. _commands:

Command reference
=================

.. _bin2tap.py:

bin2tap.py
----------
`bin2tap.py` converts a binary file produced by an assembler (see
:ref:`supportedAssemblers`) into a TAP file that can be loaded into an
emulator. For example::

  $ bin2tap.py game.bin

will create a file called `game.tap`. By default, the origin address (the
address of the first byte of code or data), the start address (the first byte
of code to run) and the stack pointer are set to 65536 minus the length of
`game.bin`. These defaults can be changed by passing options to `bin2tap.py`.
Run it with no arguments to see the list of available options::

  Usage: bin2tap.py [options] FILE.bin

    Convert a binary snapshot file into a TAP file.

  Options:
    -o ORG      Set the origin (default: 65536 - length of FILE.bin)
    -s START    Set the start address to JP to (default: ORG)
    -p STACK    Set the stack pointer (default: ORG)
    -t TAPFILE  Set the TAP filename (default: FILE.tap)

Note that the ROM tape loading routine at 1366 ($0556) and the load routine
used by `bin2tap.py` together require 14 bytes for stack operations, and so
STACK must be at least 16384+14=16398 ($400E). This means that if ORG is less
than 16398, you should use the ``-p`` option to set the stack pointer to
something appropriate. If the main data block (derived from `game.bin`)
overlaps any of the last four bytes of the stack, `bin2tap.py` will replace
those bytes with the values required by the tape loading routine for correct
operation upon returning. Stack operations will overwrite the bytes in the
address range STACK-14 to STACK-1 inclusive, so those addresses should not be
used to store essential code or data.

+---------+-------------------------+
| Version | Changes                 |
+=========+=========================+
| 1.3.1   | New                     |
+---------+-------------------------+
| 2.2.5   | Added the ``-p`` option |
+---------+-------------------------+

.. _skool2asm.py:

skool2asm.py
------------
`skool2asm.py` converts a `skool` file into an ASM file that can be fed to an
assembler (see :ref:`supportedAssemblers`). For example::

  $ skool2asm.py game.skool > game.asm

`skool2asm.py` supports many options; run it with no arguments to see a list::

  Usage: skool2asm.py [options] FILE

    Convert a skool file into an ASM file, written to standard output. FILE may
    be a regular file, or '-' for standard input.

  Options:
    -q    Be quiet
    -w    Suppress warnings
    -d    Use CR+LF to end lines
    -t    Use tab to indent instructions (default indentation is 2 spaces)
    -l    Write disassembly in lower case
    -u    Write disassembly in upper case
    -D    Write disassembly in decimal
    -H    Write disassembly in hexadecimal
    -i N  Set instruction field width to N (default=23)
    -f N  Apply fixes:
            N=0: None (default)
            N=1: @ofix only
            N=2: @ofix and @bfix
            N=3: @ofix, @bfix and @rfix (implies -r)
    -c    Create default labels for unlabelled instructions
    -s    Use safe substitutions (@ssub)
    -r    Use relocatability substitutions too (@rsub) (implies '-f 1')

See :ref:`asmModesAndDirectives` for a description of the ``@ssub`` and
``@rsub`` substitution modes, and the ``@ofix``, ``@bfix`` and ``@rfix`` bugfix
modes.

+---------+--------------------------------------------------------------+
| Version | Changes                                                      |
+=========+==============================================================+
| 1.1     | Added the ``-c`` option                                      |
+---------+--------------------------------------------------------------+
| 2.1.1   | Added the ``-u``, ``-D`` and ``-H`` options                  |
+---------+--------------------------------------------------------------+
| 2.2.2   | Added the ability to read a `skool` file from standard input |
+---------+--------------------------------------------------------------+

.. _skool2ctl.py:

skool2ctl.py
------------
`skool2ctl.py` converts a `skool` file into a
:ref:`control file <controlFiles>`. For example::

  $ skool2ctl.py game.skool > game.ctl

In addition to block types and addresses, `game.ctl` will contain block titles,
block descriptions, registers, mid-block comments, block end comments,
sub-block types and addresses, instruction-level comments, and some
:ref:`ASM directives <asmDirectives>`.

To list the options supported by `skool2ctl.py`, run it with no arguments::

  Usage: skool2ctl.py [options] FILE

    Convert a skool file into a control file, written to standard output. FILE
    may be a regular file, or '-' for standard input.

  Options:
    -w X  Write only these elements, where X is one or more of:
            b = block types and addresses
            t = block titles
            d = block descriptions
            r = registers
            m = mid-block comments and block end comments
            s = sub-block types and addresses
            c = instruction-level comments
    -h    Write addresses in hexadecimal format
    -a    Do not write ASM directives

If you need to preserve any elements that control files do not support (such as
data definition entries and ASM block directives), consider using
:ref:`skool2sft.py` to create a skool file template instead.

+---------+--------------------------------------------------------------+
| Version | Changes                                                      |
+=========+==============================================================+
| 1.1     | New                                                          |
+---------+--------------------------------------------------------------+
| 2.0.6   | Added the ``-h`` option                                      |
+---------+--------------------------------------------------------------+
| 2.2.2   | Added the ability to read a `skool` file from standard input |
+---------+--------------------------------------------------------------+
| 2.4     | Added the ``-a`` option and the ability to preserve some ASM |
|         | directives                                                   |
+---------+--------------------------------------------------------------+

.. _skool2html.py:

skool2html.py
-------------
`skool2html.py` converts a `skool` file (and its associated `ref` files, if any
exist) into a browsable disassembly in HTML format.

For example::

  $ skool2html.py game.skool

will convert the file `game.skool` into a bunch of HTML files. If any files
named `game*.ref` (e.g. `game.ref`, `game-bugs.ref`, `game-pokes.ref` and so
on) also exist, they will be used to provide further information to the
conversion process.

`skool2html.py` can operate directly on `ref` files, too. For example::

  $ skool2html.py game.ref

In this case, the `skool` file declared in the :ref:`ref-Config` section of
`game.ref` will be used; if no `skool` file is declared in `game.ref`,
`game.skool` will be used if it exists. In addition, any existing files besides
`game.ref` that are named `game*.ref` (e.g. `game-bugs.ref`, `game-pokes.ref`
and so on) will also be used.

`skool2html.py` supports several options; run it with no arguments to see a
list::

  Usage: skool2html.py [options] FILE [FILE...]

    Convert skool files and ref files to HTML. FILE may be a regular file, or '-'
    for standard input.

  Options:
    -V        Show SkoolKit version number and exit
    -p        Show path to skoolkit package directory and exit
    -q        Be quiet
    -t        Show timings
    -d DIR    Write files in this directory (default is '.')
    -o        Overwrite existing image files
    -T THEME  Use this CSS theme
    -l        Write disassembly in lower case
    -u        Write disassembly in upper case
    -D        Write disassembly in decimal
    -H        Write disassembly in hexadecimal
    -c S/L    Add the line 'L' to the ref file section 'S'; this option may be
              used multiple times
    -P PAGES  Write only these custom pages (when '-w P' is specified); PAGES
              should be a comma-separated list of IDs of pages defined in [Page:*]
              sections in the ref file(s)
    -w X      Write only these files, where X is one or more of:
                B = Graphic glitches
                b = Bugs
                c = Changelog
                d = Disassembly files
                G = Game status buffer
                g = Graphics
                i = Disassembly index
                m = Memory maps
                o = Other code
                P = Pages defined in the ref file(s)
                p = Pokes
                t = Trivia
                y = Glossary

When `skool2html.py` is run, it looks for `skool` files, `ref` files, CSS
files, JavaScript files and font files required by the disassembly in the
following directories, in the order listed:

* The directory that contains the `skool` or `ref` file named on the command
  line
* The current working directory
* `./resources`
* `~/.skoolkit`
* `/usr/share/skoolkit`
* `$PACKAGE_DIR/resources`

where `$PACKAGE_DIR` is the directory in which the `skoolkit` package is
installed (as shown by ``skool2html.py -p``).

+---------+-----------------------------------------------------------------+
| Version | Changes                                                         |
+=========+=================================================================+
| 1.4     | Added the ``-V`` option                                         |
+---------+-----------------------------------------------------------------+
| 2.1     | Added the ``-o`` and ``-P`` options                             |
+---------+-----------------------------------------------------------------+
| 2.1.1   | Added the ``-l``, ``-u``, ``-D`` and ``-H`` options             |
+---------+-----------------------------------------------------------------+
| 2.2     | No longer writes the Skool Daze and Back to Skool disassemblies |
|         | by default; added the ``-d`` option                             |
+---------+-----------------------------------------------------------------+
| 2.2.2   | Added the ability to read a `skool` file from standard input    |
+---------+-----------------------------------------------------------------+
| 2.3.1   | Added support for reading multiple `ref` files per disassembly  |
+---------+-----------------------------------------------------------------+
| 3.0.2   | No longer shows timings by default; added the ``-t`` option     |
+---------+-----------------------------------------------------------------+
| 3.1     | Added the ``-c`` option                                         |
+---------+-----------------------------------------------------------------+
| 3.2     | Added `~/.skoolkit` to the search path                          |
+---------+-----------------------------------------------------------------+
| 3.3.2   | Added `$PACKAGE_DIR/resources` to the search path; added the    |
|         | ``-p`` and ``-T`` options                                       |
+---------+-----------------------------------------------------------------+ 

.. _skool2sft.py:

skool2sft.py
------------
`skool2sft.py`  converts a `skool` file into a
:ref:`skool file template <skoolFileTemplates>`. For example::

  $ skool2sft.py game.skool > game.sft

To list the options supported by `skool2sft.py`, run it with no arguments::

  Usage: skool2sft.py [options] FILE

    Convert a skool file into a skool file template, written to standard output.
    FILE may be a regular file, or '-' for standard input.

  Options:
    -h  Write addresses in hexadecimal format

+---------+---------+
| Version | Changes |
+=========+=========+
| 2.4     | New     |
+---------+---------+

.. _sna2skool.py:

sna2skool.py
------------
`sna2skool.py` converts a binary (raw memory) file or a SNA, SZX or Z80
snapshot into a `skool` file. For example::

  $ sna2skool.py game.z80 > game.skool

Now `game.skool` can be converted into a browsable HTML disassembly using
:ref:`skool2html.py <skool2html.py>`, or into an assembler-ready ASM file using
:ref:`skool2asm.py <skool2asm.py>`.

`sna2skool.py` supports several options; run it with no arguments to see a
list::

  Usage: sna2skool.py [options] file

    Convert a binary (raw memory) file or a SNA, SZX or Z80 snapshot into a skool
    file.

  Options:
    -c FILE  Use FILE as the control file (default is file.ctl)
    -T FILE  Use FILE as the skool file template (default is file.sft)
    -g FILE  Generate a control file in FILE
    -M FILE  Use FILE as a code execution map when generating the control file
    -h       Write hexadecimal addresses in the generated control file
    -H       Write hexadecimal addresses and operands in the disassembly
    -L       Write the disassembly in lower case
    -s ADDR  Specify the address at which to start disassembling (default=16384)
    -o ADDR  Specify the origin address of file.bin (default: 65536 - length)
    -p PAGE  Specify the page (0-7) of a 128K snapshot to map to 49152-65535
    -t       Show ASCII text in the comment fields
    -r       Don't add comments that list entry point referrers
    -n N     Set the max number of bytes per DEFB statement to N (default=8)
    -m M     Group DEFB blocks by addresses that are divisible by M
    -z       Write bytes with leading zeroes in DEFB statements
    -l L     Set the max number of characters per DEFM statement to L (default=66)

The ``-M`` option may be used (in conjunction with the ``-g`` option) to
specify a code execution map to use when generating a control file. The
supported file formats are:

* Profiles created by the Fuse emulator
* Code execution logs created by the SpecEmu, Spud and Zero emulators
* Map files created by the Z80 emulator

If the file specified by the ``-M`` option is 8192 bytes long, it is assumed to
be a Z80 map file; otherwise it is assumed to be in one of the other supported
formats.

+---------+-----------------------------------------------------------------+
| Version | Changes                                                         |
+=========+=================================================================+
| 1.0.4   | Added the ``-g`` and ``-s`` options                             |
+---------+-----------------------------------------------------------------+
| 1.0.5   | Added the ``-t`` option                                         |
+---------+-----------------------------------------------------------------+
| 2.0     | Added the ``-n``, ``-m`` and ``-z`` options                     |
+---------+-----------------------------------------------------------------+
| 2.0.1   | Added the ``-o``, ``-r`` and ``-l`` options, and the ability to |
|         | read binary files                                               |
+---------+-----------------------------------------------------------------+
| 2.0.6   | Added the ``-h`` option                                         |
+---------+-----------------------------------------------------------------+
| 2.1     | Added the ``-H`` option                                         |
+---------+-----------------------------------------------------------------+
| 2.1.2   | Added the ``-L`` option                                         |
+---------+-----------------------------------------------------------------+
| 2.4     | Added the ``-T`` option                                         |
+---------+-----------------------------------------------------------------+
| 3.2     | Added the ``-p`` option, and the ability to read SZX snapshots  |
|         | and 128K Z80 snapshots                                          |
+---------+-----------------------------------------------------------------+
| 3.3     | Added the ``-M`` option, along with support for code execution  |
|         | maps produced by Fuse, SpecEmu, Spud, Zero and Z80; added the   |
|         | ability to read 128K SNA snapshots                              |
+---------+-----------------------------------------------------------------+
