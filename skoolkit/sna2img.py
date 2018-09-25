# Copyright 2013, 2015-2018 Richard Dymond (rjdymond@gmail.com)
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

import os
import argparse
import re
from builtins import open

from skoolkit import SkoolKitError, integer, VERSION, skoolmacro
from skoolkit.image import ImageWriter, GIF_ENABLE_ANIMATION, PNG_ENABLE_ANIMATION
from skoolkit.snapshot import make_snapshot, move, poke
from skoolkit.graphics import Frame, flip_udgs, rotate_udgs, adjust_udgs, build_udg, font_udgs, scr_udgs
from skoolkit.skool2bin import BinWriter

def _parse_font(snapshot, param_str):
    end, crop_rect, fname, frame, alt, params = skoolmacro.parse_font(param_str)
    message, addr, chars, attr, scale = params
    udgs = font_udgs(snapshot, addr, attr, message[:chars])
    return Frame(udgs, scale, 0, *crop_rect)

def _parse_scr(snapshot, param_str):
    end, crop_rect, fname, frame, alt, params = skoolmacro.parse_scr(param_str)
    scale, x, y, w, h, df, af = params
    udgs = scr_udgs(snapshot, x, y, w, h, df, af)
    return Frame(udgs, scale, 0, *crop_rect)

def _parse_udg(snapshot, param_str):
    end, crop_rect, fname, frame, alt, params = skoolmacro.parse_udg(param_str)
    addr, attr, scale, step, inc, flip, rotate, mask, mask_addr, mask_step = params
    udgs = [[build_udg(snapshot, addr, attr, step, inc, flip, rotate, mask, mask_addr, mask_step)]]
    return Frame(udgs, scale, mask, *crop_rect)

def _parse_udgarray(snapshot, param_str):
    end, crop_rect, fname, frame, alt, params = skoolmacro.parse_udgarray(param_str, 0, snapshot, False)
    udg_array, scale, flip, rotate, mask = params
    udgs = adjust_udgs(udg_array, flip, rotate)
    return Frame(udgs, scale, mask, *crop_rect)

MACROS = {
    'FONT': _parse_font,
    'SCR': _parse_scr,
    'UDG': _parse_udg,
    'UDGARRAY': _parse_udgarray
}

def _int_pair(arg, sep, desc):
    try:
        pair = [int(c) for c in arg.split(sep, 1)]
        return (pair[0], pair[1])
    except (ValueError, IndexError):
        raise argparse.ArgumentTypeError("invalid {}: '{}'".format(desc, arg))

def _coords(arg):
    return _int_pair(arg, ',', 'coordinates')

def _dimensions(arg):
    return _int_pair(arg, 'x', 'dimensions')

def _write_image(frame, img_file, animated):
    iw_options = {}
    if not animated:
        iw_options[GIF_ENABLE_ANIMATION] = 0
        iw_options[PNG_ENABLE_ANIMATION] = 0
    image_writer = ImageWriter(options=iw_options)
    image_format = 'gif' if img_file.lower()[-4:] == '.gif' else 'png'
    with open(img_file, "wb") as f:
        image_writer.write_image([frame], f, image_format)

def run(infile, outfile, options):
    if options.binary or options.org is not None or infile[-4:].lower() in ('.sna', '.szx', '.z80'):
        snapshot = make_snapshot(infile, options.org)[0]
    elif infile[-4:].lower() == '.scr':
        snapshot = make_snapshot(infile, 16384)[0]
    else:
        try:
            snapshot = BinWriter(infile, fix_mode=options.fix_mode).snapshot
        except SkoolKitError:
            raise
        except:
            raise SkoolKitError('Unable to parse {} as a skool file'.format(infile))

    for spec in options.moves:
        move(snapshot, spec)
    for spec in options.pokes:
        poke(snapshot, spec)

    if options.macro is not None:
        match = re.match('(#?)(FONT|SCR|UDG|UDGARRAY)([^A-Z]|$)', options.macro)
        if match:
            macro = match.group(2)
            try:
                frame = MACROS[macro](snapshot, options.macro[match.end(2):])
            except skoolmacro.MacroParsingError as e:
                raise SkoolKitError('Invalid #{} macro: {}'.format(macro, e.args[0]))
        else:
            raise SkoolKitError('Macro must be #FONT, #SCR, #UDG or #UDGARRAY')
    else:
        (x, y), (w, h) = options.origin, options.size
        frame = Frame(scr_udgs(snapshot, x, y, w, h), options.scale)

    if options.invert:
        for row in frame.udgs:
            for udg in row:
                if udg.attr & 128:
                    udg.data = [b^255 for b in udg.data]
                    udg.attr &= 127

    flip_udgs(frame.udgs, options.flip)
    rotate_udgs(frame.udgs, options.rotate)

    _write_image(frame, outfile, options.animated)

def main(args):
    parser = argparse.ArgumentParser(
        usage='sna2img.py [options] INPUT [OUTPUT]',
        description="Convert a Spectrum screenshot or other graphic data into a PNG or GIF file. "
                    "INPUT may be a binary (raw memory) file, a SCR file, a skool file, or a SNA, SZX or Z80 snapshot.",
        add_help=False
    )
    parser.add_argument('infile', help=argparse.SUPPRESS, nargs='?')
    parser.add_argument('outfile', help=argparse.SUPPRESS, nargs='?')
    group = parser.add_argument_group('Options')
    group.add_argument('-b', '--bfix', dest='fix_mode', action='store_const', const=2, default=0,
                       help="Parse a skool file in @bfix mode.")
    group.add_argument('-B', '--binary', dest='binary', action='store_true',
                       help="Read the input as a binary (raw memory) file.")
    group.add_argument('-e', '--expand', dest='macro', metavar='MACRO',
                       help="Expand a #FONT, #SCR, #UDG or #UDGARRAY macro. The '#' prefix may be omitted.")
    group.add_argument('-f', '--flip', metavar='N', type=int, default=0,
                       help="Flip the image horizontally (N=1), vertically (N=2), or both (N=3).")
    group.add_argument('-i', '--invert', action='store_true',
                       help="Invert video for cells that are flashing.")
    group.add_argument('-m', '--move', dest='moves', metavar='src,size,dest', action='append', default=[],
                       help='Move a block of bytes of the given size from src to dest. This option may be used multiple times.')
    group.add_argument('-n', '--no-animation', dest='animated', action='store_false',
                       help="Do not animate flashing cells.")
    group.add_argument('-o', '--origin', metavar='X,Y', type=_coords, default='0,0',
                       help="Top-left crop at (X,Y).")
    group.add_argument('-O', '--org', dest='org', metavar='ORG', type=integer,
                       help="Set the origin address of a binary file (default: 65536 minus the length of the file).")
    group.add_argument('-p', '--poke', dest='pokes', metavar='a[-b[-c]],[^+]v', action='append', default=[],
                       help="POKE N,v for N in {a, a+c, a+2c..., b}. "
                            "Prefix 'v' with '^' to perform an XOR operation, or '+' to perform an ADD operation. "
                            "This option may be used multiple times.")
    group.add_argument('-r', '--rotate', metavar='N', type=int, default=0,
                       help="Rotate the image 90*N degrees clockwise.")
    group.add_argument('-s', '--scale', type=int, default=1,
                       help="Set the scale of the image (default=1).")
    group.add_argument('-S', '--size', metavar='WxH', type=_dimensions, default='32x24',
                       help="Crop to this width and height (in tiles).")
    group.add_argument('-V', '--version', action='version', version='SkoolKit {}'.format(VERSION),
                       help='Show SkoolKit version number and exit.')
    namespace, unknown_args = parser.parse_known_args(args)
    infile = namespace.infile
    if unknown_args or infile is None:
        parser.exit(2, parser.format_help())
    outfile = namespace.outfile
    if outfile is None:
        prefix, sep, suffix = infile.rpartition('.')
        outfile = os.path.basename(prefix or suffix) + '.png'
    run(infile, outfile, namespace)
