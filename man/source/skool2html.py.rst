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

-l, --lower
  Write the disassembly in lower case.

-o, --rebuild-images
  Overwrite existing image files.

-p, --package-dir
  Show the path to the skoolkit package directory and exit.

-P, --pages `PAGES`
  Specify the custom pages to write; `PAGES` should be a comma-separated list
  of IDs of pages defined in ``[Page:*]`` sections in the ref file(s).

-q, --quiet
  Be quiet.

-t, --time
  Show timings.

-T, --theme `THEME`
  Specify the CSS theme to use; see the section on ``THEMES`` below.

-u, --upper
  Write the disassembly in upper case.

-V, --version
  Show the SkoolKit version number and exit.

-w, --write `X`
  Write only these files, where `X` is one or more of:

  |
  |   ``B`` = Graphic glitches    ``m`` = Memory maps
  |   ``b`` = Bugs                ``o`` = Other code
  |   ``c`` = Changelog           ``P`` = Custom pages
  |   ``d`` = Disassembly files   ``p`` = Pokes
  |   ``G`` = Game status buffer  ``t`` = Trivia
  |   ``g`` = Graphics            ``y`` = Glossary
  |   ``i`` = Disassembly index

FILES
=====
When ``skool2html.py`` is run, it looks for skool files, ref files, CSS files,
JavaScript files and font files required by the disassembly in the following
directories, in the order listed:

|
| - The directory containing the skool/ref file named on the command line
| - The current working directory
| - ./resources
| - ~/.skoolkit
| - /usr/share/skoolkit
| - $PACKAGE_DIR/resources

where $PACKAGE_DIR is the directory in which the skoolkit package is installed
(as shown by ``skool2html.py -p``).

If an input file's name ends with '.ref', it will be treated as a ref file;
otherwise it will be treated as a skool file.

THEMES
======
The ``-T`` option sets the CSS theme. For example, if `game.ref` specifies the
CSS files to use thus:

|
|   [Paths]
|   StyleSheet=skoolkit.css;game.css

then:

|
|   ``skool2html.py -T dark game.ref``

will use `skoolkit-dark.css` and `game-dark.css` if they exist, and fall back
to `skoolkit.css` and `game.css` if they don't.

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

5. Build the HTML disassembly for 'game1' using the CSS file ``game.css``
   instead of the default ``skoolkit.css``:

   |
   |   ``skool2html.py -c Path/StyleSheet=game.css game1.ref``
