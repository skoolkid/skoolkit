# -*- coding: utf-8 -*-

# Copyright 2012-2014 Richard Dymond (rjdymond@gmail.com)
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
BD2_BITS = [BITS4[n] for n in (0, 1, 3, 7, 8, 12, 14, 15)]

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
        bd1_fs_method_dict[0] = (self._bd1_nt_method, None)         # Unmasked
        bd1_fs_method_dict[1] = (None, self._build_image_data_bd12) # Masked

        # Bit depth 2
        bd2_fs_method_dict = self.png_method_dict[2][1]
        bd2_fs_method_dict[0] = (None, self._build_image_data_bd2_nt) # Unmasked
        bd2_fs_method_dict[1] = (self._bd2_at_method, None)           # Masked

        # Bit depth 4
        bd4_fs_method_dict = self.png_method_dict[4][1]
        bd4_fs_method_dict[0] = (self._bd4_nt_method, None)           # Unmasked
        bd4_fs_method_dict[1] = (None, self._build_image_data_bd_any) # Masked

    def _bd1_nt_method(self, frame):
        if frame.tiles == 1 and frame.scale in (1, 2, 4, 8):
            return self._build_image_data_bd1_nt_1udg
        return self._build_image_data_bd1_nt

    def _bd2_at_method(self, frame):
        if frame.all_masked and (frame.scale == 2 or frame.scale & 3 == 0):
            return self._build_image_data_bd2_at
        return self._build_image_data_bd12

    def _bd4_nt_method(self, frame):
        if frame.scale == 1:
            min_index = 40
        elif frame.scale == 2:
            min_index = 68
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
                # PY: No need to convert data to bytes in Python 3
                img_data.extend(compressor.compress(bytes(scanline * rows)))
                y += scale
        img_data.extend(compressor.flush())
        return img_data

    def _build_image_data_bd12(self, frame, bit_depth, mask):
        # Bit depth 1 or 2, full size
        compressor = zlib.compressobj(self.compression_level)
        img_data = bytearray()
        scale = frame.scale
        attr_map = frame.attr_map
        if bit_depth == 2:
            pixels = ('00' * scale, '01' * scale, '10' * scale, '11' * scale)
        else:
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
                # PY: No need to convert data to bytes in Python 3
                img_data.extend(compressor.compress(bytes(scanline * scale)))
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
            # PY: No need to convert data to bytes in Python 3
            img_data.extend(compressor.compress(bytes(scanline0 * scale)))
            img_data.extend(compressor.compress(bytes(scanline1 * scale)))
            img_data.extend(compressor.compress(bytes(scanline2 * scale)))
            img_data.extend(compressor.compress(bytes(scanline3 * scale)))
            img_data.extend(compressor.compress(bytes(scanline4 * scale)))
            img_data.extend(compressor.compress(bytes(scanline5 * scale)))
            img_data.extend(compressor.compress(bytes(scanline6 * scale)))
            img_data.extend(compressor.compress(bytes(scanline7 * scale)))
        img_data.extend(compressor.flush())
        return img_data

    def _build_image_data_bd4_nt2(self, frame, **kwargs):
        # Bit depth 4, full size, no masks, small
        scale = frame.scale
        attr_dict = {}
        if scale == 1:
            for attr, (paper, ink) in frame.attr_map.items():
                pp = paper * 17
                pi = paper * 16 + ink
                ip = ink * 16 + paper
                ii = ink * 17
                attr_dict[attr] = (
                    (pp, pp), (pp, pi), (pp, ip), (pp, ii),
                    (pi, pp), (pi, pi), (pi, ip), (pi, ii),
                    (ip, pp), (ip, pi), (ip, ip), (ip, ii),
                    (ii, pp), (ii, pi), (ii, ip), (ii, ii)
                )
        elif scale & 1:
            h_scale = scale // 2
            t_scale = scale + h_scale
            d_scale = scale * 2
            for attr, (paper, ink) in frame.attr_map.items():
                pp = (paper * 17,)
                pi = (paper * 16 + ink,)
                ip = (ink * 16 + paper,)
                ii = (ink * 17,)
                attr_dict[attr] = (
                    pp * d_scale,
                    pp * t_scale + pi + ii * h_scale,
                    pp * scale + ii * h_scale + ip + pp * h_scale,
                    pp * scale + ii * scale,
                    pp * h_scale + pi + ii * h_scale + pp * scale,
                    pp * h_scale + pi + ii * h_scale + pp * h_scale + pi + ii * h_scale,
                    pp * h_scale + pi + ii * scale + ip + pp * h_scale,
                    pp * h_scale + pi + ii * t_scale,
                    ii * h_scale + ip + pp * t_scale,
                    ii * h_scale + ip + pp * scale + pi + ii * h_scale,
                    ii * h_scale + ip + pp * h_scale + ii * h_scale + ip + pp * h_scale,
                    ii * h_scale + ip + pp * h_scale + ii * scale,
                    ii * scale + pp * scale,
                    ii * scale + pp * h_scale + pi + ii * h_scale,
                    ii * t_scale + ip + pp * h_scale,
                    ii * d_scale
                )
        else:
            h_scale = scale // 2
            for attr, (paper, ink) in frame.attr_map.items():
                p = (paper * 17,) * h_scale
                i = (ink * 17,) * h_scale
                attr_dict[attr] = (
                    p * 4,         p * 3 + i,     p * 2 + i + p, p * 2 + i * 2,
                    p + i + p * 2, (p + i) * 2,   p + i * 2 + p, p + i * 3,
                    i + p * 3,     i + p * 2 + i, (i + p) * 2,   i + p + i * 2,
                    i * 2 + p * 2, i * 2 + p + i, i * 3 + p,     i * 4
                )

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
                pixels = attr_dict[udg.attr & 127]
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
            # PY: No need to convert data to bytes in Python 3
            img_data.extend(compressor.compress(bytes(scanline0 * scale)))
            img_data.extend(compressor.compress(bytes(scanline1 * scale)))
            img_data.extend(compressor.compress(bytes(scanline2 * scale)))
            img_data.extend(compressor.compress(bytes(scanline3 * scale)))
            img_data.extend(compressor.compress(bytes(scanline4 * scale)))
            img_data.extend(compressor.compress(bytes(scanline5 * scale)))
            img_data.extend(compressor.compress(bytes(scanline6 * scale)))
            img_data.extend(compressor.compress(bytes(scanline7 * scale)))
        img_data.extend(compressor.flush())
        return img_data

    def _build_image_data_bd2_nt(self, frame, **kwargs):
        # Bit depth 2, full size, no masks
        scale = frame.scale
        scale_m = scale & 3
        q = scale // 4
        attrs = {}
        if scale_m == 2:
            for attr, (p, i) in frame.attr_map.items():
                c = ((p * 85,), (p * 80 + i * 5,), (i * 80 + p * 5,), (i * 85,))
                attrs[attr] = [c[b3 * 3] * q + c[b3 * 2 + b2] + c[b2 * 3] * q + c[b1 * 3] * q + c[b1 * 2 + b0] + c[b0 * 3] * q for b3, b2, b1, b0 in BITS4]
        elif scale_m == 0:
            for attr, (p, i) in frame.attr_map.items():
                c = ((p * 85,), (i * 85,))
                attrs[attr] = [c[b3] * q + c[b2] * q + c[b1] * q + c[b0] * q for b3, b2, b1, b0 in BITS4]
        elif scale == 1:
            for attr, t in frame.attr_map.items():
                attrs[attr] = [(t[b3] * 64 + t[b2] * 16 + t[b1] * 4 + t[b0],) for b3, b2, b1, b0 in BITS4]
        elif scale_m == 1:
            for attr, t in frame.attr_map.items():
                c = [(t[b3] * 64 + t[b2] * 16 + t[b1] * 4 + t[b0],) for b3, b2, b1, b0 in BD2_BITS]
                attrs[attr] = [c[b3 * 7] * q + c[b3 * 4 + b2 * 3] + c[b2 * 7] * (q - 1) + c[b2 * 5 + b1 * 2] + c[b1 * 7] * (q - 1) + c[b1 * 6 + b0] + c[b0 * 7] * q for b3, b2, b1, b0 in BITS4]
        else:
            for attr, t in frame.attr_map.items():
                c = [(t[b3] * 64 + t[b2] * 16 + t[b1] * 4 + t[b0],) for b3, b2, b1, b0 in BD2_BITS]
                attrs[attr] = [c[b3 * 7] * q + c[b3 * 6 + b2] + c[b2 * 7] * q + c[b2 * 5 + b1 * 2] + c[b1 * 7] * q + c[b1 * 4 + b0 * 3] + c[b0 * 7] * q for b3, b2, b1, b0 in BITS4]

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
            # PY: No need to convert data to bytes in Python 3
            img_data.extend(compressor.compress(bytes(scanline0 * scale)))
            img_data.extend(compressor.compress(bytes(scanline1 * scale)))
            img_data.extend(compressor.compress(bytes(scanline2 * scale)))
            img_data.extend(compressor.compress(bytes(scanline3 * scale)))
            img_data.extend(compressor.compress(bytes(scanline4 * scale)))
            img_data.extend(compressor.compress(bytes(scanline5 * scale)))
            img_data.extend(compressor.compress(bytes(scanline6 * scale)))
            img_data.extend(compressor.compress(bytes(scanline7 * scale)))
        img_data.extend(compressor.flush())
        return img_data

    def _build_image_data_bd2_at(self, frame, mask, **kwargs):
        # Bit depth 2, full size, fully masked, scale 2 or a multiple of 4
        attrs = {}
        scale = frame.scale
        if scale & 3 == 0:
            q = scale // 4
            b = ((0,) * q, (85,) * q, (170,) * q, (255,) * q) # 00000000, 01010101, 10101010, 11111111
            for attr, (p, i) in frame.attr_map.items():
                c = mask.colours(b, p, i, 0)
                attrs[attr] = [c[b3] + c[b2] + c[b1] + c[b0] for b3, b2, b1, b0 in BIT_PAIRS2]
        elif scale == 2:
            for attr, (paper, ink) in frame.attr_map.items():
                p = mask.colours((paper, ink, 0), 0, 1, 2)
                attrs[attr] = [(p[b3] * 80 + p[b2] * 5, p[b1] * 80 + p[b0] * 5) for b3, b2, b1, b0 in BIT_PAIRS2]

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
                mask_bytes = udg.mask
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
            # PY: No need to convert data to bytes in Python 3
            img_data.extend(compressor.compress(bytes(scanline0 * scale)))
            img_data.extend(compressor.compress(bytes(scanline1 * scale)))
            img_data.extend(compressor.compress(bytes(scanline2 * scale)))
            img_data.extend(compressor.compress(bytes(scanline3 * scale)))
            img_data.extend(compressor.compress(bytes(scanline4 * scale)))
            img_data.extend(compressor.compress(bytes(scanline5 * scale)))
            img_data.extend(compressor.compress(bytes(scanline6 * scale)))
            img_data.extend(compressor.compress(bytes(scanline7 * scale)))
        img_data.extend(compressor.flush())
        return img_data

    def _build_image_data_bd1_nt_1udg(self, frame, **kwargs):
        # 1 UDG, 2 colours, full size, no masks, scale 1, 2, 4 or 8
        udg = frame.udgs[0][0]
        img_data = bytearray()
        xor = frame.attr_map[udg.attr & 127][0] * 255

        scale = frame.scale
        if scale == 4:
            for b in udg.data:
                b7, b6, b5, b4, b3, b2, b1, b0 = BITS8[b ^ xor]
                img_data.extend((0, b7 * 240 + b6 * 15, b5 * 240 + b4 * 15, b3 * 240 + b2 * 15, b1 * 240 + b0 * 15) * 4)
        elif scale == 2:
            for b in udg.data:
                b7, b6, b5, b4, b3, b2, b1, b0 = BITS8[b ^ xor]
                img_data.extend((0, b7 * 192 + b6 * 48 + b5 * 12 + b4 * 3, b3 * 192 + b2 * 48 + b1 * 12 + b0 * 3) * 2)
        elif scale == 1:
            for b in udg.data:
                img_data.extend((0, b ^ xor))
        elif scale == 8:
            for b in udg.data:
                b7, b6, b5, b4, b3, b2, b1, b0 = BITS8[b ^ xor]
                img_data.extend((0, b7 * 255, b6 * 255, b5 * 255, b4 * 255, b3 * 255, b2 * 255, b1 * 255, b0 * 255) * 8)

        # PY: No need to convert data to bytes in Python 3
        return zlib.compress(bytes(img_data), self.compression_level)

    def _build_image_data_bd1_nt(self, frame, **kwargs):
        # 2 colours, full size, no masks
        compressor = zlib.compressobj(self.compression_level)
        scale = frame.scale
        attr_map = frame.attr_map
        e_scale = scale // 8
        scale_m = scale & 7
        img_data = bytearray()
        for row in frame.udgs:
            for i in range(8):
                scanline = bytearray((0,))
                for udg in row:
                    byte = udg.data[i] ^ (attr_map[udg.attr & 127][0] * 255)
                    if scale == 1:
                        scanline.append(byte)
                        continue
                    b7, b6, b5, b4, b3, b2, b1, b0 = BITS8[byte]
                    if scale == 2:
                        scanline.append(b7 * 192 + b6 * 48 + b5 * 12 + b4 * 3)
                        scanline.append(b3 * 192 + b2 * 48 + b1 * 12 + b0 * 3)
                    elif scale == 3:
                        scanline.append(b7 * 224 + b6 * 28 + b5 * 3)
                        scanline.append(b5 * 128 + b4 * 112 + b3 * 14 + b2)
                        scanline.append(b2 * 192 + b1 * 56 + b0 * 7)
                    elif scale == 4:
                        scanline.append(b7 * 240 + b6 * 15)
                        scanline.append(b5 * 240 + b4 * 15)
                        scanline.append(b3 * 240 + b2 * 15)
                        scanline.append(b1 * 240 + b0 * 15)
                    elif scale == 5:
                        scanline.append(b7 * 248 + b6 * 7)
                        scanline.append(b6 * 192 + b5 * 62 + b4)
                        scanline.append(b4 * 240 + b3 * 15)
                        scanline.append(b3 * 128 + b2 * 124 + b1 * 3)
                        scanline.append(b1 * 224 + b0 * 31)
                    elif scale == 6:
                        scanline.append(b7 * 252 + b6 * 3)
                        scanline.append(b6 * 240 + b5 * 15)
                        scanline.append(b5 * 192 + b4 * 63)
                        scanline.append(b3 * 252 + b2 * 3)
                        scanline.append(b2 * 240 + b1 * 15)
                        scanline.append(b1 * 192 + b0 * 63)
                    elif scale == 7:
                        scanline.append(b7 * 254 + b6)
                        scanline.append(b6 * 252 + b5 * 3)
                        scanline.append(b5 * 248 + b4 * 7)
                        scanline.append(b4 * 240 + b3 * 15)
                        scanline.append(b3 * 224 + b2 * 31)
                        scanline.append(b2 * 192 + b1 * 63)
                        scanline.append(b1 * 128 + b0 * 127)
                    elif scale == 8:
                        scanline.append(b7 * 255)
                        scanline.append(b6 * 255)
                        scanline.append(b5 * 255)
                        scanline.append(b4 * 255)
                        scanline.append(b3 * 255)
                        scanline.append(b2 * 255)
                        scanline.append(b1 * 255)
                        scanline.append(b0 * 255)
                    elif scale_m == 0:
                        scanline.extend((b7 * 255,) * e_scale)
                        scanline.extend((b6 * 255,) * e_scale)
                        scanline.extend((b5 * 255,) * e_scale)
                        scanline.extend((b4 * 255,) * e_scale)
                        scanline.extend((b3 * 255,) * e_scale)
                        scanline.extend((b2 * 255,) * e_scale)
                        scanline.extend((b1 * 255,) * e_scale)
                        scanline.extend((b0 * 255,) * e_scale)
                    elif scale_m == 1:
                        scanline.extend((b7 * 255,) * e_scale)
                        scanline.append(b7 * 128 + b6 * 127)
                        scanline.extend((b6 * 255,) * (e_scale - 1))
                        scanline.append(b6 * 192 + b5 * 63)
                        scanline.extend((b5 * 255,) * (e_scale - 1))
                        scanline.append(b5 * 224 + b4 * 31)
                        scanline.extend((b4 * 255,) * (e_scale - 1))
                        scanline.append(b4 * 240 + b3 * 15)
                        scanline.extend((b3 * 255,) * (e_scale - 1))
                        scanline.append(b3 * 248 + b2 * 7)
                        scanline.extend((b2 * 255,) * (e_scale - 1))
                        scanline.append(b2 * 252 + b1 * 3)
                        scanline.extend((b1 * 255,) * (e_scale - 1))
                        scanline.append(b1 * 254 + b0)
                        scanline.extend((b0 * 255,) * e_scale)
                    elif scale_m == 2:
                        scanline.extend((b7 * 255,) * e_scale)
                        scanline.append(b7 * 192 + b6 * 63)
                        scanline.extend((b6 * 255,) * (e_scale - 1))
                        scanline.append(b6 * 240 + b5 * 15)
                        scanline.extend((b5 * 255,) * (e_scale - 1))
                        scanline.append(b5 * 252 + b4 * 3)
                        scanline.extend((b4 * 255,) * e_scale)
                        scanline.extend((b3 * 255,) * e_scale)
                        scanline.append(b3 * 192 + b2 * 63)
                        scanline.extend((b2 * 255,) * (e_scale - 1))
                        scanline.append(b2 * 240 + b1 * 15)
                        scanline.extend((b1 * 255,) * (e_scale - 1))
                        scanline.append(b1 * 252 + b0 * 3)
                        scanline.extend((b0 * 255,) * e_scale)
                    elif scale_m == 3:
                        scanline.extend((b7 * 255,) * e_scale)
                        scanline.append(b7 * 224 + b6 * 31)
                        scanline.extend((b6 * 255,) * (e_scale - 1))
                        scanline.append(b6 * 252 + b5 * 3)
                        scanline.extend((b5 * 255,) * e_scale)
                        scanline.append(b5 * 128 + b4 * 127)
                        scanline.extend((b4 * 255,) * (e_scale - 1))
                        scanline.append(b4 * 240 + b3 * 15)
                        scanline.extend((b3 * 255,) * (e_scale - 1))
                        scanline.append(b3 * 254 + b2)
                        scanline.extend((b2 * 255,) * e_scale)
                        scanline.append(b2 * 192 + b1 * 63)
                        scanline.extend((b1 * 255,) * (e_scale - 1))
                        scanline.append(b1 * 248 + b0 * 7)
                        scanline.extend((b0 * 255,) * e_scale)
                    elif scale_m == 4:
                        scanline.extend((b7 * 255,) * e_scale)
                        scanline.append(b7 * 240 + b6 * 15)
                        scanline.extend((b6 * 255,) * e_scale)
                        scanline.extend((b5 * 255,) * e_scale)
                        scanline.append(b5 * 240 + b4 * 15)
                        scanline.extend((b4 * 255,) * e_scale)
                        scanline.extend((b3 * 255,) * e_scale)
                        scanline.append(b3 * 240 + b2 * 15)
                        scanline.extend((b2 * 255,) * e_scale)
                        scanline.extend((b1 * 255,) * e_scale)
                        scanline.append(b1 * 240 + b0 * 15)
                        scanline.extend((b0 * 255,) * e_scale)
                    elif scale_m == 5:
                        scanline.extend((b7 * 255,) * e_scale)
                        scanline.append(b7 * 248 + b6 * 7)
                        scanline.extend((b6 * 255,) * e_scale)
                        scanline.append(b6 * 192 + b5 * 63)
                        scanline.extend((b5 * 255,) * (e_scale - 1))
                        scanline.append(b5 * 254 + b4)
                        scanline.extend((b4 * 255,) * e_scale)
                        scanline.append(b4 * 240 + b3 * 15)
                        scanline.extend((b3 * 255,) * e_scale)
                        scanline.append(b3 * 128 + b2 * 127)
                        scanline.extend((b2 * 255,) * (e_scale - 1))
                        scanline.append(b2 * 252 + b1 * 3)
                        scanline.extend((b1 * 255,) * e_scale)
                        scanline.append(b1 * 224 + b0 * 31)
                        scanline.extend((b0 * 255,) * e_scale)
                    elif scale_m == 6:
                        scanline.extend((b7 * 255,) * e_scale)
                        scanline.append(b7 * 252 + b6 * 3)
                        scanline.extend((b6 * 255,) * e_scale)
                        scanline.append(b6 * 240 + b5 * 15)
                        scanline.extend((b5 * 255,) * e_scale)
                        scanline.append(b5 * 192 + b4 * 63)
                        scanline.extend((b4 * 255,) * e_scale)
                        scanline.extend((b3 * 255,) * e_scale)
                        scanline.append(b3 * 252 + b2 * 3)
                        scanline.extend((b2 * 255,) * e_scale)
                        scanline.append(b2 * 240 + b1 * 15)
                        scanline.extend((b1 * 255,) * e_scale)
                        scanline.append(b1 * 192 + b0 * 63)
                        scanline.extend((b0 * 255,) * e_scale)
                    elif scale_m == 7:
                        scanline.extend((b7 * 255,) * e_scale)
                        scanline.append(b7 * 254 + b6)
                        scanline.extend((b6 * 255,) * e_scale)
                        scanline.append(b6 * 252 + b5 * 3)
                        scanline.extend((b5 * 255,) * e_scale)
                        scanline.append(b5 * 248 + b4 * 7)
                        scanline.extend((b4 * 255,) * e_scale)
                        scanline.append(b4 * 240 + b3 * 15)
                        scanline.extend((b3 * 255,) * e_scale)
                        scanline.append(b3 * 224 + b2 * 31)
                        scanline.extend((b2 * 255,) * e_scale)
                        scanline.append(b2 * 192 + b1 * 63)
                        scanline.extend((b1 * 255,) * e_scale)
                        scanline.append(b1 * 128 + b0 * 127)
                        scanline.extend((b0 * 255,) * e_scale)
                # PY: No need to convert data to bytes in Python 3
                img_data.extend(compressor.compress(bytes(scanline * scale)))
        img_data.extend(compressor.flush())
        return img_data

    def _build_image_data_bd0(self, frame, **kwargs):
        # 1 colour (i.e. blank), full size; placing the integer value in
        # brackets means it is evaluated before 'multiplying' the tuple (and is
        # therefore quicker)
        scanlines = bytearray((0,) * ((1 + frame.width // 8) * frame.height))
        # PY: No need to convert data to bytes in Python 3
        return zlib.compress(bytes(scanlines), self.compression_level)
