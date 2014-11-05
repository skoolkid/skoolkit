#!/usr/bin/env python
import sys
import os
from collections import deque

GIF89A = [71, 73, 70, 56, 57, 97]

PALETTE = {
    (0, 254, 0): 'TRANSPARENT',
    (0, 0, 0): 'BLACK',
    (0, 0, 197): 'BLUE',
    (197, 0, 0): 'RED',
    (197, 0, 197): 'MAGENTA',
    (0, 198, 0): 'GREEN',
    (0, 198, 197): 'CYAN',
    (197, 198, 0): 'YELLOW',
    (205, 198, 205): 'WHITE',
    (0, 0, 255): 'BRIGHT_BLUE',
    (255, 0, 0): 'BRIGHT_RED',
    (255, 0, 255): 'BRIGHT_MAGENTA',
    (0, 255, 0): 'BRIGHT_GREEN',
    (0, 255, 255): 'BRIGHT_CYAN',
    (255, 255, 0): 'BRIGHT_YELLOW',
    (255, 255, 255): 'BRIGHT_WHITE'
}

class GIFError(Exception):
    pass

def _byte_str(data, hex=False):
    fmt = '{:X}' if hex else '{}'
    return ','.join(fmt.format(b) for b in data)

def _to_int(data):
    return 256 * data[1] + data[0]

def _to_chars(data):
    return ''.join(chr(b) for b in data)

def _bin_str(num, num_bits=8):
    return ''.join(['1' if num & (1 << (n - 1)) else '0' for n in range(num_bits, 0, -1)])

def parse_args(args):
    p_args = []
    show_diff = False
    debug = False
    i = 0
    while i < len(args):
        arg = args[i]
        if arg == '-a':
            pass
        elif arg == '-d':
            show_diff = True
        elif arg == '--debug':
            debug = True
        elif arg.startswith('-'):
            show_usage()
        else:
            p_args.append(arg)
        i += 1
    if (show_diff and len(p_args) != 2) or (not show_diff and len(p_args) != 1):
        show_usage()
    return p_args, show_diff, debug

def show_usage():
    sys.stderr.write("""
Usage: {0} [options] FILE
       {0} -d FILE FILE

  Analyse a GIF file, or compare two GIF files.

Available options:
  -a       Show a detailed analysis of the file (default)
  -d       Show the differences in appearance between two images
  --debug  Show LZW-decoding debug info
""".lstrip().format(os.path.basename(sys.argv[0])))
    sys.exit()

class Frame:
    def __init__(self):
        self.x = None
        self.y = None
        self.width = None
        self.height = None
        self.delay = None
        self.gce_flags = None
        self.tc_index = None
        self.image_desc_flags = None
        self.pixels = []

class GifInfo:
    def __init__(self):
        self.width = None
        self.height = None
        self.bg_colour_index = None
        self.pixel_aspect_ratio = None
        self.palette = []
        self.frames = []

def _get_gif_info(data):
    magic_number = data[:6]
    if magic_number != GIF89A:
        raise GIFError("Invalid magic number: {}".format(magic_number))

    gif_info = GifInfo()
    gif_info.width = _to_int(data[6:8])
    gif_info.height = _to_int(data[8:10])
    gct_flags = data[10]
    palette_size = 1 << 1 + (gct_flags & 7)
    gif_info.pixel_aspect_ratio = data[12]
    for i in range(13, 13 + 3 * palette_size, 3):
        gif_info.palette.append(data[i:i + 3])
    i = 13 + 3 * palette_size
    gif_info.bg_colour = gif_info.palette[data[11]]

    if data[i:i + 2] == [33, 255]:
        # Application Extension Block
        i += 2
        while data[i]:
            i += 1 + data[i]
        i += 1

    while True:
        if data[i:i + 2] == [33, 249]:
            # Graphic Control Extension
            frame = Frame()
            i += 2
            length = data[i]
            i += 1
            frame.gce_flags = data[i]
            frame.delay = _to_int(data[i + 1:i + 3])
            frame.tc_index = data[i + 3]
            i += 1 + length
            gif_info.frames.append(frame)
        elif data[i] == 44:
            # Image descriptor
            frame = gif_info.frames[-1]
            frame.x = _to_int(data[i + 1:i + 3])
            frame.y = _to_int(data[i + 3:i + 5])
            frame.width = _to_int(data[i + 5:i + 7])
            frame.height = _to_int(data[i + 7:i + 9])
            frame.image_desc_flags = data[i + 9]
            i += 10
            min_code_size = data[i]
            i += 1
            lzw_data = []
            while True:
                length = data[i]
                i += 1
                if length == 0:
                    # End of image data
                    break
                lzw_data.extend(data[i:i + length])
                i += length
            output, lzw_bits = _decode_lzw_data(min_code_size, lzw_data)
            j = 0
            while j < len(output):
                frame.pixels.append([gif_info.palette[p] for p in output[j:j + frame.width]])
                j += frame.width
        elif data[i] == 59:
            # GIF trailer
            break
        else:
            # Unknown block
            raise GIFError("Unknown block ID: {}".format(data[i]))

    return gif_info

def show_diffs(fname1, bytes1, fname2, bytes2):
    diffs = []
    gif_info1 = _get_gif_info(bytes1)
    gif_info2 = _get_gif_info(bytes2)

    if gif_info1.width != gif_info2.width:
        diffs.append('width: {}, {}'.format(gif_info1.width, gif_info2.width))
    if gif_info1.height != gif_info2.height:
        diffs.append('height: {}, {}'.format(gif_info1.height, gif_info2.height))
    if gif_info1.bg_colour != gif_info2.bg_colour:
        diffs.append('background colour: {}, {}'.format(gif_info1.bg_colour, gif_info2.bg_colour))
    if gif_info1.pixel_aspect_ratio != gif_info2.pixel_aspect_ratio:
        diffs.append('pixel aspect ratio: {}, {}'.format(gif_info1.pixel_aspect_ratio, gif_info2.pixel_aspect_ratio))
    if len(gif_info1.frames) != len(gif_info2.frames):
        diffs.append('frames: {}, {}'.format(len(gif_info1.frames), len(gif_info2.frames)))
    if not diffs:
        for i, (f1, f2) in enumerate(zip(gif_info1.frames, gif_info2.frames), 1):
            frame_diffs = []
            if f1.width != f2.width:
                frame_diffs.append('frame {} width: {}, {}'.format(i, f1.width, f2.width))
            if f1.height != f2.height:
                frame_diffs.append('frame {} height: {}, {}'.format(i, f1.height, f2.height))
            if f1.x != f2.x:
                frame_diffs.append('frame {} x-offset: {}, {}'.format(i, f1.x, f2.x))
            if f1.y != f2.y:
                frame_diffs.append('frame {} y-offset: {}, {}'.format(i, f1.y, f2.y))
            if f1.delay != f2.delay:
                frame_diffs.append('frame {} delay: {}, {}'.format(i, f1.delay, f2.delay))
            if f1.gce_flags != f2.gce_flags:
                frame_diffs.append('frame {} GCE flags: {}, {}'.format(i, f1.gce_flags, f2.gce_flags))
            if f1.tc_index != f2.tc_index:
                frame_diffs.append('frame {} transparent colour index: {}, {}'.format(i, f1.tc_index, f2.tc_index))
            if f1.image_desc_flags != f2.image_desc_flags:
                frame_diffs.append('frame {} Image Descriptor flags: {}, {}'.format(i, f1.image_desc_flags, f2.image_desc_flags))
            if frame_diffs:
                diffs.extend(frame_diffs)
            else:
                for y, (row1, row2) in enumerate(zip(f1.pixels, f2.pixels)):
                    for x, (rgb1, rgb2) in enumerate(zip(row1, row2)):
                        if rgb1 != rgb2:
                            diffs.append('frame {}, pixel at ({},{}): {}, {}'.format(i, x, y, rgb1, rgb2))

    if diffs:
        print(fname1)
        print(fname2)
        for line in diffs:
            print('  {}'.format(line))

def _print_aeb(data, i):
    aeb_header = data[i:i + 2]
    print('{:5d} {} (Application Extension Block)'.format(i, _byte_str(aeb_header)))
    i += 2
    length = data[i] # Should be 11
    print('{0:5d} {1} ({1} bytes follow)'.format(i, length))
    i += 1
    app_name = _to_chars(data[i:i + 8])
    print('{:5d} {} (application name: {})'.format(i, _byte_str(data[i:i + 8]), app_name))
    i += 8
    auth_code = _to_chars(data[i:i + 3])
    print('{:5d} {} (authentication code: {})'.format(i, _byte_str(data[i:i + 3]), auth_code))
    i += 3
    while True:
        length = data[i]
        if length == 0:
            print('{:5d} {} (end)'.format(i, length))
            return i + 1
        print('{0:5d} {1} ({1} bytes follow)'.format(i, length))
        i += 1
        block = data[i:i + length]
        j = 0
        while j < len(block):
            blocklet = block[j:j + 16]
            print('{:5d} {}'.format(i, _byte_str(blocklet)))
            i += len(blocklet)
            j += len(blocklet)

def _print_gce(data, i):
    gce_header = data[i:i + 2]
    print('{:5d} {} (Graphic Control Extension)'.format(i, _byte_str(gce_header)))
    i += 2
    length = data[i] # Should be 4
    print('{0:5d} {1} ({1} bytes follow)'.format(i, length))
    i += 1
    flags = data[i]
    print('{:5d} {} (flags)'.format(i, flags))
    i += 1
    delay = data[i:i + 2]
    print('{:5d} {} (delay={}/100)'.format(i, _byte_str(delay), _to_int(delay)))
    i += 2
    tc_index = data[i]
    print('{:5d} {} (transparent colour index)'.format(i, tc_index))
    i += 1
    end = data[i] # Should be 0
    print('{:5d} {} (end)'.format(i, end))
    return i + 1

def _print_img_desc(data, i):
    id_header = data[i]
    print('{:5d} {} (Image descriptor)'.format(i, id_header))
    i += 1
    left_x = data[i:i + 2]
    print('{:5d} {} (top-left corner x={})'.format(i, _byte_str(left_x), _to_int(left_x)))
    i += 2
    top_y = data[i:i + 2]
    print('{:5d} {} (top-left corner y={})'.format(i, _byte_str(top_y), _to_int(top_y)))
    i += 2
    img_width = data[i:i + 2]
    print('{:5d} {} (image width={})'.format(i, _byte_str(img_width), _to_int(img_width)))
    i += 2
    img_height = data[i:i + 2]
    print('{:5d} {} (image height={})'.format(i, _byte_str(img_height), _to_int(img_height)))
    i += 2
    flags = data[i]
    print('{:5d} {} (flags)'.format(i, flags))
    return i + 1, _to_int(img_width)

def _print_lzw_block(data, i, lzw_blocks, width):
    min_code_size = data[i]
    print('{:5d} {} (minimum code size)'.format(i, min_code_size))
    i += 1
    all_lzw_data = []
    while True:
        length = data[i]
        if length == 0:
            print('{:5d} {} (end of image data)'.format(i, length))
            lzw_blocks.append((min_code_size, width, all_lzw_data))
            return i + 1
        print('{0:5d} {1} ({1} bytes of LZW data follow)'.format(i, length))
        i += 1
        lzw_data = data[i:i + length]
        all_lzw_data.extend(lzw_data)
        j = 0
        while j < len(lzw_data):
            blocklet = lzw_data[j:j + 16]
            print('{:5d} {}'.format(i, _byte_str(blocklet)))
            i += len(blocklet)
            j += len(blocklet)

def _decode_lzw_data(min_code_size, lzw_data, debug=False):
    # Initialise the dictionary
    clear_code = 1 << min_code_size
    stop_code = clear_code + 1
    init_d = {}
    for n in range(clear_code):
        init_d[n] = (n,)
    init_d[clear_code] = 0
    init_d[stop_code] = 0
    d = {}

    lzw_bits = deque()
    for lzw_byte in lzw_data:
        for j in range(8):
            lzw_bits.appendleft(lzw_byte & 1)
            lzw_byte >>= 1

    code_size = min_code_size + 1
    code_count = 0
    output = []
    prefix = None
    while 1:
        if debug:
            print('Bits remaining to decode: {}'.format(len(lzw_bits)))
        if len(lzw_bits) < code_size:
            if debug:
                print('Unexpected end of LZW stream')
            break

        code = 0
        m = 1
        for k in range(code_size):
            code += m * lzw_bits.pop()
            m *= 2
        code_count += 1

        if code == clear_code:
            if debug:
                print('  Code #{}: {}={} (CLEAR)'.format(code_count, code, _bin_str(code, code_size)))
            d = init_d.copy()
            code_size = min_code_size + 1
            prefix = None
            if debug:
                print('  Initialised dictionary')
            continue
        elif code == stop_code:
            if debug:
                print('  Code #{}: {}={} (STOP)'.format(code_count, code, _bin_str(code, code_size)))
            break

        if debug:
            print('  Code #{}: {}={}'.format(code_count, code, _bin_str(code, code_size)))

        out = d[code]
        if out is None:
            out = prefix + prefix[0:1]
            d[code] = out
            if debug:
                print('  Added entry for code {}: {}'.format(code, out))
        else:
            if prefix:
                d[len(d) - 1] = prefix + out[0:1]
            if debug:
                print('  Added entry for code {}: {}'.format(len(d) - 1, d[len(d) - 1]))
        if debug:
            print('  Added to output: {}'.format(out))
            print('  Dictionary size: {}'.format(len(d)))

        # Increase the code size if necessary
        if len(d) == 1 << code_size and len(lzw_bits) > code_size and code_size < 12:
            code_size += 1
            if debug:
                print('  Increased code size to {}'.format(code_size))

        output.extend(out)
        prefix = out
        d[len(d)] = None

    return output, lzw_bits

def _print_pixels(lzw_block, index):
    min_code_size, width, lzw_data = lzw_block
    print('----- Image data, frame {}, width={} (decompressed) -----'.format(index, width))

    output, lzw_bits = _decode_lzw_data(min_code_size, lzw_data, debug)

    if debug and lzw_bits:
        print('Bits remaining in LZW stream: {}'.format(''.join(str(b) for b in lzw_bits)))

    x = y = j = 0
    block_len = min((32, width))
    while j < len(output):
        blocklet = output[j:j + block_len]
        print('({:3d},{:3d}) {}'.format(x, y, _byte_str(blocklet, True)))
        x += block_len
        if x >= width:
            x -= width
            y += 1
        j += len(blocklet)

def analyse_gif(data):
    lzw_blocks = []

    magic_number = data[:6]
    if magic_number != GIF89A:
        raise GIFError("Invalid magic number: {}".format(magic_number))

    print('{:5d} {} {}'.format(0, _byte_str(magic_number), _to_chars(magic_number)))
    print('')

    i = 6
    ls_width = data[i:i + 2]
    print('{:5d} {} (logical screen width={})'.format(i, _byte_str(ls_width), _to_int(ls_width)))
    i = 8
    ls_height = data[i:i + 2]
    print('{:5d} {} (logical screen height={})'.format(i, _byte_str(ls_height), _to_int(ls_height)))
    print('')

    i = 10
    gct_flags = data[i]
    palette_size = 1 << 1 + (gct_flags & 7)
    print('{:5d} {} (GCT flags; palette size={})'.format(i, gct_flags, palette_size))
    i = 11
    bg_colour = data[i]
    print('{:5d} {} (background colour index)'.format(i, bg_colour))
    i = 12
    pa_ratio = data[i]
    print('{:5d} {} (pixel aspect ratio)'.format(i, pa_ratio))
    p = 0
    for i in range(13, 13 + 3 * palette_size, 3):
        entry = tuple(data[i:i + 3])
        print('{:5d} {} (palette entry {}: {})'.format(i, _byte_str(entry), p, PALETTE.get(entry, 'UNKNOWN')))
        p += 1
    i = 13 + 3 * palette_size
    print('')

    if data[i:i + 2] == [33, 255]:
        i = _print_aeb(data, i)
        print('')

    while True:
        if data[i:i + 2] == [33, 249]:
            # Graphic Control Extension
            i = _print_gce(data, i)
            print('')
        elif data[i] == 44:
            # Image descriptor
            i, width = _print_img_desc(data, i)
            print('')
            i = _print_lzw_block(data, i, lzw_blocks, width)
            print('')
        elif data[i] == 59:
            gif_trailer = data[i]
            print('{:5d} {} (GIF trailer)'.format(i, gif_trailer))
            break
        else:
            print('{:5d} {}... UNKNOWN'.format(i, _byte_str(data[i:i + 8])))
            break

    for j, lzw_block in enumerate(lzw_blocks):
        print('')
        _print_pixels(lzw_block, j + 1)

###############################################################################
# Begin
###############################################################################
files, show_diff, debug = parse_args(sys.argv[1:])

file_data = []
for infile in files:
    with open(infile, 'rb') as f:
        file_data.append(list(bytearray(f.read()))) # PY: 'list(f.read())' in Python 3

try:
    if show_diff:
        show_diffs(files[0], file_data[0], files[1], file_data[1])
    else:
        analyse_gif(file_data[0])
except GIFError as e:
    sys.stderr.write('ERROR: {}\n'.format(e.args[0]))
