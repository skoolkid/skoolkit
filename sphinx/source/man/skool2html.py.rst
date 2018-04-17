:orphan:

=============
skool2html.py
=============

SYNOPSIS
========
``skool2html.py`` [options] SKOOLFILE [REFFILE...]

DESCRIPTION
===========
``skool2html.py`` converts a skool file and ref files to HTML. When SKOOLFILE
is '-', ``skool2html.py`` reads from standard input.

OPTIONS
=======
-1, --asm-one-page
  Write all routines and data blocks to a single page. This option is shorthand
  for ``-c Game/AsmSinglePageTemplate=AsmAllInOne``.

-a, --asm-labels
  Use ASM labels (defined by ``@label`` directives).

-c, --config `S/L`
  Add the line `L` to the ref file section `S`; this option may be used
  multiple times.

-C, --create-labels
  Create default labels for unlabelled instructions. This option is intended
  for use alongside the ``-a`` option.

-d, --output-dir `DIR`
  Specify the directory in which to write files; the default output directory
  is the current working directory.

-D, --decimal
  Write the disassembly in decimal.

-H, --hex
  Write the disassembly in hexadecimal.

-I, --ini `param=value`
  Set the value of a configuration parameter (see ``CONFIGURATION``),
  overriding any value found in ``skoolkit.ini``. This option may be used
  multiple times.

-j, --join-css `NAME`
  Concatenate CSS files into a single file with this name.

-l, --lower
  Write the disassembly in lower case.

-o, --rebuild-images
  Overwrite existing image files.

-p, --package-dir
  Show the path to the skoolkit package directory and exit.

-P, --pages `PAGES`
  Write only these pages (when using ``--write P``); `PAGES` is a
  comma-separated list of page IDs.

-q, --quiet
  Be quiet.

-r, --ref-sections `PREFIX`
  Show the default ref file sections whose names start with `PREFIX` and exit.

-R, --ref-file
  Show the entire default ref file and exit.

-s, --search-dirs
  Show the locations that ``skool2html.py`` searches for resources.

-S, --search `DIR`
  Add this directory to the resource search path; this option may be used
  multiple times.

--show-config
  Show configuration parameter values.

-t, --time
  Show timings.

-T, --theme `THEME`
  Specify the CSS theme to use; this option may be used multiple times. See the
  section on ``THEMES`` below.

-u, --upper
  Write the disassembly in upper case.

--var `name=value`
  Define a variable that can be used by the ``@if`` directive and the ``#IF``
  and ``#MAP`` macros. This option may be used multiple times.

-V, --version
  Show the SkoolKit version number and exit.

-w, --write `X`
  Write only these files, where `X` is one or more of:

  |
  |   ``d`` = Disassembly files   ``o`` = Other code
  |   ``i`` = Disassembly index   ``P`` = Other pages
  |   ``m`` = Memory maps

-W, --writer `CLASS`
  Specify the HTML writer class to use; this option is shorthand for
  ``--config Config/HtmlWriterClass=CLASS``.

FILES
=====
``skool2html.py`` searches the following directories for ref files, CSS files,
JavaScript files, font files, and files listed in the [Resources] section of
the ref file:

|
| - The directory containing the skool file named on the command line
| - The current working directory
| - ./resources
| - ~/.skoolkit
| - $PACKAGE_DIR/resources
| - Any other directories specified by the ``-S``/``--search`` option

where $PACKAGE_DIR is the directory in which the skoolkit package is installed
(as shown by ``skool2html.py -p``). When you need a reminder of these
locations, run ``skool2html.py -s``.

THEMES
======
The ``-T`` option sets the CSS theme. For example, if ``game.ref`` specifies
the CSS files to use thus:

|
|   [Game]
|   StyleSheet=skoolkit.css;game.css

then:

|
|   ``skool2html.py -T dark -T wide game.skool``

will use the following CSS files, if they exist, in the order listed:

|
|   skoolkit.css
|   skoolkit-dark.css
|   skoolkit-wide.css
|   game.css
|   game-dark.css
|   game-wide.css
|   dark.css
|   wide.css

CONFIGURATION
=============
``skool2html.py`` will read configuration from a file named ``skoolkit.ini`` in
the current working directory or in ``~/.skoolkit``, if present. The recognised
configuration parameters are:

:AsmLabels: Use ASM labels (``1``), or don't (``0``, the default).
:AsmOnePage: Write all routines and data blocks to a single page (``1``), or to
  multiple pages (``0``, the default).
:Base: Convert addresses and instruction operands to hexadecimal (``16``) or
  decimal (``10``), or leave them as they are (``0``, the default).
:Case: Write the disassembly in lower case (``1``) or upper case (``2``), or
  leave it as it is (``0``, the default).
:CreateLabels: Create default labels for unlabelled instructions (``1``), or
  don't (``0``, the default).
:JoinCss: If specified, concatenate CSS files into a single file with this
  name.
:OutputDir: Write files in this directory (default: ``.``).
:Quiet: Be quiet (``1``) or verbose (``0``, the default).
:RebuildImages: Overwrite existing image files (``1``), or leave them alone
  (``0``, the default).
:Search: Directory to add to the resource search path. To specify two or more
  directories, separate them with commas.
:Theme: CSS theme to use. To specify two or more themes, separate them with
  commas.
:Time: Show timings (``1``), or don't (``0``, the default).

Configuration parameters must appear in a ``[skool2html]`` section. For
example, to make ``skool2html.py`` use ASM labels and write the disassembly in
hexadecimal by default (without having to use the ``-H`` and ``-a`` options on
the command line), add the following section to ``skoolkit.ini``::

  [skool2html]
  AsmLabels=1
  Base=16

Configuration parameters may also be set on the command line by using the
``--ini`` option. Parameter values set this way will override any found in
``skoolkit.ini``.

EXAMPLES
========
1. Build the entire HTML disassembly for 'game':

   |
   |   ``skool2html.py game.skool``

2. Build the entire HTML disassembly for 'game' in lower case, using
   hexadecimal notation, in the ``html`` directory:

   |
   |   ``skool2html.py -d html -l -H game.skool``

3. Write only the 'Bugs' and 'Pokes' pages for 'game':

   |
   |   ``skool2html.py -w P -P Bugs,Pokes game.skool``
