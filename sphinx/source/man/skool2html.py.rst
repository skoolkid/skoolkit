:orphan:

=============
skool2html.py
=============

SYNOPSIS
========
``skool2html.py`` [options] FILE [FILE...]

DESCRIPTION
===========
``skool2html.py`` converts source skool and ref files to HTML. When FILE is
'-', ``skool2html.py`` reads from standard input.

OPTIONS
=======
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

-j, --join-css `NAME`
  Concatenate CSS files into a single file with this name.

-l, --lower
  Write the disassembly in lower case.

-o, --rebuild-images
  Overwrite existing image files.

-p, --package-dir
  Show the path to the skoolkit package directory and exit.

-P, --pages `PAGES`
  Write only these custom pages (when using ``--write P``); `PAGES` is a
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

-t, --time
  Show timings.

-T, --theme `THEME`
  Specify the CSS theme to use; this option may be used multiple times. See the
  section on ``THEMES`` below.

-u, --upper
  Write the disassembly in upper case.

-V, --version
  Show the SkoolKit version number and exit.

-w, --write `X`
  Write only these files, where `X` is one or more of:

  |
  |   ``B`` = Graphic glitches    ``o`` = Other code
  |   ``b`` = Bugs                ``P`` = Custom pages
  |   ``c`` = Changelog           ``p`` = Pokes
  |   ``d`` = Disassembly files   ``t`` = Trivia
  |   ``i`` = Disassembly index   ``y`` = Glossary
  |   ``m`` = Memory maps

-W, --writer `CLASS`
  Specify the HTML writer class to use; this option is shorthand for
  ``--config Config/HtmlWriterClass=CLASS``.

FILES
=====
``skool2html.py`` searches the following directories for skool files, ref
files, CSS files, JavaScript files, font files, and files listed in the
[Resources] section of the ref file:

|
| - The directory containing the skool/ref file named on the command line
| - The current working directory
| - ./resources
| - ~/.skoolkit
| - $PACKAGE_DIR/resources
| - Any other directories specified by the ``-S``/``--search`` option

where $PACKAGE_DIR is the directory in which the skoolkit package is installed
(as shown by ``skool2html.py -p``). When you need a reminder of these
locations, run ``skool2html.py -s``.

If an input file's name ends with '.ref', it will be treated as a ref file;
otherwise it will be treated as a skool file.

THEMES
======
The ``-T`` option sets the CSS theme. For example, if ``game.ref`` specifies
the CSS files to use thus:

|
|   [Game]
|   StyleSheet=skoolkit.css;game.css

then:

|
|   ``skool2html.py -T dark -T wide game.ref``

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

EXAMPLES
========
1. Build the entire HTML disassembly for 'game1' from a ref file:

   |
   |   ``skool2html.py game1.ref``

2. Build the entire HTML disassembly for 'game2' from a skool file:

   |
   |   ``skool2html.py game2.skool``

3. Build the entire HTML disassemblies for 'game1' and 'game2', in lower case,
   using hexadecimal notation, in the ``html`` directory:

   |
   |   ``skool2html.py -d html -l -H game1.ref game2.skool``

4. Write only the 'Bugs', 'Pokes' and 'Trivia' pages for 'game1':

   |
   |   ``skool2html.py -w bpt game1.ref``
