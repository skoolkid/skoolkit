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

BITS4 = [[int(d) for d in '{:04b}'.format(n)] for n in range(16)]
BIT_PAIRS = [[((n << m) & 128) // 64 + ((n << m) & 8) // 8 for m in range(4)] for n in range(256)]

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
        frame1_data, frame2_data = self._build_image_data(frame1, palette_size, bit_depth, attr_map, flash_rect)

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
            f2_x_offset, f2_y_offset, f2_width, f2_height = flash_rect
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
        # and each value is the method to use to build the image data

        # Create default values
        self.png_method_dict = {}
        for bit_depth in (0, 1, 2, 4):
            bd_method_dict = self.png_method_dict[bit_depth] = {}
            for full_size in (0, 1):
                fs_method_dict = bd_method_dict[full_size] = {}
                for masked in (0, 1):
                    fs_method_dict[masked] = self._build_image_data_bd_any

        # Bit depth 0 (1 colour)
        bd0_fs_method_dict = self.png_method_dict[0][1]
        bd0_fs_method_dict[0] = self._build_image_data_bd0 # Unmasked
        bd0_fs_method_dict[1] = self._build_image_data_bd0 # Masked

        # Bit depth 1 (2 colours)
        bd1_fs_method_dict = self.png_method_dict[1][1]
        bd1_fs_method_dict[0] = self._build_image_data_bd1_nt # Unmasked
        bd1_fs_method_dict[1] = self._build_image_data_bd1_at # Masked

        # Bit depth 2
        bd2_fs_method_dict = self.png_method_dict[2][1]
        bd2_fs_method_dict[0] = self._build_image_data_bd2_nt # Unmasked
        bd2_fs_method_dict[1] = self._build_image_data_bd2_at # Masked

        # Bit depth 4
        bd4_fs_method_dict = self.png_method_dict[4][1]
        bd4_fs_method_dict[0] = self._build_image_data_bd4_nt # Unmasked
        bd4_fs_method_dict[1] = self._build_image_data_bd_any # Masked

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
        build_method = self.png_method_dict[bd][full_size][masked]
        frame.attr_map = attr_map

        frame1 = build_method(frame, mask, bit_depth)

        # Frame 2
        frame2 = None
        if flash_rect:
            f2_x, f2_y, f2_w, f2_h = flash_rect
            f2_frame = frame.swap_colours(frame.x + f2_x, frame.y + f2_y, f2_w, f2_h)
            f2_attr_map = attr_map.copy()
            for attr, (paper, ink) in attr_map.items():
                new_attr = (attr & 192) + (attr & 7) * 8 + (attr & 56) // 8
                f2_attr_map[new_attr] = (ink, paper)
            f2_frame.attr_map = f2_attr_map
            frame2 = build_method(f2_frame, mask, bit_depth)

        return frame1, frame2

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

    def _scan_frame(self, frame, scan_udg_f, *args):
        compressor = zlib.compressobj(self.compression_level)
        img_data = bytearray()
        scale = frame.scale
        for row in frame.udgs:
            scanlines = (
                bytearray((0,)), bytearray((0,)), bytearray((0,)), bytearray((0,)),
                bytearray((0,)), bytearray((0,)), bytearray((0,)), bytearray((0,))
            )
            for udg in row:
                scan_udg_f(udg, scanlines, *args)
            img_data.extend(compressor.compress(scanlines[0] * scale))
            img_data.extend(compressor.compress(scanlines[1] * scale))
            img_data.extend(compressor.compress(scanlines[2] * scale))
            img_data.extend(compressor.compress(scanlines[3] * scale))
            img_data.extend(compressor.compress(scanlines[4] * scale))
            img_data.extend(compressor.compress(scanlines[5] * scale))
            img_data.extend(compressor.compress(scanlines[6] * scale))
            img_data.extend(compressor.compress(scanlines[7] * scale))
        img_data.extend(compressor.flush())
        return img_data

    def _build_image_data_bd_any(self, frame, mask, bit_depth):
        # Build image data at any bit depth using a generic method
        compressor = zlib.compressobj(self.compression_level)
        img_data = bytearray()
        scale = frame.scale
        attrs = frame.attr_map
        x0, y0 = frame.x, frame.y
        width, height = frame.width, frame.height
        y1 = y0 + height
        inc = 8 * scale
        r0, r1 = y0 // inc, y1 // inc + 1
        c0, c1 = x0 // inc, (x0 + width) // inc + 1
        p0 = x0 % inc
        p1 = p0 + width
        bd4 = bit_depth == 4
        if bd4:
            pixels = (
                (0,) * scale, (1,) * scale, (2,) * scale, (3,) * scale,
                (4,) * scale, (5,) * scale, (6,) * scale, (7,) * scale,
                (8,) * scale, (9,) * scale, (10,) * scale, (11,) * scale,
                (12,) * scale, (13,) * scale, (14,) * scale, (15,) * scale
            )
            padding = (0,) * (width & 1)
        else:
            pixels = ('0' * scale, '1' * scale, '2' * scale, '3' * scale)
            digits = 8 // bit_depth
            padding = '0' * (-width & (digits - 1))
            base = 2 ** bit_depth
        trans = pixels[0]

        k0, k1 = (y0 % inc) // scale, min(8, 1 + (y1 - inc * r0 - 1) // scale)
        y = scale * (y0 // scale)
        rows = min(y - y0 + scale, height)
        for row in frame.udgs[r0:r1]:
            scanlines = (
                bytearray((0,)), bytearray((0,)), bytearray((0,)), bytearray((0,)),
                bytearray((0,)), bytearray((0,)), bytearray((0,)), bytearray((0,))
            )
            pixel_rows = ([], [], [], [], [], [], [], [])
            for udg in row[c0:c1]:
                paper, ink = attrs[udg.attr & 127]
                for k in range(k0, k1):
                    b = mask.apply(udg, k, pixels[paper], pixels[ink], trans)
                    p = pixel_rows[k]
                    if bd4:
                        for px in b:
                            p.extend(px)
                    else:
                        p.extend(b)
            for i in range(k0, k1):
                p = pixel_rows[i]
                if bd4:
                    p = p[p0:p1]
                    p.extend(padding)
                    scanlines[i].extend([p[j] * 16 + p[j + 1] for j in range(0, len(p), 2)])
                else:
                    r = ''.join(p)[p0:p1] + padding
                    scanlines[i].extend([int(r[n:n + digits], base) for n in range(0, len(r), digits)])
            img_data.extend(compressor.compress(scanlines[k0] * rows))
            y += (k1 - k0) * scale
            if k1 > k0 + 1:
                for i in range(k0 + 1, k1 - 1):
                    img_data.extend(compressor.compress(scanlines[i] * scale))
                img_data.extend(compressor.compress(scanlines[k1 - 1] * min(scale, y1 - y + scale)))
            rows = min(scale, y1 - y)
            k0, k1 = 0, min(8, 1 + (y1 - y - 1) // scale)

        img_data.extend(compressor.flush())
        return img_data

    def _scan_udg_bd4_nt(self, udg, scanlines, attrs):
        pixels = attrs[udg.attr & 127]
        udg_bytes = udg.data
        byte = udg_bytes[0]
        scanlines[0].extend(pixels[byte // 16])
        scanlines[0].extend(pixels[byte & 15])
        byte = udg_bytes[1]
        scanlines[1].extend(pixels[byte // 16])
        scanlines[1].extend(pixels[byte & 15])
        byte = udg_bytes[2]
        scanlines[2].extend(pixels[byte // 16])
        scanlines[2].extend(pixels[byte & 15])
        byte = udg_bytes[3]
        scanlines[3].extend(pixels[byte // 16])
        scanlines[3].extend(pixels[byte & 15])
        byte = udg_bytes[4]
        scanlines[4].extend(pixels[byte // 16])
        scanlines[4].extend(pixels[byte & 15])
        byte = udg_bytes[5]
        scanlines[5].extend(pixels[byte // 16])
        scanlines[5].extend(pixels[byte & 15])
        byte = udg_bytes[6]
        scanlines[6].extend(pixels[byte // 16])
        scanlines[6].extend(pixels[byte & 15])
        byte = udg_bytes[7]
        scanlines[7].extend(pixels[byte // 16])
        scanlines[7].extend(pixels[byte & 15])

    def _build_image_data_bd4_nt(self, frame, *args):
        # Bit depth 4, full size, no masks
        p = _get_bytes(4, frame.scale)
        attrs = {attr: [p[t[d] * 16 + t[c]] + p[t[b] * 16 + t[a]] for d, c, b, a in BITS4] for attr, t in frame.attr_map.items()}
        return self._scan_frame(frame, self._scan_udg_bd4_nt, attrs)

    def _scan_udg_bd2_nt(self, udg, scanlines, attrs):
        pixels = attrs[udg.attr & 127]
        udg_bytes = udg.data
        byte = udg_bytes[0]
        scanlines[0].extend(pixels[byte // 16])
        scanlines[0].extend(pixels[byte & 15])
        byte = udg_bytes[1]
        scanlines[1].extend(pixels[byte // 16])
        scanlines[1].extend(pixels[byte & 15])
        byte = udg_bytes[2]
        scanlines[2].extend(pixels[byte // 16])
        scanlines[2].extend(pixels[byte & 15])
        byte = udg_bytes[3]
        scanlines[3].extend(pixels[byte // 16])
        scanlines[3].extend(pixels[byte & 15])
        byte = udg_bytes[4]
        scanlines[4].extend(pixels[byte // 16])
        scanlines[4].extend(pixels[byte & 15])
        byte = udg_bytes[5]
        scanlines[5].extend(pixels[byte // 16])
        scanlines[5].extend(pixels[byte & 15])
        byte = udg_bytes[6]
        scanlines[6].extend(pixels[byte // 16])
        scanlines[6].extend(pixels[byte & 15])
        byte = udg_bytes[7]
        scanlines[7].extend(pixels[byte // 16])
        scanlines[7].extend(pixels[byte & 15])

    def _build_image_data_bd2_nt(self, frame, *args):
        # Bit depth 2, full size, no masks
        bits = _get_bytes(2, frame.scale)
        attrs = {attr: [bits[t[d] * 64 + t[c] * 16 + t[b] * 4 + t[a]] for d, c, b, a in BITS4] for attr, t in frame.attr_map.items()}
        return self._scan_frame(frame, self._scan_udg_bd2_nt, attrs)

    def _scan_udg_bd2_at(self, udg, scanlines, attrs):
        pixels = attrs[udg.attr & 127]
        udg_bytes = udg.data
        mask_bytes = udg.mask or udg_bytes
        byte = udg_bytes[0]
        mask_byte = mask_bytes[0]
        scanlines[0].extend(pixels[(byte & 240) + mask_byte // 16])
        scanlines[0].extend(pixels[(byte & 15) * 16 + (mask_byte & 15)])
        byte = udg_bytes[1]
        mask_byte = mask_bytes[1]
        scanlines[1].extend(pixels[(byte & 240) + mask_byte // 16])
        scanlines[1].extend(pixels[(byte & 15) * 16 + (mask_byte & 15)])
        byte = udg_bytes[2]
        mask_byte = mask_bytes[2]
        scanlines[2].extend(pixels[(byte & 240) + mask_byte // 16])
        scanlines[2].extend(pixels[(byte & 15) * 16 + (mask_byte & 15)])
        byte = udg_bytes[3]
        mask_byte = mask_bytes[3]
        scanlines[3].extend(pixels[(byte & 240) + mask_byte // 16])
        scanlines[3].extend(pixels[(byte & 15) * 16 + (mask_byte & 15)])
        byte = udg_bytes[4]
        mask_byte = mask_bytes[4]
        scanlines[4].extend(pixels[(byte & 240) + mask_byte // 16])
        scanlines[4].extend(pixels[(byte & 15) * 16 + (mask_byte & 15)])
        byte = udg_bytes[5]
        mask_byte = mask_bytes[5]
        scanlines[5].extend(pixels[(byte & 240) + mask_byte // 16])
        scanlines[5].extend(pixels[(byte & 15) * 16 + (mask_byte & 15)])
        byte = udg_bytes[6]
        mask_byte = mask_bytes[6]
        scanlines[6].extend(pixels[(byte & 240) + mask_byte // 16])
        scanlines[6].extend(pixels[(byte & 15) * 16 + (mask_byte & 15)])
        byte = udg_bytes[7]
        mask_byte = mask_bytes[7]
        scanlines[7].extend(pixels[(byte & 240) + mask_byte // 16])
        scanlines[7].extend(pixels[(byte & 15) * 16 + (mask_byte & 15)])

    def _build_image_data_bd2_at(self, frame, mask, *args):
        # Bit depth 2, full size, masked
        attrs = {}
        bits = _get_bytes(2, frame.scale)
        for attr, (paper, ink) in frame.attr_map.items():
            p = mask.colours((paper, ink, 0), 0, 1, 2)
            attrs[attr] = [bits[p[d] * 64 + p[c] * 16 + p[b] * 4 + p[a]] for d, c, b, a in BIT_PAIRS]
        return self._scan_frame(frame, self._scan_udg_bd2_at, attrs)

    def _scan_udg_bd1_nt(self, udg, scanlines, attrs, bits):
        paper, ink = attrs[udg.attr & 127]
        b_mask = paper * 255
        if ink == paper:
            data = bits[b_mask]
            scanlines[0].extend(data)
            scanlines[1].extend(data)
            scanlines[2].extend(data)
            scanlines[3].extend(data)
            scanlines[4].extend(data)
            scanlines[5].extend(data)
            scanlines[6].extend(data)
            scanlines[7].extend(data)
        else:
            udg_data = udg.data
            scanlines[0].extend(bits[udg_data[0] ^ b_mask])
            scanlines[1].extend(bits[udg_data[1] ^ b_mask])
            scanlines[2].extend(bits[udg_data[2] ^ b_mask])
            scanlines[3].extend(bits[udg_data[3] ^ b_mask])
            scanlines[4].extend(bits[udg_data[4] ^ b_mask])
            scanlines[5].extend(bits[udg_data[5] ^ b_mask])
            scanlines[6].extend(bits[udg_data[6] ^ b_mask])
            scanlines[7].extend(bits[udg_data[7] ^ b_mask])

    def _build_image_data_bd1_nt(self, frame, *args):
        # 2 colours, full size, no masks
        bits = _get_bytes(1, frame.scale)
        return self._scan_frame(frame, self._scan_udg_bd1_nt, frame.attr_map, bits)

    def _scan_udg_bd1_at(self, udg, scanlines, mask, attrs, pixels, bits):
        p, i = attrs[udg.attr & 127]
        paper, ink = pixels[p], pixels[i]
        scanlines[0].extend(bits[int(''.join(mask.apply(udg, 0, paper, ink, '0')), 2)])
        scanlines[1].extend(bits[int(''.join(mask.apply(udg, 1, paper, ink, '0')), 2)])
        scanlines[2].extend(bits[int(''.join(mask.apply(udg, 2, paper, ink, '0')), 2)])
        scanlines[3].extend(bits[int(''.join(mask.apply(udg, 3, paper, ink, '0')), 2)])
        scanlines[4].extend(bits[int(''.join(mask.apply(udg, 4, paper, ink, '0')), 2)])
        scanlines[5].extend(bits[int(''.join(mask.apply(udg, 5, paper, ink, '0')), 2)])
        scanlines[6].extend(bits[int(''.join(mask.apply(udg, 6, paper, ink, '0')), 2)])
        scanlines[7].extend(bits[int(''.join(mask.apply(udg, 7, paper, ink, '0')), 2)])

    def _build_image_data_bd1_at(self, frame, mask, *args):
        # Bit depth 1, full size, masked
        pixels = ('0', '1')
        bits = _get_bytes(1, frame.scale)
        return self._scan_frame(frame, self._scan_udg_bd1_at, mask, frame.attr_map, pixels, bits)

    def _build_image_data_bd0(self, frame, *args):
        # 1 colour (i.e. blank), full size; placing the integer value in
        # brackets means it is evaluated before 'multiplying' the tuple (and is
        # therefore quicker)
        scanlines = bytearray((0,) * ((1 + frame.width // 8) * frame.height))
        return zlib.compress(scanlines, self.compression_level)
