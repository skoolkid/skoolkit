# -*- coding: utf-8 -*-

# Copyright 2013, 2015, 2016 Richard Dymond (rjdymond@gmail.com)
#
# This file is part of SkoolKit.
#
# SkoolKit is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later
# version.
#
# SkoolKit is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
# A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with
# SkoolKit. If not, see <http://www.gnu.org/licenses/>.

import sys
import os
import argparse
try:
    from __builtin__ import open
except ImportError: # pragma: no cover
    # Import this so that it can be mocked
    from builtins import open # pragma: no cover

from skoolkit import SkoolKitError, read_bin_file, VERSION
from skoolkit.image import ImageWriter, GIF_ENABLE_ANIMATION, PNG_ENABLE_ANIMATION
from skoolkit.snapshot import get_snapshot
from skoolkit.skoolhtml import Udg, Frame
from skoolkit.tap2sna import poke

def _get_screen_udg(scr, row, col):
    attr = scr[6144 + 32 * row + col]
    address = 2048 * (row // 8) + 32 * (row % 8) + col
    udg_bytes = [scr[address + 256 * n] for n in range(8)]
    return Udg(attr, udg_bytes)

def _get_screenshot(scr, x=0, y=0, w=32, h=24, flip=False):
    scr_udgs = []
    for r in range(y, y + h):
        scr_udgs.append([])
        for c in range(x, x + w):
            udg = _get_screen_udg(scr, r, c)
            if flip:
                udg.flip()
                scr_udgs[-1].insert(0, udg)
            else:
                scr_udgs[-1].append(udg)
    return scr_udgs

def _write_image(udgs, img_file, scale, animated):
    iw_options = {}
    if not animated:
        iw_options[GIF_ENABLE_ANIMATION] = 0
        iw_options[PNG_ENABLE_ANIMATION] = 0
    image_writer = ImageWriter(options=iw_options)
    image_format = 'gif' if img_file.lower()[-4:] == '.gif' else 'png'
    frame = Frame(udgs, scale)
    with open(img_file, "wb") as f:
        image_writer.write_image([frame], f, image_format)

def run(infile, outfile, options):
    x, y = [int(c) for c in options.origin.split(',', 1)]
    w, h = [int(c) for c in options.size.split('x', 1)]
    w = min(32 - x, w)
    h = min(24 - y, h)

    if infile[-4:].lower() == '.scr':
        scr = read_bin_file(infile, 6912)
        snapshot = [0] * 65536
        snapshot[16384:16384 + len(scr)] = scr
    else:
        snapshot = get_snapshot(infile)

    for spec in options.pokes:
        poke(snapshot, spec)

    scr = snapshot[16384:23296]

    if options.invert:
        for i in range(6144, 6912):
            if scr[i] & 128:
                df = 2048 * (i // 256 - 24) + i % 256
                for j in range(df, df + 2048, 256):
                    scr[j] ^= 255
                scr[i] -= 128

    scrshot = _get_screenshot(scr, x, y, w, h, options.flip)
    _write_image(scrshot, outfile, options.scale, options.animated)

def main(args):
    parser = argparse.ArgumentParser(
        usage='scr2img.py [options] INPUT [OUTPUT]',
        description="Convert a Spectrum screenshot (or a portion of it) into a PNG or GIF file. "
                    "INPUT may be a SCR file, or a SNA, SZX or Z80 snapshot.",
        add_help=False
    )
    parser.add_argument('infile', help=argparse.SUPPRESS, nargs='?')
    parser.add_argument('outfile', help=argparse.SUPPRESS, nargs='?')
    group = parser.add_argument_group('Options')
    group.add_argument('-f', '--flip', action='store_true',
                       help="Flip the image horizontally")
    group.add_argument('-i', '--invert', action='store_true',
                       help="Invert video for cells that are flashing")
    group.add_argument('-n', '--no-animation', dest='animated', action='store_false',
                       help="Do not animate flashing cells")
    group.add_argument('-o', '--origin', metavar='X,Y', default='0,0',
                       help="Top-left crop at (X,Y)")
    group.add_argument('-p', '--poke', dest='pokes', metavar='a[-b[-c]],v', action='append', default=[],
                       help='POKE N,v for N in {a, a+c, a+2c..., b} (this option may be used multiple times)')
    group.add_argument('-s', '--scale', type=int, default=1,
                       help="Set the scale of the image (default=1)")
    group.add_argument('-S', '--size', metavar='WxH', default='32,24',
                       help="Crop to this width and height (in tiles)")
    group.add_argument('-V', '--version', action='version', version='SkoolKit {}'.format(VERSION),
                       help='Show SkoolKit version number and exit')
    namespace, unknown_args = parser.parse_known_args(args)
    infile = namespace.infile
    if unknown_args or infile is None:
        parser.exit(2, parser.format_help())
    if infile[-4:].lower() not in ('.scr', '.sna', '.szx', '.z80'):
        raise SkoolKitError('Unrecognised input file type')
    outfile = namespace.outfile
    if outfile is None:
        outfile = os.path.basename(infile[:-4]) + '.png'
    run(infile, outfile, namespace)
