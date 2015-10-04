.. _commands:

Commands
========

.. _bin2tap.py:

bin2tap.py
----------
`bin2tap.py` converts a binary (raw memory) file or a SNA, SZX or Z80 snapshot
into a TAP file. For example::

  $ bin2tap.py game.bin

will create a file called `game.tap`. By default, the origin address (the
address of the first byte of code or data), the start address (the first byte
of code to run) and the stack pointer are set to 65536 minus the length of
`game.bin`. These values can be changed by passing options to `bin2tap.py`. Run
it with no arguments to see the list of available options::

  usage: bin2tap.py [options] FILE

  Convert a binary (raw memory) file or a SNA, SZX or Z80 snapshot into a TAP
  file.

  Options:
    -c N, --clear N       Use a 'CLEAR N' command in the BASIC loader and leave
                          the stack pointer alone
    -e ADDR, --end ADDR   Set the end address when reading a snapshot
    -o ORG, --org ORG     Set the origin address (default: 16384 for a snapshot,
                          otherwise 65536 minus the length of FILE)
    -p STACK, --stack STACK
                          Set the stack pointer (default: ORG)
    -s START, --start START
                          Set the start address to JP to (default: ORG)
    -t TAPFILE, --tapfile TAPFILE
                          Set the TAP filename
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

If the input file contains a program that returns to BASIC, you should use the
``--clear`` option to add a CLEAR command to the BASIC loader. This option
leaves the stack pointer alone, enabling the program to return to BASIC without
crashing. The lowest usable address with the ``--clear`` option on a bare 48K
Spectrum is 23952 ($5D90).

+---------+-----------------------------------------------------------------+
| Version | Changes                                                         |
+=========+=================================================================+
| 4.5     | Added the ``--clear`` and ``--end`` options, and the ability to |
|         | convert SNA, SZX and Z80 snapshots                              |
+---------+-----------------------------------------------------------------+
| 3.4     | Added the ``-V`` option and the long options                    |
+---------+-----------------------------------------------------------------+
| 2.2.5   | Added the ``-p`` option                                         |
+---------+-----------------------------------------------------------------+
| 1.3.1   | New                                                             |
+---------+-----------------------------------------------------------------+

.. _skool2asm.py:

skool2asm.py
------------
`skool2asm.py` converts a `skool` file into an ASM file that can be fed to an
assembler (see :ref:`supportedAssemblers`). For example::

  $ skool2asm.py game.skool > game.asm

`skool2asm.py` supports many options; run it with no arguments to see a list::

  usage: skool2asm.py [options] FILE

  Convert a skool file into an ASM file and write it to standard output. FILE may
  be a regular file, or '-' for standard input.

  Options:
    -c, --create-labels   Create default labels for unlabelled instructions
    -D, --decimal         Write the disassembly in decimal
    -E ADDR, --end ADDR   Stop converting at this address
    -f N, --fixes N       Apply fixes:
                            N=0: None (default)
                            N=1: @ofix only
                            N=2: @ofix and @bfix
                            N=3: @ofix, @bfix and @rfix (implies -r)
    -H, --hex             Write the disassembly in hexadecimal
    -l, --lower           Write the disassembly in lower case
    -p, --package-dir     Show path to skoolkit package directory and exit
    -P p=v, --set p=v     Set the value of ASM writer property 'p' to 'v'; this
                          option may be used multiple times
    -q, --quiet           Be quiet
    -r, --rsub            Apply safe substitutions (@ssub) and relocatability
                          substitutions (@rsub) (implies '-f 1')
    -s, --ssub            Apply safe substitutions (@ssub)
    -S ADDR, --start ADDR
                          Start converting at this address
    -u, --upper           Write the disassembly in upper case
    -V, --version         Show SkoolKit version number and exit
    -w, --no-warnings     Suppress warnings
    -W CLASS, --writer CLASS
                          Specify the ASM writer class to use

See :ref:`asmModesAndDirectives` for a description of the ``@ssub`` and
``@rsub`` substitution modes, and the ``@ofix``, ``@bfix`` and ``@rfix`` bugfix
modes.

See the :ref:`set` directive for information on the ASM writer properties that
can be set by the ``--set`` option.

+---------+--------------------------------------------------------------+
| Version | Changes                                                      |
+=========+==============================================================+
| 5.0     | Added the ``--set`` option                                   |
+---------+--------------------------------------------------------------+
| 4.5     | Added the ``--start`` and ``--end`` options                  |
+---------+--------------------------------------------------------------+
| 4.1     | Added the ``--writer`` option                                |
+---------+--------------------------------------------------------------+
| 3.4     | Added the ``-V`` and ``-p`` options and the long options     |
+---------+--------------------------------------------------------------+
| 2.2.2   | Added the ability to read a `skool` file from standard input |
+---------+--------------------------------------------------------------+
| 2.1.1   | Added the ``-u``, ``-D`` and ``-H`` options                  |
+---------+--------------------------------------------------------------+
| 1.1     | Added the ``-c`` option                                      |
+---------+--------------------------------------------------------------+

.. _skool2bin.py:

skool2bin.py
------------
`skool2bin.py` converts a `skool` file into a binary (raw memory) file. For
example::

  $ skool2bin.py game.skool

To list the options supported by `skool2bin.py`, run it with no arguments::

  usage: skool2bin.py [options] file.skool [file.bin]

  Convert a skool file into a binary (raw memory) file. 'file.skool' may be a
  regular file, or '-' for standard input. If 'file.bin' is not given, it
  defaults to the name of the input file with '.skool' replaced by '.bin'.

  Options:
    -E ADDR, --end ADDR   Stop converting at this address
    -i, --isub            Apply instruction substitutions (@isub)
    -S ADDR, --start ADDR
                          Start converting at this address
    -V, --version         Show SkoolKit version number and exit

+---------+---------+
| Version | Changes |
+=========+=========+
| 5.0     | New     |
+---------+---------+

.. _skool2ctl.py:

skool2ctl.py
------------
`skool2ctl.py` converts a `skool` file into a
:ref:`control file <controlFiles>`. For example::

  $ skool2ctl.py game.skool > game.ctl

In addition to block types and addresses, `game.ctl` will contain block titles,
block descriptions, registers, mid-block comments, block start and end
comments, sub-block types and addresses, instruction-level comments, and some
:ref:`ASM directives <asmDirectives>`.

To list the options supported by `skool2ctl.py`, run it with no arguments::

  usage: skool2ctl.py [options] FILE

  Convert a skool file into a control file and write it to standard output. FILE
  may be a regular file, or '-' for standard input.

  Options:
    -a, --no-asm-dirs     Do not write ASM directives
    -b, --preserve-base   Preserve the base of decimal and hexadecimal values in
                          instruction operands and DEFB/DEFM/DEFS/DEFW statements
    -E ADDR, --end ADDR   Stop converting at this address
    -h, --hex             Write addresses in upper case hexadecimal format
    -l, --hex-lower       Write addresses in lower case hexadecimal format
    -S ADDR, --start ADDR
                          Start converting at this address
    -V, --version         Show SkoolKit version number and exit
    -w X, --write X       Write only these elements, where X is one or more of:
                            b = block types and addresses
                            t = block titles
                            d = block descriptions
                            r = registers
                            m = mid-block comments and block start/end comments
                            s = sub-block types and addresses
                            c = instruction-level comments

If you need to preserve any elements that control files do not support (such as
data definition entries and ASM block directives), consider using
:ref:`skool2sft.py` to create a skool file template instead.

+---------+--------------------------------------------------------------+
| Version | Changes                                                      |
+=========+==============================================================+
| 4.5     | Added the ``--start`` and ``--end`` options                  |
+---------+--------------------------------------------------------------+
| 4.4     | Added the ``--hex-lower`` option                             |
+---------+--------------------------------------------------------------+
| 3.7     | Added the ``--preserve-base`` option                         |
+---------+--------------------------------------------------------------+
| 3.4     | Added the ``-V`` option and the long options                 |
+---------+--------------------------------------------------------------+
| 2.4     | Added the ``-a`` option and the ability to preserve some ASM |
|         | directives                                                   |
+---------+--------------------------------------------------------------+
| 2.2.2   | Added the ability to read a `skool` file from standard input |
+---------+--------------------------------------------------------------+
| 2.0.6   | Added the ``-h`` option                                      |
+---------+--------------------------------------------------------------+
| 1.1     | New                                                          |
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

In this case, the `skool` file declared in the :ref:`ref-Config` section will
be used; if no `skool` file is declared, `game.skool` will be used if it
exists. In addition, any existing files besides `game.ref` that are named
`game*.ref` (e.g. `game-bugs.ref`, `game-pokes.ref` and so on) will also be
used, along with any extra files named in the ``RefFiles`` parameter in the
:ref:`ref-Config` section.

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
    -j NAME, --join-css NAME
                          Concatenate CSS files into a single file with this name
    -l, --lower           Write the disassembly in lower case
    -o, --rebuild-images  Overwrite existing image files
    -p, --package-dir     Show path to skoolkit package directory and exit
    -P PAGES, --pages PAGES
                          Write only these custom pages (when using '--write P');
                          PAGES is a comma-separated list of page IDs
    -q, --quiet           Be quiet
    -r PREFIX, --ref-sections PREFIX
                          Show default ref file sections whose names start with
                          PREFIX and exit
    -R, --ref-file        Show the entire default ref file and exit
    -s, --search-dirs     Show the locations skool2html.py searches for resources
    -S DIR, --search DIR  Add this directory to the resource search path; this
                          option may be used multiple times
    -t, --time            Show timings
    -T THEME, --theme THEME
                          Use this CSS theme; this option may be used multiple
                          times
    -u, --upper           Write the disassembly in upper case
    -V, --version         Show SkoolKit version number and exit
    -w X, --write X       Write only these files, where X is one or more of:
                            B = Graphic glitches    o = Other code
                            b = Bugs                P = Custom pages
                            c = Changelog           p = Pokes
                            d = Disassembly files   t = Trivia
                            i = Disassembly index   y = Glossary
                            m = Memory maps
    -W CLASS, --writer CLASS
                          Specify the HTML writer class to use; shorthand for
                          '--config Config/HtmlWriterClass=CLASS'

`skool2html.py` searches the following directories for `skool` files, `ref`
files, CSS files, JavaScript files, font files, and files listed in the
:ref:`resources` section of the `ref` file:

* The directory that contains the `skool` or `ref` file named on the command
  line
* The current working directory
* `./resources`
* `~/.skoolkit`
* `$PACKAGE_DIR/resources`
* Any other directories specified by the ``-S``/``--search`` option

where `$PACKAGE_DIR` is the directory in which the `skoolkit` package is
installed (as shown by ``skool2html.py -p``). When you need a reminder of these
locations, run ``skool2html.py -s``.

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
* `dark.css`
* `wide.css`

+---------+------------------------------------------------------------------+
| Version | Changes                                                          |
+=========+==================================================================+
| 5.0     | The ``--theme`` option also looks for a CSS file whose base name |
|         | matches the theme name                                           |
+---------+------------------------------------------------------------------+
| 4.1     | Added the ``--search`` and ``--writer`` options                  |
+---------+------------------------------------------------------------------+
| 4.0     | Added the ``--ref-sections`` and ``--ref-file`` options          |
+---------+------------------------------------------------------------------+
| 3.6     | Added the ``--join-css`` and ``--search-dirs`` options           |
+---------+------------------------------------------------------------------+
| 3.5     | Added support for multiple CSS themes                            |
+---------+------------------------------------------------------------------+
| 3.4     | Added the ``-a`` and ``-C`` options and the long options         |
+---------+------------------------------------------------------------------+
| 3.3.2   | Added `$PACKAGE_DIR/resources` to the search path; added the     |
|         | ``-p`` and ``-T`` options                                        |
+---------+------------------------------------------------------------------+
| 3.2     | Added `~/.skoolkit` to the search path                           |
+---------+------------------------------------------------------------------+
| 3.1     | Added the ``-c`` option                                          |
+---------+------------------------------------------------------------------+
| 3.0.2   | No longer shows timings by default; added the ``-t`` option      |
+---------+------------------------------------------------------------------+
| 2.3.1   | Added support for reading multiple `ref` files per disassembly   |
+---------+------------------------------------------------------------------+
| 2.2.2   | Added the ability to read a `skool` file from standard input     |
+---------+------------------------------------------------------------------+
| 2.2     | No longer writes the Skool Daze and Back to Skool disassemblies  |
|         | by default; added the ``-d`` option                              |
+---------+------------------------------------------------------------------+
| 2.1.1   | Added the ``-l``, ``-u``, ``-D`` and ``-H`` options              |
+---------+------------------------------------------------------------------+
| 2.1     | Added the ``-o`` and ``-P`` options                              |
+---------+------------------------------------------------------------------+
| 1.4     | Added the ``-V`` option                                          |
+---------+------------------------------------------------------------------+

.. _skool2sft.py:

skool2sft.py
------------
`skool2sft.py`  converts a `skool` file into a
:ref:`skool file template <skoolFileTemplates>`. For example::

  $ skool2sft.py game.skool > game.sft

To list the options supported by `skool2sft.py`, run it with no arguments::

  usage: skool2sft.py [options] FILE

  Convert a skool file into a skool file template and write it to standard
  output. FILE may be a regular file, or '-' for standard input.

  Options:
    -b, --preserve-base   Preserve the base of decimal and hexadecimal values in
                          instruction operands and DEFB/DEFM/DEFS/DEFW
                          statements
    -E ADDR, --end ADDR   Stop converting at this address
    -h, --hex             Write addresses in upper case hexadecimal format
    -l, --hex-lower       Write addresses in lower case hexadecimal format
    -S ADDR, --start ADDR
                          Start converting at this address
    -V, --version         Show SkoolKit version number and exit

+---------+----------------------------------------------+
| Version | Changes                                      |
+=========+==============================================+
| 4.5     | Added the ``--start`` and ``--end`` options  |
+---------+----------------------------------------------+
| 4.4     | Added the ``--hex-lower`` option             |
+---------+----------------------------------------------+
| 3.7     | Added the ``--preserve-base`` option         |
+---------+----------------------------------------------+
| 3.4     | Added the ``-V`` option and the long options |
+---------+----------------------------------------------+
| 2.4     | New                                          |
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
    -e ADDR, --end ADDR   Stop disassembling at this address (default=65536)
    -g FILE, --generate-ctl FILE
                          Generate a control file in FILE
    -h, --ctl-hex         Write upper case hexadecimal addresses in the
                          generated control file
    -H, --skool-hex       Write hexadecimal addresses and operands in the
                          disassembly
    -i, --ctl-hex-lower   Write lower case hexadecimal addresses in the
                          generated control file
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
                          Start disassembling at this address (default=16384)
    -t, --text            Show ASCII text in the comment fields
    -T FILE, --sft FILE   Use FILE as the skool file template
    -V, --version         Show SkoolKit version number and exit
    -w W, --line-width W  Set the maximum line width of the skool file (default:
                          79)
    -z, --defb-zfill      Pad decimal values in DEFB statements with leading
                          zeroes

If the input filename does not end with '.sna', '.szx' or '.z80', it is assumed
to be a binary file.

By default, any :ref:`control file <controlFiles>` or
:ref:`skool file template <skoolFileTemplates>` whose name (minus the '.ctl' or
'.sft' suffix) matches the input filename (minus the '.bin', '.sna', '.szx' or
'.z80' suffix, if any) will be used, if present.

The ``-M`` option may be used (in conjunction with the ``-g`` option) to
specify a code execution map to use when generating a control file. The
supported file formats are:

* Profiles created by the Fuse emulator
* Code execution logs created by the SpecEmu, Spud and Zero emulators
* Map files created by the SpecEmu and Z80 emulators

If the file specified by the ``-M`` option is 8192 bytes long, it is assumed to
be a Z80 map file; if it is 65536 bytes long, it is assumed to be a SpecEmu map
file; otherwise it is assumed to be in one of the other supported formats.

+---------+-----------------------------------------------------------------+
| Version | Changes                                                         |
+=========+=================================================================+
| 5.0     | Added support for SpecEmu's 64K code execution map files        |
+---------+-----------------------------------------------------------------+
| 4.4     | Added the ``--ctl-hex-lower`` and ``--end`` options             |
+---------+-----------------------------------------------------------------+
| 4.3     | Added the ``--line-width`` option                               |
+---------+-----------------------------------------------------------------+
| 3.4     | Added the ``-V`` and ``-R`` options and the long options        |
+---------+-----------------------------------------------------------------+
| 3.3     | Added the ``-M`` option, along with support for code execution  |
|         | maps produced by Fuse, SpecEmu, Spud, Zero and Z80; added the   |
|         | ability to read 128K SNA snapshots                              |
+---------+-----------------------------------------------------------------+
| 3.2     | Added the ``-p`` option, and the ability to read SZX snapshots  |
|         | and 128K Z80 snapshots                                          |
+---------+-----------------------------------------------------------------+
| 2.4     | Added the ``-T`` option                                         |
+---------+-----------------------------------------------------------------+
| 2.1.2   | Added the ``-L`` option                                         |
+---------+-----------------------------------------------------------------+
| 2.1     | Added the ``-H`` option                                         |
+---------+-----------------------------------------------------------------+
| 2.0.6   | Added the ``-h`` option                                         |
+---------+-----------------------------------------------------------------+
| 2.0.1   | Added the ``-o``, ``-r`` and ``-l`` options, and the ability to |
|         | read binary files                                               |
+---------+-----------------------------------------------------------------+
| 2.0     | Added the ``-n``, ``-m`` and ``-z`` options                     |
+---------+-----------------------------------------------------------------+
| 1.0.5   | Added the ``-t`` option                                         |
+---------+-----------------------------------------------------------------+
| 1.0.4   | Added the ``-g`` and ``-s`` options                             |
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

Note that support for TZX files is limited to block types 0x10 (standard speed
data), 0x11 (turbo speed data) and 0x14 (pure data).

By default, `tap2sna.py` loads bytes from every data block on the tape, using
the start address given in the corresponding header. For tapes that contain
headerless data blocks, headers with incorrect start addresses, or irrelevant
blocks, the ``--ram`` option can be used to load bytes from specific blocks at
the appropriate addresses. For example::

  $ tap2sna.py --ram load=3,30000 game.tzx game.z80

loads the third block on the tape at address 30000, and ignores all other
blocks. (To see information on the blocks in a TAP or TZX file, use the
:ref:`tapinfo.py` command.) The ``--ram`` option can also be used to move
blocks of bytes from one location to another, POKE values into individual
addresses or address ranges, and modify memory with XOR and ADD operations
before the snapshot is saved. For more information on the operations that the
``--ram`` option can perform, run::

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

+---------+----------------------------------------------------------------+
| Version | Changes                                                        |
+=========+================================================================+
| 4.5     | Added support for TZX block type 0x14 (pure data), for loading |
|         | the first and last bytes of a tape block, and for modifying    |
|         | memory with XOR and ADD operations                             |
+---------+----------------------------------------------------------------+
| 3.5     | New                                                            |
+---------+----------------------------------------------------------------+

.. _tapinfo.py:

tapinfo.py
----------
`tapinfo.py` shows information on the blocks in a TAP or TZX file. For
example::

  $ tapinfo.py game.tzx

To list the options supported by `tapinfo.py`, run it with no arguments::

  usage: tapinfo.py FILE

  Show the blocks in a TAP or TZX file.

  Options:
    -b IDs, --tzx-blocks IDs
                          Show TZX blocks with these IDs only; 'IDs' is a comma-
                          separated list of hexadecimal block IDs, e.g. 10,11,2a
    -V, --version         Show SkoolKit version number and exit

+---------+---------+
| Version | Changes |
+=========+=========+
| 5.0     | New     |
+---------+---------+
