.. _commands:

Commands
========

.. _bin2sna.py:

bin2sna.py
----------
`bin2sna.py` converts a binary (raw memory) file into a Z80 snapshot. For
example::

  $ bin2sna.py game.bin

will create a file named `game.z80`. By default, the origin address (the
address of the first byte of code or data), the start address (the first byte
of code to run) and the stack pointer are set to 65536 minus the length of
`game.bin`. These values can be changed by passing options to `bin2sna.py`. Run
it with no arguments to see the list of available options::

  usage: bin2sna.py [options] file.bin [file.z80]

  Convert a binary (raw memory) file into a Z80 snapshot. 'file.bin' may be a
  regular file, or '-' for standard input. If 'file.z80' is not given, it
  defaults to the name of the input file with '.bin' replaced by '.z80', or
  'program.z80' if reading from standard input.

  Options:
    -b BORDER, --border BORDER
                          Set the border colour (default: 7).
    -o ORG, --org ORG     Set the origin address (default: 65536 minus the
                          length of file.bin).
    -p STACK, --stack STACK
                          Set the stack pointer (default: ORG).
    -P a[-b[-c]],[^+]v, --poke a[-b[-c]],[^+]v
                          POKE N,v for N in {a, a+c, a+2c..., b}. Prefix 'v'
                          with '^' to perform an XOR operation, or '+' to
                          perform an ADD operation. This option may be used
                          multiple times.
    -r name=value, --reg name=value
                          Set the value of a register. Do '--reg help' for more
                          information. This option may be used multiple times.
    -s START, --start START
                          Set the address at which to start execution (default:
                          ORG).
    -S name=value, --state name=value
                          Set a hardware state attribute. Do '--state help' for
                          more information. This option may be used multiple
                          times.
    -V, --version         Show SkoolKit version number and exit.

+---------+-------------------------------------------------------------------+
| Version | Changes                                                           |
+=========+===================================================================+
| 8.10    | Added the ``issue2`` hardware state attribute                     |
+---------+-------------------------------------------------------------------+
| 8.9     | Added the ``tstates`` hardware state attribute                    |
+---------+-------------------------------------------------------------------+
| 6.3     | Added the ``--poke`` option                                       |
+---------+-------------------------------------------------------------------+
| 6.2     | Added the ``--reg`` and ``--state`` options; the ``--org``,       |
|         | ``--stack`` and ``--start`` options accept a hexadecimal integer  |
|         | prefixed by '0x'                                                  |
+---------+-------------------------------------------------------------------+
| 5.2     | New                                                               |
+---------+-------------------------------------------------------------------+

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

  usage: bin2tap.py [options] FILE [file.tap]

  Convert a binary (raw memory) file or a SNA, SZX or Z80 snapshot into a TAP
  file. FILE may be a regular file, or '-' to read a binary file from standard
  input.

  Options:
    -b BEGIN, --begin BEGIN
                          Begin conversion at this address (default: ORG for a
                          binary file, 16384 for a snapshot).
    -c N, --clear N       Use a 'CLEAR N' command in the BASIC loader and leave
                          the stack pointer alone.
    -e END, --end END     End conversion at this address.
    -o ORG, --org ORG     Set the origin address for a binary file (default:
                          65536 minus the length of FILE).
    -p STACK, --stack STACK
                          Set the stack pointer (default: BEGIN).
    -s START, --start START
                          Set the start address to JP to (default: BEGIN).
    -S FILE, --screen FILE
                          Add a loading screen to the TAP file. FILE may be a
                          snapshot or a 6912-byte SCR file.
    -V, --version         Show SkoolKit version number and exit.

Note that the ROM tape loading routine at 1366 (0x0556) and the load routine
used by `bin2tap.py` together require 14 bytes for stack operations, and so
STACK must be at least 16384+14=16398 (0x400E). This means that if ORG is less
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
Spectrum is 23952 (0x5D90).

+---------+-------------------------------------------------------------------+
| Version | Changes                                                           |
+=========+===================================================================+
| 8.3     | Added the ``--begin`` option; the ``--end`` option applies to raw |
|         | memory files as well as snapshots                                 |
+---------+-------------------------------------------------------------------+
| 6.2     | The ``--clear``, ``--end``, ``--org``, ``--stack`` and            |
|         | ``--start`` options accept a hexadecimal integer prefixed by '0x' |
+---------+-------------------------------------------------------------------+
| 5.3     | Added the ``--screen`` option                                     |
+---------+-------------------------------------------------------------------+
| 5.2     | Added the ability to read a binary file from standard input;      |
|         | added a second positional argument specifying the TAP filename    |
+---------+-------------------------------------------------------------------+
| 4.5     | Added the ``--clear`` and ``--end`` options, and the ability to   |
|         | convert SNA, SZX and Z80 snapshots                                |
+---------+-------------------------------------------------------------------+
| 3.4     | Added the ``-V`` option and the long options                      |
+---------+-------------------------------------------------------------------+
| 2.2.5   | Added the ``-p`` option                                           |
+---------+-------------------------------------------------------------------+
| 1.3.1   | New                                                               |
+---------+-------------------------------------------------------------------+

.. _skool2asm.py:

skool2asm.py
------------
`skool2asm.py` converts a skool file into an ASM file that can be fed to an
assembler (see :ref:`supportedAssemblers`). For example::

  $ skool2asm.py game.skool > game.asm

`skool2asm.py` supports many options; run it with no arguments to see a list::

  usage: skool2asm.py [options] FILE

  Convert a skool file into an ASM file and write it to standard output. FILE may
  be a regular file, or '-' for standard input.

  Options:
    -c, --create-labels   Create default labels for unlabelled instructions.
    -D, --decimal         Write the disassembly in decimal.
    -E ADDR, --end ADDR   Stop converting at this address.
    -f N, --fixes N       Apply fixes:
                            N=0: None (default)
                            N=1: @ofix only
                            N=2: @ofix and @bfix
                            N=3: @ofix, @bfix and @rfix (implies -r)
    -F, --force           Force conversion, ignoring @start and @end directives.
    -H, --hex             Write the disassembly in hexadecimal.
    -I p=v, --ini p=v     Set the value of the configuration parameter 'p' to
                          'v'. This option may be used multiple times.
    -l, --lower           Write the disassembly in lower case.
    -p, --package-dir     Show path to skoolkit package directory and exit.
    -P p=v, --set p=v     Set the value of ASM writer property 'p' to 'v'. This
                          option may be used multiple times.
    -q, --quiet           Be quiet.
    -r, --rsub            Apply safe substitutions (@ssub) and relocatability
                          substitutions (@rsub) (implies '-f 1').
    --show-config         Show configuration parameter values.
    -s, --ssub            Apply safe substitutions (@ssub).
    -S ADDR, --start ADDR
                          Start converting at this address.
    -u, --upper           Write the disassembly in upper case.
    --var name=value      Define a variable that can be used by @if and the SMPL
                          macros. This option may be used multiple times.
    -V, --version         Show SkoolKit version number and exit.
    -w, --no-warnings     Suppress warnings.
    -W CLASS, --writer CLASS
                          Specify the ASM writer class to use.

See :ref:`asmModesAndDirectives` for a description of the ``@ssub`` and
``@rsub`` substitution modes, and the ``@ofix``, ``@bfix`` and ``@rfix`` bugfix
modes.

See the :ref:`set` directive for information on the ASM writer properties that
can be set by the ``--set`` option.

.. _skool2asm-conf:

Configuration
^^^^^^^^^^^^^
`skool2asm.py` will read configuration from a file named `skoolkit.ini` in the
current working directory or in `~/.skoolkit`, if present. The recognised
configuration parameters are:

* ``Address`` - the format of the default link text for the :ref:`R` macro when
  the target address has no label (default: ''); this format string recognises
  the replacement field ``address``; if the format string is blank, the address
  is formatted exactly as it appears in the skool file (without any ``$``
  prefix)
* ``Base`` - convert addresses and instruction operands to hexadecimal (``16``)
  or decimal (``10``), or leave them as they are (``0``, the default)
* ``Case`` - write the disassembly in lower case (``1``) or upper case (``2``),
  or leave it as it is (``0``, the default)
* ``CreateLabels`` - create default labels for unlabelled instructions (``1``),
  or don't (``0``, the default)
* ``EntryLabel`` - the format of the default label for the first instruction in
  a routine or data block (default: ``L{address}``)
* ``EntryPointLabel`` - the format of the default label for an instruction
  other than the first in a routine or data block (default: ``{main}_{index}``)
* ``Quiet`` - be quiet (``1``) or verbose (``0``, the default)
* ``Set-property`` - set an ASM writer property value, e.g. ``Set-bullet=+``
  (see the :ref:`set` directive for a list of available properties)
* ``Templates`` - file from which to read custom :ref:`asmTemplates`
* ``Warnings`` - show warnings (``1``, the default), or suppress them (``0``)

``EntryLabel`` and ``EntryPointLabel`` are standard Python format strings.
``EntryLabel`` recognises the following replacement fields:

* ``address`` - the address of the routine or data block as it appears in the
  skool file
* ``location`` - the address of the routine or data block as an integer

``EntryPointLabel`` recognises the following replacement fields:

* ``address`` - the address of the instruction as it appears in the skool file
* ``index`` - 0 for the first unlabelled instruction in the routine or data
  block, 1 for the second, etc.
* ``location`` - the address of the instruction as an integer
* ``main`` - the label of the first instruction in the routine or data block

Configuration parameters must appear in a ``[skool2asm]`` section. For example,
to make `skool2asm.py` write the disassembly in hexadecimal with a line width
of 120 characters by default (without having to use the ``-H`` and ``-P``
options on the command line), add the following section to `skoolkit.ini`::

  [skool2asm]
  Base=16
  Set-line-width=120

Configuration parameters may also be set on the command line by using the
``--ini`` option. Parameter values set this way will override any found in
`skoolkit.ini`.

+---------+-------------------------------------------------------------------+
| Version | Changes                                                           |
+=========+===================================================================+
| 8.5     | Added the ``Address``, ``EntryLabel`` and ``EntryPointLabel``     |
|         | configuration parameters                                          |
+---------+-------------------------------------------------------------------+
| 7.2     | Added the ``Templates`` configuration parameter and support for   |
|         | :ref:`asmTemplates`                                               |
+---------+-------------------------------------------------------------------+
| 7.0     | :ref:`nonEntryBlocks` are reproduced verbatim; added the          |
|         | ``--force`` option                                                |
+---------+-------------------------------------------------------------------+
| 6.4     | Added the ``--var`` option                                        |
+---------+-------------------------------------------------------------------+
| 6.2     | Added the ``--show-config`` option; the ``--end`` and ``--start`` |
|         | options accept a hexadecimal integer prefixed by '0x'             |
+---------+-------------------------------------------------------------------+
| 6.1     | Configuration is read from `skoolkit.ini` if present; added the   |
|         | ``--ini`` option                                                  |
+---------+-------------------------------------------------------------------+
| 5.0     | Added the ``--set`` option                                        |
+---------+-------------------------------------------------------------------+
| 4.5     | Added the ``--start`` and ``--end`` options                       |
+---------+-------------------------------------------------------------------+
| 4.1     | Added the ``--writer`` option                                     |
+---------+-------------------------------------------------------------------+
| 3.4     | Added the ``-V`` and ``-p`` options and the long options          |
+---------+-------------------------------------------------------------------+
| 2.2.2   | Added the ability to read a skool file from standard input        |
+---------+-------------------------------------------------------------------+
| 2.1.1   | Added the ``-u``, ``-D`` and ``-H`` options                       |
+---------+-------------------------------------------------------------------+
| 1.1     | Added the ``-c`` option                                           |
+---------+-------------------------------------------------------------------+

.. _skool2bin.py:

skool2bin.py
------------
`skool2bin.py` converts a skool file into a binary (raw memory) file. For
example::

  $ skool2bin.py game.skool

To list the options supported by `skool2bin.py`, run it with no arguments::

  usage: skool2bin.py [options] file.skool [file.bin]

  Convert a skool file into a binary (raw memory) file. 'file.skool' may be a
  regular file, or '-' for standard input. If 'file.bin' is not given, it
  defaults to the name of the input file with '.skool' replaced by '.bin'.
  'file.bin' may be a regular file, or '-' for standard output.

  Options:
    -b, --bfix            Apply @ofix and @bfix directives.
    -d, --data            Process @defb, @defs and @defw directives.
    -E ADDR, --end ADDR   Stop converting at this address.
    -i, --isub            Apply @isub directives.
    -o, --ofix            Apply @ofix directives.
    -r, --rsub            Apply @isub, @ssub and @rsub directives (implies
                          --ofix).
    -R, --rfix            Apply @ofix, @bfix and @rfix directives (implies
                          --rsub).
    -s, --ssub            Apply @isub and @ssub directives.
    -S ADDR, --start ADDR
                          Start converting at this address.
    -v, --verbose         Show info on each converted instruction.
    -V, --version         Show SkoolKit version number and exit.
    -w, --no-warnings     Suppress warnings.

The ``--verbose`` option shows information on each converted instruction, such
as whether it was inserted before or after another instruction (by a ``@*sub``
or ``@*fix`` directive), and its original address (if it was relocated by the
insertion, removal or replacement of other instructions). For example::

  40000 9C40 > XOR A
  40001 9C41 | LD HL,40006   : 40000 9C40 LD HL,40003
  40004 9C44 + JR 40006      :            JR 40003
  40006 9C46   RET           : 40003 9C43 RET

This output shows that:

* The instruction at 40000 (XOR A) was inserted before (``>``) another
  instruction
* The instruction at 40001 (LD HL,40006) overwrote (``|``) the instruction(s)
  originally at 40000, and had its operand changed from 40003 (because the
  instruction originally at that address was relocated to 40006)
* The instruction at 40004 (JR 40006) was inserted after (``+``) another
  instruction, and also had its operand changed from 40003
* The instruction at 40006 (RET) was originally at 40003 (before other
  instructions were inserted, removed or replaced)

+---------+-------------------------------------------------------------------+
| Version | Changes                                                           |
+=========+===================================================================+
| 8.1     | Added the ``--data``, ``--rsub``, ``--rfix``, ``--verbose`` and   |
|         | ``--no-warnings`` options                                         |
+---------+-------------------------------------------------------------------+
| 7.0     | :ref:`asm-if` directives are processed                            |
+---------+-------------------------------------------------------------------+
| 6.2     | The ``--end`` and ``--start`` options accept a hexadecimal        |
|         | integer prefixed by '0x'                                          |
+---------+-------------------------------------------------------------------+
| 6.1     | Added the ability to assemble instructions whose operands contain |
|         | arithmetic expressions                                            |
+---------+-------------------------------------------------------------------+
| 5.2     | Added the ability to write the binary file to standard output     |
+---------+-------------------------------------------------------------------+
| 5.1     | Added the ``--bfix``, ``--ofix`` and ``--ssub`` options           |
+---------+-------------------------------------------------------------------+
| 5.0     | New                                                               |
+---------+-------------------------------------------------------------------+

.. _skool2ctl.py:

skool2ctl.py
------------
`skool2ctl.py` converts a skool file into a :ref:`control file <controlFiles>`.
For example::

  $ skool2ctl.py game.skool > game.ctl

In addition to block types and addresses, `game.ctl` will contain block titles,
block descriptions, registers, mid-block comments, block start and end
comments, sub-block types and addresses, instruction-level comments, non-entry
blocks, and some :ref:`ASM directives <asmDirectives>`.

To list the options supported by `skool2ctl.py`, run it with no arguments::

  usage: skool2ctl.py [options] FILE

  Convert a skool file into a control file and write it to standard output. FILE
  may be a regular file, or '-' for standard input.

  Options:
    -b, --preserve-base   Preserve the base of decimal and hexadecimal values in
                          instruction operands and DEFB/DEFM/DEFS/DEFW statements.
    -E ADDR, --end ADDR   Stop converting at this address.
    -h, --hex             Write addresses in upper case hexadecimal format.
    -I p=v, --ini p=v     Set the value of the configuration parameter 'p' to
                          'v'. This option may be used multiple times.
    -k, --keep-lines      Preserve line breaks in comments.
    -l, --hex-lower       Write addresses in lower case hexadecimal format.
    --show-config         Show configuration parameter values.
    -S ADDR, --start ADDR
                          Start converting at this address.
    -V, --version         Show SkoolKit version number and exit.
    -w X, --write X       Write only these elements, where X is one or more of:
                            a = ASM directives
                            b = block types and addresses
                            t = block titles
                            d = block descriptions
                            r = registers
                            m = mid-block comments and block start/end comments
                            s = sub-block types and addresses
                            c = instruction-level comments
                            n = non-entry blocks

.. _skool2ctl-conf:

Configuration
^^^^^^^^^^^^^
`skool2ctl.py` will read configuration from a file named `skoolkit.ini` in the
current working directory or in `~/.skoolkit`, if present. The recognised
configuration parameters are:

* ``Hex`` - write addresses in decimal (``0``, the default), lower case
  hexadecimal (``1``),  or upper case hexadecimal (``2``)
* ``KeepLines`` - preserve line breaks in comments (``1``), or don't (``0``,
  the default)
* ``PreserveBase`` - preserve the base of decimal and hexadecimal values in
  instruction operands and DEFB/DEFM/DEFS/DEFW statements (``1``), or don't
  (``0``, the default)

Configuration parameters must appear in a ``[skool2ctl]`` section. For
example, to make `skool2ctl.py` write upper case hexadecimal addresses by
default (without having to use the ``-h`` option on the command line), add the
following section to `skoolkit.ini`::

  [skool2ctl]
  Hex=2

Configuration parameters may also be set on the command line by using the
``--ini`` option. Parameter values set this way will override any found in
`skoolkit.ini`.

+---------+-------------------------------------------------------------------+
| Version | Changes                                                           |
+=========+===================================================================+
| 7.2     | Configuration is read from `skoolkit.ini` if present; added the   |
|         | ``--ini``, ``--show-config`` and ``--keep-lines`` options         |
+---------+-------------------------------------------------------------------+
| 7.0     | Added support for the 'n' identifier in the ``--write`` option    |
+---------+-------------------------------------------------------------------+
| 6.2     | The ``--end`` and ``--start`` options accept a hexadecimal        |
|         | integer prefixed by '0x'                                          |
+---------+-------------------------------------------------------------------+
| 6.0     | Added support for the 'a' identifier in the ``--write`` option    |
+---------+-------------------------------------------------------------------+
| 5.1     | A terminal ``i`` directive is appended if the skool file ends     |
|         | before 65536                                                      |
+---------+-------------------------------------------------------------------+
| 4.5     | Added the ``--start`` and ``--end`` options                       |
+---------+-------------------------------------------------------------------+
| 4.4     | Added the ``--hex-lower`` option                                  |
+---------+-------------------------------------------------------------------+
| 3.7     | Added the ``--preserve-base`` option                              |
+---------+-------------------------------------------------------------------+
| 3.4     | Added the ``-V`` option and the long options                      |
+---------+-------------------------------------------------------------------+
| 2.4     | Added the ability to preserve some ASM directives                 |
+---------+-------------------------------------------------------------------+
| 2.2.2   | Added the ability to read a skool file from standard input        |
+---------+-------------------------------------------------------------------+
| 2.0.6   | Added the ``-h`` option                                           |
+---------+-------------------------------------------------------------------+
| 1.1     | New                                                               |
+---------+-------------------------------------------------------------------+

.. _skool2html.py:

skool2html.py
-------------
`skool2html.py` converts a skool file (and its associated ref files, if any
exist) into a browsable disassembly in HTML format.

For example::

  $ skool2html.py game.skool

will convert the file `game.skool` into a bunch of HTML files. If any files
named `game*.ref` (e.g. `game.ref`, `game-bugs.ref`, `game-pokes.ref` and so
on) also exist in the same directory as `game.skool`, they will be used to
provide further information to the conversion process, along with any extra
files named in the ``RefFiles`` parameter in the :ref:`ref-Config` section, and
any other ref files named on the command line.

`skool2html.py` supports several options; run it with no arguments to see a
list::

  usage: skool2html.py [options] SKOOLFILE [REFFILE...]

  Convert a skool file and ref files to HTML. SKOOLFILE may be a regular file, or
  '-' for standard input.

  Options:
    -1, --asm-one-page    Write all routines and data blocks to a single page.
    -a, --asm-labels      Use ASM labels.
    -c S/L, --config S/L  Add the line 'L' to the ref file section 'S'. This
                          option may be used multiple times.
    -C, --create-labels   Create default labels for unlabelled instructions.
    -d DIR, --output-dir DIR
                          Write files in this directory (default is '.').
    -D, --decimal         Write the disassembly in decimal.
    -H, --hex             Write the disassembly in hexadecimal.
    -I p=v, --ini p=v     Set the value of the configuration parameter 'p' to
                          'v'. This option may be used multiple times.
    -j NAME, --join-css NAME
                          Concatenate CSS files into a single file with this name.
    -l, --lower           Write the disassembly in lower case.
    -o, --rebuild-images  Overwrite existing image files.
    -O, --rebuild-audio   Overwrite existing audio files.
    -p, --package-dir     Show path to skoolkit package directory and exit.
    -P PAGES, --pages PAGES
                          Write only these pages (when using '--write P').
                          PAGES is a comma-separated list of page IDs.
    -q, --quiet           Be quiet.
    -r PREFIX, --ref-sections PREFIX
                          Show default ref file sections whose names start with
                          PREFIX and exit.
    -R, --ref-file        Show the entire default ref file and exit.
    -s, --search-dirs     Show the locations skool2html.py searches for resources.
    -S DIR, --search DIR  Add this directory to the resource search path. This
                          option may be used multiple times.
    --show-config         Show configuration parameter values.
    -t, --time            Show timings.
    -T THEME, --theme THEME
                          Use this CSS theme. This option may be used multiple
                          times.
    -u, --upper           Write the disassembly in upper case.
    --var name=value      Define a variable that can be used by @if and the SMPL
                          macros. This option may be used multiple times.
    -V, --version         Show SkoolKit version number and exit.
    -w X, --write X       Write only these files, where X is one or more of:
                            d = Disassembly files   o = Other code
                            i = Disassembly index   P = Other pages
                            m = Memory maps
    -W CLASS, --writer CLASS
                          Specify the HTML writer class to use; shorthand for
                          '--config Config/HtmlWriterClass=CLASS'.

`skool2html.py` searches the following directories for CSS files, JavaScript
files, font files, and files listed in the :ref:`resources` section of the ref
file:

* The directory that contains the skool file named on the command line
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

  $ skool2html.py -T dark -T wide game.skool

will use the following CSS files, if they exist, in the order listed:

* `skoolkit.css`
* `skoolkit-dark.css`
* `skoolkit-wide.css`
* `game.css`
* `game-dark.css`
* `game-wide.css`
* `dark.css`
* `wide.css`

.. _skool2html-conf:

Configuration
^^^^^^^^^^^^^
`skool2html.py` will read configuration from a file named `skoolkit.ini` in the
current working directory or in `~/.skoolkit`, if present. The recognised
configuration parameters are:

* ``AsmLabels`` - use ASM labels (``1``), or don't (``0``, the default)
* ``AsmOnePage`` - write all routines and data blocks to a single page (``1``),
  or to multiple pages (``0``, the default)
* ``Base`` - convert addresses and instruction operands to hexadecimal (``16``)
  or decimal (``10``), or leave them as they are (``0``, the default)
* ``Case`` - write the disassembly in lower case (``1``) or upper case (``2``),
  or leave it as it is (``0``, the default)
* ``CreateLabels`` - create default labels for unlabelled instructions (``1``),
  or don't (``0``, the default)
* ``EntryLabel`` - the format of the default label for the first instruction in
  a routine or data block (default: ``L{address}``)
* ``EntryPointLabel`` - the format of the default label for an instruction
  other than the first in a routine or data block (default: ``{main}_{index}``)
* ``JoinCss`` - if specified, concatenate CSS files into a single file with
  this name
* ``OutputDir`` - write files in this directory (default: ``.``)
* ``Quiet`` - be quiet (``1``) or verbose (``0``, the default)
* ``RebuildAudio`` - overwrite existing audio files (``1``), or leave them
  alone (``0``, the default)
* ``RebuildImages`` - overwrite existing image files (``1``), or leave them
  alone (``0``, the default)
* ``Search`` - directory to add to the resource search path; to specify two or
  more directories, separate them with commas
* ``Theme`` - CSS theme to use; to specify two or more themes, separate them
  with commas
* ``Time`` - show timings (``1``), or don't (``0``, the default)

``EntryLabel`` and ``EntryPointLabel`` are standard Python format strings.
``EntryLabel`` recognises the following replacement fields:

* ``address`` - the address of the routine or data block as it appears in the
  skool file
* ``location`` - the address of the routine or data block as an integer

``EntryPointLabel`` recognises the following replacement fields:

* ``address`` - the address of the instruction as it appears in the skool file
* ``index`` - 0 for the first unlabelled instruction in the routine or data
  block, 1 for the second, etc.
* ``location`` - the address of the instruction as an integer
* ``main`` - the label of the first instruction in the routine or data block

Configuration parameters must appear in a ``[skool2html]`` section. For
example, to make `skool2html.py` use ASM labels and write the disassembly in
hexadecimal by default (without having to use the ``-H`` and ``-a`` options on
the command line), add the following section to `skoolkit.ini`::

  [skool2html]
  AsmLabels=1
  Base=16

Configuration parameters may also be set on the command line by using the
``--ini`` option. Parameter values set this way will override any found in
`skoolkit.ini`.

+---------+------------------------------------------------------------------+
| Version | Changes                                                          |
+=========+==================================================================+
| 8.7     | Added the ``--rebuild-audio`` option and the ``RebuildAudio``    |
|         | configuration parameter                                          |
+---------+------------------------------------------------------------------+
| 8.5     | Added the ``EntryLabel`` and ``EntryPointLabel`` configuration   |
|         | parameters                                                       |
+---------+------------------------------------------------------------------+
| 7.0     | Writes a single disassembly from the skool file given by the     |
|         | first positional argument                                        |
+---------+------------------------------------------------------------------+
| 6.4     | Added the ``--var`` option                                       |
+---------+------------------------------------------------------------------+
| 6.2     | Added the ``--show-config`` option                               |
+---------+------------------------------------------------------------------+
| 6.1     | Configuration is read from `skoolkit.ini` if present; added the  |
|         | ``--ini`` option                                                 |
+---------+------------------------------------------------------------------+
| 5.4     | Added the ``--asm-one-page`` option                              |
+---------+------------------------------------------------------------------+
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
| 2.3.1   | Added support for reading multiple ref files per disassembly     |
+---------+------------------------------------------------------------------+
| 2.2.2   | Added the ability to read a skool file from standard input       |
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

.. _sna2ctl.py:

sna2ctl.py
----------
`sna2ctl.py` generates a control file for a binary (raw memory) file or a SNA,
SZX or Z80 snapshot. For example::

  $ sna2ctl.py game.z80 > game.ctl

Now `game.ctl` can be used by :ref:`sna2skool.py` to convert `game.z80` into a
skool file split into blocks of code and data.

`sna2ctl.py` supports several options; run it with no arguments to see a list::

  usage: sna2ctl.py [options] FILE

  Generate a control file for a binary (raw memory) file or a SNA, SZX or Z80
  snapshot. FILE may be a regular file, or '-' for standard input.

  Options:
    -e ADDR, --end ADDR   Stop at this address (default=65536).
    -h, --hex             Write upper case hexadecimal addresses.
    -I p=v, --ini p=v     Set the value of the configuration parameter 'p' to
                          'v'. This option may be used multiple times.
    -l, --hex-lower       Write lower case hexadecimal addresses.
    -m FILE, --map FILE   Use FILE as a code execution map.
    -o ADDR, --org ADDR   Specify the origin address of a binary file (default:
                          65536 - length).
    -p PAGE, --page PAGE  Specify the page (0-7) of a 128K snapshot to map to
                          49152-65535.
    --show-config         Show configuration parameter values.
    -s ADDR, --start ADDR
                          Start at this address.
    -V, --version         Show SkoolKit version number and exit.

If the input filename does not end with '.sna', '.szx' or '.z80', it is assumed
to be a binary file.

The ``-m`` option may be used to specify a code execution map to use when
generating a control file. The supported file formats are:

* Profiles created by the Fuse emulator
* Code execution logs created by the SpecEmu, Spud and Zero emulators
* Map files created by the SpecEmu and Z80 emulators

If the file specified by the ``-m`` option is 8192 bytes long, it is assumed to
be a Z80 map file; if it is 65536 bytes long, it is assumed to be a SpecEmu map
file; otherwise it is assumed to be in one of the other supported formats.

.. _sna2ctl-conf:

Configuration
^^^^^^^^^^^^^
`sna2ctl.py` will read configuration from a file named `skoolkit.ini` in the
current working directory or in `~/.skoolkit`, if present. The recognised
configuration parameters are:

* ``Dictionary`` - the name of a file containing a list of allowed words, one
  per line; if specified, a string of characters will be marked as text only if
  it contains at least one of the words in this file
* ``Hex`` - write addresses in decimal (``0``, the default), lower case
  hexadecimal (``1``),  or upper case hexadecimal (``2``)
* ``TextChars`` - characters eligible for being marked as text (default:
  letters, digits, space, and the following non-alphanumeric characters:
  ``!"$%&\'()*+,-./:;<=>?[]``)
* ``TextMinLengthCode`` - the minimum length of a string of characters eligible
  for being marked as text in a block identified as code (default: ``12``)
* ``TextMinLengthData`` - the minimum length of a string of characters eligible
  for being marked as text in a block identified as data (default: ``3``)

Configuration parameters must appear in a ``[sna2ctl]`` section. For example,
to make `sna2ctl.py` write upper case hexadecimal addresses by default (without
having to use the ``-h`` option on the command line), add the following section
to `skoolkit.ini`::

  [sna2ctl]
  Hex=2

Configuration parameters may also be set on the command line by using the
``--ini`` option. Parameter values set this way will override any found in
`skoolkit.ini`.

+---------+-------------------------------------------------------------------+
| Version | Changes                                                           |
+=========+===================================================================+
| 7.2     | Added the ``Dictionary`` configuration parameter                  |
+---------+-------------------------------------------------------------------+
| 7.1     | Configuration is read from `skoolkit.ini` if present; added the   |
|         | ``--ini`` and ``--show-config`` options                           |
+---------+-------------------------------------------------------------------+
| 7.0     | New                                                               |
+---------+-------------------------------------------------------------------+

.. _sna2img.py:

sna2img.py
----------
`sna2img.py` converts the screenshot or other graphic data in a binary (raw
memory) file, SCR file, skool file, or SNA/SZX/Z80 snapshot into a PNG file.
For example::

  $ sna2img.py game.scr

will create a file named `game.png`.

To list the options supported by `sna2img.py`, run it with no arguments::

  usage: sna2img.py [options] INPUT [OUTPUT]

  Convert a Spectrum screenshot or other graphic data into a PNG file. INPUT may
  be a binary (raw memory) file, a SCR file, a skool file, or a SNA, SZX or Z80
  snapshot.

  Options:
    -b, --bfix            Parse a skool file in @bfix mode.
    -B, --binary          Read the input as a binary (raw memory) file.
    -e MACRO, --expand MACRO
                          Expand a #FONT, #SCR, #UDG or #UDGARRAY macro. The '#'
                          prefix may be omitted.
    -f N, --flip N        Flip the image horizontally (N=1), vertically (N=2),
                          or both (N=3).
    -i, --invert          Invert video for cells that are flashing.
    -m src,size,dest, --move src,size,dest
                          Move a block of bytes of the given size from src to
                          dest. This option may be used multiple times.
    -n, --no-animation    Do not animate flashing cells.
    -o X,Y, --origin X,Y  Top-left crop at (X,Y).
    -O ORG, --org ORG     Set the origin address of a binary file (default:
                          65536 minus the length of the file).
    -p a[-b[-c]],[^+]v, --poke a[-b[-c]],[^+]v
                          POKE N,v for N in {a, a+c, a+2c..., b}. Prefix 'v'
                          with '^' to perform an XOR operation, or '+' to
                          perform an ADD operation. This option may be used
                          multiple times.
    -r N, --rotate N      Rotate the image 90*N degrees clockwise.
    -s SCALE, --scale SCALE
                          Set the scale of the image (default=1).
    -S WxH, --size WxH    Crop to this width and height (in tiles).
    -V, --version         Show SkoolKit version number and exit.

+---------+-------------------------------------------------------------------+
| Version | Changes                                                           |
+=========+===================================================================+
| 6.2     | Added the ``--binary`` and ``--org`` options and the ability to   |
|         | read binary (raw memory) files; the ``--move`` and ``--poke``     |
|         | options accept hexadecimal integers prefixed by '0x'              |
+---------+-------------------------------------------------------------------+
| 6.1     | Added the ability to read skool files; added the ``--bfix`` and   |
|         | ``--move`` options                                                |
+---------+-------------------------------------------------------------------+
| 6.0     | Added the ``--expand`` option                                     |
+---------+-------------------------------------------------------------------+
| 5.4     | New                                                               |
+---------+-------------------------------------------------------------------+

.. _sna2skool.py:

sna2skool.py
------------
`sna2skool.py` converts a binary (raw memory) file or a SNA, SZX or Z80
snapshot into a skool file. For example::

  $ sna2skool.py game.z80 > game.skool

Now `game.skool` can be converted into a browsable HTML disassembly using
:ref:`skool2html.py <skool2html.py>`, or into an assembler-ready ASM file using
:ref:`skool2asm.py <skool2asm.py>`.

`sna2skool.py` supports several options; run it with no arguments to see a
list::

  usage: sna2skool.py [options] FILE

  Convert a binary (raw memory) file or a SNA, SZX or Z80 snapshot into a skool
  file. FILE may be a regular file, or '-' for standard input.

  Options:
    -c PATH, --ctl PATH   Specify a control file to use, or a directory from
                          which to read control files. PATH may be '-' for
                          standard input, or '0' to use no control file. This
                          option may be used multiple times.
    -d SIZE, --defb SIZE  Disassemble as DEFB statements of this size.
    -e ADDR, --end ADDR   Stop disassembling at this address (default=65536).
    -H, --hex             Write hexadecimal addresses and operands in the
                          disassembly.
    -I p=v, --ini p=v     Set the value of the configuration parameter 'p' to
                          'v'. This option may be used multiple times.
    -l, --lower           Write the disassembly in lower case.
    -o ADDR, --org ADDR   Specify the origin address of a binary (.bin) file
                          (default: 65536 - length).
    -p PAGE, --page PAGE  Specify the page (0-7) of a 128K snapshot to map to
                          49152-65535.
    --show-config         Show configuration parameter values.
    -s ADDR, --start ADDR
                          Start disassembling at this address.
    -V, --version         Show SkoolKit version number and exit.
    -w W, --line-width W  Set the maximum line width of the skool file (default:
                          79).

If the input filename does not end with '.sna', '.szx' or '.z80', it is assumed
to be a binary file.

By default, any files whose names start with the input filename (minus the
'.bin', '.sna', '.szx' or '.z80' suffix, if any) and end with '.ctl' will be
used as :ref:`control files <controlFiles>`.

.. _sna2skool-conf:

Configuration
^^^^^^^^^^^^^
`sna2skool.py` will read configuration from a file named `skoolkit.ini` in the
current working directory or in `~/.skoolkit`, if present. The recognised
configuration parameters are:

* ``Base`` - write addresses and instruction operands in hexadecimal (``16``)
  or decimal (``10``, the default)
* ``Case`` - write the disassembly in lower case (``1``) or upper case (``2``,
  the default)
* ``CommentWidthMin`` - minimum width of the instruction comment field in the
  skool file (default: ``10``)
* ``DefbSize`` - maximum number of bytes in a DEFB statement (default: ``8``)
* ``DefmSize`` - maximum number of characters in a DEFM statement (default:
  ``65``)
* ``DefwSize`` - maximum number of words in a DEFW statement (default: ``1``)
* ``EntryPointRef`` - template used to format the comment for an entry point
  with exactly one referrer (default: ``This entry point is used by the routine
  at {ref}.``)
* ``EntryPointRefs`` - template used to format the comment for an entry point
  with two or more referrers (default: ``This entry point is used by the
  routines at {refs} and {ref}.``)
* ``InstructionWidth`` - minimum width of the instruction field in the skool
  file (default: ``13``)
* ``LineWidth`` - maximum line width of the skool file (default: ``79``)
* ``ListRefs`` - when to add a comment that lists routine or entry point
  referrers: never (``0``), if no other comment is defined at the entry point
  (``1``, the default), or always (``2``)
* ``Ref`` - template used to format the comment for a routine with exactly one
  referrer (default: ``Used by the routine at {ref}.``)
* ``RefFormat`` - template used to format referrers in the ``{ref}`` and
  ``{refs}`` fields of the ``Ref`` and ``Refs`` templates (default:
  ``#R{address}``); the replacement field ``address`` is the address of the
  referrer formatted as a decimal or hexadecimal number in accordance with the
  ``Base`` and ``Case`` configuration parameters
* ``Refs`` - template used to format the comment for a routine with two or more
  referrers (default: ``Used by the routines at {refs} and {ref}.``)
* ``Semicolons`` - block types (``b``, ``c``, ``g``, ``i``, ``s``, ``t``,
  ``u``, ``w``) in which comment semicolons are written for instructions that
  have no comment (default: ``c``)
* ``Text`` - show ASCII text in the comment fields (``1``), or don't (``0``,
  the default)
* ``Timings`` - show instruction timings in the comment fields (``1``), or
  don't (``0``, the default)
* ``Title-b`` - template used to format the title for an untitled 'b' block
  (default: ``Data block at {address}``)
* ``Title-c`` - template used to format the title for an untitled 'c' block
  (default: ``Routine at {address}``)
* ``Title-g`` - template used to format the title for an untitled 'g' block
  (default: ``Game status buffer entry at {address}``)
* ``Title-i`` - template used to format the title for an untitled 'i' block
  (default: ``Ignored``)
* ``Title-s`` - template used to format the title for an untitled 's' block
  (default: ``Unused``)
* ``Title-t`` - template used to format the title for an untitled 't' block
  (default: ``Message at {address}``)
* ``Title-u`` - template used to format the title for an untitled 'u' block
  (default: ``Unused``)
* ``Title-w`` - template used to format the title for an untitled 'w' block
  (default: ``Data block at {address}``)
* ``Wrap`` - disassemble an instruction that wraps around the 64K boundary
  (``1``), or don't (``0``, the default)

Configuration parameters must appear in a ``[sna2skool]`` section. For example,
to make `sna2skool.py` generate hexadecimal skool files with a line width of
120 characters by default (without having to use the ``-H`` and ``-w`` options
on the command line), add the following section to `skoolkit.ini`::

  [sna2skool]
  Base=16
  LineWidth=120

Configuration parameters may also be set on the command line by using the
``--ini`` option. Parameter values set this way will override any found in
`skoolkit.ini`.

+---------+-------------------------------------------------------------------+
| Version | Changes                                                           |
+=========+===================================================================+
| 8.7     | Added the ``--defb`` option and the ``Timings`` configuration     |
|         | parameter                                                         |
+---------+-------------------------------------------------------------------+
| 8.5     | Added the ``Wrap`` configuration parameter and the ability to     |
|         | disassemble an instruction that wraps around the 64K boundary;    |
|         | added the ``RefFormat`` configuration parameter                   |
+---------+-------------------------------------------------------------------+
| 8.4     | Changed the default value of the ``DefmSize`` configuration       |
|         | parameter from 66 to 65                                           |
+---------+-------------------------------------------------------------------+
| 8.3     | Added support for reading control files from a directory          |
|         | (``--ctl DIR``)                                                   |
+---------+-------------------------------------------------------------------+
| 8.1     | Added support for ignoring default control files (``--ctl 0``)    |
+---------+-------------------------------------------------------------------+
| 8.0     | Added the ``DefwSize`` configuration parameter                    |
+---------+-------------------------------------------------------------------+
| 7.1     | Added support for reading multiple default control files, and for |
|         | using the ``--ctl`` option multiple times; added the              |
|         | ``CommentWidthMin``, ``InstructionWidth`` and ``Semicolons``      |
|         | configuration parameters                                          |
+---------+-------------------------------------------------------------------+
| 7.0     | The short option for ``--lower`` is ``-l``; the long option for   |
|         | ``-H`` is ``--hex``                                               |
+---------+-------------------------------------------------------------------+
| 6.2     | Added the ``--show-config`` option; the ``--end``, ``--org`` and  |
|         | ``--start`` options accept a hexadecimal integer prefixed by '0x' |
+---------+-------------------------------------------------------------------+
| 6.1     | Configuration is read from `skoolkit.ini` if present; added the   |
|         | ``--ini`` option                                                  |
+---------+-------------------------------------------------------------------+
| 4.4     | Added the ``--end`` option                                        |
+---------+-------------------------------------------------------------------+
| 4.3     | Added the ``--line-width`` option                                 |
+---------+-------------------------------------------------------------------+
| 3.4     | Added the ``-V`` option and the long options, and the ability to  |
|         | add a comment listing referrers at every routine entry point      |
+---------+-------------------------------------------------------------------+
| 3.3     | Added the ability to read 128K SNA snapshots                      |
+---------+-------------------------------------------------------------------+
| 3.2     | Added the ``-p`` option, and the ability to read SZX snapshots    |
|         | and 128K Z80 snapshots                                            |
+---------+-------------------------------------------------------------------+
| 2.1.2   | Added the ability to write the disassembly in lower case          |
+---------+-------------------------------------------------------------------+
| 2.1     | Added the ``-H`` option                                           |
+---------+-------------------------------------------------------------------+
| 2.0.1   | Added the ``-o`` option, and the ability to read binary files, to |
|         | set the maximum number of characters in a DEFM statement, and to  |
|         | suppress comments that list routine entry point referrers         |
+---------+-------------------------------------------------------------------+
| 2.0     | Added the ability to set the maximum number of bytes in a DEFB    |
|         | statement                                                         |
+---------+-------------------------------------------------------------------+
| 1.0.5   | Added the ability to show ASCII text in comment fields            |
+---------+-------------------------------------------------------------------+
| 1.0.4   | Added the ``-s`` option                                           |
+---------+-------------------------------------------------------------------+

.. _snapinfo.py:

snapinfo.py
-----------
`snapinfo.py` shows information on the registers or RAM in a binary (raw
memory) file or a SNA, SZX or Z80 snapshot. For example::

  $ snapinfo.py game.z80

To list the options supported by `snapinfo.py`, run it with no arguments::

  usage: snapinfo.py [options] file

  Analyse a binary (raw memory) file or a SNA, SZX or Z80 snapshot.

  Options:
    -b, --basic           List the BASIC program.
    -c PATH, --ctl PATH   When generating a call graph, specify a control file
                          to use, or a directory from which to read control
                          files. PATH may be '-' for standard input. This option
                          may be used multiple times.
    -f A[,B...[-M[-N]]], --find A[,B...[-M[-N]]]
                          Search for the byte sequence A,B... with distance
                          ranging from M to N (default=1) between bytes.
    -g, --call-graph      Generate a call graph in DOT format.
    -I p=v, --ini p=v     Set the value of the configuration parameter 'p' to
                          'v'. This option may be used multiple times.
    -o ADDR, --org ADDR   Specify the origin address of a binary (raw memory)
                          file (default: 65536 - length).
    -p A[-B[-C]], --peek A[-B[-C]]
                          Show the contents of addresses A TO B STEP C. This
                          option may be used multiple times.
    -P PAGE, --page PAGE  Specify the page (0-7) of a 128K snapshot to map to
                          49152-65535.
    --show-config         Show configuration parameter values.
    -t TEXT, --find-text TEXT
                          Search for a text string.
    -T X,Y[-M[-N]], --find-tile X,Y[-M[-N]]
                          Search for the graphic data of the tile at (X,Y) with
                          distance ranging from M to N (default=1) between
                          bytes.
    -v, --variables       List variables.
    -V, --version         Show SkoolKit version number and exit.
    -w A[-B[-C]], --word A[-B[-C]]
                          Show the words at addresses A TO B STEP C. This option
                          may be used multiple times.

With no options, `snapinfo.py` displays register values, the interrupt mode,
and the border colour. By using one of the options shown above, it can list
the BASIC program and variables (if present), show the contents of a range of
addresses, search the RAM for a sequence of byte values or a text string, or
generate a call graph.

.. _snapinfo-call-graph:

Call graphs
^^^^^^^^^^^
`snapinfo.py` can generate a call graph in `DOT format`_ from a snapshot and a
corresponding control file. For example, if `game.ctl` is present alongside
`game.z80`, then::

  $ snapinfo.py -g game.z80 > game.dot

will produce a call graph in `game.dot`, with a node for each routine declared
in `game.ctl`, and an edge between two nodes whenever the routine represented
by the first node calls, jumps to, or continues into the routine represented by
the second node.

To create a PNG image file named `game.png` from `game.dot`, the `dot` utility
(included in Graphviz_) may be used::

  $ dot -Tpng game.dot > game.png

A call graph may contain one or more 'orphans', an orphan being a node that is
not at the head of any arrow, and thus represents a routine that is (as far as
`snapinfo.py` can tell) not used by any other routines. To declare the callers
of such a routine (in case it is not a true orphan), the :ref:`refs` directive
may be used.

To help identify orphan nodes and missing edges, each of the first three lines
of the DOT file produced by `snapinfo.py` contains a list of IDs of the
following types of node:

* unconnected nodes
* orphan nodes connected to other nodes
* non-orphan nodes whose first instruction is not used

The appearance of nodes and edges in a call graph image can be configured via
the ``EdgeAttributes``, ``GraphAttributes``, ``NodeAttributes`` and
``NodeLabel`` configuration parameters (see below).

.. _snapinfo-conf:

Configuration
^^^^^^^^^^^^^
`snapinfo.py` will read configuration from a file named `skoolkit.ini` in the
current working directory or in `~/.skoolkit`, if present. The recognised
configuration parameters are:

* ``EdgeAttributes`` - the default attributes_ for edges in a call graph
  (default: none)
* ``GraphAttributes`` - the default attributes_ for a call graph (default:
  none)
* ``NodeAttributes`` - the default attributes_ for nodes in a call graph
  (default: ``shape=record``)
* ``NodeId`` - the format of the node IDs in a call graph (default:
  ``{address}``)
* ``NodeLabel`` - the format of the node labels in a call graph (default:
  ``"{address} {address:04X}\n{label}"``)
* ``Peek`` - the format of each line of the output produced by the ``--peek``
  option (default:
  ``{address:>5} {address:04X}: {value:>3}  {value:02X}  {value:08b}  {char}``)
* ``Word`` - the format of each line of the output produced by the ``--word``
  option (default: ``{address:>5} {address:04X}: {value:>5}  {value:04X}``)

``NodeId`` and ``NodeLabel`` are standard Python format strings that recognise
the replacement fields ``address`` and ``label`` (the address and label of the
first instruction in the routine represented by the node).

Configuration parameters must appear in a ``[snapinfo]`` section. For example,
to make `snapinfo.py` use open arrowheads and a cyan background colour in call
graphs by default, add the following section to `skoolkit.ini`::

  [snapinfo]
  EdgeAttributes=arrowhead=open
  GraphAttributes=bgcolor=cyan

Configuration parameters may also be set on the command line by using the
``--ini`` option. Parameter values set this way will override any found in
`skoolkit.ini`.

.. _DOT format: https://graphviz.gitlab.io/_pages/doc/info/lang.html
.. _Graphviz: https://graphviz.gitlab.io/
.. _attributes: https://graphviz.gitlab.io/_pages/doc/info/attrs.html

+---------+-------------------------------------------------------------------+
| Version | Changes                                                           |
+=========+===================================================================+
| 8.10    | Shows the value of the T-states counter and the issue 2 emulation |
|         | flag in SZX and Z80 snapshots                                     |
+---------+-------------------------------------------------------------------+
| 8.4     | Added the ``Peek`` and ``Word`` configuration parameters          |
+---------+-------------------------------------------------------------------+
| 8.3     | Added support for reading control files from a directory          |
|         | (``--ctl DIR``)                                                   |
+---------+-------------------------------------------------------------------+
| 8.2     | Configuration is read from `skoolkit.ini` if present; added the   |
|         | ability to read binary files; added the ``--call-graph``,         |
|         | ``--ctl``, ``--ini``, ``--org``, ``--page`` and ``--show-config`` |
|         | options                                                           |
+---------+-------------------------------------------------------------------+
| 6.2     | The ``--find``, ``--find-tile``, ``--peek`` and ``--word``        |
|         | options accept hexadecimal integers prefixed by '0x'              |
+---------+-------------------------------------------------------------------+
| 6.0     | Added support to the ``--find`` option for distance ranges; added |
|         | the ``--find-tile`` and ``--word`` options; the ``--peek`` option |
|         | shows UDGs and BASIC tokens                                       |
+---------+-------------------------------------------------------------------+
| 5.4     | Added the ``--variables`` option; UDGs in a BASIC program are     |
|         | shown as special symbols (e.g. ``{UDG-A}``)                       |
+---------+-------------------------------------------------------------------+
| 5.3     | New                                                               |
+---------+-------------------------------------------------------------------+

.. _snapmod.py:

snapmod.py
----------
`snapmod.py` modifies the registers and RAM in a 48K Z80 snapshot. For
example::

  $ snapmod.py --poke 32768,0 game.z80 poked.z80

To list the options supported by `snapmod.py`, run it with no arguments::

  usage: snapmod.py [options] in.z80 [out.z80]

  Modify a 48K Z80 snapshot.

  Options:
    -f, --force           Overwrite an existing snapshot.
    -m src,size,dest, --move src,size,dest
                          Move a block of bytes of the given size from src to
                          dest. This option may be used multiple times.
    -p a[-b[-c]],[^+]v, --poke a[-b[-c]],[^+]v
                          POKE N,v for N in {a, a+c, a+2c..., b}. Prefix 'v'
                          with '^' to perform an XOR operation, or '+' to
                          perform an ADD operation. This option may be used
                          multiple times.
    -r name=value, --reg name=value
                          Set the value of a register. Do '--reg help' for more
                          information. This option may be used multiple times.
    -s name=value, --state name=value
                          Set a hardware state attribute. Do '--state help' for
                          more information. This option may be used multiple
                          times.
    -V, --version         Show SkoolKit version number and exit.

+---------+-------------------------------------------------------------------+
| Version | Changes                                                           |
+=========+===================================================================+
| 8.10    | Added the ``issue2`` hardware state attribute                     |
+---------+-------------------------------------------------------------------+
| 8.9     | Added the ``tstates`` hardware state attribute                    |
+---------+-------------------------------------------------------------------+
| 6.2     | The ``--move``, ``--poke`` and ``--reg`` options accept           |
|         | hexadecimal integers prefixed by '0x'                             |
+---------+-------------------------------------------------------------------+
| 5.3     | New                                                               |
+---------+-------------------------------------------------------------------+

.. _tap2sna.py:

tap2sna.py
----------
`tap2sna.py` converts a TAP or TZX file (which may be inside a zip archive)
into a Z80 snapshot. For example::

  $ tap2sna.py game.tap game.z80

To list the options supported by `tap2sna.py`, run it with no arguments::

  usage:
    tap2sna.py [options] INPUT snapshot.z80
    tap2sna.py --tape-analysis [options] INPUT
    tap2sna.py @FILE

  Convert a TAP or TZX file (which may be inside a zip archive) into a Z80
  snapshot. INPUT may be the full URL to a remote zip archive or TAP/TZX file,
  or the path to a local file. Arguments may be read from FILE instead of (or as
  well as) being given on the command line.

  Options:
    -c name=value, --sim-load-config name=value
                          Set the value of a --sim-load configuration parameter.
                          Do '-c help' for more information. This option may be
                          used multiple times.
    -d DIR, --output-dir DIR
                          Write the snapshot file in this directory.
    -f, --force           Overwrite an existing snapshot.
    -I p=v, --ini p=v     Set the value of the configuration parameter 'p' to
                          'v'. This option may be used multiple times.
    -p STACK, --stack STACK
                          Set the stack pointer.
    --ram OPERATION       Perform a load operation or otherwise modify the
                          memory snapshot being built. Do '--ram help' for more
                          information. This option may be used multiple times.
    --reg name=value      Set the value of a register. Do '--reg help' for more
                          information. This option may be used multiple times.
    --show-config         Show configuration parameter values.
    -s START, --start START
                          Set the start address to JP to.
    --sim-load            Simulate a 48K ZX Spectrum running LOAD "".
    --state name=value    Set a hardware state attribute. Do '--state help' for
                          more information. This option may be used multiple
                          times.
    --tape-analysis       Show an analysis of the tape's tones, pulse sequences
                          and data blocks.
    --tape-name NAME      Specify the name of a TAP/TZX file in a zip archive.
    --tape-start BLOCK    Start the tape at this block number.
    --tape-stop BLOCK     Stop the tape at this block number.
    --tape-sum MD5SUM     Specify the MD5 checksum of the TAP/TZX file.
    -u AGENT, --user-agent AGENT
                          Set the User-Agent header.
    -V, --version         Show SkoolKit version number and exit.

Note that `tap2sna.py` can read data from TZX block types 0x10 (standard speed
data), 0x11 (turbo speed data) and 0x14 (pure data), but not block types 0x15
(direct recording), 0x18 (CSW recording) or 0x19 (generalized data block).

By default, `tap2sna.py` loads bytes from every data block on the tape, using
the start address given in the corresponding header. For tapes that contain
headerless data blocks, headers with incorrect start addresses, or irrelevant
blocks, the ``--ram`` option can be used to load bytes from specific blocks at
the appropriate addresses. For example::

  $ tap2sna.py --ram load=3,30000 game.tzx game.z80

loads the third block on the tape at address 30000, and ignores all other
blocks. (To see information on the blocks in a TAP or TZX file, use the
:ref:`tapinfo.py` command.)

In addition to loading specific blocks, the ``--ram`` option can also be used
to move blocks of bytes from one location to another, POKE values into
individual addresses or address ranges, modify memory with XOR and ADD
operations, initialise the system variables, or call a Python function to
modify the memory snapshot in an arbitrary way before it is saved. For more
information on these operations, run::

  $ tap2sna.py --ram help

For complex snapshots that require many options to build, it may be more
convenient to store the arguments to `tap2sna.py` in a file. For example, if
the file `game.t2s` has the following contents::

  ;
  ; tap2sna.py file for GAME
  ;
  http://example.com/pub/games/GAME.zip
  game.z80
  --ram load=4,32768         # Load the fourth block at 32768
  --ram move=40960,512,43520 # Move 40960-41471 to 43520-44031
  --ram call=:ram.modify     # Call modify(snapshot) in ./ram.py
  --ram sysvars              # Initialise the system variables
  --state iff=0              # Disable interrupts
  --stack 32768              # Stack at 32768
  --start 34816              # Start at 34816

then::

  $ tap2sna.py @game.t2s

will create `game.z80` as if the arguments specified in `game.t2s` had been
given on the command line.

.. _tap2sna-sim-load:

Simulated LOAD
^^^^^^^^^^^^^^
An alternative to the ``--ram load`` approach is the ``--sim-load`` option. It
simulates a freshly booted 48K ZX Spectrum running LOAD "" (or LOAD ""CODE, if
the first block on the tape is a 'Bytes' header). Whenever the Spectrum ROM's
load routine at $0556 is called, a shortcut is taken by "fast loading" the next
block on the tape. All other code (including any custom loader) is fully
simulated. Simulation continues until the program counter hits the start
address given by the ``--start`` option, or 15 minutes of simulated Z80 CPU
time has elapsed, or the end of the tape is reached and one of the following
conditions is satisfied:

* a custom loader was detected
* the program counter hits an address outside the ROM
* more than one second of simulated Z80 CPU time has elapsed since the end of
  the tape was reached

A simulated LOAD can also be aborted by pressing Ctrl-C. When a simulated LOAD
has completed or been aborted, the values of the registers (including the
program counter) in the simulator are used to populate the Z80 snapshot.

A simulated LOAD can be configured via parameters that are set by the
``--sim-load-config`` (or ``-c``) option. The recognised configuration
parameters are:

* ``accelerate-dec-a`` - enable acceleration of 'DEC A: JR NZ,$-1' delay loops
  (``1``, the default), or 'DEC A: JP NZ,$-1' delay loops (``2``), or neither
  (``0``)
* ``accelerator`` - a comma-separated list of tape-sampling loop accelerators
  to use (see below)
* ``contended-in`` - interpret 'IN A,($FE)' instructions in the address range
  $4000-$7FFF as reading the tape (``1``), or ignore them (``0``, the default)
* ``fast-load`` - enable fast loading (``1``, the default), or disable it
  (``0``); fast loading significantly reduces the load time for many tapes, but
  can also cause some loaders to fail
* ``finish-tape`` - run the tape to the end before stopping the simulation at
  the address specified by the ``--start`` option (``1``), or stop the
  simulation as soon as that address is reached, regardless of whether the tape
  has finished (``0``, the default)
* ``first-edge`` - the time (in T-states) from the start of the tape at which
  to place the leading edge of the first pulse (default: ``-2168``); the
  default value places the trailing edge of the first pulse at time 0, but some
  loaders (e.g. polarity-sensitive loaders) require ``first-edge=0``
* ``pause`` - pause the tape between blocks and resume playback when port 254
  is read (``1``, the default), or run the tape continuously (``0``); pausing
  can help with tapes that require (but do not actually contain) long pauses
  between blocks, but can cause some loaders to fail
* ``timeout`` - the number of seconds of Z80 CPU time after which to abort the
  simulated LOAD if it's still in progress (default: 900)
* ``trace`` - the file to which to log all instructions executed during the
  simulated LOAD (default: none)

The ``accelerator`` parameter must be either a comma-separated list of specific
accelerator names or one of the following special values:

* ``auto`` - select accelerators automatically (this is the default)
* ``list`` - list the accelerators used during a simulated LOAD, along with the
  hit/miss counts generated by the tape-sampling loop detector
* ``none`` - disable acceleration; the loading time for a game with a custom
  loader that uses an unrecognised tape-sampling loop may be reduced by
  specifying this value

The output produced by ``accelerator=list`` looks something like this::

  Accelerators: microsphere: 6695; rom: 794013; misses: 19/9

This means that the ``microsphere`` and ``rom`` tape-sampling loops were
detected, and were entered 6695 times and 794013 times respectively. In
addition, 19 instances of 'INC B' outside a recognised tape-sampling loop were
executed, and the corresponding figure for 'DEC B' is 9.

Specifying by name the types of tape-sampling loop used by a game's custom
loader may reduce the loading time. The names of the available tape-sampling
loop accelerators are:

* ``alkatraz`` (Alkatraz)
* ``alkatraz-05`` (Italy 1990, Italy 1990 - Winners Edition)
* ``alkatraz-09`` (Italy 1990, Italy 1990 - Winners Edition)
* ``alkatraz-0a`` (various games published by U.S. Gold)
* ``alkatraz-0b`` (Fast 'n' Furious)
* ``alkatraz2`` (Alkatraz 2)
* ``alternative`` (Fireman Sam, Huxley Pig)
* ``alternative2`` (Kentucky Racing)
* ``bleepload`` (Firebird BleepLoad)
* ``boguslaw-juza`` (Euro Biznes)
* ``bulldog`` (Rigel's Revenge)
* ``crl`` (Ball Breaker, Ballbreaker II)
* ``crl2`` (Terrahawks)
* ``crl3`` (Oink)
* ``crl4`` (Federation)
* ``cyberlode`` (Cyberlode 1.1 - same as ``bleepload``)
* ``cybexlab`` (17.11.1989, Belegost, Starfox)
* ``d-and-h`` (Multi-Player Soccer Manager)
* ``delphine`` (Zakliaty zámok programátorov)
* ``design-design`` (various games published by Design Design Software)
* ``digital-integration`` (Digital Integration)
* ``dinaload`` (Dinaload)
* ``edge`` (Edge - same as ``rom``)
* ``elite-uni-loader`` (Elite Uni-Loader - same as ``speedlock``)
* ``excelerator`` (The Excelerator Loader - same as ``bleepload``)
* ``flash-loader`` (Flash Loader - same as ``rom``)
* ``ftl`` (FTL - same as ``speedlock``)
* ``gargoyle`` (Gargoyle - same as ``speedlock``)
* ``gargoyle2`` (various games created or published by Gargoyle Games)
* ``gremlin`` (various games published by Gremlin Graphics)
* ``gremlin2`` (Super Cars)
* ``hewson-slowload`` (Hewson Slowload - same as ``rom``)
* ``injectaload`` (Injectaload - same as ``bleepload``)
* ``microprose`` (F-15 Strike Eagle)
* ``microsphere`` (Back to Skool, Contact Sam Cruise, Skool Daze, Sky Ranger)
* ``micro-style`` (Xenophobe)
* ``mirrorsoft`` (Action Reflex)
* ``palas`` (Bad Night)
* ``paul-owens`` (Paul Owens Protection System)
* ``poliload`` (Poliload - same as ``dinaload``)
* ``power-load`` (Power-Load - same as ``bleepload``)
* ``raxoft`` (Piskworks, Podraz 4)
* ``realtime`` (Starstrike II)
* ``rom`` (any loader whose sampling loop is the same as the ROM's)
* ``search-loader`` (Search Loader)
* ``silverbird`` (Olli & Lissa II: Halloween)
* ``softlock`` (SoftLock - same as ``rom``)
* ``software-projects`` (BC's Quest for Tires, Lode Runner)
* ``sparklers`` (Bargain Basement, Flunky)
* ``speedlock`` (Speedlock - all versions)
* ``suzy-soft`` (Big Trouble, Joe Banker, The Drinker)
* ``suzy-soft2`` (Western Girl)
* ``tiny`` (Il Cobra di Cristallo, Negy a Nyero, Phantomasa, and others)
* ``us-gold`` (Gauntlet II)
* ``weird-science`` (Flash Beer Trilogy, Ghost Castles, TV-Game)
* ``zydroload`` (Zydroload - same as ``speedlock``)

.. _tap2sna-conf:

Configuration
^^^^^^^^^^^^^
`tap2sna.py` will read configuration from a file named `skoolkit.ini` in the
current working directory or in `~/.skoolkit`, if present. The recognised
configuration parameters are:

* ``TraceLine`` - the format of each line in the trace log file for a simulated
  LOAD (default: ``${pc:04X} {i}``)
* ``TraceOperand`` - the prefix, byte format, and word format for the numeric
  operands of instructions in the trace log file for a simulated LOAD,
  separated by commas (default: ``$,02X,04X``); the byte and word formats are
  standard Python format specifiers for numeric values, and default to empty
  strings if not supplied

``TraceLine`` is a standard Python format string that recognises the following
replacement fields:

* ``i`` - the current instruction
* ``pc`` - the address of the current instruction (program counter)
* ``r[a]`` - the A register (accumulator)
* ``r[f]`` - the F (flags) register
* ``r[b]`` - the B register
* ``r[c]`` - the C register
* ``r[d]`` - the D register
* ``r[e]`` - the E register
* ``r[h]`` - the H register
* ``r[l]`` - the L register
* ``r[^a]`` - the A' register (shadow accumulator)
* ``r[^f]`` - the F' (shadow flags) register
* ``r[^b]`` - the shadow B register
* ``r[^c]`` - the shadow C register
* ``r[^d]`` - the shadow D register
* ``r[^e]`` - the shadow E register
* ``r[^h]`` - the shadow H register
* ``r[^l]`` - the shadow L register
* ``r[ixh]`` - the high byte of the IX register pair
* ``r[ixl]`` - the low byte of the IX register pair
* ``r[iyh]`` - the high byte of the IY register pair
* ``r[iyl]`` - the low byte of the IY register pair
* ``r[i]`` - the I register
* ``r[r]`` - the R register
* ``r[sp]`` - the stack pointer
* ``r[t]`` - the current timestamp

The current timestamp (``r[t]``) is the number of T-states that have elapsed
since the start of the simulation, according to the simulator's internal clock.
In order to maintain synchronisation with the tape being loaded, the
simulator's clock is adjusted to match the timestamp of the first pulse in each
block (as shown by the ``--tape-analysis`` option) when that block is reached.
(The simulator's clock may at times become desynchronised with the tape
because, by default, the tape is paused between blocks, and resumed when port
254 is read.)

Configuration parameters must appear in a ``[tap2sna]`` section. For example,
to make `tap2sna.py` write instruction addresses and operands in a trace log
file in decimal format by default, add the following section to
`skoolkit.ini`::

  [tap2sna]
  TraceLine={pc:05} {i}
  TraceOperand=

Configuration parameters may also be set on the command line by using the
``--ini`` option. Parameter values set this way will override any found in
`skoolkit.ini`.

+---------+-------------------------------------------------------------------+
| Version | Changes                                                           |
+=========+===================================================================+
| 8.10    | Configuration is read from `skoolkit.ini` if present; added the   |
|         | ``--ini``, ``--show-config`` and ``--tape-analysis`` options;     |
|         | added the ``TraceLine`` and ``TraceOperand`` configuration        |
|         | parameters; added the ``accelerate-dec-a``, ``contended-in`` and  |
|         | ``finish-tape`` simulated LOAD configuration parameters; added    |
|         | the ``issue2`` hardware state attribute; added the special        |
|         | ``auto`` and ``list`` tape-sampling loop accelerator names, and   |
|         | the ability to specify multiple accelerators; added the           |
|         | ``alkatraz-05``, ``alkatraz-09``, ``alkatraz-0a``,                |
|         | ``alkatraz-0b``, ``alternative``, ``alternative2``,               |
|         | ``boguslaw-juza``, ``bulldog``, ``crl``, ``crl2``, ``crl3``,      |
|         | ``crl4``, ``cybexlab``, ``d-and-h``, ``delphine``,                |
|         | ``design-design``, ``gargoyle2``, ``gremlin2``, ``microprose``,   |
|         | ``micro-style``, ``mirrorsoft``, ``palas``, ``raxoft``,           |
|         | ``realtime``, ``silverbird``, ``software-projects``,              |
|         | ``sparklers``, ``suzy-soft``, ``suzy-soft2``, ``tiny``,           |
|         | ``us-gold`` and ``weird-science`` tape-sampling loop accelerators |
+---------+-------------------------------------------------------------------+
| 8.9     | Added the ``--sim-load-config``, ``--tape-name``,                 |
|         | ``--tape-start``, ``--tape-stop`` and ``--tape-sum`` options;     |
|         | added support for TZX loops, pauses, and unused bits in data      |
|         | blocks; added support for quoted arguments in an arguments file;  |
|         | added the ``tstates`` hardware state attribute                    |
+---------+-------------------------------------------------------------------+
| 8.8     | The ``--sim-load`` option performs any ``call/move/poke/sysvars`` |
|         | operations specified by ``--ram``                                 |
+---------+-------------------------------------------------------------------+
| 8.7     | Added the ``--sim-load`` option; when a headerless block is       |
|         | ignored because no ``--ram load`` options have been specified, a  |
|         | warning is printed                                                |
+---------+-------------------------------------------------------------------+
| 8.6     | Added support to the ``--ram`` option for the ``call`` operation  |
+---------+-------------------------------------------------------------------+
| 8.4     | Added support to the ``--ram`` option for the ``sysvars``         |
|         | operation                                                         |
+---------+-------------------------------------------------------------------+
| 6.3     | Added the ``--user-agent`` option                                 |
+---------+-------------------------------------------------------------------+
| 6.2     | The ``--ram``, ``--reg``, ``--stack`` and ``--start`` options     |
|         | accept hexadecimal integers prefixed by '0x'                      |
+---------+-------------------------------------------------------------------+
| 5.3     | Added the ``--stack`` and ``--start`` options                     |
+---------+-------------------------------------------------------------------+
| 4.5     | Added support for TZX block type 0x14 (pure data), for loading    |
|         | the first and last bytes of a tape block, and for modifying       |
|         | memory with XOR and ADD operations                                |
+---------+-------------------------------------------------------------------+
| 3.5     | New                                                               |
+---------+-------------------------------------------------------------------+

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
                          Show TZX blocks with these IDs only. 'IDs' is a comma-
                          separated list of hexadecimal block IDs, e.g.
                          10,11,2a.
    -B N[,A], --basic N[,A]
                          List the BASIC program in block N loaded at address A
                          (default 23755).
    -d, --data            Show the entire contents of header and data blocks.
    -V, --version         Show SkoolKit version number and exit.

+---------+-------------------------------------------------------------------+
| Version | Changes                                                           |
+=========+===================================================================+
| 8.9     | Shows full info for TZX block types 0x10 and 0x11                 |
+---------+-------------------------------------------------------------------+
| 8.3     | Added the ``--data`` option                                       |
+---------+-------------------------------------------------------------------+
| 8.1     | Shows contents of TZX block types 0x33 (hardware type) and 0x35   |
|         | (custom info)                                                     |
+---------+-------------------------------------------------------------------+
| 7.1     | Shows pulse lengths in TZX block type 0x13 and full info for TZX  |
|         | block type 0x14                                                   |
+---------+-------------------------------------------------------------------+
| 6.2     | The ``--basic`` option accepts a hexadecimal address prefixed by  |
|         | '0x'                                                              |
+---------+-------------------------------------------------------------------+
| 6.0     | Added the ``--basic`` option                                      |
+---------+-------------------------------------------------------------------+
| 5.0     | New                                                               |
+---------+-------------------------------------------------------------------+

.. _trace.py:

trace.py
--------
`trace.py` simulates the execution of machine code in a 48K memory snapshot.
For example::

  $ trace.py --start 32768 --stop 49152 game.z80

To list the options supported by `trace.py`, run it with no arguments::

  usage: trace.py [options] FILE

  Trace Z80 machine code execution. FILE may be a binary (raw memory) file, a
  SNA, SZX or Z80 snapshot, or '.' for no snapshot.

  Options:
    --audio               Show audio delays.
    --depth DEPTH         Simplify audio delays to this depth (default: 2).
    -D, --decimal         Show decimal values in verbose mode.
    --dump FILE           Dump a Z80 snapshot to this file after execution.
    -i, --interrupts      Execute interrupt routines.
    --max-operations MAX  Maximum number of instructions to execute.
    --max-tstates MAX     Maximum number of T-states to run for.
    -o ADDR, --org ADDR   Specify the origin address of a binary (raw memory)
                          file (default: 65536 - length).
    -p a[-b[-c]],[^+]v, --poke a[-b[-c]],[^+]v
                          POKE N,v for N in {a, a+c, a+2c..., b}. Prefix 'v'
                          with '^' to perform an XOR operation, or '+' to
                          perform an ADD operation. This option may be used
                          multiple times.
    -r name=value, --reg name=value
                          Set the value of a register. Do '--reg help' for more
                          information. This option may be used multiple times.
    --rom FILE            Patch in a ROM at address 0 from this file. By default
                          the 48K ZX Spectrum ROM is used.
    -s ADDR, --start ADDR
                          Start execution at this address.
    -S ADDR, --stop ADDR  Stop execution at this address.
    --stats               Show stats after execution.
    -v, --verbose         Show executed instructions. Repeat this option to show
                          register values too.
    -V, --version         Show SkoolKit version number and exit.

By default, `trace.py` silently simulates code execution beginning with the
instruction at the address specified by the ``--start`` option (or the program
counter in the snapshot) and ending when the instruction at the address
specified by ``--stop`` (if any) is reached, and does not execute interrupt
routines. Use the ``--verbose`` option to show each instruction executed.
Repeat the ``--verbose`` option (``-vv``) to show register values too. Use the
``--interrupts`` option to enable the execution of interrupt routines.

When the ``--audio`` option is given, `trace.py` tracks changes in the state
of the ZX Spectrum speaker, and then prints a list of the delays (in T-states)
between those changes. This list can be supplied to the :ref:`AUDIO` macro to
produce a WAV file for the sound effect that would be produced by the same code
running on a real ZX Spectrum.

+---------+-------------------------------------------------------------------+
| Version | Changes                                                           |
+=========+===================================================================+
| 8.9     | Added the ``--interrupts`` option; reads and writes the T-states  |
|         | counter in Z80 snapshots and reads the T-states counter in SZX    |
|         | snapshots                                                         |
+---------+-------------------------------------------------------------------+
| 8.8     | New                                                               |
+---------+-------------------------------------------------------------------+
