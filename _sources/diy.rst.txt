.. _disassemblyDIY:

Disassembly DIY
===============
The following sections describe how to use SkoolKit to get started on your own
Spectrum game disassembly.

Getting started
---------------
The first thing to do is select a Spectrum game to disassemble. For the purpose
of this discussion, we'll use `Hungry Horace`_. To build a pristine snapshot of
the game, run the following command in the directory where SkoolKit was
unpacked::

  $ tap2sna.py @examples/hungry_horace.t2s

(If that doesn't work, or you prefer to make your own snapshot, just grab a
copy of the game, load it in an emulator, and save a Z80 snapshot named
`hungry_horace.z80`.)

The next thing to do is create a skool file from this snapshot. Run the
following command from the SkoolKit directory::

  $ sna2skool.py hungry_horace.z80 > hungry_horace.skool

Note that the '.skool' file name suffix is merely a convention, not a
requirement. In general, any suffix besides '.ref' (which is used by
`skool2html.py` to identify ref files) will do. If you are fond of the
traditional three-letter suffix, then perhaps '.sks' (for 'SkoolKit source') or
'.kit' would be more to your liking. However, for the purpose of this
particular tutorial, it would be best to stick with '.skool'.

Now take a look at `hungry_horace.skool`. As you can see, by default,
`sna2skool.py` disassembles everything from 16384 to 65535, treating it all as
code. Needless to say, this is not particularly useful - unless you have no
idea where the code and data blocks are yet, and want to use this disassembly
to find out.

Once you have figured out where the code and data blocks are, it would be handy
if you could supply `sna2skool.py` with this information, so that it can
disassemble the blocks accordingly. That is where the control file comes in.

.. _Hungry Horace: https://spectrumcomputing.co.uk/entry/2390/

The control file
----------------
In its most basic form, a control file contains a list of start addresses of
code and data blocks. Each address is marked with a 'control directive', which
is a single letter that indicates what the block contains: ``c`` for a code
block, or ``b`` for a data block (for example). A control file may contain
annotations too, which will be interpreted as routine titles, descriptions,
instruction-level comments or whatever else depending on the control directive
they accompany.

A control file for Hungry Horace might start like this::

  b 16384 Loading screen
  i 23296
  c 24576 The game has just loaded
  c 25167
  ...

This control file declares that there is:

* a data block at 16384 titled 'Loading screen'
* a block at 23296 that should be ignored
* a code block (routine) at 24576 titled 'The game has just loaded'
* another code block at 25167

For more information on control file directives and their syntax, see
:ref:`controlFiles`.

A skeleton disassembly
----------------------
So if we had a control file for Hungry Horace, we could produce a much more
useful skool file. As it happens, SkoolKit includes one: `hungry_horace.ctl`.
You can use it with `sna2skool.py` thus::

  $ sna2skool.py -c examples/hungry_horace.ctl hungry_horace.z80 > hungry_horace.skool

This time, `hungry_horace.skool` is split up into meaningful blocks, with code
as code, data as data (DEFBs), and text as text (DEFMs). Much nicer.

By default, `sna2skool.py` produces a disassembly with addresses and
instruction operands in decimal notation. If you prefer to work in hexadecimal,
use the ``--hex`` option::

  $ sna2skool.py --hex -c examples/hungry_horace.ctl hungry_horace.z80 > hungry_horace.skool

The next step is to create an HTML disassembly from this skool file::

  $ skool2html.py hungry_horace.skool

Now open `hungry_horace/index.html` in a web browser. There's not much there,
but it's a base from which you can start adding explanatory comments.

In order to replace 'hungry_horace' in the page titles and headers with
something more appropriate, or add a game logo image, or otherwise customise
the disassembly, we need to create a ref file. Again, as it happens, SkoolKit
includes an example ref file for Hungry Horace: `hungry_horace.ref`. To use it
with the skool file we've just created::

  $ skool2html.py hungry_horace.skool examples/hungry_horace.ref

Now the disassembly will sport a game logo image.

See :ref:`refFiles` for more information on how to use a ref file to configure
and customise a disassembly.

Generating a control file
-------------------------
If you are planning to create a disassembly of some game other than Hungry
Horace, you will need to create your own control file. To get started, you can
use :ref:`sna2ctl.py` to perform a rudimentary static code analysis of the
snapshot file and generate a corresponding control file::

  $ sna2ctl.py game.z80 > game.ctl
  $ sna2skool.py -c game.ctl game.z80 > game.skool

This will do a reasonable job of splitting the snapshot into blocks, but won't
be 100% accurate (except by accident). You will need to examine the resultant
skool file (`game.skool`) to see which blocks have been incorrectly marked as
text, data or code, and then edit the control file (`game.ctl`) accordingly.

To generate a better control file, you could use a code execution map produced
by an emulator to tell `sna2ctl.py` where at least some of the code is in the
snapshot. `sna2ctl.py` will read a map (otherwise known as a profile or trace)
produced by Fuse, SpecEmu, Spud, Zero or Z80 when specified by the ``-m``
option::

  $ sna2ctl.py -m game.map game.z80 > game.ctl

Needless to say, in general, the better the map, the more accurate the
resulting control file will be. To create a good map file, you should ideally
play the game from start to finish in the emulator, in an attempt to exercise
as much code as possible. If that sounds like too much work, and your emulator
supports playing back RZX files, you could grab a recording of your chosen game
from the `RZX Archive <https://rzxarchive.co.uk>`_, and set the emulator's
profiler or tracer going while the recording plays back.

By default, `sna2ctl.py` and `sna2skool.py` generate control files and skool
files with addresses and instruction operands in decimal notation. If you
prefer to work in hexadecimal, use the ``--hex`` option of each command to
produce a hexadecimal control file and a hexadecimal skool file::

  $ sna2ctl.py --hex game.z80 > game.ctl
  $ sna2skool.py --hex -c game.ctl game.z80 > game.skool

Developing the disassembly
--------------------------
When you're happy that your control file does a decent job of distinguishing
the code blocks from the data blocks in your memory snapshot, it's time to
start work on adding annotations that describe what the code does and what the
data is for.

Figuring out what the code blocks do and what the data blocks contain can be a
time-consuming job. It's probably not a good idea to go through each block one
by one, in order, and move to the next only when it’s fully documented - unless
you're looking for a nervous breakdown. Instead it's better to approach the job
like this:

1. Skim the code blocks for any code whose purpose is familiar or obvious,
   such as drawing something on the screen, or producing a sound effect.
2. Document that code (and any related data) as far as possible.
3. Find another code block that calls the code block just documented, and
   figure out when, why and how it uses it.
4. Document that code (and any related data) as far as possible.
5. If there’s anything left to document, return to step 3.
6. Done!

It also goes without saying that figuring out what a piece of code or data
might be used for is easier if you’ve played the game to death already.

As for where to write annotations, you now have a choice. You can add them
either to the control file or to the skool file. The recommended approach,
unless you are already familiar with the syntax of skool files, is to add
annotations to the control file. The benefits of continuing to work on the
control file are:

* its syntax is much simpler than that of the skool file
* you are never in danger of breaking the skool file, and potentially causing
  :ref:`skool2asm.py` and :ref:`skool2html.py` to fail
* if you ever need to modify how an address range is disassembled, it is
  usually as simple as replacing one letter (e.g. ``c`` for code) with another
  (e.g. ``t`` for text)

If you would rather edit the skool file, however, then it is highly recommended
to do so only for the purpose of adding, removing or updating annotations.
Don't be tempted to manually convert code to data, or vice versa. Unless
extreme care is taken, doing so could easily result in a broken skool file that
is very difficult to fix.

Annotating the code and data in a skool file is done by adding comments just as
you would in a regular assembly language source file. For example, you might
add a comment to the instruction at 26429 in `hungry_horace.skool` thus:

.. parsed-literal::
   :class: nonexistent

    26429 DEC A         ; Decrement the number of lives

See the :ref:`skool file format <skoolFileFormat>` reference for a full
description of the kinds of annotations that are supported in skool files.
Note also that SkoolKit supports many :ref:`skool macros <skoolMacros>` that
can be used in comments and will be converted into hyperlinks and images (for
example) in the HTML version of the disassembly.

As you become more familiar with the layout of the code and data blocks in the
disassembly, you may find that some blocks need to be split up, joined, or
otherwise reorganised. If you are working on the skool file, the best way to do
this is to regenerate the skool file from a new control file. To ensure that
you don't lose all the annotations you've already added to the skool file,
though, you should use :ref:`skool2ctl.py <skool2ctl.py>` to preserve them.

First, create a control file that keeps your annotations intact::

  $ skool2ctl.py game.skool > game-2.ctl

Now edit `game-2.ctl` to fit your better understanding of the layout of the
code and data blocks. Then generate a new skool file::

  $ sna2skool.py -c game-2.ctl game.z80 > game-2.skool

This new skool file, `game-2.skool`, will contain your reorganised code and
data blocks, and all the annotations you carefully added to `game.skool`.

Adding pokes, bugs and trivia
-----------------------------
Adding 'Pokes', 'Bugs', and 'Trivia' pages to a disassembly is done by adding
:ref:`[Poke:*] <boxpages>`, :ref:`[Bug:*] <boxpages>`, and
:ref:`[Fact:*] <boxpages>` sections to the ref file. For any such sections that
are present, `skool2html.py` will add links to the disassembly index page.

For example, let's add a poke. Add the following lines to `hungry_horace.ref`::

  [Poke:infiniteLives:Infinite lives]
  The following POKE gives Horace infinite lives:

  POKE 26429,0

Now run `skool2html.py` again::

  $ skool2html.py hungry_horace.skool examples/hungry_horace.ref

Open `hungry_horace/index.html` and you will see a link to the 'Pokes' page in
the 'Reference' section.

The format of a ``Bug`` or ``Fact`` section is the same, except that the
section name prefix is ``Bug:`` or ``Fact:`` (instead of ``Poke:``) as
appropriate.

Add one ``Poke``, ``Bug`` or ``Fact`` section for each poke, bug or trivia
entry to be documented. Entries will appear on the 'Pokes', 'Bugs' or 'Trivia'
page in the same order as the sections appear in the ref file.

See :ref:`refFiles` for more information on the format of the ``Poke``,
``Bug``, and ``Fact`` (and other) sections that may appear in a ref file.

Themes
------
In addition to the default theme (defined in `skoolkit.css`), SkoolKit includes
some alternative themes:

* dark (dark colours): `skoolkit-dark.css`
* green (mostly green): `skoolkit-green.css`
* plum (mostly purple): `skoolkit-plum.css`
* wide (wide comment fields on the disassembly pages, and wide boxes on the
  Changelog, Glossary, Trivia, Bugs and Pokes pages): `skoolkit-wide.css`

In order to use a theme, run `skool2html.py` with the ``-T`` option; for
example, to use the 'dark' theme::

  $ skool2html.py -T dark game.skool

Themes may be combined; for example, to use both the 'plum' and 'wide' themes::

  $ skool2html.py -T plum -T wide game.skool

Base switching
--------------
If you would like to build both decimal and hexadecimal versions of your
disassembly in HTML format and have them link to each other, then one possible
approach is to define a custom page footer that contains a link to the
corresponding page in the alternative disassembly.

An example of such a page footer can be found in *examples/bases.ref*, and the
required Python code that generates the appropriate link for each page can be
found in *examples/bases.py*. To use *bases.ref* and *bases.py* with your
disassembly, first place copies of them alongside your existing skool and ref
files. Then::

  $ skool2html.py -D -c Config/GameDir=html/dec -c Config/InitModule=:bases game.skool bases.ref
  $ skool2html.py -H -c Config/GameDir=html/hex -c Config/InitModule=:bases game.skool bases.ref

The first command here builds the decimal version of the disassembly in the
directory *html/dec*, and the second command builds the hexadecimal version in
the directory *html/hex*. The footer of each page in the decimal version will
contain a link to the corresponding page in the hexadecimal version, and vice
versa.
