#!/usr/bin/env python
import sys
import os
import zlib

PY3 = sys.version_info >= (3,)

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

class PNGError(Exception):
    pass

def _byte_str(data):
    return ','.join(str(b) for b in data)

def _to_int(data):
    if len(data) == 4:
        return 16777216 * data[0] + 65536 * data[1] + 256 * data[2] + data[3]
    return 256 * data[0] + data[1]

def _to_chars(data):
    return ''.join(chr(b) for b in data)

def decompress(data):
    if PY3:
        return list(zlib.decompress(bytes(data)))
    return [ord(c) for c in zlib.decompress(bytes(bytearray(data)))]

def parse_args(args):
    p_args = []
    show_diff = False
    show_filters = False
    i = 0
    while i < len(args):
        arg = args[i]
        if arg == '-a':
            pass
        elif arg == '-d':
            show_diff = True
        elif arg == '-f':
            show_filters = True
        elif arg.startswith('-'):
            show_usage()
        else:
            p_args.append(arg)
        i += 1
    if (show_diff and len(p_args) != 2) or (not show_diff and len(p_args) != 1):
        show_usage()
    return p_args, show_diff, show_filters

def show_usage():
    sys.stderr.write("""
Usage: {0} [options] FILE
       {0} -d FILE FILE

  Analyse a PNG file, or compare two PNG files.

Available options:
  -a  Show a detailed analysis of the file (default)
  -d  Show the differences in appearance between two images
  -f  Show the filter types used in the image data
""".lstrip().format(os.path.basename(sys.argv[0])))
    sys.exit()

def _paeth(a, b, c):
    p = a + b - c
    pa = abs(p - a)
    pb = abs(p - b)
    pc = abs(p - c)
    if pa <= pb and pa <= pc:
        return a
    if pb <= pc:
        return b
    return c

def _get_png_info(data):
    width = height = None
    palette = []
    pixels = []

    idat_data = []
    i = 0
    while i < len(data):
        if i == 0:
            i = 8 # Signature
            continue
        chunk_length = _to_int(data[i:i + 4])
        chunk_type = _to_chars(data[i + 4:i + 8])
        chunk_data = data[i + 8:i + 8 + chunk_length]
        if chunk_type == 'IHDR':
            # See http://www.libpng.org/pub/png/spec/iso/index-object.html#11IHDR
            width = _to_int(chunk_data[:4])
            height = _to_int(chunk_data[4:8])
            bit_depth = chunk_data[8]
        elif chunk_type == 'PLTE':
            # See http://www.libpng.org/pub/png/spec/iso/index-object.html#11PLTE
            j = 0
            while j < chunk_length:
                entry = chunk_data[j:j + 3]
                palette.append(entry)
                j += len(entry)
        elif chunk_type == 'IDAT':
            # See http://www.libpng.org/pub/png/spec/iso/index-object.html#11IDAT
            idat_data.extend(data[i + 8:i + 8 + chunk_length])
        i += 8 + chunk_length + 4

    u_data = decompress(idat_data)

    if bit_depth == 4:
        scanline_len = 2 + width // 2 if width & 1 else 1 + width // 2
    elif bit_depth == 2:
        scanline_len = 2 + width // 4 if width & 3 else 1 + width // 4
    else:
        scanline_len = 2 + width // 8 if width & 7 else 1 + width // 8

    scanline = [0] * scanline_len
    for i, byte in enumerate(u_data):
        s_index = i % scanline_len
        if s_index == 0:
            if i:
                pixels.append(pixel_row[:width])
            filter_type = byte
            if filter_type > 4:
                raise PNGError('Invalid filter type {0}'.format(filter_type))
            pixel_row = []
            prev_scanline = scanline
            scanline = [0]
            continue

        if filter_type == 1:
            # Sub
            byte += scanline[s_index - 1]
        elif filter_type == 2:
            # Up
            byte += prev_scanline[s_index]
        elif filter_type == 3:
            # Average
            byte += (scanline[s_index - 1] + prev_scanline[s_index]) // 2
        elif filter_type == 4:
            # Paeth
            byte += _paeth(scanline[s_index - 1], prev_scanline[s_index], prev_scanline[s_index - 1])
        byte &= 255
        scanline.append(byte)

        if bit_depth == 4:
            pixel_row.append(palette[(byte & 240) // 16])
            pixel_row.append(palette[byte & 15])
        elif bit_depth == 2:
            for b in range(4):
                pixel_row.append(palette[(byte & 192) // 64])
                byte *= 4
        else:
            for b in range(8):
                pixel_row.append(palette[(byte & 128) // 128])
                byte *= 2
    pixels.append(pixel_row[:width])

    return width, height, pixels

def show_diffs(fname1, data1, fname2, data2):
    diffs = []
    try:
        w1, h1, p1 = _get_png_info(data1)
    except zlib.error:
        diffs.append('Error while decompressing data: {}'.format(fname1))
        w1, h1, p1 = 0, 0, []
    try:
        w2, h2, p2 = _get_png_info(data2)
    except zlib.error:
        diffs.append('Error while decompressing data: {}'.format(fname2))
        w2, h2, p2 = 0, 0, []

    if not diffs:
        if w1 != w2:
            diffs.append('width: {}, {}'.format(w1, w2))
        if h1 != h2:
            diffs.append('height: {}, {}'.format(h1, h2))
        if not diffs:
            for y, (row1, row2) in enumerate(zip(p1, p2)):
                for x, (rgb1, rgb2) in enumerate(zip(row1, row2)):
                    if rgb1 != rgb2:
                        diffs.append('pixel at ({},{}): {}, {}'.format(x, y, rgb1, rgb2))

    if diffs:
        print(fname1)
        print(fname2)
        for line in diffs:
            print('  {}'.format(line))

def analyse_filters(data):
    idat_data = []
    i = 0
    while i < len(data):
        if i == 0:
            # Signature
            i = 8
            continue
        chunk_length = _to_int(data[i:i + 4])
        i += 4
        chunk_type = _to_chars(data[i:i + 4])
        i += 4
        if chunk_type == 'IHDR':
            chunk_data = data[i:i + chunk_length]
            width = _to_int(chunk_data[:4])
            height = _to_int(chunk_data[4:8])
            bit_depth = chunk_data[8]
        elif chunk_type == 'IDAT':
            idat_data.extend(data[i:i + chunk_length])
        i += chunk_length
        i += 4 # Jump over chunk CRC

    u_data = decompress(idat_data)

    if bit_depth == 8:
        scanline_len = 1 + width
    elif bit_depth == 4:
        scanline_len = 2 + width // 2 if width & 1 else 1 + width // 2
    elif bit_depth == 2:
        scanline_len = 2 + width // 4 if width & 3 else 1 + width // 4
    elif bit_depth == 1:
        scanline_len = 2 + width // 8 if width & 7 else 1 + width // 8

    filters = set()
    j = 0
    for i in range(height):
        filters.add(u_data[j])
        j += scanline_len

    sorted_filters = list(filters)
    sorted_filters.sort()
    print(', '.join(str(f) for f in sorted_filters))

def analyse_png(data):
    idat_data = []
    fdat_data = []
    i = 0
    while i < len(data):
        if i == 0:
            print('{:5d} {} (signature)'.format(i, _byte_str(data[i:8])))
            i = 8
            continue
        chunk_length_bytes = data[i:i + 4]
        chunk_length = _to_int(chunk_length_bytes)
        print('\n{:5d} {} (chunk length: {})'.format(i, _byte_str(chunk_length_bytes), chunk_length))
        i += 4
        chunk_type_bytes = data[i:i + 4]
        chunk_type = _to_chars(chunk_type_bytes)
        print('{:5d} {} (chunk type: {})'.format(i, _byte_str(chunk_type_bytes), chunk_type))
        i += 4
        chunk_data = data[i:i + chunk_length]
        if chunk_type == 'IHDR':
            # See http://www.libpng.org/pub/png/spec/iso/index-object.html#11IHDR
            width_bytes = chunk_data[:4]
            width = _to_int(width_bytes)
            print('{:5d} {} (width: {})'.format(i, _byte_str(width_bytes), width))
            height = chunk_data[4:8]
            print('{:5d} {} (height: {})'.format(i + 4, _byte_str(height), _to_int(height)))
            bit_depth = chunk_data[8]
            print('{:5d} {} (bit depth)'.format(i + 8, bit_depth))
            print('{:5d} {} (colour type)'.format(i + 9, chunk_data[9]))
            print('{:5d} {} (compression method)'.format(i + 10, chunk_data[10]))
            print('{:5d} {} (filter method)'.format(i + 11, chunk_data[11]))
            print('{:5d} {} (interlace method)'.format(i + 12, chunk_data[12]))
            i += chunk_length
        elif chunk_type == 'PLTE':
            # See http://www.libpng.org/pub/png/spec/iso/index-object.html#11PLTE
            j = 0
            p = 1
            num_entries = chunk_length // 3
            while j < chunk_length:
                entry = tuple(chunk_data[j:j + 3])
                print('{:5d} {} (palette entry {}/{}: {})'.format(i, _byte_str(entry), p, num_entries, PALETTE.get(entry, 'UNKNOWN')))
                i += len(entry)
                j += len(entry)
                p += 1
        elif chunk_type == 'acTL':
            # See https://wiki.mozilla.org/APNG_Specification#.60acTL.60:_The_Animation_Control_Chunk
            num_frames = chunk_data[:4]
            num_plays = chunk_data[4:8]
            print('{:5d} {} (num_frames: {})'.format(i, _byte_str(num_frames), _to_int(num_frames)))
            print('{:5d} {} (num_plays: {})'.format(i + 4, _byte_str(num_plays), _to_int(num_plays)))
            i += chunk_length
        elif chunk_type == 'fcTL':
            # See https://wiki.mozilla.org/APNG_Specification#.60fcTL.60:_The_Frame_Control_Chunk
            sequence_number = chunk_data[:4]
            f_width = chunk_data[4:8]
            f_height = chunk_data[8:12]
            x_offset = chunk_data[12:16]
            y_offset = chunk_data[16:20]
            delay_num = chunk_data[20:22]
            delay_den = chunk_data[22:24]
            dispose_op = chunk_data[24]
            blend_op = chunk_data[25]
            print('{:5d} {} (sequence_number: {})'.format(i, _byte_str(sequence_number), _to_int(sequence_number)))
            print('{:5d} {} (width: {})'.format(i + 4, _byte_str(f_width), _to_int(f_width)))
            print('{:5d} {} (height: {})'.format(i + 8, _byte_str(f_height), _to_int(f_height)))
            print('{:5d} {} (x_offset: {})'.format(i + 12, _byte_str(x_offset), _to_int(x_offset)))
            print('{:5d} {} (y_offset: {})'.format(i + 16, _byte_str(y_offset), _to_int(y_offset)))
            print('{:5d} {} (delay_num: {})'.format(i + 20, _byte_str(delay_num), _to_int(delay_num)))
            print('{:5d} {} (delay_den: {})'.format(i + 22, _byte_str(delay_den), _to_int(delay_den)))
            print('{:5d} {} (dispose_op: {})'.format(i + 24, dispose_op, dispose_op))
            print('{:5d} {} (blend_op: {})'.format(i + 25, blend_op, blend_op))
            i += chunk_length
        elif chunk_type in ('IDAT', 'fdAT'):
            # See http://www.libpng.org/pub/png/spec/iso/index-object.html#11IDAT
            # See https://wiki.mozilla.org/APNG_Specification#.60fdAT.60:_The_Frame_Data_Chunk
            if chunk_type == 'IDAT':
                idat_data.extend(chunk_data)
            else:
                sequence_number = chunk_data[:4]
                chunk_data = chunk_data[4:]
                print('{:5d} {} (sequence number: {})'.format(i, _byte_str(sequence_number), _to_int(sequence_number)))
                i += 4
                fdat_data.extend(chunk_data)
            print('{:5d} {} (zlib compression method/flags)'.format(i, chunk_data[0]))
            print('{:5d} {} (additional flags/check bits)'.format(i + 1, chunk_data[1]))
            i += 2
            compressed_data = chunk_data[2:-4]
            j = 0
            while j < len(compressed_data):
                chunklet = compressed_data[j:j + 8]
                print('{:5d} {} (deflated chunk data)'.format(i, _byte_str(chunklet)))
                i += len(chunklet)
                j += len(chunklet)
            zlib_crc = chunk_data[-4:]
            print('{:5d} {} (zlib CRC)'.format(i, _byte_str(zlib_crc)))
            i += 4
        else:
            j = 0
            while j < len(chunk_data):
                chunklet = chunk_data[j:j + 8]
                print('{:5d} {} (chunk data)'.format(i, _byte_str(chunklet)))
                i += len(chunklet)
                j += len(chunklet)
        chunk_crc = data[i:i + 4]
        print('{:5d} {} (chunk CRC)'.format(i, _byte_str(chunk_crc)))
        i += 4

    if bit_depth == 4:
        scanline_len = 2 + width // 2 if width & 1 else 1 + width // 2
    elif bit_depth == 2:
        scanline_len = 2 + width // 4 if width & 3 else 1 + width // 4
    else:
        scanline_len = 2 + width // 8 if width & 7 else 1 + width // 8
    block_len = min(16, scanline_len)

    u_data = decompress(idat_data)
    print('\n----- IDAT data (decompressed) -----')
    j = 0
    while j < len(u_data):
        blocklet = u_data[j:j + block_len]
        print('    {}'.format(_byte_str(blocklet)))
        j += len(blocklet)

    if fdat_data:
        u_data = decompress(fdat_data)
        print('\n----- fdAT data (decompressed) -----')
        j = 0
        while j < len(u_data):
            blocklet = u_data[j:j + block_len]
            print('    {}'.format(_byte_str(blocklet)))
            j += len(blocklet)

###############################################################################
# Begin
###############################################################################
files, show_diff, show_filters = parse_args(sys.argv[1:])

file_data = []
for infile in files:
    with open(infile, 'rb') as f:
        file_data.append(list(bytearray(f.read()))) # PY: 'list(f.read())' in Python 3

if show_filters:
    analyse_filters(file_data[0])
elif show_diff:
    try:
        show_diffs(files[0], file_data[0], files[1], file_data[1])
    except PNGError as e:
        sys.stderr.write('ERROR: {0}\n'.format(e.args[0]))
else:
    analyse_png(file_data[0])
