# -*- coding: utf-8 -*-

# Copyright 2012-2013 Richard Dymond (rjdymond@gmail.com)
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
FDAT = (102, 100, 65, 84, 0, 0, 0, 2)
IEND_CHUNK = (0, 0, 0, 0, 73, 69, 78, 68, 174, 66, 96, 130)
CRC_MASK = 4294967295

BITS4 = [[(n & m) // m for m in (8, 4, 2, 1)] for n in range(16)]
BITS8 = [[(n & m) // m for m in (128, 64, 32, 16, 8, 4, 2, 1)] for n in range(256)]
BIT_PAIRS = [((n & 192) >> 6, (n & 48) >> 4, (n & 12) >> 2, n & 3) for n in range(256)]
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

# Bytes for all possible bit patterns at even scales at bit depth 2
BD2_BYTES2 = (
    (0,),   # 00000000 (0000)
    (5,),   # 00000101 (0011)
    (10,),  # 00001010 (0022)
    (15,),  # 00001111 (0033)
    (80,),  # 01010000 (1100)
    (85,),  # 01010101 (1111)
    (90,),  # 01011010 (1122)
    (95,),  # 01011111 (1133)
    (160,), # 10100000 (2200)
    (165,), # 10100101 (2211)
    (170,), # 10101010 (2222)
    (175,), # 10101111 (2233)
    (240,), # 11110000 (3300)
    (245,), # 11110101 (3311)
    (250,), # 11111010 (3322)
    (255,)  # 11111111 (3333)
)

class PngWriter:
    def __init__(self, alpha=255, compression_level=9):
        self.alpha = alpha
        self.compression_level = compression_level
        self._create_crc_table()
        self._create_png_method_dict()
        self.trns = list(TRNS)
        self.png_signature = bytearray(PNG_SIGNATURE)
        self.actl_chunk = bytearray(ACTL_CHUNK)
        self.idat = bytearray(IDAT)
        self.fdat = bytearray(FDAT)
        self.iend_chunk = bytearray(IEND_CHUNK)

    def write_image(self, udg_array, img_file, scale, x, y, width, height, full_size, palette, attr_map, trans, flash_rect):
        bit_depth, plte_chunk, frame1, frame2, frame2_rect = self._build_image_data(udg_array, scale, x, y, width, height, full_size, palette, attr_map, trans, flash_rect)

        # PNG signature
        img_file.write(self.png_signature)

        # IHDR
        self._write_ihdr_chunk(img_file, width, height, bit_depth)

        # PLTE
        self._write_chunk(img_file, plte_chunk)

        # tRNS
        if trans and self.alpha != 255:
            self._write_chunk(img_file, self.trns + [self.alpha])

        # acTL and fcTL
        if frame2:
            img_file.write(self.actl_chunk)
            self._write_fctl_chunk(img_file, 0, width, height)

        # IDAT
        self._write_img_data_chunk(img_file, self.idat + frame1)

        # fcTL and fdAT
        if frame2:
            f2_x, f2_y, f2_w, f2_h = frame2_rect
            self._write_fctl_chunk(img_file, 1, f2_w, f2_h, f2_x, f2_y)
            self._write_img_data_chunk(img_file, self.fdat + frame2)

        # IEND
        img_file.write(self.iend_chunk)

    def _compress_bytes(self, compressor, array, data):
        # PY: No need to convert data to bytes in Python 3
        array.extend(compressor.compress(bytes(data)))

    def _compress_all_bytes(self, data):
        # PY: No need to convert data to bytes in Python 3
        return zlib.compress(bytes(data), self.compression_level)

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
        #   trans: 0 (no transparent colour), 1 (some UDGs have masks), or 2
        #          (all UDGs have masks)
        #   flash: 1 (invert paper/ink for flashing cells), 0 (don't)
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
                for trans in (0, 1, 2):
                    ht_method_dict = fs_method_dict[trans] = {}
                    for flash in (0, 1):
                        ht_method_dict[flash] = default_methods

        # Bit depth 0 (1 colour)
        bd0_methods = (None, self._build_image_data_bd1_blank)
        bd0_fs_method_dict = self.png_method_dict[0][1]
        bd0_fs_method_dict[0][0] = bd0_methods
        bd0_fs_method_dict[0][1] = bd0_methods
        bd0_fs_method_dict[1][0] = bd0_methods
        bd0_fs_method_dict[1][1] = bd0_methods
        bd0_fs_method_dict[2][0] = bd0_methods
        bd0_fs_method_dict[2][1] = bd0_methods

        # Bit depth 1 (2 colours)
        bd1_methods = (self._bd1_method, None)
        bd1_fs_method_dict = self.png_method_dict[1][1]
        bd1_fs_method_dict[0][0] = (self._bd1_nt_nf_method, None)
        bd1_fs_method_dict[0][1] = bd1_methods
        bd1_fs_method_dict[1][0] = bd1_methods
        bd1_fs_method_dict[1][1] = bd1_methods
        bd1_fs_method_dict[2][0] = bd1_methods
        bd1_fs_method_dict[2][1] = bd1_methods

        # Bit depth 2
        bd2_methods = (None, self._build_image_data_bd2)
        bd2_fs_method_dict = self.png_method_dict[2][1]
        bd2_fs_method_dict[0][0] = (None, self._build_image_data_bd2_nt_nf)
        bd2_fs_method_dict[0][1] = bd2_methods
        bd2_fs_method_dict[1][0] = bd2_methods
        bd2_fs_method_dict[1][1] = bd2_methods
        bd2_fs_method_dict[2][0] = (self._bd2_at_nf_method, None)
        bd2_fs_method_dict[2][1] = bd2_methods

        # Bit depth 4
        bd4_methods = (None, self._build_image_data_bd4)
        bd4_fs_method_dict = self.png_method_dict[4][1]
        bd4_fs_method_dict[0][0] = (self._bd4_nt_nf_method, None)
        bd4_fs_method_dict[0][1] = bd4_methods
        bd4_fs_method_dict[1][0] = bd4_methods
        bd4_fs_method_dict[1][1] = bd4_methods
        bd4_fs_method_dict[2][0] = bd4_methods
        bd4_fs_method_dict[2][1] = bd4_methods

    def _bd1_method(self, num_udgs, num_attrs, scale):
        if num_udgs >= 5:
            return self._build_image_data_bd1
        if num_attrs <= 2 and num_udgs >= 3:
            return self._build_image_data_bd1
        return self._build_image_data_bd_any

    def _bd1_nt_nf_method(self, num_udgs, num_attrs, scale):
        if num_udgs == 1 and scale in (1, 2, 4, 8):
            return self._build_image_data_bd1_nt_nf_1udg
        return self._bd1_method(num_udgs, num_attrs, scale)

    def _bd2_at_nf_method(self, num_udgs, num_attrs, scale):
        if scale == 2 or scale & 3 == 0:
            return self._build_image_data_bd2_at_nf
        return self._build_image_data_bd2

    def _bd4_nt_nf_method(self, num_udgs, num_attrs, scale):
        if scale == 2:
            min_index = 10
        elif scale == 1:
            min_index = 7
        else:
            min_index = 39
        if num_udgs / num_attrs >= min_index:
            return self._build_image_data_bd4_nt_nf
        return self._build_image_data_bd4

    def _to_bytes(self, num):
        return (num >> 24, (num >> 16) & 255, (num >> 8) & 255, num & 255)

    def _write_ihdr_chunk(self, img_file, width, height, bit_depth):
        data = list(IHDR) # chunk type
        data.extend(self._to_bytes(width)) # width
        data.extend(self._to_bytes(height)) # height
        data.extend((bit_depth, 3)) # bit depth and colour type
        data.extend((0, 0, 0)) # compression, filter and interlace methods
        self._write_chunk(img_file, data)

    def _write_fctl_chunk(self, img_file, frame_num, width, height, x_offset=0, y_offset=0):
        data = list(FCTL) # chunk type
        data.extend(self._to_bytes(frame_num)) # frame number
        data.extend(self._to_bytes(width)) # width
        data.extend(self._to_bytes(height)) # height
        data.extend(self._to_bytes(x_offset)) # x offset
        data.extend(self._to_bytes(y_offset)) # y offset
        data.extend((0, 8)) # delay numerator
        data.extend((0, 25)) # delay denominator
        data.append(0) # frame disposal operation
        data.append(0) # frame blending operation
        self._write_chunk(img_file, data)

    def _build_image_data(self, udg_array, scale, x, y, width, height, full_size, palette, attr_map, trans, flash_rect):
        palette_size = len(palette) // 3
        if palette_size > 4:
            bit_depth = 4
        elif palette_size > 2:
            bit_depth = 2
        else:
            bit_depth = 1
        plte_chunk = list(PLTE)
        plte_chunk.extend(palette)

        frame2 = frame2_rect = None
        if flash_rect:
            if full_size:
                f2_tx, f2_ty, f2_tw, f2_th = flash_rect
                sf = 8 * scale
                frame2_rect = (f2_tx * sf, f2_ty * sf, f2_tw * sf, f2_th * sf)
            else:
                frame2_rect = flash_rect

        if palette_size == 1:
            bd = 0
        else:
            bd = bit_depth
        method_dict = self.png_method_dict[bd][full_size][trans]

        # Frame 1
        f1_method, f1_build_method = method_dict[0]
        if f1_method:
            num_tiles = len(udg_array[0]) * len(udg_array)
            f1_build_method = f1_method(num_tiles, len(attr_map), scale)
        frame1 = f1_build_method(udg_array, scale, attr_map, trans, False, x, y, width, height, bit_depth)

        # Frame 2
        if frame2_rect:
            if full_size and (f2_tw < len(udg_array[0]) or f2_th < len(udg_array)):
                f2_udg_array = [udg_array[i][f2_tx:f2_tx + f2_tw] for i in range(f2_ty, f2_ty + f2_th)]
            else:
                f2_udg_array = udg_array
            f2_x, f2_y, f2_w, f2_h = frame2_rect
            f2_method, f2_build_method = method_dict[1]
            if f2_method:
                f2_build_method = f2_method(len(f2_udg_array[0]) * len(f2_udg_array), len(attr_map), scale)
            frame2 = f2_build_method(f2_udg_array, scale, attr_map, trans, True, x + f2_x, y + f2_y, f2_w, f2_h, bit_depth)

        return bit_depth, plte_chunk, frame1, frame2, frame2_rect

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

    def _build_image_data_bd_any(self, udg_array, scale, attr_map, trans, flash, x, y, width, height, bit_depth):
        # Build image data at any bit depth using a generic method
        compressor = zlib.compressobj(self.compression_level)
        img_data = bytearray()
        y_count = 0
        inc = 8 * scale
        for row in udg_array:
            if y_count >= y + height:
                break
            if y_count + inc <= y:
                y_count += inc
                continue
            for i in range(8):
                if y_count + scale <= y:
                    y_count += scale
                    continue
                if y_count >= y:
                    num_lines = min(y + height - y_count, scale)
                else:
                    num_lines = y_count - y + scale
                y_count += scale
                p = []
                x_count = 0
                for udg in row:
                    if x_count >= x + width:
                        break
                    if x_count + inc <= x:
                        x_count += inc
                        continue
                    byte = udg.data[i]
                    attr = udg.attr
                    paper, ink = attr_map[attr & 127]
                    if flash and attr & 128:
                        paper, ink = ink, paper
                    if trans and udg.mask:
                        mask_byte = udg.mask[i]
                        byte &= mask_byte
                    else:
                        mask_byte = 0
                    for b in range(8):
                        if x_count >= x + width:
                            break
                        if x_count + scale <= x:
                            x_count += scale
                            byte *= 2
                            mask_byte *= 2
                            continue
                        if x_count >= x:
                            num_bits = min(x + width - x_count, scale)
                        else:
                            num_bits = x_count - x + scale
                        x_count += scale
                        if byte & 128:
                            p.extend((ink,) * num_bits)
                        elif mask_byte & 128 == 0:
                            p.extend((paper,) * num_bits)
                        else:
                            p.extend((0,) * num_bits)
                        byte *= 2
                        mask_byte *= 2
                scanline = bytearray((0,))
                if bit_depth == 1:
                    p.extend((0,) * (8 - len(p) & 7))
                    scanline.extend([p[j] * 128 + p[j + 1] * 64 + p[j + 2] * 32 + p[j + 3] * 16 + p[j + 4] * 8 + p[j + 5] * 4 + p[j + 6] * 2 + p[j + 7] for j in range(0, len(p), 8)])
                elif bit_depth == 2:
                    p.extend((0,) * (4 - len(p) & 3))
                    scanline.extend([p[j] * 64 + p[j + 1] * 16 + p[j + 2] * 4 + p[j + 3] for j in range(0, len(p), 4)])
                elif bit_depth == 4:
                    p.extend((0,) * (2 - len(p) & 1))
                    scanline.extend([p[j] * 16 + p[j + 1] for j in range(0, len(p), 2)])
                self._compress_bytes(compressor, img_data, scanline * num_lines)
        img_data.extend(compressor.flush())
        return img_data

    def _build_image_data_bd4_nt_nf(self, udg_array, scale, attr_map, trans=0, flash=0, x=0, y=0, width=0, height=0, bit_depth=0):
        # Build image data with bit depth 4 for an image with no transparency
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
        for row in udg_array:
            for i in range(8):
                scanline = bytearray((0,))
                for udg in row:
                    scanline.extend(attrs[udg.attr & 127][udg.data[i]])
                self._compress_bytes(compressor, img_data, scanline * scale)
        img_data.extend(compressor.flush())
        return img_data

    def _build_image_data_bd4(self, udg_array, scale, attr_map, trans, flash, x=0, y=0, width=0, height=0, bit_depth=0):
        # Build image data with bit depth 4
        attr_dict = {}
        attr_dict_t = {}
        for attr, (p, i) in attr_map.items():
            attr_dict[attr] = (p * 17, p * 16 + i, i * 16 + p, i * 17)
            if trans:
                attr_dict_t[attr] = (0, p, p * 16, i, i * 16)

        compressor = zlib.compressobj(self.compression_level)
        img_data = bytearray()
        scale_odd = scale & 1
        h_scale = scale // 2
        for row in udg_array:
            for i in range(8):
                scanline = bytearray((0,))
                for udg in row:
                    attr = udg.attr
                    pp, pi, ip, ii = attr_dict[attr & 127]
                    if flash and attr & 128:
                        pp, pi, ip, ii = ii, ip, pi, pp
                    pph = (pp,) * h_scale
                    iih = (ii,) * h_scale
                    byte = udg.data[i]
                    if trans and udg.mask:
                        # Apply mask
                        tt, tp, pt, ti, it = attr_dict_t[attr & 127]
                        if flash and attr & 128:
                            tp, pt, ti, it = ti, it, tp, pt
                        tth = (tt,) * h_scale
                        mask_byte = udg.mask[i]
                        byte &= mask_byte
                        for b in range(4):
                            bits = byte & 192
                            mask_bits = mask_byte & 192
                            if bits == 192:
                                # ink + ink
                                scanline.extend((ii,) * scale)
                            elif bits == 128:
                                scanline.extend(iih)
                                if mask_bits & 64:
                                    # ink + transparent
                                    if scale_odd:
                                        scanline.append(it)
                                    scanline.extend(tth)
                                else:
                                    # ink + paper
                                    if scale_odd:
                                        scanline.append(ip)
                                    scanline.extend(pph)
                            elif bits == 64:
                                if mask_bits & 128:
                                    # transparent + ink
                                    scanline.extend(tth)
                                    if scale_odd:
                                        scanline.append(ti)
                                else:
                                    # paper + ink
                                    scanline.extend(pph)
                                    if scale_odd:
                                        scanline.append(pi)
                                scanline.extend(iih)
                            else:
                                if mask_bits == 192:
                                    # transparent + transparent
                                    scanline.extend((tt,) * scale)
                                elif mask_bits == 128:
                                    # transparent + paper
                                    scanline.extend(tth)
                                    if scale_odd:
                                        scanline.append(tp)
                                    scanline.extend(pph)
                                elif mask_bits == 64:
                                    # paper + transparent
                                    scanline.extend(pph)
                                    if scale_odd:
                                        scanline.append(pt)
                                    scanline.extend(tth)
                                else:
                                    # paper + paper
                                    scanline.extend((pp,) * scale)
                            byte *= 4
                            mask_byte *= 4
                    else:
                        # No mask
                        if byte == 0:
                            scanline.extend((pp,) * 4 * scale)
                        elif byte == 255:
                            scanline.extend((ii,) * 4 * scale)
                        else:
                            for b in range(4):
                                bits = byte & 192
                                if bits == 0:
                                    # paper + paper
                                    scanline.extend((pp,) * scale)
                                elif bits == 192:
                                    # ink + ink
                                    scanline.extend((ii,) * scale)
                                elif bits == 128:
                                    # ink + paper
                                    scanline.extend(iih)
                                    if scale_odd:
                                        scanline.append(ip)
                                    scanline.extend(pph)
                                else:
                                    # paper + ink
                                    scanline.extend(pph)
                                    if scale_odd:
                                        scanline.append(pi)
                                    scanline.extend(iih)
                                byte *= 4
                self._compress_bytes(compressor, img_data, scanline * scale)
        img_data.extend(compressor.flush())
        return img_data

    def _build_image_data_bd2_nt_nf(self, udg_array, scale, attr_map, trans=0, flash=0, x=0, y=0, width=0, height=0, bit_depth=0):
        # Build image data with bit depth 2 for an image with no transparency
        scale_m = scale & 3
        q = scale // 4
        attrs = {}
        if scale_m == 2:
            for attr, (p, i) in attr_map.items():
                c = ((p * 85,), (p * 80 + i * 5,), (i * 80 + p * 5,), (i * 85,))
                attrs[attr] = [c[b3 * 3] * q + c[b3 * 2 + b2] + c[b2 * 3] * q + c[b1 * 3] * q + c[b1 * 2 + b0] + c[b0 * 3] * q for b3, b2, b1, b0 in BITS4]
        elif scale_m == 0:
            for attr, (p, i) in attr_map.items():
                c = ((p * 85,), (i * 85,))
                attrs[attr] = [c[b3] * q + c[b2] * q + c[b1] * q + c[b0] * q for b3, b2, b1, b0 in BITS4]
        elif scale_m == 1:
            if scale == 1:
                for attr, t in attr_map.items():
                    attrs[attr] = [(t[b3] * 64 + t[b2] * 16 + t[b1] * 4 + t[b0],) for b3, b2, b1, b0 in BITS4]
            else:
                for attr, t in attr_map.items():
                    c = [(t[b3] * 64 + t[b2] * 16 + t[b1] * 4 + t[b0],) for b3, b2, b1, b0 in BD2_BITS]
                    attrs[attr] = [c[b3 * 7] * q + c[b3 * 4 + b2 * 3] + c[b2 * 7] * (q - 1) + c[b2 * 5 + b1 * 2] + c[b1 * 7] * (q - 1) + c[b1 * 6 + b0] + c[b0 * 7] * q for b3, b2, b1, b0 in BITS4]
        else:
            for attr, t in attr_map.items():
                c = [(t[b3] * 64 + t[b2] * 16 + t[b1] * 4 + t[b0],) for b3, b2, b1, b0 in BD2_BITS]
                attrs[attr] = [c[b3 * 7] * q + c[b3 * 6 + b2] + c[b2 * 7] * q + c[b2 * 5 + b1 * 2] + c[b1 * 7] * q + c[b1 * 4 + b0 * 3] + c[b0 * 7] * q for b3, b2, b1, b0 in BITS4]

        compressor = zlib.compressobj(self.compression_level)
        img_data = bytearray()
        for row in udg_array:
            for i in range(8):
                scanline = bytearray((0,))
                for udg in row:
                    attr_bytes = attrs[udg.attr & 127]
                    byte = udg.data[i]
                    scanline.extend(attr_bytes[(byte & 240) // 16] + attr_bytes[byte & 15])
                self._compress_bytes(compressor, img_data, scanline * scale)
        img_data.extend(compressor.flush())
        return img_data

    def _build_image_data_bd2_at_nf(self, udg_array, scale, attr_map, trans=2, flash=0, x=0, y=0, width=0, height=0, bit_depth=0):
        # Build image data with bit depth 2 for a masked image when scale & 3 == 0 or scale == 2
        q = scale // 4
        attrs = {}
        if scale & 3 == 0:
            b = ((0,) * q, (85,) * q, (170,) * q, (255,) * q) # 00000000, 01010101, 10101010, 11111111
            for attr, (p, i) in attr_map.items():
                c = (b[p], b[0], b[p], b[i]) # 00 (paper), 01 (transparent), 10 (paper), 11 (ink)
                attrs[attr] = [c[b3 * 2 + m3] + c[b2 * 2 + m2] + c[b1 * 2 + m1] + c[b0 * 2 + m0] for b3, b2, b1, b0, m3, m2, m1, m0 in BITS8]
        elif scale == 2:
            for attr, (paper, ink) in attr_map.items():
                p = (paper, 0, paper, ink) # 00, 01, 10, 11
                attrs[attr] = [BD2_BYTES2[p[b3 * 2 + m3] * 4 + p[b2 * 2 + m2]] + BD2_BYTES2[p[b1 * 2 + m1] * 4 + p[b0 * 2 + m0]] for b3, b2, b1, b0, m3, m2, m1, m0 in BITS8]

        compressor = zlib.compressobj(self.compression_level)
        img_data = bytearray()
        for row in udg_array:
            for i in range(8):
                scanline = bytearray((0,))
                for udg in row:
                    attr_bytes = attrs[udg.attr & 127]
                    byte = udg.data[i]
                    mask_byte = udg.mask[i]
                    scanline.extend(attr_bytes[(byte & 240) + (mask_byte & 240) // 16] + attr_bytes[(byte & 15) * 16 + (mask_byte & 15)])
                self._compress_bytes(compressor, img_data, scanline * scale)
        img_data.extend(compressor.flush())
        return img_data

    def _build_image_data_bd2(self, udg_array, scale, attr_map, trans, flash, x=0, y=0, width=0, height=0, bit_depth=0):
        # Build image data with bit depth 2
        attr_dict = {}
        for attr, q in attr_map.items():
            attr_dict[attr] = [q[b3] * 64 + q[b2] * 16 + q[b1] * 4 + q[b0] for b3, b2, b1, b0 in BITS4]

        compressor = zlib.compressobj(self.compression_level)
        scale_m = scale & 3
        q_scale = scale // 4
        img_data = bytearray()
        for row in udg_array:
            for i in range(8):
                scanline = bytearray((0,))
                for udg in row:
                    attr = udg.attr
                    byte = udg.data[i]
                    attrs = attr_dict[attr & 127]
                    if trans and udg.mask:
                        # Apply mask
                        p = []
                        mask_byte = udg.mask[i]
                        byte &= mask_byte
                        paper, ink = attr_map[attr & 127]
                        if flash and attr & 128:
                            paper, ink = ink, paper
                        for b in range(8):
                            if byte & 128:
                                p.extend((ink,) * scale)
                            elif mask_byte & 128:
                                p.extend((0,) * scale)
                            else:
                                p.extend((paper,) * scale)
                            byte *= 2
                            mask_byte *= 2
                        scanline.extend([p[j] * 64 + p[j + 1] * 16 + p[j + 2] * 4 + p[j + 3] for j in range(0, len(p), 4)])
                    else:
                        # No mask
                        if flash and attr & 128:
                            byte ^= 255
                        for bits in ((byte & 240) // 16, byte & 15):
                            b3, b2, b1, b0 = BITS4[bits]
                            if scale_m == 0:
                                scanline.extend((attrs[b3 * 15],) * q_scale)
                                scanline.extend((attrs[b2 * 15],) * q_scale)
                                scanline.extend((attrs[b1 * 15],) * q_scale)
                                scanline.extend((attrs[b0 * 15],) * q_scale)
                            elif scale_m == 1:
                                if scale == 1:
                                    scanline.append(attrs[bits])
                                    continue
                                scanline.extend((attrs[b3 * 15],) * q_scale)
                                scanline.append(attrs[b3 * 8 + b2 * 7])
                                scanline.extend((attrs[b2 * 15],) * (q_scale - 1))
                                scanline.append(attrs[b2 * 12 + b1 * 3])
                                scanline.extend((attrs[b1 * 15],) * (q_scale - 1))
                                scanline.append(attrs[b1 * 14 + b0])
                                scanline.extend((attrs[b0 * 15],) * q_scale)
                            elif scale_m == 2:
                                scanline.extend((attrs[b3 * 15],) * q_scale)
                                scanline.append(attrs[b3 * 12 + b2 * 3])
                                scanline.extend((attrs[b2 * 15],) * q_scale)
                                scanline.extend((attrs[b1 * 15],) * q_scale)
                                scanline.append(attrs[b1 * 12 + b0 * 3])
                                scanline.extend((attrs[b0 * 15],) * q_scale)
                            else:
                                scanline.extend((attrs[b3 * 15],) * q_scale)
                                scanline.append(attrs[b3 * 14 + b2])
                                scanline.extend((attrs[b2 * 15],) * q_scale)
                                scanline.append(attrs[b2 * 12 + b1 * 3])
                                scanline.extend((attrs[b1 * 15],) * q_scale)
                                scanline.append(attrs[b1 * 8 + b0 * 7])
                                scanline.extend((attrs[b0 * 15],) * q_scale)
                self._compress_bytes(compressor, img_data, scanline * scale)
        img_data.extend(compressor.flush())
        return img_data

    def _build_image_data_bd1_nt_nf_1udg(self, udg_array, scale, attr_map, trans, flash, x=0, y=0, width=0, height=0, bit_depth=0):
        # Build image data with bit depth 1 for a single UDG
        udg = udg_array[0][0]
        img_bytes = {}
        for p, i in attr_map.values():
            if p:
                xor = 255
            else:
                xor = 0
        if scale == 4:
            for b in set(udg.data):
                b7, b6, b5, b4, b3, b2, b1, b0 = BITS8[b ^ xor]
                img_bytes[b] = (b7 * 240 + b6 * 15, b5 * 240 + b4 * 15, b3 * 240 + b2 * 15, b1 * 240 + b0 * 15)
        elif scale == 2:
            for b in set(udg.data):
                b7, b6, b5, b4, b3, b2, b1, b0 = BITS8[b ^ xor]
                img_bytes[b] = (b7 * 192 + b6 * 48 + b5 * 12 + b4 * 3, b3 * 192 + b2 * 48 + b1 * 12 + b0 * 3)
        elif scale == 1:
            for b in set(udg.data):
                img_bytes[b] = (b ^ xor,)
        elif scale == 8:
            for b in set(udg.data):
                b7, b6, b5, b4, b3, b2, b1, b0 = BITS8[b ^ xor]
                img_bytes[b] = (b7 * 255, b6 * 255, b5 * 255, b4 * 255, b3 * 255, b2 * 255, b1 * 255, b0 * 255)

        img_data = bytearray()
        for b in udg.data:
            img_data.extend(((0,) + img_bytes[b]) * scale)
        return self._compress_all_bytes(img_data)

    def _build_image_data_bd1(self, udg_array, scale, attr_map, trans, flash, x=0, y=0, width=0, height=0, bit_depth=0):
        # Build image data with bit depth 1 and a 2-colour palette
        attr_dict = {}
        for attr, q in attr_map.items():
            attr_dict[attr] = [q[b7] * 128 + q[b6] * 64 + q[b5] * 32 + q[b4] * 16 + q[b3] * 8 + q[b2] * 4 + q[b1] * 2 + q[b0] for b7, b6, b5, b4, b3, b2, b1, b0 in BITS8]

        compressor = zlib.compressobj(self.compression_level)
        e_scale = scale // 8
        scale_m = scale & 7
        if trans:
            t = (0,) * scale
            ink = paper = (1,) * scale
        img_data = bytearray()
        for row in udg_array:
            for i in range(8):
                scanline = bytearray((0,))
                for udg in row:
                    byte = udg.data[i]
                    if trans and udg.mask:
                        # Apply mask
                        p = []
                        mask_byte = udg.mask[i]
                        byte &= mask_byte
                        for b in range(8):
                            if byte & 128:
                                p.extend(ink)
                            elif mask_byte & 128:
                                p.extend(t)
                            else:
                                p.extend(paper)
                            byte *= 2
                            mask_byte *= 2
                        scanline.extend([p[j] * 128 + p[j + 1] * 64 + p[j + 2] * 32 + p[j + 3] * 16 + p[j + 4] * 8 + p[j + 5] * 4 + p[j + 6] * 2 + p[j + 7] for j in range(0, len(p), 8)])
                    else:
                        # No mask
                        attr = udg.attr
                        if flash and attr & 128:
                            byte ^= 255
                        b7, b6, b5, b4, b3, b2, b1, b0 = BITS8[byte]
                        attrs = attr_dict[attr & 127]
                        if scale_m == 0:
                            scanline.extend((attrs[b7 * 255],) * e_scale)
                            scanline.extend((attrs[b6 * 255],) * e_scale)
                            scanline.extend((attrs[b5 * 255],) * e_scale)
                            scanline.extend((attrs[b4 * 255],) * e_scale)
                            scanline.extend((attrs[b3 * 255],) * e_scale)
                            scanline.extend((attrs[b2 * 255],) * e_scale)
                            scanline.extend((attrs[b1 * 255],) * e_scale)
                            scanline.extend((attrs[b0 * 255],) * e_scale)
                        elif scale_m == 1:
                            if scale == 1:
                                scanline.append(attrs[byte])
                                continue
                            scanline.extend((attrs[b7 * 255],) * e_scale)
                            scanline.append(attrs[b7 * 128 + b6 * 127])
                            scanline.extend((attrs[b6 * 255],) * (e_scale - 1))
                            scanline.append(attrs[b6 * 192 + b5 * 63])
                            scanline.extend((attrs[b5 * 255],) * (e_scale - 1))
                            scanline.append(attrs[b5 * 224 + b4 * 31])
                            scanline.extend((attrs[b4 * 255],) * (e_scale - 1))
                            scanline.append(attrs[b4 * 240 + b3 * 15])
                            scanline.extend((attrs[b3 * 255],) * (e_scale - 1))
                            scanline.append(attrs[b3 * 248 + b2 * 7])
                            scanline.extend((attrs[b2 * 255],) * (e_scale - 1))
                            scanline.append(attrs[b2 * 252 + b1 * 3])
                            scanline.extend((attrs[b1 * 255],) * (e_scale - 1))
                            scanline.append(attrs[b1 * 254 + b0])
                            scanline.extend((attrs[b0 * 255],) * e_scale)
                        elif scale_m == 2:
                            if scale == 2:
                                scanline.append(attrs[b7 * 192 + b6 * 48 + b5 * 12 + b4 * 3])
                                scanline.append(attrs[b3 * 192 + b2 * 48 + b1 * 12 + b0 * 3])
                                continue
                            scanline.extend((attrs[b7 * 255],) * e_scale)
                            scanline.append(attrs[b7 * 192 + b6 * 63])
                            scanline.extend((attrs[b6 * 255],) * (e_scale - 1))
                            scanline.append(attrs[b6 * 240 + b5 * 15])
                            scanline.extend((attrs[b5 * 255],) * (e_scale - 1))
                            scanline.append(attrs[b5 * 252 + b4 * 3])
                            scanline.extend((attrs[b4 * 255],) * e_scale)
                            scanline.extend((attrs[b3 * 255],) * e_scale)
                            scanline.append(attrs[b3 * 192 + b2 * 63])
                            scanline.extend((attrs[b2 * 255],) * (e_scale - 1))
                            scanline.append(attrs[b2 * 240 + b1 * 15])
                            scanline.extend((attrs[b1 * 255],) * (e_scale - 1))
                            scanline.append(attrs[b1 * 252 + b0 * 3])
                            scanline.extend((attrs[b0 * 255],) * e_scale)
                        elif scale_m == 3:
                            if scale == 3:
                                scanline.append(attrs[b7 * 224 + b6 * 28 + b5 * 3])
                                scanline.append(attrs[b5 * 128 + b4 * 112 + b3 * 14 + b2])
                                scanline.append(attrs[b2 * 192 + b1 * 56 + b0 * 7])
                                continue
                            scanline.extend((attrs[b7 * 255],) * e_scale)
                            scanline.append(attrs[b7 * 224 + b6 * 31])
                            scanline.extend((attrs[b6 * 255],) * (e_scale - 1))
                            scanline.append(attrs[b6 * 252 + b5 * 3])
                            scanline.extend((attrs[b5 * 255],) * e_scale)
                            scanline.append(attrs[b5 * 128 + b4 * 127])
                            scanline.extend((attrs[b4 * 255],) * (e_scale - 1))
                            scanline.append(attrs[b4 * 240 + b3 * 15])
                            scanline.extend((attrs[b3 * 255],) * (e_scale - 1))
                            scanline.append(attrs[b3 * 254 + b2])
                            scanline.extend((attrs[b2 * 255],) * e_scale)
                            scanline.append(attrs[b2 * 192 + b1 * 63])
                            scanline.extend((attrs[b1 * 255],) * (e_scale - 1))
                            scanline.append(attrs[b1 * 248 + b0 * 7])
                            scanline.extend((attrs[b0 * 255],) * e_scale)
                        elif scale_m == 4:
                            scanline.extend((attrs[b7 * 255],) * e_scale)
                            scanline.append(attrs[b7 * 240 + b6 * 15])
                            scanline.extend((attrs[b6 * 255],) * e_scale)
                            scanline.extend((attrs[b5 * 255],) * e_scale)
                            scanline.append(attrs[b5 * 240 + b4 * 15])
                            scanline.extend((attrs[b4 * 255],) * e_scale)
                            scanline.extend((attrs[b3 * 255],) * e_scale)
                            scanline.append(attrs[b3 * 240 + b2 * 15])
                            scanline.extend((attrs[b2 * 255],) * e_scale)
                            scanline.extend((attrs[b1 * 255],) * e_scale)
                            scanline.append(attrs[b1 * 240 + b0 * 15])
                            scanline.extend((attrs[b0 * 255],) * e_scale)
                        elif scale_m == 5:
                            if scale == 5:
                                scanline.append(attrs[b7 * 248 + b6 * 7])
                                scanline.append(attrs[b6 * 192 + b5 * 62 + b4])
                                scanline.append(attrs[b4 * 240 + b3 * 15])
                                scanline.append(attrs[b3 * 128 + b2 * 124 + b1 * 3])
                                scanline.append(attrs[b1 * 224 + b0 * 31])
                                continue
                            scanline.extend((attrs[b7 * 255],) * e_scale)
                            scanline.append(attrs[b7 * 248 + b6 * 7])
                            scanline.extend((attrs[b6 * 255],) * e_scale)
                            scanline.append(attrs[b6 * 192 + b5 * 63])
                            scanline.extend((attrs[b5 * 255],) * (e_scale - 1))
                            scanline.append(attrs[b5 * 254 + b4])
                            scanline.extend((attrs[b4 * 255],) * e_scale)
                            scanline.append(attrs[b4 * 240 + b3 * 15])
                            scanline.extend((attrs[b3 * 255],) * e_scale)
                            scanline.append(attrs[b3 * 128 + b2 * 127])
                            scanline.extend((attrs[b2 * 255],) * (e_scale - 1))
                            scanline.append(attrs[b2 * 252 + b1 * 3])
                            scanline.extend((attrs[b1 * 255],) * e_scale)
                            scanline.append(attrs[b1 * 224 + b0 * 31])
                            scanline.extend((attrs[b0 * 255],) * e_scale)
                        elif scale_m == 6:
                            scanline.extend((attrs[b7 * 255],) * e_scale)
                            scanline.append(attrs[b7 * 252 + b6 * 3])
                            scanline.extend((attrs[b6 * 255],) * e_scale)
                            scanline.append(attrs[b6 * 240 + b5 * 15])
                            scanline.extend((attrs[b5 * 255],) * e_scale)
                            scanline.append(attrs[b5 * 192 + b4 * 63])
                            scanline.extend((attrs[b4 * 255],) * e_scale)
                            scanline.extend((attrs[b3 * 255],) * e_scale)
                            scanline.append(attrs[b3 * 252 + b2 * 3])
                            scanline.extend((attrs[b2 * 255],) * e_scale)
                            scanline.append(attrs[b2 * 240 + b1 * 15])
                            scanline.extend((attrs[b1 * 255],) * e_scale)
                            scanline.append(attrs[b1 * 192 + b0 * 63])
                            scanline.extend((attrs[b0 * 255],) * e_scale)
                        elif scale_m == 7:
                            scanline.extend((attrs[b7 * 255],) * e_scale)
                            scanline.append(attrs[b7 * 254 + b6])
                            scanline.extend((attrs[b6 * 255],) * e_scale)
                            scanline.append(attrs[b6 * 252 + b5 * 3])
                            scanline.extend((attrs[b5 * 255],) * e_scale)
                            scanline.append(attrs[b5 * 248 + b4 * 7])
                            scanline.extend((attrs[b4 * 255],) * e_scale)
                            scanline.append(attrs[b4 * 240 + b3 * 15])
                            scanline.extend((attrs[b3 * 255],) * e_scale)
                            scanline.append(attrs[b3 * 224 + b2 * 31])
                            scanline.extend((attrs[b2 * 255],) * e_scale)
                            scanline.append(attrs[b2 * 192 + b1 * 63])
                            scanline.extend((attrs[b1 * 255],) * e_scale)
                            scanline.append(attrs[b1 * 128 + b0 * 127])
                            scanline.extend((attrs[b0 * 255],) * e_scale)
                self._compress_bytes(compressor, img_data, scanline * scale)
        img_data.extend(compressor.flush())
        return img_data

    def _build_image_data_bd1_blank(self, udg_array, scale, attr_map, trans=0, flash=0, x=0, y=0, width=0, height=0, bit_depth=0):
        # Build image data with bit depth 1 and a single-colour palette;
        # placing the integer value in brackets means it is evaluated before
        # 'multiplying' the tuple (and is therefore quicker)
        scanlines = bytearray((0,) * ((1 + len(udg_array[0]) * scale) * len(udg_array) * scale * 8))
        return self._compress_all_bytes(scanlines)
