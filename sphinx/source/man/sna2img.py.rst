:orphan:

==========
sna2img.py
==========

SYNOPSIS
========
``sna2img.py`` [options] INPUT [OUTPUT]

DESCRIPTION
===========
``sna2img.py`` converts a Spectrum screenshot (or a portion of it) into a PNG
or GIF file. INPUT may be a SCR file, or a SNA, SZX or Z80 snapshot.

OPTIONS
=======
-f N, --flip N
  Flip the image horizontally (N=1), vertically (N=2), or both (N=3).

-i, --invert
  Invert video and reset the FLASH bit for cells that are flashing.

-n, --no-animation
  Do not animate flashing cells.

-o X,Y, --origin X,Y
  Top-left crop the image at tile coordinates (X,Y).

-p, --poke `a[-b[-c]],[^+]v`
  POKE N,v for N in {a, a+c, a+2c..., b}. Prefix 'v' with '^' to perform an
  XOR operation, or '+' to perform an ADD operation. This option may be used
  multiple times.

-r N, --rotate N
  Rotate the image 90*N degrees clockwise.

-s SCALE, --scale SCALE
  Set the scale of the image (default=1).

-S WxH, --size WxH
  Crop the image to this width and height (in tiles).

-V, --version
  Show the SkoolKit version number and exit.

EXAMPLES
========
1. Convert ``game.scr`` into a PNG file named ``game.png``:

   |
   |   ``sna2img.py game.scr``

2. Convert the screenshot in ``game.z80`` into a GIF file named ``scr.gif`` at
   scale 2:

   |
   |   ``sna2im.py -s 2 game.z80 scr.gif``
