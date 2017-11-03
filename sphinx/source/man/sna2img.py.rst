:orphan:

==========
sna2img.py
==========

SYNOPSIS
========
``sna2img.py`` [options] INPUT [OUTPUT]

DESCRIPTION
===========
``sna2img.py`` converts a Spectrum screenshot or other graphic data into a PNG
or GIF file. INPUT may be a binary (raw memory) file, a SCR file, a skool file,
or a SNA, SZX or Z80 snapshot.

OPTIONS
=======
-b, --bfix
  When INPUT is a skool file, parse it in @bfix mode.

-B, --binary
  Read INPUT as a binary (raw memory) file.

-e, --expand `MACRO`
  Expand a #FONT, #SCR, #UDG or #UDGARRAY macro. The '#' prefix may be omitted,
  and any filename parameter is ignored.

-f, --flip `N`
  Flip the image horizontally (N=1), vertically (N=2), or both (N=3).

-i, --invert
  Invert video and reset the FLASH bit for cells that are flashing.

-m, --move `src,size,dest`
  Move a block of bytes of the given size from 'src' to 'dest'. This option may
  be used multiple times. 'src', 'size' and 'dest' must each be a decimal
  number, or a hexadecimal number prefixed by '0x'.

-n, --no-animation
  Do not animate flashing cells.

-o, --origin `X,Y`
  Top-left crop the image at tile coordinates (X,Y).

-O, --org `ORG`
  Set the origin address of a binary file. This option implies ``--binary``.
  The default origin address is 65536 minus the length of the file. `ORG` must
  be a decimal number, or a hexadecimal number prefixed by '0x'.

-p, --poke `a[-b[-c]],[^+]v`
  POKE N,v for N in {a, a+c, a+2c..., b}. Prefix 'v' with '^' to perform an
  XOR operation, or '+' to perform an ADD operation. This option may be used
  multiple times. 'a', 'b', 'c' and 'v' must each be a decimal number, or a
  hexadecimal number prefixed by '0x'.

-r, --rotate `N`
  Rotate the image 90*N degrees clockwise.

-s, --scale `SCALE`
  Set the scale of the image (default=1).

-S, --size `WxH`
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
   |   ``sna2img.py -s 2 game.z80 scr.gif``

3. Expand a #FONT macro and write the image to ``font.png``:

   |
   |   ``sna2img.py -e FONT32768,26 game.skool font.png``
