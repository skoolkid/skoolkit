.. _commands:

Commands
========

.. _bin2sna.py:

bin2sna.py
----------
`bin2sna.py` converts a binary (raw memory) file into an SZX or Z80 snapshot.
For example::

  $ bin2sna.py game.bin

will create a file named `game.z80`.

If the input file is 128K in length, it is assumed to hold the contents of RAM
banks 0-7 in order, and `bin2sna.py` will write a corresponding 128K snapshot.
Otherwise, the ``--page`` option is required to write a 128K snapshot, and the
contents of individual RAM banks may be specified by ``--bank`` options. If the
input file is less than 128K in length and no ``--page`` option is given, a 48K
snapshot is written.

Run `bin2sna.py` with no arguments to see the list of available options::

  usage: bin2sna.py [options] file.bin [OUTFILE]

  Convert a binary (raw memory) file into an SZX or Z80 snapshot. 'file.bin' may
  be a regular file, or '-' for standard input. If 'OUTFILE' is not given, it
  defaults to the name of the input file with '.bin' replaced by '.z80', or
  'program.z80' if reading from standard input.

  Options:
    --bank N,file         Load RAM bank N (0-7) from the named file. This option
                          may be used multiple times.
    -b BORDER, --border BORDER
                          Set the border colour (default: 7).
    -o ORG, --org ORG     Set the origin address (default: 65536 minus the
                          length of file.bin).
    --page N              Specify the RAM bank (N=0-7) mapped to 49152 (0xC000)
                          in the main input file. This option creates a 128K
                          snapshot.
    -p STACK, --stack STACK
                          Set the stack pointer (default: ORG).
    -P [p:]a[-b[-c]],[^+]v, --poke [p:]a[-b[-c]],[^+]v
                          POKE N,v in RAM bank p for N in {a, a+c, a+2c..., b}.
                          Prefix 'v' with '^' to perform an XOR operation, or
                          '+' to perform an ADD operation. This option may be
                          used multiple times.
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
| 9.1     | Added the ``--bank`` and ``--page`` options and support for       |
|         | writing 128K snapshots; the ``--poke`` option can modify specific |
|         | RAM banks                                                         |
+---------+-------------------------------------------------------------------+
| 9.0     | Added support for writing SZX snapshots; added the ``fe``         |
|         | hardware state attribute                                          |
+---------+-------------------------------------------------------------------+
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
into a PZX or TAP file. For example::

  $ bin2tap.py game.bin

will create a file called `game.tap`. By default, the origin address (the
address of the first byte of code or data), the start address (the first byte
of code to run) and the stack pointer are set to 65536 minus the length of
`game.bin`. These values can be changed by passing options to `bin2tap.py`. Run
it with no arguments to see the list of available options::

  usage: bin2tap.py [options] FILE [OUTFILE]

  Convert a binary (raw memory) file or a SNA, SZX or Z80 snapshot into a PZX or
  TAP file. FILE may be a regular file, or '-' to read a binary file from
  standard input. If OUTFILE is not given, a TAP file is created.

  Options:
    --7ffd N              Add 128K RAM banks to the tape file and write N to
                          port 0x7ffd after they've loaded.
    --banks N[,N...]      Add only these 128K RAM banks to the tape file
                          (default: 0,1,3,4,6,7).
    -b BEGIN, --begin BEGIN
                          Begin conversion at this address (default: ORG for a
                          binary file, 16384 for a snapshot).
    -c N, --clear N       Use a 'CLEAR N' command in the BASIC loader and leave
                          the stack pointer alone.
    -e END, --end END     End conversion at this address.
    --loader ADDR         Place the 128K RAM bank loader at this address
                          (default: CLEAR address + 1).
    -o ORG, --org ORG     Set the origin address for a binary file (default:
                          65536 minus the length of FILE).
    -p STACK, --stack STACK
                          Set the stack pointer (default: BEGIN).
    -s START, --start START
                          Set the start address to JP to (default: BEGIN).
    -S FILE, --screen FILE
                          Add a loading screen to the tape file. FILE may be a
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
Spectrum is 23972 (5DA4) if a loading screen is used, or 23952 (0x5D90)
otherwise.

To create a tape file that loads a 128K game, use the ``--7ffd``, ``--begin``
and ``--clear`` options along with a 128K snapshot or a 128K binary file as
input, where:

* ``--7ffd`` specifies the value to write to port 0x7FFD after all the RAM
  banks have loaded and before starting the game
* ``--begin`` specifies the start address of the code/data below 49152 (0xC000)
  to include on the tape
* ``--clear`` specifies the address of the CLEAR command in the BASIC loader

By default, the 128K RAM bank loader (which is 39-45 bytes long, depending on
the number of RAM banks to load) is placed one above the CLEAR address. Use the
``--loader`` option to place it at an alternative address. The lowest usable
address with the ``--clear`` option on a bare 128K Spectrum is 23977 (0x5DA9)
if a loading screen is used, or 23957 (0x5D95) otherwise.

By default, 128K RAM banks 0, 1, 3, 4, 6 and 7 are added to the tape file. If
one or more of these RAM banks are not required, use the ``--banks`` option to
specify a smaller set of RAM banks to add. If none of these RAM banks are
required, use ``,`` (a single comma) as the argument to the ``--banks`` option.
The contents of RAM banks 5 and 2 - from the ``--begin`` address and up to but
not including the ``--end`` address (if given) - are included in the main code
block on the tape.

+---------+-------------------------------------------------------------------+
| Version | Changes                                                           |
+=========+===================================================================+
| 9.3     | Added support for writing PZX files                               |
+---------+-------------------------------------------------------------------+
| 9.1     | Added the ``--7ffd``, ``--banks`` and ``--loader`` options and    |
|         | support for writing 128K TAP files                                |
+---------+-------------------------------------------------------------------+
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

.. _rzxinfo.py:

rzxinfo.py
----------
`rzxinfo.py` shows the blocks in or extracts the snapshots from an RZX file.
For example::

  $ rzxinfo.py game.rzx

To list the options supported by `rzxinfo.py`, run it with no arguments::

  usage: rzxinfo.py [options] FILE

  Show the blocks in or extract the snapshots from an RZX file.

  Options:
    --extract      Extract snapshots.
    --frames       Show the contents of every frame.
    -V, --version  Show SkoolKit version number and exit.

+---------+---------+
| Version | Changes |
+=========+=========+
| 9.2     | New     |
+---------+---------+

.. _rzxplay.py:

rzxplay.py
----------
`rzxplay.py` plays an RZX file. For example::

  $ rzxplay.py game.rzx

To list the options supported by `rzxplay.py`, run it with no arguments::

  usage: rzxplay.py [options] FILE [OUTFILE]

  Play an RZX file. If 'OUTFILE' is given, an SZX or Z80 snapshot or an RZX file
  is written after playback has completed.

  Options:
    --flags FLAGS    Set playback flags. Do '--flags help' for more information.
    --force          Force playback when unsupported hardware is detected.
    --fps FPS        Run at this many frames per second (default: 50). 0 means
                     maximum speed.
    --map FILE       Log addresses of executed instructions to a file.
    --no-screen      Run without a screen.
    --python         Use the pure Python Z80 simulator.
    --quiet          Don't print progress percentage.
    --scale SCALE    Scale display up by this factor (1-4; default: 2).
    --snapshot FILE  Specify an external snapshot file to start with.
    --stop FRAMES    Stop after playing this many frames.
    --trace FILE     Log executed instructions to a file.
    -V, --version    Show SkoolKit version number and exit.

`rzxplay.py` can play RZX files that were recorded in 48K, 128K or +2 mode with
no peripherals (e.g. Interface 1) attached. The ``--force`` option can be used
to make `rzxplay.py` attempt playback of files that were recorded on
unsupported machines or with unsupported hardware attached, but they are
unlikely to play to the end.

If `pygame`_ is installed, `rzxplay.py` will use it to render the Spectrum's
screen contents at 50 frames per second by default. Use the ``--fps`` option
to change the frame rate. Specifying ``--fps 0`` makes `rzxplay.py` run at
maximum speed. To disable the screen and make `rzxplay.py` run even faster, use
the ``--no-screen`` option.

The ``--map`` option can be used to log the addresses of instructions executed
during playback to a file. This file can then be used by :ref:`sna2ctl.py` to
produce a control file. If the file specified by the ``--map`` option already
exists, any addresses it contains will be merged with those of the instructions
executed.

The ``--flags`` option sets flags that control the playback of RZX frames when
interrupts are enabled. If an RZX file fails to play to completion, setting one
or more of these flags may help. ``FLAGS`` is the sum of the following values,
chosen according to the desired outcome:

* 1 - When the last instruction in a frame is either 'LD A,I' or 'LD A,R',
  reset bit 2 of the flags register. This is the expected behaviour of a real
  Z80, but some RZX files fail when this flag is set.

* 2 - When the last instruction in a frame is 'EI', and the next frame is a
  short one (i.e. has a fetch count of 1 or 2), block the interrupt in the next
  frame. By default, and according to RZX convention, `rzxplay.py` accepts an
  interrupt at the start of every frame except the first, regardless of whether
  the instruction just executed would normally block it. However, some RZX
  files contain a short frame immediately after an 'EI' to indicate that the
  interrupt should in fact be blocked, and therefore require this flag to be
  set to play back correctly.

If ``OUTFILE`` is given, and ends with either '.z80' or '.szx', then a snapshot
in the corresponding format is written when playback ends. Similarly, if
``OUTFILE`` ends with '.rzx', then an RZX file is written when playback ends.
However, this makes sense only if ``--stop`` is used to end playback somewhere
in the middle of the input RZX file, otherwise the output RZX file will be
empty (i.e. contain no frames).

.. _pygame: https://pygame.org/

+---------+---------+
| Version | Changes |
+=========+=========+
| 9.2     | New     |
+---------+---------+

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
    -B, --banks           Process @bank directives and write RAM banks 0-7 to a
                          128K file.
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
| 9.1     | Added the ``--banks`` option                                      |
+---------+-------------------------------------------------------------------+
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

* Files created by the ``--map`` option of :ref:`rzxplay.py`
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
| 9.2     | Added support for reading code execution maps produced by         |
|         | :ref:`rzxplay.py`                                                 |
+---------+-------------------------------------------------------------------+
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
    -e ADDR, --end ADDR   Stop disassembling at this address (default: 65536).
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
* ``Opcodes`` - comma-separated list of values specifying additional opcode
  sequences to disassemble (see below)
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

The ``Opcodes`` list is empty by default, but may contain any of the following
values:

* ``ED63`` - LD (nn),HL (4-byte variant)
* ``ED6B`` - LD HL,(nn) (4-byte variant)
* ``ED70`` - IN F,(C)
* ``ED71`` - OUT (C),0
* ``IM`` - IM 0/1/2 variants (ED followed by 4E/66/6E/76/7E)
* ``NEG`` - NEG variants (ED followed by 4C/54/5C/64/6C/74/7C)
* ``RETN`` - RETN variants (ED followed by 55/5D/65/6D/75/7D)
* ``XYCB`` - undocumented instructions with DDCB or FDCB opcode prefixes (see
  below)
* ``ALL`` - all of the above

When ``XYCB`` is in the list, the following instructions are disassembled
(where 'XY' is IX or IY, and 'r' is B, C, D, E, H, L or A):

* RLC (XY+d),r
* RRC (XY+d),r
* RL (XY+d),r
* RR (XY+d),r
* SLA (XY+d),r
* SRA (XY+d),r
* SLL (XY+d),r
* SRL (XY+d),r
* BIT n,(XY+d) (variants)
* RES n,(XY+d),r
* SET n,(XY+d),r

Whenever an instruction with a variant opcode sequence is disassembled,
`sna2skool.py` will insert a :ref:`bytes` directive into the skool file (if one
is not already provided by a control file) to ensure that the instruction
assembles back to the same byte values when processed by :ref:`skool2asm.py`,
:ref:`skool2html.py` or :ref:`skool2bin.py`.

Also note that if your skool file contains any non-standard instructions (such
as 'IN F,(C)') or instructions that derive from variant opcode sequences (such
as 'BIT 0,(IX+0)' from DDCB0040 instead of the standard DDCB0046), care must be
taken when using an assembler on the output of :ref:`skool2asm.py` to ensure
that instructions not only assemble successfully, but also assemble back to the
original byte values, if desired. The :ref:`isub` directive may be used for
this purpose; for example::

  @isub=DEFB 221,203,0,64 ; This is BIT 0,(IX+0)
   40000 BIT 0,(IX+0) ; The opcode sequence here is DDCB0040

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
| 9.3     | Added the ``Opcodes`` configuration parameter                     |
+---------+-------------------------------------------------------------------+
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
the border colour, and various other attributes. By using one of the options
shown above, it can list the BASIC program and variables (if present), show the
contents of a range of addresses, search the RAM for a sequence of byte values
or a text string, or generate a call graph.

By default, the ``--find``, ``--find-text`` and ``--find-tile`` options search
all RAM banks in a 128K snapshot; use the ``--page`` option to restrict the
search to the address range 16384-65535 (0x4000-0xFFFF).

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
| 9.3     | The ``--find``, ``--find-text`` and ``--find-tile`` options       |
|         | search all RAM banks in a 128K snapshot by default                |
+---------+-------------------------------------------------------------------+
| 9.0     | Shows the current AY register in 128K SZX and Z80 snapshots       |
+---------+-------------------------------------------------------------------+
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
`snapmod.py` modifies the registers and RAM in an SZX or Z80 snapshot. For
example::

  $ snapmod.py --poke 32768,0 game.z80 poked.z80

To list the options supported by `snapmod.py`, run it with no arguments::

  usage: snapmod.py [options] infile [outfile]

  Modify an SZX or Z80 snapshot.

  Options:
    -m [s:]src,size,[d:]dest, --move [s:]src,size,[d:]dest
                          Copy a block of bytes of the given size from src in
                          RAM bank s to dest in RAM bank d. This option may be
                          used multiple times.
    -p [p:]a[-b[-c]],[^+]v, --poke [p:]a[-b[-c]],[^+]v
                          POKE N,v in RAM bank p for N in {a, a+c, a+2c..., b}.
                          Prefix 'v' with '^' to perform an XOR operation, or
                          '+' to perform an ADD operation. This option may be
                          used multiple times.
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
| 9.1     | Added support for modifying SZX snapshots and 128K snapshots; the |
|         | ``--move`` and ``--poke`` options can modify specific RAM banks   |
+---------+-------------------------------------------------------------------+
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
`tap2sna.py` converts a PZX, TAP or TZX file (which may be inside a zip
archive) into an SZX or Z80 snapshot. For example::

  $ tap2sna.py game.tap game.z80

To list the options supported by `tap2sna.py`, run it with no arguments::

  usage:
    tap2sna.py [options] INPUT [OUTFILE]
    tap2sna.py @FILE [args]

  Convert a PZX, TAP or TZX file (which may be inside a zip archive) into an SZX
  or Z80 snapshot. INPUT may be the full URL to a remote zip archive or tape
  file, or the path to a local file. Arguments may be read from FILE instead of
  (or as well as) being given on the command line.

  Options:
    -c name=value, --sim-load-config name=value
                          Set the value of a simulated LOAD configuration
                          parameter. Do '-c help' for more information, or '-c
                          help-name' for help on a specific parameter. This
                          option may be used multiple times.
    -d DIR, --output-dir DIR
                          Write the snapshot file in this directory.
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
    --state name=value    Set a hardware state attribute. Do '--state help' for
                          more information. This option may be used multiple
                          times.
    --tape-analysis       Show an analysis of the tape's tones, pulse sequences
                          and data blocks.
    --tape-name NAME      Specify the name of a tape file in a zip archive.
    --tape-start BLOCK    Start the tape at this block number.
    --tape-stop BLOCK     Stop the tape at this block number.
    --tape-sum MD5SUM     Specify the MD5 checksum of the tape file.
    -u AGENT, --user-agent AGENT
                          Set the User-Agent header.
    -V, --version         Show SkoolKit version number and exit.

Note that `tap2sna.py` cannot read data from TZX block types 0x18 (CSW
recording) or 0x19 (generalized data block).

By default, `tap2sna.py` attempts to load a tape exactly as a 48K Spectrum
would (see :ref:`tap2sna-sim-load`). If that doesn't work, the ``--ram`` option
can be used to load bytes from specific tape blocks at the appropriate
addresses. For example::

  $ tap2sna.py --ram load=3,30000 game.tzx game.z80

loads the third block on the tape at address 30000, and ignores all other
blocks. (To see information on the blocks in a tape file, use the
:ref:`tapinfo.py` command.)

The ``--ram`` option can also be used to move blocks of bytes from one location
to another, POKE values into individual addresses or address ranges, modify
memory with XOR and ADD operations, initialise the system variables, or call a
Python function to modify the memory snapshot in an arbitrary way before it is
saved. For more information on these operations, run::

  $ tap2sna.py --ram help

For complex snapshots that require many options to build, it may be more
convenient to store the arguments to `tap2sna.py` in a file. For example, if
the file `game.t2s` has the following contents::

  ;
  ; tap2sna.py file for GAME
  ;
  http://example.com/pub/games/GAME.zip
  -c fast-load=0       # Disable fast loading
  -c accelerator=none  # Disable tape-sampling loop acceleration
  --state issue2=1     # Enable issue 2 keyboard emulation
  --start 34816        # Start at 34816

then::

  $ tap2sna.py @game.t2s

will create `game.z80` as if the arguments specified in `game.t2s` had been
given on the command line. When `tap2sna.py` reads arguments from a file whose
name ends with '.t2s', the output snapshot filename defaults to the name of
that arguments file with '.t2s' replaced by either '.z80' or '.szx' (depending
on the value of the ``DefaultSnapshotFormat`` configuration parameter).

.. _tap2sna-sim-load:

Simulated LOAD
^^^^^^^^^^^^^^
By default, `tap2sna.py` simulates a freshly booted 48K ZX Spectrum running
LOAD "" (or LOAD ""CODE, if the first block on the tape is a 'Bytes' header).
Whenever the Spectrum ROM's load routine at $0556 is called, a shortcut is
taken by "fast loading" the next block on the tape. All other code (including
any custom loader) is fully simulated. Simulation continues until the program
counter hits the start address given by the ``--start`` option, or 15 minutes
of simulated Z80 CPU time has elapsed, or the end of the tape is reached and
one of the following conditions is satisfied:

* a custom loader was detected
* the program counter hits an address outside the ROM
* more than one second of simulated Z80 CPU time has elapsed since the end of
  the tape was reached

A simulated LOAD can also be aborted by pressing Ctrl-C. When a simulated LOAD
has completed or been aborted, the values of the registers (including the
program counter) in the simulator are used to populate the snapshot.

A simulated LOAD can be configured via parameters that are set by the
``--sim-load-config`` (or ``-c``) option. The recognised configuration
parameters are:

* ``accelerate-dec-a`` - enable acceleration of 'DEC A: JR NZ,$-1' delay loops
  (``1``, the default), or 'DEC A: JP NZ,$-1' delay loops (``2``), or neither
  (``0``)
* ``accelerator`` - a comma-separated list of tape-sampling loop accelerators
  to use (see :ref:`tap2sna-accelerators`)
* ``cmio`` - enable simulation of memory contention and I/O contention delays
  (``1``), or disable it (``0``); this is disabled by default to improve
  performance, but some loaders may require it; when this is enabled, all
  acceleration is disabled
* ``fast-load`` - enable fast loading whenever the ROM loader is called (``1``,
  the default), or disable it (``0``); fast loading (also known as "flash
  loading") significantly reduces the load time for many tapes, but can also
  cause some loaders to fail
* ``finish-tape`` - run the tape to the end before stopping the simulation at
  the address specified by the ``--start`` option (``1``), or stop the
  simulation as soon as that address is reached, regardless of whether the tape
  has finished (``0``, the default)
* ``first-edge`` - the time (in T-states) from the start of the tape at which
  to place the leading edge of the first pulse (default: ``0``)
* ``in-flags`` - various flags specifying how to handle 'IN' instructions (see
  below)
* ``load`` - a space-separated list of keys to press to build an alternative
  command line to load the tape (see :ref:`tap2sna-load`)
* ``machine`` - the type of machine to simulate: a 48K Spectrum (``48``, the
  default), or a 128K Spectrum (``128``)
* ``pause`` - pause the tape between blocks and resume playback when port 254
  is read (``1``, the default), or run the tape continuously (``0``); pausing
  can help with tapes that require (but do not actually contain) long pauses
  between blocks, but can cause some loaders to fail
* ``polarity`` - the EAR bit reading produced by the first pulse on the tape:
  ``0`` (the default) or ``1``; subsequent pulses give readings that alternate
  between 0 and 1
* ``python`` - whether to use the pure Python Z80 simulator (``1``), or the
  much faster C version if available (``0``, the default)
* ``timeout`` - the number of seconds of Z80 CPU time after which to abort the
  simulated LOAD if it's still in progress (default: 900)
* ``trace`` - the file to which to log all instructions executed during the
  simulated LOAD (default: none)

The ``in-flags`` parameter is the sum of the following values, chosen according
to the desired behaviour:

* 1 - interpret 'IN A,($FE)' instructions in the address range $4000-$7FFF as
  reading the tape (by default they are ignored)
* 2 - ignore 'IN' instructions in the address range $4000-$FFFF (i.e. in RAM)
  that read port $FE
* 4 - yield a simulated port reading when executing an 'IN r,(C)' instruction
  (by default such an instruction always yields the value $FF)

By default, the EAR bit reading produced by a pulse is 0 if the 0-based index
of the pulse is even (i.e. first, third, fifth pulses etc.), or 1 otherwise.
This can be reversed by setting ``polarity=1``. Run *tap2sna.py* with the
``--tape-analysis`` option to see the timings and EAR bit readings of the
pulses on a tape.

.. _tap2sna-accelerators:

Accelerators
^^^^^^^^^^^^
The ``accelerator`` simulated LOAD configuration parameter must be either a
comma-separated list of specific accelerator names or one of the following
special values:

* ``auto`` - select accelerators automatically (this is the default)
* ``list`` - list the accelerators used during a simulated LOAD, along with the
  hit/miss counts generated by the tape-sampling loop detector
* ``none`` - disable acceleration; the loading time for a game with a custom
  loader that uses an unrecognised tape-sampling loop may be reduced by
  specifying this value

A tape-sampling loop accelerator works by effectively fast-forwarding the tape
(and the state of the loop itself) to the next edge whenever the loop is
entered. This technique is known as "edge loading".

The output produced by ``accelerator=list`` looks something like this::

  Accelerators: microsphere: 6695; rom: 794013; misses: 19/9; dec-a: 800708/0/224

This means that:

* the ``microsphere`` and ``rom`` tape-sampling loops were detected, and were
  entered 6695 times and 794013 times respectively
* 19 instances of 'INC B' outside a recognised tape-sampling loop were
  executed, and the corresponding figure for 'DEC B' is 9
* 800708 'DEC A: JR NZ,$-1' delay loops were entered, no 'DEC A: JP NZ,$-1'
  delay loops were entered, and 224 instances of 'DEC A' outside such delay
  loops were executed

Specifying by name the types of tape-sampling loop used by a game's custom
loader may reduce the loading time. To show the names of the available
tape-sampling loop accelerators::

  $ tap2sna.py -c help-accelerator

.. _tap2sna-load:

LOAD command
^^^^^^^^^^^^
The ``load`` simulated LOAD configuration parameter may be used to specify an
alternative command line to load the tape in cases where neither 'LOAD ""' nor
'LOAD ""CODE' works. Its value is a space-separated list of 'words' (a 'word'
being a sequence of any characters other than space), each of which is broken
down into a sequence of one or more keypresses. If a word contains the '+'
symbol, the tokens it separates are converted into keypresses made
simultaneously. If a word matches a BASIC token, the corresponding sequence of
keypresses to produce that token are substituted. Otherwise, each character in
the word is converted individually into the appropriate keypresses.

The following special tokens are also recognised:

* ``CS`` - CAPS SHIFT
* ``SS`` - SYMBOL SHIFT
* ``SPACE`` - SPACE
* ``ENTER`` - ENTER
* ``DOWN`` - Cursor down ('CS+6')
* ``GOTO`` - GO TO ('g')
* ``GOSUB`` - GO SUB ('h')
* ``DEFFN`` - DEF FN ('CS+SS SS+1')
* ``OPEN#`` - OPEN # ('CS+SS SS+4')
* ``CLOSE#`` - CLOSE # ('CS+SS SS+5')
* ``PC=address`` - Stop the keyboard input simulation at this address

The ``PC=address`` token, if present, must appear last. The default address is
either 0x0605 (when a 48K Spectrum is being simulated) or 0x13BE (on a 128K
Spectrum). The simulated LOAD begins at this address.

``ENTER`` is automatically appended to the command line if not already present.

For example, the ``load`` parameter may be set to::

  CLEAR 34999: LOAD "" CODE : RANDOMIZE USR 35000

Note that the spaces around ``CLEAR``, ``LOAD``, ``CODE``, ``RANDOMIZE`` and
``USR`` are required in order for them to be recognised as BASIC tokens.

.. _tap2sna-conf:

Configuration
^^^^^^^^^^^^^
`tap2sna.py` will read configuration from a file named `skoolkit.ini` in the
current working directory or in `~/.skoolkit`, if present. The recognised
configuration parameters are:

* ``DefaultSnapshotFormat`` - the format of the snapshot written when no output
  snapshot argument is specified; valid values are ``z80`` (the default) and
  ``szx``
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
* ``m[address]`` - the contents of a memory address
* ``pc`` - the address of the current instruction (program counter)
* ``r[X]`` - the 'X' register (see below)
* ``t`` - the current timestamp

When using the ``m`` (memory) replacement field, ``address`` must be either a
decimal number, or a hexadecimal number prefixed by '$' or '0x'.

The register name ``X`` in ``r[X]`` must be one of the following::

  a b c d e f h l bc de hl
  ^a ^b ^c ^d ^e ^f ^h ^l ^bc ^de ^hl
  ix ixh ixl iy iyh iyl
  i r sp

The names that begin with ``^`` denote the shadow registers.

The current timestamp (``t``) is the number of T-states that have elapsed since
the start of the simulation, according to the simulator's internal clock. In
order to maintain synchronisation with the tape being loaded, the simulator's
clock is adjusted to match the timestamp of the first pulse in each block (as
shown by the ``--tape-analysis`` option) when that block is reached. (The
simulator's clock may at times become desynchronised with the tape because, by
default, the tape is paused between blocks, and resumed when port 254 is read.)

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
| 9.3     | Added support for PZX files; added support for the ``m`` (memory) |
|         | replacement field in the ``TraceLine`` configuration parameter    |
+---------+-------------------------------------------------------------------+
| 9.2     | Added support for TZX block type 0x15 (direct recording); added   |
|         | the ``python`` simulated LOAD configuration parameter             |
+---------+-------------------------------------------------------------------+
| 9.1     | The ``--ram move`` and ``--ram poke`` options can modify specific |
|         | RAM banks; added the ``cmio`` simulated LOAD configuration        |
|         | parameter                                                         |
+---------+-------------------------------------------------------------------+
| 9.0     | A simulated LOAD is performed by default; an existing snapshot    |
|         | will be overwritten by default; added the ``load``, ``machine``,  |
|         | ``polarity`` and ``in-flags`` simulated LOAD configuration        |
|         | parameters; the output snapshot argument is optional; added       |
|         | support for writing SZX snapshots; added the                      |
|         | ``DefaultSnapshotFormat`` configuration parameter; added the      |
|         | ``fe`` hardware state attribute; added support for register pairs |
|         | (``r[bc]``, ``r[de]`` etc.) in the ``TraceLine`` configuration    |
|         | parameter; added the ``antirom``, ``ernieware`` and ``housenka``  |
|         | tape-sampling loop accelerators; shows 'DEC A' delay loop         |
|         | statistics when ``accelerator=list``                              |
+---------+-------------------------------------------------------------------+
| 8.10    | Configuration is read from `skoolkit.ini` if present; added the   |
|         | ``--ini``, ``--show-config`` and ``--tape-analysis`` options;     |
|         | added the ``TraceLine`` and ``TraceOperand`` configuration        |
|         | parameters; added the ``accelerate-dec-a`` and ``finish-tape``    |
|         | simulated LOAD configuration parameters; added the ``issue2``     |
|         | hardware state attribute; added the special ``auto`` and ``list`` |
|         | tape-sampling loop accelerator names, and the ability to specify  |
|         | multiple accelerators; added the ``alkatraz-05``,                 |
|         | ``alkatraz-09``, ``alkatraz-0a``, ``alkatraz-0b``,                |
|         | ``alternative``, ``alternative2``, ``boguslaw-juza``,             |
|         | ``bulldog``, ``crl``, ``crl2``, ``crl3``, ``crl4``, ``cybexlab``, |
|         | ``d-and-h``, ``delphine``, ``design-design``, ``gargoyle2``,      |
|         | ``gremlin2``, ``microprose``, ``micro-style``, ``mirrorsoft``,    |
|         | ``palas``, ``raxoft``, ``realtime``, ``silverbird``,              |
|         | ``software-projects``, ``sparklers``, ``suzy-soft``,              |
|         | ``suzy-soft2``, ``tiny``, ``us-gold`` and ``weird-science``       |
|         | tape-sampling loop accelerators                                   |
+---------+-------------------------------------------------------------------+
| 8.9     | Added the ``--sim-load-config``, ``--tape-name``,                 |
|         | ``--tape-start``, ``--tape-stop`` and ``--tape-sum`` options;     |
|         | added support for TZX loops, pauses, and unused bits in data      |
|         | blocks; added support for quoted arguments in an arguments file;  |
|         | added the ``tstates`` hardware state attribute                    |
+---------+-------------------------------------------------------------------+
| 8.8     | A simulated LOAD performs any ``call/move/poke/sysvars``          |
|         | operations specified by ``--ram``                                 |
+---------+-------------------------------------------------------------------+
| 8.7     | Added support for simulating a 48K Spectrum LOADing a tape; when  |
|         | a headerless block is ignored because no ``--ram load`` options   |
|         | have been specified, a warning is printed                         |
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
`tapinfo.py` shows information on the blocks in a PZX, TAP or TZX file. For
example::

  $ tapinfo.py game.tzx

To list the options supported by `tapinfo.py`, run it with no arguments::

  usage: tapinfo.py FILE

  Show the blocks in a PZX, TAP or TZX file.

  Options:
    -b N[,A], --basic N[,A]
                          List the BASIC program in block N loaded at address A
                          (default 23755).
    -d, --data            Show the entire contents of header and data blocks.
    --tape-start BLOCK    Start at this tape block number.
    --tape-stop BLOCK     Stop at this tape block number.
    -V, --version         Show SkoolKit version number and exit.

+---------+-------------------------------------------------------------------+
| Version | Changes                                                           |
+=========+===================================================================+
| 9.3     | Added support for PZX files; added the ``--tape-start`` and       |
|         | ``--tape-stop`` options; shows info for TZX block types 0x18 (CSW |
|         | recording) and 0x2B (set signal level); recognises deprecated TZX |
|         | block types 0x16, 0x17,0x34 and 0x40                              |
+---------+-------------------------------------------------------------------+
| 9.2     | Shows info for TZX block type 0x15 (direct recording)             |
+---------+-------------------------------------------------------------------+
| 9.0     | Shows the LINE number (if present) for 'Program:' header blocks;  |
|         | renders BASIC tokens in header block names                        |
+---------+-------------------------------------------------------------------+
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
`trace.py` simulates the execution of machine code in a 48K, 128K or +2 memory
snapshot. For example::

  $ trace.py --start 32768 --stop 49152 game.z80

To list the options supported by `trace.py`, run it with no arguments::

  usage: trace.py [options] FILE [OUTFILE]

  Trace Z80 machine code execution. FILE may be a binary (raw memory) file, a
  SNA, SZX or Z80 snapshot, or '48', '128' or '+2' for no snapshot. If 'OUTFILE'
  is given, an SZX/Z80 snapshot or WAV file is written after execution has
  completed.

  Options:
    --audio               Show audio delays.
    -c, --cmio            Simulate memory and I/O contention.
    --depth DEPTH         Simplify audio delays to this depth (default: 2).
    -D, --decimal         Show decimal values in verbose mode.
    -I p=v, --ini p=v     Set the value of the configuration parameter 'p' to
                          'v'. This option may be used multiple times.
    -m MAX, --max-operations MAX
                          Maximum number of instructions to execute.
    -M MAX, --max-tstates MAX
                          Maximum number of T-states to run for.
    -n, --no-interrupts   Don't execute interrupt routines.
    -o ADDR, --org ADDR   Specify the origin address of a binary (raw memory)
                          file (default: 65536 - length).
    -p [p:]a[-b[-c]],[^+]v, --poke [p:]a[-b[-c]],[^+]v
                          POKE N,v in RAM bank p for N in {a, a+c, a+2c..., b}
                          before execution begins. Prefix 'v' with '^' to
                          perform an XOR operation, or '+' to perform an ADD
                          operation. This option may be used multiple times.
    --python              Use the pure Python Z80 simulator.
    -r name=value, --reg name=value
                          Set the value of a register before execution begins.
                          Do '--reg help' for more information. This option may
                          be used multiple times.
    --rom FILE            Patch in a ROM at address 0 from this file.
    --show-config         Show configuration parameter values.
    -s ADDR, --start ADDR
                          Start execution at this address.
    -S ADDR, --stop ADDR  Stop execution at this address.
    --state name=value    Set a hardware state attribute before execution
                          begins. Do '--state help' for more information. This
                          option may be used multiple times.
    --stats               Show stats after execution.
    -v, --verbose         Show executed instructions. Repeat this option to show
                          register values too.
    -V, --version         Show SkoolKit version number and exit.

By default, `trace.py` silently simulates code execution beginning with the
instruction at the address specified by the ``--start`` option (or the program
counter in the snapshot) and ending when the instruction at the address
specified by ``--stop`` (if any) is reached. Use the ``--verbose`` option to
show each instruction executed. Repeat the ``--verbose`` option (``-vv``) to
show register values too.

When the ``--audio`` option is given, `trace.py` tracks changes in the state
of the ZX Spectrum speaker, and then prints a list of the delays (in T-states)
between those changes. This list can be supplied to the :ref:`AUDIO` macro to
produce a WAV file for the sound effect that would be produced by the same code
running on a real ZX Spectrum.

.. _trace-conf:

Configuration
^^^^^^^^^^^^^
`trace.py` will read configuration from a file named `skoolkit.ini` in the
current working directory or in `~/.skoolkit`, if present. The recognised
configuration parameters are:

* ``TraceLine`` - the format of each instruction line when ``-v`` is used
  (default: ``${pc:04X} {i}``)
* ``TraceLine2`` - the format of each instruction line when ``-vv`` is used
  (use ``--show-config`` to see the default value)
* ``TraceLineDecimal`` - the format of each instruction line when ``-Dv`` is
  used (default: ``{pc:05} {i}``)
* ``TraceLineDecimal2`` - the format of each instruction line when ``-Dvv`` is
  used (use ``--show-config`` to see the default value)
* ``TraceOperand`` - the prefix, byte format, and word format for the numeric
  operands of instructions, separated by commas (default: ``$,02X,04X``); the
  byte and word formats are standard Python format specifiers for numeric
  values, and default to empty strings if not supplied
* ``TraceOperandDecimal`` - as ``TraceOperand`` when ``-D`` is used (default:
  ``,,``)

The ``TraceLine*`` parameters are standard Python format strings that recognise
the following replacement fields:

* ``i`` - the current instruction
* ``m[address]`` - the contents of a memory address
* ``pc`` - the address of the current instruction (program counter)
* ``r[X]`` - the 'X' register (see below)
* ``t`` - the current timestamp (in T-states)

When using the ``m`` (memory) replacement field, ``address`` must be either a
decimal number, or a hexadecimal number prefixed by '$' or '0x'.

The register name ``X`` in ``r[X]`` must be one of the following::

  a b c d e f h l bc de hl
  ^a ^b ^c ^d ^e ^f ^h ^l ^bc ^de ^hl
  ix ixh ixl iy iyh iyl
  i r sp

The names that begin with ``^`` denote the shadow registers.

Wherever ``\n`` appears in a ``TraceLine*`` parameter value, it is replaced by
a newline character.

Configuration parameters must appear in a ``[trace]`` section. For example,
to make `trace.py` write a timestamp for each instruction when ``-v`` is used,
add the following section to `skoolkit.ini`::

  [trace]
  TraceLine={t:>10} ${pc:04X} {i}

Configuration parameters may also be set on the command line by using the
``--ini`` option. Parameter values set this way will override any found in
`skoolkit.ini`.

+---------+-------------------------------------------------------------------+
| Version | Changes                                                           |
+=========+===================================================================+
| 9.3     | Added the ``--state`` option; added support for writing a WAV     |
|         | file after execution has completed; added support for the ``m``   |
|         | (memory) replacement field in the ``TraceLine*`` configuration    |
|         | parameters                                                        |
+---------+-------------------------------------------------------------------+
| 9.2     | Added the ``--python`` option; added support for +2 snapshots     |
+---------+-------------------------------------------------------------------+
| 9.1     | The ``--poke`` option can modify specific RAM banks; added the    |
|         | ``--cmio`` option                                                 |
+---------+-------------------------------------------------------------------+
| 9.0     | Configuration is read from `skoolkit.ini` if present; added the   |
|         | ``--ini``, ``--no-interrupts`` and ``--show-config`` options;     |
|         | interrupt routines are executed by default; added support for     |
|         | 128K snapshots; added support for writing SZX snapshots; added    |
|         | the ``-m`` and ``-M`` short options                               |
+---------+-------------------------------------------------------------------+
| 8.9     | Reads and writes the T-states counter in Z80 snapshots and reads  |
|         | the T-states counter in SZX snapshots                             |
+---------+-------------------------------------------------------------------+
| 8.8     | New                                                               |
+---------+-------------------------------------------------------------------+
