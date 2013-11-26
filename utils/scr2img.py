#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import os

# Use the current development version of SkoolKit
SKOOLKIT_HOME = os.environ.get('SKOOLKIT_HOME')
if not SKOOLKIT_HOME:
    sys.stderr.write('SKOOLKIT_HOME is not set; aborting\n')
    sys.exit(1)
if not os.path.isdir(SKOOLKIT_HOME):
    sys.stderr.write('SKOOLKIT_HOME={0}; directory not found\n'.format(SKOOLKIT_HOME))
    sys.exit(1)
sys.path.insert(0, SKOOLKIT_HOME)

from skoolkit.image import ImageWriter, GIF_ENABLE_ANIMATION, PNG_ENABLE_ANIMATION
from skoolkit.snapshot import get_snapshot
from skoolkit.skoolhtml import Udg, Frame

def get_screen_udg(scr, row, col):
    attr = scr[6144 + 32 * row + col]
    address = 2048 * (row // 8) + 32 * (row % 8) + col
    udg_bytes = [scr[address + 256 * n] for n in range(8)]
    return Udg(attr, udg_bytes)

def get_screenshot(scr, x=0, y=0, w=32, h=24, flip=False):
    scr_udgs = []
    for r in range(y, y + h):
        scr_udgs.append([])
        for c in range(x, x + w):
            udg = get_screen_udg(scr, r, c)
            if flip:
                udg.flip()
                scr_udgs[-1].insert(0, udg)
            else:
                scr_udgs[-1].append(udg)
    return scr_udgs

def get_block_array(udg_array):
    # Convert UDG array into byte array
    byte_array = []
    for row in udg_array:
        for line in range(8):
            byte_array.append([(udg.attr, udg.data[line]) for udg in row])

    # Convert byte array into pixel array
    pixel_array = []
    for row in byte_array:
        pixel_array.append([])
        for attr, byte in row:
            bright = (attr & 64) // 8
            ink = bright + (attr & 7)
            paper = bright + (attr & 56) // 8
            for b in range(8):
                if byte & 128:
                    pixel_array[-1].append((ink, 1, 1))
                else:
                    pixel_array[-1].append((paper, 1, 1))
                byte *= 2

    return pixel_array

def get_bb_coords(snapshot):
    blackboard = None
    width = 10
    if snapshot[53792] == 128:
        # Back to Skool
        leftcol = snapshot[32767]
        eric_x, eric_y = snapshot[53761:53763]
        if eric_y <= 3:
            # Top floor
            if 2 <= eric_x <= 10:
                blackboard = (2, 2, width, 5)
            elif 40 <= eric_x <= 48:
                blackboard = (40 - leftcol, 2, width, 5)
            elif 160 <= eric_x <= 168:
                blackboard = (160 - leftcol, 2, width, 5)
        elif eric_y <= 10:
            # Middle floor
            if 31 <= eric_x <= 39:
                blackboard = (31 - leftcol, 8, width, 6)
            elif 160 <= eric_x <= 168:
                blackboard = (160 - leftcol, 8, width, 6)
    elif snapshot[56084] == 0:
        # Skool Daze
        leftcol = snapshot[32512]
        eric_y, eric_x = snapshot[44129:44131]
        if 152 <= eric_y <= 155:
            # Top floor
            if 41 <= eric_x <= 49:
                blackboard = (41 - leftcol, 2, width, 5)
        elif 156 <= eric_y <= 162:
            # Middle floor
            if 25 <= eric_x <= 33:
                blackboard = (25 - leftcol, 8, width, 6)
            elif 40 <= eric_x <= 48:
                blackboard = (40 - leftcol, 8, width, 6)
    else:
        sys.stderr.write("ERROR: Unrecognised snapshot\n")
        sys.exit(1)
    if not blackboard:
        sys.stderr.write("ERROR: Cannot identify blackboard next to Eric\n")
        sys.exit(1)
    return blackboard

def write_image(udgs, img_file, scale, no_anim):
    iw_options = {}
    if no_anim:
        iw_options[GIF_ENABLE_ANIMATION] = 0
        iw_options[PNG_ENABLE_ANIMATION] = 0
    image_writer = ImageWriter(options=iw_options)
    image_format = 'gif' if img_file.lower()[-4:] == '.gif' else 'png'
    frame = Frame(udgs, scale)
    with open(img_file, "wb") as f:
        image_writer.write_image([frame], f, image_format)

def parse_args(args):
    x, y = 0, 0
    w, h = 32, 24
    scale = 1
    pokes = []
    flip = False
    no_anim = False
    invert = False
    files = []

    i = 0
    while i < len(args):
        arg = args[i]
        if arg == '-xy':
            x, y = [int(c) for c in args[i + 1].split(',')]
            i += 1
        elif arg == '-wh':
            w, h = [int(c) for c in args[i + 1].split(',')]
            i += 1
        elif arg == '-s':
            scale = int(args[i + 1])
            i += 1
        elif arg == '-p':
            addr, val = args[i + 1].split(',', 1)
            pokes.append((addr, int(val)))
            i += 1
        elif arg == '-bb':
            x = None
        elif arg == '-f':
            flip = True
        elif arg == '-na':
            no_anim = True
        elif arg == '-i':
            invert = True
        else:
            files.append(arg)
        i += 1

    if x is not None:
        w = min((32 - x, w))
        h = min((24 - y, h))
    return scale, x, y, w, h, flip, no_anim, invert, pokes, files

###############################################################################
# Begin
###############################################################################
scale, x, y, w, h, flip, no_anim, invert, pokes, files = parse_args(sys.argv[1:])
if not (0 < len(files) < 3):
    sys.stderr.write("""Usage: {} [options] INPUT [OUTPUT]

  Convert a Spectrum screenshot (or a portion of it) to a PNG or GIF file.
  INPUT may be a SCR file, or a SNA, Z80 or SZX snapshot.

Options:
  -s N            Set scale to N (default=1)
  -p a[-b[-c]],v  Do POKE N,v for N in {{a,a+c,a+2c...,b}} (may be used multiple
                  times)
  -xy X,Y         Set top-left to (X,Y)
  -wh W,H         Set width and height to (W,H)
  -bb             Create an image of the blackboard next to Eric (in Skool Daze
                  or Back to Skool)
  -f              Flip the image
  -na             Do not create an animated PNG or GIF for a screenshot that
                  contains flashing cells
  -i              Invert video for cells that are flashing
""".format(os.path.basename(sys.argv[0])))
    sys.exit(1)

infile = files[0]
if len(files) > 1:
    outfile = files[1]
elif infile[-4:].lower() in ('.sna', '.z80', '.szx', '.scr'):
    outfile = "{}.png".format(os.path.basename(infile[:-4]))
else:
    outfile = "{}.png".format(os.path.basename(infile))

if infile[-4:].lower() == '.scr':
    snapshot = [0] * 65536
    with open(infile, 'rb') as f:
        scr = bytearray(f.read(6912))
    snapshot[16384:16384 + len(scr)] = list(scr)
else:
    snapshot = get_snapshot(infile)

for addr, val in pokes:
    step = 1
    if type(addr) is int:
        addr1 = addr
        addr2 = addr1
    elif '-' in addr:
        addr1, addr2 = addr.split('-', 1)
        addr1 = int(addr1)
        if '-' in addr2:
            addr2, step = [int(i) for i in addr2.split('-', 1)]
        else:
            addr2 = int(addr2)
    else:
        addr1 = int(addr)
        addr2 = addr1
    addr2 += 1
    value = val if type(val) is int else val(addr1)
    for a in range(addr1, addr2, step):
        snapshot[a] = value

scr = snapshot[16384:23296]

if invert:
    # Invert any character squares with the FLASH bit set
    for i in range(6144, 6912):
        if scr[i] & 128:
            df = 2048 * (i // 256 - 24) + i % 256
            for j in range(df, df + 2048, 256):
                scr[j] ^= 255
            scr[i] -= 128

if x is None:
    x, y, w, h = get_bb_coords(snapshot)

scrshot = get_screenshot(scr, x, y, w, h, flip)
write_image(scrshot, outfile, scale, no_anim)
