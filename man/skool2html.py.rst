=============
skool2html.py
=============

-----------------------------------
convert skool and ref files to HTML
-----------------------------------

:Author: rjdymond@gmail.com
:Date: 2013-05-07
:Manual section: 1

SYNOPSIS
========
``skool2html.py`` [options] FILE [FILE...]

DESCRIPTION
===========
``skool2html.py`` converts source skool and ref files to HTML. When FILE is
'-', ``skool2html.py`` reads from standard input.

OPTIONS
=======
-V       Show SkoolKit version number and exit
-p       Show path to skoolkit package directory and exit
-q       Be quiet
-t       Show timings
-d DIR   Write files in this directory
-o       Overwrite existing image files
-T THM   Use this CSS theme
-l       Write the disassembly in lower case
-u       Write the disassembly in upper case
-D       Write the disassembly in decimal
-H       Write the disassembly in hexadecimal
-c ARG   Add a line to a ref file section (where the format of `ARG` is
         SectionName/Line); this option may be used multiple times
-P IDS   Write only these custom pages (when ``-w P`` is specified); `IDS`
         should be a comma-separated list of IDs of pages defined in
         ``[Page:*]`` sections in the ref file(s)
-w X     Write only these pages, where ``X`` is one or more of:

         |
         |   ``B`` = Graphic glitches
         |   ``b`` = Bugs
         |   ``c`` = Changelog
         |   ``d`` = Disassembly files
         |   ``G`` = Game status buffer
         |   ``g`` = Graphics
         |   ``i`` = Disassembly index
         |   ``m`` = Memory maps
         |   ``o`` = Other code
         |   ``P`` = Pages defined in the ref file(s)
         |   ``p`` = Pokes
         |   ``t`` = Trivia
         |   ``y`` = Glossary

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
