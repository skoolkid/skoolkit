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

  usage: bin2tap.py [options] FILE.bin

  Convert a binary snapshot file into a TAP file.

  Options:
    -o ORG, --org ORG     Set the origin address (default: 65536 minus the
                          length of FILE.bin)
    -p STACK, --stack STACK
                          Set the stack pointer (default: ORG)
    -s START, --start START
                          Set the start address to JP to (default: ORG)
    -t TAPFILE, --tapfile TAPFILE
                          Set the TAP filename (default: FILE.tap)
    -V, --version         Show SkoolKit version number and exit

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

+---------+----------------------------------------------+
| Version | Changes                                      |
+=========+==============================================+
| 1.3.1   | New                                          |
+---------+----------------------------------------------+
| 2.2.5   | Added the ``-p`` option                      |
+---------+----------------------------------------------+
| 3.4     | Added the ``-V`` option and the long options |
+---------+----------------------------------------------+

.. _skool2asm.py:

skool2asm.py
------------
`skool2asm.py` converts a `skool` file into an ASM file that can be fed to an
assembler (see :ref:`supportedAssemblers`). For example::

  $ skool2asm.py game.skool > game.asm

`skool2asm.py` supports many options; run it with no arguments to see a list::

  usage: skool2asm.py [options] file

  Convert a skool file into an ASM file, written to standard output. FILE may be
  a regular file, or '-' for standard input.

  Options:
    -c, --create-labels   Create default labels for unlabelled instructions
    -d, --crlf            Use CR+LF to end lines
    -D, --decimal         Write the disassembly in decimal
    -f N, --fixes N       Apply fixes:
                            N=0: None (default)
                            N=1: @ofix only
                            N=2: @ofix and @bfix
                            N=3: @ofix, @bfix and @rfix (implies -r)
    -H, --hex             Write the disassembly in hexadecimal
    -i N, --inst-width N  Set instruction field width (default=23)
    -l, --lower           Write the disassembly in lower case
    -p, --package-dir     Show path to skoolkit package directory and exit
    -q, --quiet           Be quiet
    -r, --rsub            Use relocatability substitutions too (@rsub) (implies
                          '-f 1')
    -s, --ssub            Use safe substitutions (@ssub)
    -t, --tabs            Use tab to indent instructions (default indentation is
                          2 spaces)
    -u, --upper           Write the disassembly in upper case
    -V, --version         Show SkoolKit version number and exit
    -w, --no-warnings     Suppress warnings

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
| 3.4     | Added the ``-V`` and ``-p`` options and the long options     |
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

  usage: skool2ctl.py [options] FILE

  Convert a skool file into a control file, written to standard output. FILE may
  be a regular file, or '-' for standard input.

  Options:
    -a, --no-asm-dirs  Do not write ASM directives
    -h, --hex          Write addresses in hexadecimal format
    -V, --version      Show SkoolKit version number and exit
    -w X, --write X    Write only these elements, where X is one or more of:
                         b = block types and addresses
                         t = block titles
                         d = block descriptions
                         r = registers
                         m = mid-block comments and block end comments
                         s = sub-block types and addresses
                         c = instruction-level comments

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
| 3.4     | Added the ``-V`` option and the long options                 |
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

If an input file's name ends with '.ref', it will be treated as a `ref` file;
otherwise it will be treated as a `skool` file.

`skool2html.py` supports several options; run it with no arguments to see a
list::

  usage: skool2html.py [options] FILE [FILE...]

  Convert skool files and ref files to HTML. FILE may be a regular file, or '-'
  for standard input.

  Options:
    -a, --asm-labels      Use ASM labels
    -c S/L, --config S/L  Add the line 'L' to the ref file section 'S'; this
                          option may be used multiple times
    -C, --create-labels   Create default labels for unlabelled instructions
    -d DIR, --output-dir DIR
                          Write files in this directory (default is '.')
    -D, --decimal         Write the disassembly in decimal
    -H, --hex             Write the disassembly in hexadecimal
    -l, --lower           Write the disassembly in lower case
    -o, --rebuild-images  Overwrite existing image files
    -p, --package-dir     Show path to skoolkit package directory and exit
    -P PAGES, --pages PAGES
                          Write only these custom pages (when '-w P' is
                          specified); PAGES should be a comma-separated list of
                          IDs of pages defined in [Page:*] sections in the ref
                          file(s)
    -q, --quiet           Be quiet
    -t, --time            Show timings
    -T THEME, --theme THEME
                          Use this CSS theme; this option may be used multiple
                          times
    -u, --upper           Write the disassembly in upper case
    -V, --version         Show SkoolKit version number and exit
    -w X, --write X       Write only these files, where X is one or more of:
                            B = Graphic glitches    m = Memory maps
                            b = Bugs                o = Other code
                            c = Changelog           P = Custom pages
                            d = Disassembly files   p = Pokes
                            G = Game status buffer  t = Trivia
                            g = Graphics            y = Glossary
                            i = Disassembly index

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

The ``-T`` option sets the CSS theme. For example, if `game.ref` specifies the
CSS files to use thus::

  [Game]
  StyleSheet=skoolkit.css;game.css

then::

  $ skool2html.py -T dark -T wide game.ref

will use the following CSS files, if they exist, in the order listed:

* `skoolkit.css`
* `skoolkit-dark.css`
* `skoolkit-wide.css`
* `game.css`
* `game-dark.css`
* `game-wide.css`

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
| 3.4     | Added the ``-a`` and ``-C`` options and the long options        |
+---------+-----------------------------------------------------------------+
| 3.5     | Added support for multiple CSS themes                           |
+---------+-----------------------------------------------------------------+

.. _skool2sft.py:

skool2sft.py
------------
`skool2sft.py`  converts a `skool` file into a
:ref:`skool file template <skoolFileTemplates>`. For example::

  $ skool2sft.py game.skool > game.sft

To list the options supported by `skool2sft.py`, run it with no arguments::

  usage: skool2sft.py [options] FILE

  Convert a skool file into a skool file template, written to standard output.
  FILE may be a regular file, or '-' for standard input.

  Options:
    -h, --hex      Write addresses in hexadecimal format
    -V, --version  Show SkoolKit version number and exit

+---------+----------------------------------------------+
| Version | Changes                                      |
+=========+==============================================+
| 2.4     | New                                          |
+---------+----------------------------------------------+
| 3.4     | Added the ``-V`` option and the long options |
+---------+----------------------------------------------+

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

  usage: sna2skool.py [options] file

  Convert a binary (raw memory) file or a SNA, SZX or Z80 snapshot into a skool
  file.

  Options:
    -c FILE, --ctl FILE   Use FILE as the control file
    -g FILE, --generate-ctl FILE
                          Generate a control file in FILE
    -h, --ctl-hex         Write hexadecimal addresses in the generated control
                          file
    -H, --skool-hex       Write hexadecimal addresses and operands in the
                          disassembly
    -l L, --defm-size L   Set the maximum number of characters per DEFM
                          statement to L (default=66)
    -L, --lower           Write the disassembly in lower case
    -m M, --defb-mod M    Group DEFB blocks by addresses that are divisible by M
    -M FILE, --map FILE   Use FILE as a code execution map when generating a
                          control file
    -n N, --defb-size N   Set the maximum number of bytes per DEFB statement to
                          N (default=8)
    -o ADDR, --org ADDR   Specify the origin address of a binary (.bin) file
                          (default: 65536 - length)
    -p PAGE, --page PAGE  Specify the page (0-7) of a 128K snapshot to map to
                          49152-65535
    -r, --no-erefs        Don't add comments that list entry point referrers
    -R, --erefs           Always add comments that list entry point referrers
    -s ADDR, --start ADDR
                          Specify the address at which to start disassembling
                          (default=16384)
    -t, --text            Show ASCII text in the comment fields
    -T FILE, --sft FILE   Use FILE as the skool file template
    -V, --version         Show SkoolKit version number and exit
    -z, --defb-zfill      Write bytes with leading zeroes in DEFB statements

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
| 3.4     | Added the ``-V`` and ``-R`` options and the long options        |
+---------+-----------------------------------------------------------------+

.. _tap2sna.py:

tap2sna.py
----------
`tap2sna.py` converts a TAP or TZX file (which may be inside a zip archive)
into a Z80 snapshot. For example::

  $ tap2sna.py game.tap game.z80

To list the options supported by `tap2sna.py`, run it with no arguments::

  usage:
    tap2sna.py [options] INPUT snapshot.z80
    tap2sna.py @FILE

  Convert a TAP or TZX file (which may be inside a zip archive) into a Z80
  snapshot. INPUT may be the full URL to a remote zip archive or TAP/TZX file,
  or the path to a local file. Arguments may be read from FILE instead of (or as
  well as) being given on the command line.

  Options:
    -d DIR, --output-dir DIR
                          Write the snapshot file in this directory.
    -f, --force           Overwrite an existing snapshot.
    --ram OPERATION       Perform a load, move or poke operation on the memory
                          snapshot being built. Do '--ram help' for more
                          information. This option may be used multiple times.
    --reg name=value      Set the value of a register. Do '--reg help' for more
                          information. This option may be used multiple times.
    --state name=value    Set a hardware state attribute. Do '--state help' for
                          more information. This option may be used multiple
                          times.
    -V, --version         Show SkoolKit version number and exit.

Note that support for TZX files is limited to block types 0x10 (Standard Speed
Data Block) and 0x11 (Turbo Speed Data Block).

By default, `tap2sna.py` loads bytes from every data block on the tape, using
the start address given in the corresponding header. For tapes that contain
headerless data blocks, headers with incorrect start addresses, or irrelevant
blocks, the ``--ram`` option can be used to load bytes from specific blocks at
the appropriate addresses. For example::

  $ tap2sna.py --ram load=3,30000 game.tzx game.z80

loads the third block on the tape at address 30000, and ignores all other
blocks. The ``--ram`` option can also be used to move blocks of bytes from one
location to another, and POKE values into individual addresses or address
ranges before the snapshot is saved. For more information on the operations
that the ``--ram`` option can perform, run::

  $ tap2sna.py --ram help

For complex snapshots that require many ``--ram``, ``--reg`` or ``--state``
options to build, it may be more convenient to store the arguments to
`tap2sna.py` in a file. For example, if the file `game.t2s` has the following
contents::

  ;
  ; tap2sna.py file for GAME
  ;
  http://example.com/pub/games/GAME.zip
  game.z80
  --ram load=4,32768         # Load the fourth block at 32768
  --ram move=40960,512,43520 # Move 40960-41471 to 43520-44031
  --reg pc=34816             # Start at 34816
  --reg sp=32768             # Stack at 32768
  --state iff=0              # Disable interrupts

then::

  $ tap2sna.py @game.t2s

will create `game.z80` as if the arguments specified in `game.t2s` had been
given on the command line.

+---------+---------+
| Version | Changes |
+=========+=========+
| 3.5     | New     |
+---------+---------+
