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
    -c N, --clear N       Use a 'CLEAR N' command in the BASIC loader and leave
                          the stack pointer alone.
    -e ADDR, --end ADDR   Set the end address when reading a snapshot.
    -o ORG, --org ORG     Set the origin address (default: 16384 for a snapshot,
                          otherwise 65536 minus the length of FILE).
    -p STACK, --stack STACK
                          Set the stack pointer (default: ORG).
    -s START, --start START
                          Set the start address to JP to (default: ORG).
    -S FILE, --screen FILE
                          Add a loading screen to the TAP file. FILE may be a
                          snapshot or a 6912-byte SCR file.
    -V, --version         Show SkoolKit version number and exit.

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

+---------+-------------------------------------------------------------------+
| Version | Changes                                                           |
+=========+===================================================================+
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
    --var name=value      Define a variable that can be used by @if, #IF and #MAP.
                          This option may be used multiple times.
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

* ``Base`` - convert addresses and instruction operands to hexadecimal (``16``)
  or decimal (``10``), or leave them as they are (``0``, the default)
* ``Case`` - write the disassembly in lower case (``1``) or upper case (``2``),
  or leave it as it is (``0``, the default)
* ``CreateLabels`` - create default labels for unlabelled instructions (``1``),
  or don't (``0``, the default)
* ``Quiet`` - be quiet (``1``) or verbose (``0``, the default)
* ``Set-property`` - set an ASM writer property value, e.g. ``Set-bullet=+``
  (see the :ref:`set` directive for a list of available properties)
* ``Templates`` - file from which to read custom :ref:`asmTemplates`
* ``Warnings`` - show warnings (``1``, the default), or suppress them (``0``)

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
    -E ADDR, --end ADDR   Stop converting at this address.
    -i, --isub            Apply @isub directives.
    -o, --ofix            Apply @ofix directives.
    -s, --ssub            Apply @isub and @ssub directives.
    -S ADDR, --start ADDR
                          Start converting at this address.
    -V, --version         Show SkoolKit version number and exit.

+---------+-------------------------------------------------------------------+
| Version | Changes                                                           |
+=========+===================================================================+
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

If you need to preserve any elements that control files do not support (such as
ASM block directives), consider using :ref:`skool2sft.py` to create a skool
file template instead.

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
    --var name=value      Define a variable that can be used by @if, #IF and #MAP.
                          This option may be used multiple times.
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
* ``JoinCss`` - if specified, concatenate CSS files into a single file with
  this name
* ``OutputDir`` - write files in this directory (default: ``.``)
* ``Quiet`` - be quiet (``1``) or verbose (``0``, the default)
* ``RebuildImages`` - overwrite existing image files (``1``), or leave them
  alone (``0``, the default)
* ``Search`` - directory to add to the resource search path; to specify two or
  more directories, separate them with commas
* ``Theme`` - CSS theme to use; to specify two or more themes, separate them
  with commas
* ``Time`` - show timings (``1``), or don't (``0``, the default)

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

.. _skool2sft.py:

skool2sft.py
------------
`skool2sft.py`  converts a skool file into a
:ref:`skool file template <skoolFileTemplates>`. For example::

  $ skool2sft.py game.skool > game.sft

To list the options supported by `skool2sft.py`, run it with no arguments::

  usage: skool2sft.py [options] FILE

  Convert a skool file into a skool file template and write it to standard
  output. FILE may be a regular file, or '-' for standard input.

  Options:
    -b, --preserve-base   Preserve the base of decimal and hexadecimal values in
                          instruction operands and DEFB/DEFM/DEFS/DEFW
                          statements.
    -E ADDR, --end ADDR   Stop converting at this address.
    -h, --hex             Write addresses in upper case hexadecimal format.
    -l, --hex-lower       Write addresses in lower case hexadecimal format.
    -S ADDR, --start ADDR
                          Start converting at this address.
    -V, --version         Show SkoolKit version number and exit.

.. note::
   Skool file templates and `skool2sft.py` are deprecated since version 7.2.
   Use :ref:`control files <controlFiles>` and :ref:`skool2ctl.py` instead.

+---------+-------------------------------------------------------------+
| Version | Changes                                                     |
+=========+=============================================================+
| 6.2     | The ``--end`` and ``--start`` options accept a hexadecimal  |
|         | integer prefixed by '0x'                                    |
+---------+-------------------------------------------------------------+
| 5.1     | ``i`` blocks are preserved in the same way as code and data |
|         | blocks (instead of verbatim)                                |
+---------+-------------------------------------------------------------+
| 4.5     | Added the ``--start`` and ``--end`` options                 |
+---------+-------------------------------------------------------------+
| 4.4     | Added the ``--hex-lower`` option                            |
+---------+-------------------------------------------------------------+
| 3.7     | Added the ``--preserve-base`` option                        |
+---------+-------------------------------------------------------------+
| 3.4     | Added the ``-V`` option and the long options                |
+---------+-------------------------------------------------------------+
| 2.4     | New                                                         |
+---------+-------------------------------------------------------------+

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
                          Start at this address (default=16384).
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
memory) file, SCR file, skool file, or SNA/SZX/Z80 snapshot into a PNG or GIF
file. For example::

  $ sna2img.py game.scr

will create a file named `game.png`.

To list the options supported by `sna2img.py`, run it with no arguments::

  usage: sna2img.py [options] INPUT [OUTPUT]

  Convert a Spectrum screenshot or other graphic data into a PNG or GIF file.
  INPUT may be a binary (raw memory) file, a SCR file, a skool file, or a SNA,
  SZX or Z80 snapshot.

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
    -c FILE, --ctl FILE   Use FILE as a control file (may be '-' for standard
                          input). This option may be used multiple times.
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
                          Start disassembling at this address (default=16384).
    -T FILE, --sft FILE   Use FILE as the skool file template (may be '-' for
                          standard input).
    -V, --version         Show SkoolKit version number and exit.
    -w W, --line-width W  Set the maximum line width of the skool file (default:
                          79).

If the input filename does not end with '.sna', '.szx' or '.z80', it is assumed
to be a binary file.

By default, any file whose name is equal to the input filename (minus the
'.bin', '.sna', '.szx' or '.z80' suffix, if any) followed by '.sft' will be
used as a :ref:`skool file template <skoolFileTemplates>`.

Otherwise, any files whose names start with the input filename (minus the
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
* ``DefbMod`` - group DEFB blocks by addresses that are divisible by this
  number (default: ``1``)
* ``DefbSize`` - maximum number of bytes per DEFB statement (default: ``8``)
* ``DefbZfill`` - pad decimal values in DEFB statements with leading zeroes
  (``1``), or leave them unpadded (``0``, the default)
* ``DefmSize`` - maximum number of characters in a DEFM statement (default:
  ``66``)
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
* ``Refs`` - template used to format the comment for a routine with two or more
  referrers (default: ``Used by the routines at {refs} and {ref}.``)
* ``Semicolons`` - block types (``b``, ``c``, ``g``, ``i``, ``s``, ``t``,
  ``u``, ``w``) in which comment semicolons are written for instructions that
  have no comment (default: ``c``)
* ``Text`` - show ASCII text in the comment fields (``1``), or don't (``0``,
  the default)
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
| 2.4     | Added the ``-T`` option                                           |
+---------+-------------------------------------------------------------------+
| 2.1.2   | Added the ability to write the disassembly in lower case          |
+---------+-------------------------------------------------------------------+
| 2.1     | Added the ``-H`` option                                           |
+---------+-------------------------------------------------------------------+
| 2.0.1   | Added the ``-o`` option, and the ability to read binary files, to |
|         | set the maximum number of characters in a DEFM statement, and to  |
|         | suppress comments that list routine entry point referrers         |
+---------+-------------------------------------------------------------------+
| 2.0     | Added the ability to group DEFB blocks by addresses divisible by  |
|         | a given number, to set the maximum number of bytes in a DEFB      |
|         | statement, and to pad decimal values in DEFB statements with      |
|         | leading zeroes                                                    |
+---------+-------------------------------------------------------------------+
| 1.0.5   | Added the ability to show ASCII text in comment fields            |
+---------+-------------------------------------------------------------------+
| 1.0.4   | Added the ``-s`` option                                           |
+---------+-------------------------------------------------------------------+

.. _snapinfo.py:

snapinfo.py
-----------
`snapinfo.py` shows information on the registers and RAM in a SNA, SZX or Z80
snapshot. For example::

  $ snapinfo.py game.z80

To list the options supported by `snapinfo.py`, run it with no arguments::

  usage: snapinfo.py [options] file

  Analyse an SNA, SZX or Z80 snapshot.

  Options:
    -b, --basic           List the BASIC program.
    -f A[,B...[-M[-N]]], --find A[,B...[-M[-N]]]
                          Search for the byte sequence A,B... with distance
                          ranging from M to N (default=1) between bytes.
    -p A[-B[-C]], --peek A[-B[-C]]
                          Show the contents of addresses A TO B STEP C. This
                          option may be used multiple times.
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
addresses, or search the RAM for a sequence of byte values or a text string.

+---------+-------------------------------------------------------------------+
| Version | Changes                                                           |
+=========+===================================================================+
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
    tap2sna.py @FILE

  Convert a TAP or TZX file (which may be inside a zip archive) into a Z80
  snapshot. INPUT may be the full URL to a remote zip archive or TAP/TZX file,
  or the path to a local file. Arguments may be read from FILE instead of (or as
  well as) being given on the command line.

  Options:
    -d DIR, --output-dir DIR
                          Write the snapshot file in this directory.
    -f, --force           Overwrite an existing snapshot.
    -p STACK, --stack STACK
                          Set the stack pointer.
    --ram OPERATION       Perform a load, move or poke operation on the memory
                          snapshot being built. Do '--ram help' for more
                          information. This option may be used multiple times.
    --reg name=value      Set the value of a register. Do '--reg help' for more
                          information. This option may be used multiple times.
    -s START, --start START
                          Set the start address to JP to.
    --state name=value    Set a hardware state attribute. Do '--state help' for
                          more information. This option may be used multiple
                          times.
    -u AGENT, --user-agent AGENT
                          Set the User-Agent header.
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
  --state iff=0              # Disable interrupts
  --stack 32768              # Stack at 32768
  --start 34816              # Start at 34816

then::

  $ tap2sna.py @game.t2s

will create `game.z80` as if the arguments specified in `game.t2s` had been
given on the command line.

+---------+-------------------------------------------------------------------+
| Version | Changes                                                           |
+=========+===================================================================+
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
    -V, --version         Show SkoolKit version number and exit.

+---------+-------------------------------------------------------------------+
| Version | Changes                                                           |
+=========+===================================================================+
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
