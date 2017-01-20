# Copyright 2012-2014, 2016-2017 Richard Dymond (rjdymond@gmail.com)
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

import zlib

# http://www.libpng.org/pub/png/spec/iso/index-object.html
# https://wiki.mozilla.org/APNG_Specification
PNG_SIGNATURE = (137, 80, 78, 71, 13, 10, 26, 10)
IHDR = (73, 72, 68, 82)
PLTE = (80, 76, 84, 69)
TRNS = (116, 82, 78, 83)
ACTL_CHUNK = (0, 0, 0, 8, 97, 99, 84, 76, 0, 0, 0, 2, 0, 0, 0, 0, 243, 141, 147, 112)
FCTL = (102, 99, 84, 76)
IDAT = (73, 68, 65, 84)
FDAT = (102, 100, 65, 84)
IEND_CHUNK = (0, 0, 0, 0, 73, 69, 78, 68, 174, 66, 96, 130)
CRC_MASK = 4294967295

BITS4 = [[(n & m) // m for m in (8, 4, 2, 1)] for n in range(16)]
BITS8 = [[(n & m) // m for m in (128, 64, 32, 16, 8, 4, 2, 1)] for n in range(256)]
BIT_PAIRS = [((n & 192) >> 6, (n & 48) >> 4, (n & 12) >> 2, n & 3) for n in range(256)]
BIT_PAIRS2 = [[((n << m) & 128) // 64 + ((n << m) & 8) // 8 for m in range(4)] for n in range(256)]
BD4_MAP0 = (
    ((0, 1),),
    ((0, 2), (1, 2)),
    ((1, 2), (0, 2)),
    ((1, 1),)
)
BD4_MAP1 = (
    ((0, 1),),
    ((0, 2), (1, 0), (3, 2)),
    ((3, 2), (2, 0), (0, 2)),
    ((3, 1),)
)

BD_BYTES = {d: {1: [(i,) for i in range(256)]} for d in (1, 2, 4)}

def _get_bytes(depth, scale):
    bd_bytes = BD_BYTES.setdefault(depth, {})
    if scale not in bd_bytes:
        bd_bytes[scale] = []
        for p in ['{:08b}'.format(v) for v in range(256)]:
            if depth == 1:
                b = ''.join([d * scale for d in p])
            elif depth == 2:
                b = p[:2] * scale + p[2:4] * scale + p[4:6] * scale + p[6:] * scale
            else:
                b = p[:4] * scale + p[4:] * scale
            bd_bytes[scale].append(tuple([int(b[i:i + 8], 2) for i in range(0, len(b), 8)]))
    return bd_bytes[scale]

class PngWriter:
    def __init__(self, alpha=255, compression_level=9, masks=None):
        self.alpha = alpha
        self.compression_level = compression_level
        self.masks = masks
        self._create_crc_table()
        self._create_png_method_dict()
        self.trns = list(TRNS)
        self.png_signature = bytearray(PNG_SIGNATURE)
        self.actl_chunk = bytearray(ACTL_CHUNK)
        self.idat = bytearray(IDAT)
        self.fdat = bytearray(FDAT)
        self.fdat2 = bytearray(FDAT + (0, 0, 0, 2))
        self.iend_chunk = bytearray(IEND_CHUNK)

    def write_image(self, frames, img_file, palette, attr_map, has_trans, flash_rect):
        bit_depth, palette_size = self._get_bit_depth(palette)
        frame1 = frames[0]
        width, height = frame1.width, frame1.height
        frame1_data, frame2_data, frame2_rect = self._build_image_data(frame1, palette_size, bit_depth, attr_map, flash_rect)

        # PNG signature
        img_file.write(self.png_signature)

        # IHDR
        self._write_ihdr_chunk(img_file, width, height, bit_depth)

        # PLTE
        self._write_plte_chunk(img_file, palette)

        # tRNS
        if has_trans and self.alpha != 255:
            self._write_chunk(img_file, self.trns + [self.alpha])

        # acTL
        if len(frames) == 1 and flash_rect:
            img_file.write(self.actl_chunk)
        elif len(frames) > 1:
            actl_chunk = (97, 99, 84, 76, 0, 0, 0, len(frames), 0, 0, 0, 0)
            self._write_chunk(img_file, actl_chunk)

        # fcTL
        if len(frames) > 1 or flash_rect:
            seq_num = 0
            self._write_fctl_chunk(img_file, seq_num, frame1.delay, width, height)

        # IDAT
        self._write_img_data_chunk(img_file, self.idat + frame1_data)

        # fcTL and fdAT
        if len(frames) == 1 and flash_rect:
            f2_x_offset, f2_y_offset, f2_width, f2_height = frame2_rect
            self._write_fctl_chunk(img_file, 1, frame1.delay, f2_width, f2_height, f2_x_offset, f2_y_offset)
            self._write_img_data_chunk(img_file, self.fdat2 + frame2_data)
        for frame in frames[1:]:
            frame_data = self._build_image_data(frame, palette_size, bit_depth, attr_map)[0]
            seq_num += 1
            self._write_fctl_chunk(img_file, seq_num, frame.delay, frame.width, frame.height)
            seq_num += 1
            fdat = self.fdat + bytearray(self._to_bytes(seq_num))
            self._write_img_data_chunk(img_file, fdat + frame_data)

        # IEND
        img_file.write(self.iend_chunk)

    def _create_crc_table(self):
        self.crc_table = []
        for i in range(256):
            c = i
            for k in range(8):
                if c & 1:
                    c = 3988292384 ^ (c >> 1)
                else:
                    c = c >> 1
            self.crc_table.append(c)

    def _create_png_method_dict(self):
        # The PNG method dictionary is keyed on:
        #   bit_depth: 0 (1 colour), 1 (2 colours), 2 or 4
        #   full_size: 0 (cropped), 1 (full size)
        #      masked: 0 (unmasked), 1 (partially or fully masked)
        # and the values are 2-element tuples:
        #   (method1, method2)
        # where method1, if not None, returns the appropriate method to use to
        # build the image data (based on the number of UDGs, the number of
        # distinct attributes, and the scale); otherwise method2 is used to
        # build the image data

        # Create default values
        self.png_method_dict = {}
        default_methods = (None, self._build_image_data_bd_any)
        for bit_depth in (0, 1, 2, 4):
            bd_method_dict = self.png_method_dict[bit_depth] = {}
            for full_size in (0, 1):
                fs_method_dict = bd_method_dict[full_size] = {}
                for masked in (0, 1):
                    fs_method_dict[masked] = default_methods

        # Bit depth 0 (1 colour)
        bd0_methods = (None, self._build_image_data_bd0)
        bd0_fs_method_dict = self.png_method_dict[0][1]
        bd0_fs_method_dict[0] = bd0_methods # Unmasked
        bd0_fs_method_dict[1] = bd0_methods # Masked

        # Bit depth 1 (2 colours)
        bd1_fs_method_dict = self.png_method_dict[1][1]
        bd1_fs_method_dict[0] = (self._bd1_nt_method, None)           # Unmasked
        bd1_fs_method_dict[1] = (None, self._build_image_data_bd1_at) # Masked

        # Bit depth 2
        bd2_fs_method_dict = self.png_method_dict[2][1]
        bd2_fs_method_dict[0] = (None, self._build_image_data_bd2_nt) # Unmasked
        bd2_fs_method_dict[1] = (None, self._build_image_data_bd2_at) # Masked

        # Bit depth 4
        bd4_fs_method_dict = self.png_method_dict[4][1]
        bd4_fs_method_dict[0] = (self._bd4_nt_method, None)           # Unmasked
        bd4_fs_method_dict[1] = (None, self._build_image_data_bd_any) # Masked

    def _bd1_nt_method(self, frame):
        if frame.tiles == 1 and frame.scale < 10:
            return self._build_image_data_bd1_nt_1udg
        return self._build_image_data_bd1_nt

    def _bd4_nt_method(self, frame):
        if frame.scale == 1:
            min_index = 51
        elif frame.scale == 2:
            min_index = 80
        else:
            min_index = 230
        if frame.tiles / len(frame.attr_map) >= min_index:
            return self._build_image_data_bd4_nt1
        return self._build_image_data_bd4_nt2

    def _to_bytes(self, num):
        return (num >> 24, (num >> 16) & 255, (num >> 8) & 255, num & 255)

    def _write_ihdr_chunk(self, img_file, width, height, bit_depth):
        data = list(IHDR) # chunk type
        data.extend(self._to_bytes(width)) # width
        data.extend(self._to_bytes(height)) # height
        data.extend((bit_depth, 3)) # bit depth and colour type
        data.extend((0, 0, 0)) # compression, filter and interlace methods
        self._write_chunk(img_file, data)

    def _write_plte_chunk(self, img_file, palette):
        data = list(PLTE)
        data.extend(palette)
        self._write_chunk(img_file, data)

    def _write_fctl_chunk(self, img_file, seq_num, delay, width, height, x_offset=0, y_offset=0):
        data = list(FCTL) # chunk type
        data.extend(self._to_bytes(seq_num)) # sequence number
        data.extend(self._to_bytes(width)) # width
        data.extend(self._to_bytes(height)) # height
        data.extend(self._to_bytes(x_offset)) # x offset
        data.extend(self._to_bytes(y_offset)) # y offset
        data.extend((delay // 256, delay % 256)) # delay numerator
        data.extend((0, 100)) # delay denominator
        data.append(0) # frame disposal operation
        data.append(0) # frame blending operation
        self._write_chunk(img_file, data)

    def _get_bit_depth(self, palette):
        palette_size = len(palette) // 3
        if palette_size > 4:
            bit_depth = 4
        elif palette_size > 2:
            bit_depth = 2
        else:
            bit_depth = 1
        return bit_depth, palette_size

    def _build_image_data(self, frame, palette_size, bit_depth, attr_map, flash_rect=None):
        masked = frame.mask and frame.has_masks
        if masked:
            mask = self.masks[frame.mask]
        else:
            mask = self.masks[0]
        full_size = not frame.cropped
        if palette_size == 1:
            bd = 0
        else:
            bd = bit_depth
        method, build_method = self.png_method_dict[bd][full_size][masked]
        frame.attr_map = attr_map
        if method:
            build_method = method(frame)

        frame1 = build_method(frame, bit_depth=bit_depth, mask=mask)

        # Frame 2
        frame2 = frame2_rect = None
        if flash_rect:
            f2_x, f2_y, f2_w, f2_h = flash_rect
            if full_size:
                f2_frame = frame.swap_colours(f2_x, f2_y, f2_w, f2_h)
                sf = 8 * frame.scale
                frame2_rect = (f2_x * sf, f2_y * sf, f2_w * sf, f2_h * sf)
            else:
                f2_frame = frame.swap_colours(x=frame.x + f2_x, y=frame.y + f2_y, width=f2_w, height=f2_h)
                frame2_rect = flash_rect
            f2_attr_map = attr_map.copy()
            for attr, (paper, ink) in attr_map.items():
                new_attr = (attr & 192) + (attr & 7) * 8 + (attr & 56) // 8
                f2_attr_map[new_attr] = (ink, paper)
            f2_frame.attr_map = f2_attr_map
            frame2 = build_method(f2_frame, bit_depth=bit_depth, mask=mask)

        return frame1, frame2, frame2_rect

    def _get_crc(self, byte_list):
        crc = CRC_MASK
        for b in byte_list:
            crc = self.crc_table[(crc ^ b) & 255] ^ (crc >> 8)
        return self._to_bytes(crc ^ CRC_MASK)

    def _write_chunk(self, img_file, chunk_data):
        img_file.write(bytearray(self._to_bytes(len(chunk_data) - 4))) # length
        img_file.write(bytearray(chunk_data))
        img_file.write(bytearray(self._get_crc(chunk_data))) # CRC

    def _write_img_data_chunk(self, img_file, img_data):
        img_file.write(bytearray(self._to_bytes(len(img_data) - 4))) # length
        img_file.write(img_data)
        img_file.write(bytearray(self._get_crc(img_data))) # CRC

    def _build_image_data_bd_any(self, frame, bit_depth, mask):
        # Build image data at any bit depth using a generic method
        compressor = zlib.compressobj(self.compression_level)
        img_data = bytearray()
        scale = frame.scale
        attr_map = frame.attr_map
        x0 = frame.x
        y0 = frame.y
        x1 = x0 + frame.width
        y1 = y0 + frame.height
        inc = 8 * scale
        min_col = x0 // inc
        max_col = x1 // inc
        min_row = y0 // inc
        max_row = y1 // inc
        x0_floor = inc * min_col
        x1_floor = inc * max_col
        x1_pixel_floor = scale * (x1 // scale)
        y1_pixel_floor = scale * (y1 // scale)
        trans_pixels = (0,) * scale

        y = inc * min_row
        for row in frame.udgs[min_row:max_row + 1]:
            min_k = max(0, (y0 - y) // scale)
            max_k = min(8, 1 + (y1 - 1 - y) // scale)
            y += min_k * scale
            for k in range(min_k, max_k):
                p = []
                x = x0_floor
                for udg in row[min_col:max_col + 1]:
                    paper, ink = attr_map[udg.attr & 127]
                    if x0 <= x < x1_floor:
                        # Full width UDG
                        for pixels in mask.apply(udg, k, (paper,) * scale, (ink,) * scale, trans_pixels):
                            p.extend(pixels)
                        x += inc
                    else:
                        # UDG cropped on the left or right
                        min_j = max(0, (x0 - x) // scale)
                        max_j = min(8, 1 + (x1 - 1 - x) // scale)
                        x += min_j * scale
                        for pixel in mask.apply(udg, k, paper, ink, 0)[min_j:max_j]:
                            if x < x0:
                                cols = x - x0 + scale
                            elif x < x1_pixel_floor:
                                cols = scale
                            else:
                                cols = x1 - x
                            p.extend((pixel,) * cols)
                            x += scale
                scanline = bytearray((0,))
                if bit_depth == 1:
                    p.extend((0,) * (-len(p) & 7))
                    scanline.extend([p[j] * 128 + p[j + 1] * 64 + p[j + 2] * 32 + p[j + 3] * 16 + p[j + 4] * 8 + p[j + 5] * 4 + p[j + 6] * 2 + p[j + 7] for j in range(0, len(p), 8)])
                elif bit_depth == 2:
                    p.extend((0,) * (-len(p) & 3))
                    scanline.extend([p[j] * 64 + p[j + 1] * 16 + p[j + 2] * 4 + p[j + 3] for j in range(0, len(p), 4)])
                elif bit_depth == 4:
                    p.extend((0,) * (len(p) & 1))
                    scanline.extend([p[j] * 16 + p[j + 1] for j in range(0, len(p), 2)])
                if y < y0:
                    rows = y - y0 + scale
                elif y < y1_pixel_floor:
                    rows = scale
                else:
                    rows = y1 - y
                img_data.extend(compressor.compress(scanline * rows))
                y += scale
        img_data.extend(compressor.flush())
        return img_data

    def _build_image_data_bd4_nt1(self, frame, **kwargs):
        # Bit depth 4, full size, no masks, large
        scale = frame.scale
        attr_map = frame.attr_map
        attrs = {}
        if scale == 1:
            for attr, (p, i) in attr_map.items():
                b = (p * 17, p * 16 + i, i * 16 + p, i * 17)
                attrs[attr] = [[b[bit] for bit in BIT_PAIRS[j]] for j in range(256)]
        elif scale == 2:
            for attr, (p, i) in attr_map.items():
                b = (p * 17, i * 17)
                attrs[attr] = [[b[bit] for bit in BITS8[j]] for j in range(256)]
        elif scale & 1:
            for attr, (p, i) in attr_map.items():
                b = ((p * 17,), (p * 16 + i,), (i * 16 + p,), (i * 17,))
                attrs[attr] = []
                for j in range(256):
                    byte_list = []
                    attrs[attr].append(byte_list)
                    for bit in BIT_PAIRS[j]:
                        for k, s in BD4_MAP1[bit]:
                            if s:
                                byte_list.extend(b[k] * (scale // s))
                            else:
                                byte_list.extend(b[k])
        else:
            for attr, (p, i) in attr_map.items():
                b = ((p * 17,), (i * 17,))
                attrs[attr] = []
                for j in range(256):
                    byte_list = []
                    attrs[attr].append(byte_list)
                    for bit in BIT_PAIRS[j]:
                        for k, s in BD4_MAP0[bit]:
                            byte_list.extend(b[k] * (scale // s))

        compressor = zlib.compressobj(self.compression_level)
        img_data = bytearray()
        for row in frame.udgs:
            scanline0 = bytearray((0,))
            scanline1 = bytearray((0,))
            scanline2 = bytearray((0,))
            scanline3 = bytearray((0,))
            scanline4 = bytearray((0,))
            scanline5 = bytearray((0,))
            scanline6 = bytearray((0,))
            scanline7 = bytearray((0,))
            for udg in row:
                pixels = attrs[udg.attr & 127]
                udg_bytes = udg.data
                scanline0.extend(pixels[udg_bytes[0]])
                scanline1.extend(pixels[udg_bytes[1]])
                scanline2.extend(pixels[udg_bytes[2]])
                scanline3.extend(pixels[udg_bytes[3]])
                scanline4.extend(pixels[udg_bytes[4]])
                scanline5.extend(pixels[udg_bytes[5]])
                scanline6.extend(pixels[udg_bytes[6]])
                scanline7.extend(pixels[udg_bytes[7]])
            img_data.extend(compressor.compress(scanline0 * scale))
            img_data.extend(compressor.compress(scanline1 * scale))
            img_data.extend(compressor.compress(scanline2 * scale))
            img_data.extend(compressor.compress(scanline3 * scale))
            img_data.extend(compressor.compress(scanline4 * scale))
            img_data.extend(compressor.compress(scanline5 * scale))
            img_data.extend(compressor.compress(scanline6 * scale))
            img_data.extend(compressor.compress(scanline7 * scale))
        img_data.extend(compressor.flush())
        return img_data

    def _build_image_data_bd4_nt2(self, frame, **kwargs):
        # Bit depth 4, full size, no masks, small
        scale = frame.scale
        p = _get_bytes(4, scale)
        attrs = {attr: [p[t[d] * 16 + t[c]] + p[t[b] * 16 + t[a]] for d, c, b, a in BITS4] for attr, t in frame.attr_map.items()}

        compressor = zlib.compressobj(self.compression_level)
        img_data = bytearray()
        for row in frame.udgs:
            scanline0 = bytearray((0,))
            scanline1 = bytearray((0,))
            scanline2 = bytearray((0,))
            scanline3 = bytearray((0,))
            scanline4 = bytearray((0,))
            scanline5 = bytearray((0,))
            scanline6 = bytearray((0,))
            scanline7 = bytearray((0,))
            for udg in row:
                pixels = attrs[udg.attr & 127]
                udg_bytes = udg.data
                byte = udg_bytes[0]
                scanline0.extend(pixels[byte // 16])
                scanline0.extend(pixels[byte & 15])
                byte = udg_bytes[1]
                scanline1.extend(pixels[byte // 16])
                scanline1.extend(pixels[byte & 15])
                byte = udg_bytes[2]
                scanline2.extend(pixels[byte // 16])
                scanline2.extend(pixels[byte & 15])
                byte = udg_bytes[3]
                scanline3.extend(pixels[byte // 16])
                scanline3.extend(pixels[byte & 15])
                byte = udg_bytes[4]
                scanline4.extend(pixels[byte // 16])
                scanline4.extend(pixels[byte & 15])
                byte = udg_bytes[5]
                scanline5.extend(pixels[byte // 16])
                scanline5.extend(pixels[byte & 15])
                byte = udg_bytes[6]
                scanline6.extend(pixels[byte // 16])
                scanline6.extend(pixels[byte & 15])
                byte = udg_bytes[7]
                scanline7.extend(pixels[byte // 16])
                scanline7.extend(pixels[byte & 15])
            img_data.extend(compressor.compress(scanline0 * scale))
            img_data.extend(compressor.compress(scanline1 * scale))
            img_data.extend(compressor.compress(scanline2 * scale))
            img_data.extend(compressor.compress(scanline3 * scale))
            img_data.extend(compressor.compress(scanline4 * scale))
            img_data.extend(compressor.compress(scanline5 * scale))
            img_data.extend(compressor.compress(scanline6 * scale))
            img_data.extend(compressor.compress(scanline7 * scale))

        img_data.extend(compressor.flush())
        return img_data

    def _build_image_data_bd2_nt(self, frame, **kwargs):
        # Bit depth 2, full size, no masks
        scale = frame.scale
        compressor = zlib.compressobj(self.compression_level)
        img_data = bytearray()
        bits = _get_bytes(2, scale)
        attrs = {attr: [bits[t[d] * 64 + t[c] * 16 + t[b] * 4 + t[a]] for d, c, b, a in BITS4] for attr, t in frame.attr_map.items()}

        for row in frame.udgs:
            scanline0 = bytearray((0,))
            scanline1 = bytearray((0,))
            scanline2 = bytearray((0,))
            scanline3 = bytearray((0,))
            scanline4 = bytearray((0,))
            scanline5 = bytearray((0,))
            scanline6 = bytearray((0,))
            scanline7 = bytearray((0,))
            for udg in row:
                pixels = attrs[udg.attr & 127]
                udg_bytes = udg.data
                byte = udg_bytes[0]
                scanline0.extend(pixels[byte // 16])
                scanline0.extend(pixels[byte & 15])
                byte = udg_bytes[1]
                scanline1.extend(pixels[byte // 16])
                scanline1.extend(pixels[byte & 15])
                byte = udg_bytes[2]
                scanline2.extend(pixels[byte // 16])
                scanline2.extend(pixels[byte & 15])
                byte = udg_bytes[3]
                scanline3.extend(pixels[byte // 16])
                scanline3.extend(pixels[byte & 15])
                byte = udg_bytes[4]
                scanline4.extend(pixels[byte // 16])
                scanline4.extend(pixels[byte & 15])
                byte = udg_bytes[5]
                scanline5.extend(pixels[byte // 16])
                scanline5.extend(pixels[byte & 15])
                byte = udg_bytes[6]
                scanline6.extend(pixels[byte // 16])
                scanline6.extend(pixels[byte & 15])
                byte = udg_bytes[7]
                scanline7.extend(pixels[byte // 16])
                scanline7.extend(pixels[byte & 15])
            img_data.extend(compressor.compress(scanline0 * scale))
            img_data.extend(compressor.compress(scanline1 * scale))
            img_data.extend(compressor.compress(scanline2 * scale))
            img_data.extend(compressor.compress(scanline3 * scale))
            img_data.extend(compressor.compress(scanline4 * scale))
            img_data.extend(compressor.compress(scanline5 * scale))
            img_data.extend(compressor.compress(scanline6 * scale))
            img_data.extend(compressor.compress(scanline7 * scale))

        img_data.extend(compressor.flush())
        return img_data

    def _build_image_data_bd2_at(self, frame, mask, **kwargs):
        # Bit depth 2, full size, masked
        attrs = {}
        scale = frame.scale
        compressor = zlib.compressobj(self.compression_level)
        img_data = bytearray()
        bits = _get_bytes(2, scale)
        for attr, (paper, ink) in frame.attr_map.items():
            p = mask.colours((paper, ink, 0), 0, 1, 2)
            attrs[attr] = [bits[p[d] * 64 + p[c] * 16 + p[b] * 4 + p[a]] for d, c, b, a in BIT_PAIRS2]

        for row in frame.udgs:
            scanline0 = bytearray((0,))
            scanline1 = bytearray((0,))
            scanline2 = bytearray((0,))
            scanline3 = bytearray((0,))
            scanline4 = bytearray((0,))
            scanline5 = bytearray((0,))
            scanline6 = bytearray((0,))
            scanline7 = bytearray((0,))
            for udg in row:
                pixels = attrs[udg.attr & 127]
                udg_bytes = udg.data
                mask_bytes = udg.mask or udg_bytes
                byte = udg_bytes[0]
                mask_byte = mask_bytes[0]
                scanline0.extend(pixels[(byte & 240) + mask_byte // 16])
                scanline0.extend(pixels[(byte & 15) * 16 + (mask_byte & 15)])
                byte = udg_bytes[1]
                mask_byte = mask_bytes[1]
                scanline1.extend(pixels[(byte & 240) + mask_byte // 16])
                scanline1.extend(pixels[(byte & 15) * 16 + (mask_byte & 15)])
                byte = udg_bytes[2]
                mask_byte = mask_bytes[2]
                scanline2.extend(pixels[(byte & 240) + mask_byte // 16])
                scanline2.extend(pixels[(byte & 15) * 16 + (mask_byte & 15)])
                byte = udg_bytes[3]
                mask_byte = mask_bytes[3]
                scanline3.extend(pixels[(byte & 240) + mask_byte // 16])
                scanline3.extend(pixels[(byte & 15) * 16 + (mask_byte & 15)])
                byte = udg_bytes[4]
                mask_byte = mask_bytes[4]
                scanline4.extend(pixels[(byte & 240) + mask_byte // 16])
                scanline4.extend(pixels[(byte & 15) * 16 + (mask_byte & 15)])
                byte = udg_bytes[5]
                mask_byte = mask_bytes[5]
                scanline5.extend(pixels[(byte & 240) + mask_byte // 16])
                scanline5.extend(pixels[(byte & 15) * 16 + (mask_byte & 15)])
                byte = udg_bytes[6]
                mask_byte = mask_bytes[6]
                scanline6.extend(pixels[(byte & 240) + mask_byte // 16])
                scanline6.extend(pixels[(byte & 15) * 16 + (mask_byte & 15)])
                byte = udg_bytes[7]
                mask_byte = mask_bytes[7]
                scanline7.extend(pixels[(byte & 240) + mask_byte // 16])
                scanline7.extend(pixels[(byte & 15) * 16 + (mask_byte & 15)])
            img_data.extend(compressor.compress(scanline0 * scale))
            img_data.extend(compressor.compress(scanline1 * scale))
            img_data.extend(compressor.compress(scanline2 * scale))
            img_data.extend(compressor.compress(scanline3 * scale))
            img_data.extend(compressor.compress(scanline4 * scale))
            img_data.extend(compressor.compress(scanline5 * scale))
            img_data.extend(compressor.compress(scanline6 * scale))
            img_data.extend(compressor.compress(scanline7 * scale))

        img_data.extend(compressor.flush())
        return img_data

    def _build_image_data_bd1_nt_1udg(self, frame, **kwargs):
        # 1 UDG, 2 colours, full size, no masks
        udg = frame.udgs[0][0]
        img_data = bytearray()
        xor = frame.attr_map[udg.attr & 127][0] * 255
        scale = frame.scale
        if scale == 1:
            for b in udg.data:
                img_data.extend((0, b ^ xor))
        else:
            bits = _get_bytes(1, scale)
            for b in udg.data:
                img_data.extend(((0,) + bits[b ^ xor]) * scale)
        return zlib.compress(img_data, self.compression_level)

    def _build_image_data_bd1_nt(self, frame, **kwargs):
        # 2 colours, full size, no masks
        compressor = zlib.compressobj(self.compression_level)
        scale = frame.scale
        attr_map = frame.attr_map
        img_data = bytearray()
        bits = _get_bytes(1, scale)

        for row in frame.udgs:
            scanline0 = bytearray((0,))
            scanline1 = bytearray((0,))
            scanline2 = bytearray((0,))
            scanline3 = bytearray((0,))
            scanline4 = bytearray((0,))
            scanline5 = bytearray((0,))
            scanline6 = bytearray((0,))
            scanline7 = bytearray((0,))
            for udg in row:
                paper, ink = attr_map[udg.attr & 127]
                b_mask = paper * 255
                if ink == paper:
                    data = bits[b_mask]
                    scanline0.extend(data)
                    scanline1.extend(data)
                    scanline2.extend(data)
                    scanline3.extend(data)
                    scanline4.extend(data)
                    scanline5.extend(data)
                    scanline6.extend(data)
                    scanline7.extend(data)
                else:
                    scanline0.extend(bits[udg.data[0] ^ b_mask])
                    scanline1.extend(bits[udg.data[1] ^ b_mask])
                    scanline2.extend(bits[udg.data[2] ^ b_mask])
                    scanline3.extend(bits[udg.data[3] ^ b_mask])
                    scanline4.extend(bits[udg.data[4] ^ b_mask])
                    scanline5.extend(bits[udg.data[5] ^ b_mask])
                    scanline6.extend(bits[udg.data[6] ^ b_mask])
                    scanline7.extend(bits[udg.data[7] ^ b_mask])
            img_data.extend(compressor.compress(scanline0 * scale))
            img_data.extend(compressor.compress(scanline1 * scale))
            img_data.extend(compressor.compress(scanline2 * scale))
            img_data.extend(compressor.compress(scanline3 * scale))
            img_data.extend(compressor.compress(scanline4 * scale))
            img_data.extend(compressor.compress(scanline5 * scale))
            img_data.extend(compressor.compress(scanline6 * scale))
            img_data.extend(compressor.compress(scanline7 * scale))

        img_data.extend(compressor.flush())
        return img_data

    def _build_image_data_bd1_at(self, frame, mask, **kwargs):
        # Bit depth 1, full size, masked
        compressor = zlib.compressobj(self.compression_level)
        img_data = bytearray()
        scale = frame.scale
        attr_map = frame.attr_map
        pixels = ('0' * scale, '1' * scale)
        trans = pixels[0]
        for row in frame.udgs:
            for j in range(8):
                pixel_row = ['00000000']
                for udg in row:
                    p, i = attr_map[udg.attr & 127]
                    pixel_row.extend(mask.apply(udg, j, pixels[p], pixels[i], trans))
                r = ''.join(pixel_row)
                scanline = bytearray([int(r[k:k + 8], 2) for k in range(0, len(r), 8)])
                img_data.extend(compressor.compress(scanline * scale))
        img_data.extend(compressor.flush())
        return img_data

    def _build_image_data_bd0(self, frame, **kwargs):
        # 1 colour (i.e. blank), full size; placing the integer value in
        # brackets means it is evaluated before 'multiplying' the tuple (and is
        # therefore quicker)
        scanlines = bytearray((0,) * ((1 + frame.width // 8) * frame.height))
        return zlib.compress(scanlines, self.compression_level)
