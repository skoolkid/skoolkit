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

# http://www.w3.org/Graphics/GIF/spec-gif89a.txt
GIF89A = (71, 73, 70, 56, 57, 97)
GIF_FRAME_DELAY = 32
AEB = (33, 255, 11, 78, 69, 84, 83, 67, 65, 80, 69, 50, 46, 48, 3, 1, 0, 0, 0)
GIF_TRAILER = 59

BINSTR = [''.join([str((m >> n) & 1) for n in range(11, -1, -1)]) for m in range(4096)]

class GifWriter:
    def __init__(self, transparency, compression):
        self.transparency = transparency
        self.compression = compression
        self.gif_header = bytearray(GIF89A)
        self.aeb = bytearray(AEB)
        self.gif_trailer = bytearray((GIF_TRAILER,))

    def write_image(self, udg_array, img_file, scale, x, y, width, height, full_size, palette, attr_map, trans, flash_rect):
        transparent = self.transparency and trans

        # Header
        img_file.write(self.gif_header)

        # Logical screen descriptor
        data = bytearray()
        data.extend((width % 256, width // 256)) # logical screen width
        data.extend((height % 256, height // 256)) # logical screen height
        img_file.write(data)

        # Global Colour Table
        min_code_size = self._write_gct(img_file, palette)

        if flash_rect:
            img_file.write(self.aeb)
            self._write_gce(img_file, GIF_FRAME_DELAY, transparent)
        elif transparent:
            self._write_gce(img_file, 0, transparent)

        # Frame 1
        self._write_image_descriptor(img_file, width, height)
        self._write_gif_image_data(img_file, udg_array, scale, trans, x, y, width, height, full_size, min_code_size, attr_map)

        if flash_rect:
            # Frame 2
            f2_x, f2_y, f2_w, f2_h = flash_rect
            f2_udg_array = udg_array
            if full_size:
                if f2_w < width or f2_h < height:
                    f2_udg_array = [udg_array[i][f2_x:f2_x + f2_w] for i in range(f2_y, f2_y + f2_h)]
                f2_x *= 8 * scale
                f2_y *= 8 * scale
                f2_w *= 8 * scale
                f2_h *= 8 * scale
            self._write_gce(img_file, GIF_FRAME_DELAY, transparent)
            self._write_image_descriptor(img_file, f2_w, f2_h, f2_x, f2_y)
            self._write_gif_image_data(img_file, f2_udg_array, scale, trans, x + f2_x, y + f2_y, f2_w, f2_h, full_size, min_code_size, attr_map, True)

        # GIF trailer
        img_file.write(self.gif_trailer)

    def _get_pixels(self, udg_array, scale, trans, x, y, width, height, flash, attr_map):
        pixels = []
        y_count = 0
        inc = 8 * scale
        for row in udg_array:
            if y_count >= y + height:
                break
            if y_count + inc <= y:
                y_count += inc
                continue
            for k in range(8):
                if y_count + scale <= y:
                    y_count += scale
                    continue
                if y_count >= y:
                    num_lines = min(y + height - y_count, scale)
                else:
                    num_lines = y_count - y + scale
                y_count += scale
                x_count = 0
                pixel_row = []
                for udg in row:
                    if x_count >= x + width:
                        break
                    if x_count + inc <= x:
                        x_count += inc
                        continue
                    paper, ink = attr_map[udg.attr & 127]
                    if flash and udg.attr & 128:
                        paper, ink = ink, paper
                    byte = udg.data[k]
                    if trans and udg.mask:
                        mask_byte = udg.mask[k]
                        byte &= mask_byte
                    else:
                        mask_byte = 0
                    for j in range(8):
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
                            pixel_row.extend((ink,) * num_bits)
                        elif mask_byte & 128 == 0:
                            pixel_row.extend((paper,) * num_bits)
                        else:
                            pixel_row.extend((0,) * num_bits)
                        byte *= 2
                        mask_byte *= 2
                for i in range(num_lines):
                    pixels += pixel_row
        return pixels

    def _get_all_pixels(self, udg_array, scale, trans, flash, attr_map):
        attr_index = {}
        for attr, (paper, ink) in attr_map.items():
            attr_index[attr] = ((paper,) * scale, (ink,) * scale)

        pixels = []
        t = (0,) * scale
        for row in udg_array:
            for k in range(8):
                pixel_row = []
                for udg in row:
                    p, i = attr_index[udg.attr & 127]
                    if flash and udg.attr & 128:
                        p, i = i, p
                    byte = udg.data[k]
                    if trans and udg.mask:
                        mask_byte = udg.mask[k]
                        byte &= mask_byte
                    else:
                        mask_byte = 0
                    for j in range(8):
                        if byte & 128:
                            pixel_row.extend(i)
                        elif mask_byte & 128 == 0:
                            pixel_row.extend(p)
                        else:
                            pixel_row.extend(t)
                        byte *= 2
                        mask_byte *= 2
                for i in range(scale):
                    pixels += pixel_row
        return pixels

    def _get_pixels_as_str(self, udg_array, scale, trans, x, y, width, height, flash, attr_map):
        pixels = []
        y_count = 0
        inc = 8 * scale
        for row in udg_array:
            if y_count >= y + height:
                break
            if y_count + inc <= y:
                y_count += inc
                continue
            for k in range(8):
                if y_count + scale <= y:
                    y_count += scale
                    continue
                if y_count >= y:
                    num_lines = min(y + height - y_count, scale)
                else:
                    num_lines = y_count - y + scale
                y_count += scale
                x_count = 0
                pixel_row = []
                for udg in row:
                    if x_count >= x + width:
                        break
                    if x_count + inc <= x:
                        x_count += inc
                        continue
                    paper, ink = attr_map[udg.attr & 127]
                    if flash and udg.attr & 128:
                        paper, ink = ink, paper
                    byte = udg.data[k]
                    if trans and udg.mask:
                        mask_byte = udg.mask[k]
                        byte &= mask_byte
                    else:
                        mask_byte = 0
                    for j in range(8):
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
                            pixel_row.append(chr(ink) * num_bits)
                        elif mask_byte & 128 == 0:
                            pixel_row.append(chr(paper) * num_bits)
                        else:
                            pixel_row.append(chr(0) * num_bits)
                        byte *= 2
                        mask_byte *= 2
                for i in range(num_lines):
                    pixels += pixel_row
        return ''.join(pixels)

    def _get_all_pixels_as_str(self, udg_array, scale, trans, flash, attr_map):
        attr_index = {}
        for attr, (paper, ink) in attr_map.items():
            attr_index[attr] = (chr(paper) * scale, chr(ink) * scale)

        pixels = []
        t = chr(0) * scale
        for row in udg_array:
            for k in range(8):
                pixel_row = []
                for udg in row:
                    p, i = attr_index[udg.attr & 127]
                    if flash and udg.attr & 128:
                        p, i = i, p
                    byte = udg.data[k]
                    if trans and udg.mask:
                        mask_byte = udg.mask[k]
                        byte &= mask_byte
                    else:
                        mask_byte = 0
                    for j in range(8):
                        if byte & 128:
                            pixel_row.append(i)
                        elif mask_byte & 128 == 0:
                            pixel_row.append(p)
                        else:
                            pixel_row.append(t)
                        byte *= 2
                        mask_byte *= 2
                for i in range(scale):
                    pixels += pixel_row
        return ''.join(pixels)

    def _compress(self, pixels, min_code_size):
        # Initialise the dictionary
        init_d = {}
        for i in range(1 << min_code_size):
            init_d[chr(i)] = i

        # Add initial (dummy) STOP and CLEAR codes
        clear_code = 1 << min_code_size
        stop_code = clear_code + 1
        init_d[clear_code] = 0
        init_d[stop_code] = 0

        d = init_d.copy()
        code_size = min_code_size + 1
        output = []
        bit_buf = BINSTR[clear_code][-code_size:]
        i = 0
        while 1:
            # Check for max dictionary length
            if len(d) == 4096:
                # Output a CLEAR code
                bit_buf = BINSTR[clear_code] + bit_buf
                # Initialise the dictionary and reset the code size
                d = init_d.copy()
                code_size = min_code_size + 1

            # Find the next substring not yet in the dictionary
            j = 1
            while i + j <= len(pixels):
                new_substr = pixels[i:i + j]
                if new_substr in d:
                    substr = new_substr
                    j += 1
                else:
                    break
            bit_buf = BINSTR[d[substr]][-code_size:] + bit_buf

            # Flush any full bytes in the bit buffer to the output
            while len(bit_buf) > 7:
                output.append(int(bit_buf[-8:], 2))
                bit_buf = bit_buf[:-8]

            if new_substr not in d:
                if len(d) == 1 << code_size:
                    code_size += 1
                # Add the code for the new substring
                d[new_substr] = len(d)
                i += len(substr)
            else:
                break

        # Output the STOP code
        bit_buf = BINSTR[stop_code][-code_size:] + bit_buf

        # Flush any remaining bits from the buffer
        while bit_buf:
            output.append(int(bit_buf[-8:], 2))
            bit_buf = bit_buf[:-8]

        return output

    def _write_gct(self, img_file, palette):
        data = bytearray()
        gct_flag = 1 # Global Colour Table (GCT) follows
        colour_res = 7 # number of bits per RGB channel = colour_res + 1 = 8
        sort_flag = 0 # GCT is not sorted
        palette_size = len(palette) // 3
        if palette_size > 8:
            gct_size = 3
            num_entries = 16
            min_code_size = 4
        elif palette_size > 4:
            gct_size = 2
            num_entries = 8
            min_code_size = 3
        elif palette_size > 2:
            gct_size = 1
            num_entries = 4
            min_code_size = 2
        else:
            gct_size = 0
            num_entries = 2
            min_code_size = 2
        data.append(128 * gct_flag + 16 * colour_res + 8 * sort_flag + gct_size)
        data.append(0) # background colour index (redundant)
        data.append(0) # pixel aspect ratio (none)
        data.extend(palette)
        for i in range(num_entries - palette_size):
            data.extend((0, 0, 0))
        img_file.write(data)
        return min_code_size

    def _write_gce(self, img_file, delay, transparent):
        data = bytearray()
        data.extend((33, 249)) # Graphic Control Extension
        data.append(4) # 4 bytes follow
        if transparent:
            data.append(1) # transparency
        else:
            data.append(0)
        data.extend((delay % 256, delay // 256)) # delay before next frame
        data.append(0) # transparent colour
        data.append(0) # end of GCE block
        img_file.write(data)

    def _write_image_descriptor(self, img_file, width, height, x_offset=0, y_offset=0):
        data = bytearray()
        data.append(44) # Image separator
        data.extend((x_offset % 256, x_offset // 256)) # image left position
        data.extend((y_offset % 256, y_offset // 256)) # image top position
        data.extend((width % 256, width // 256)) # image width
        data.extend((height % 256, height // 256)) # image height
        data.append(0) # no local colour table
        img_file.write(data)

    def _write_gif_image_data(self, img_file, udg_array, scale, trans, x, y, width, height, full_size, min_code_size, attr_map, flash=False):
        if self.compression:
            data = bytearray((min_code_size,))
            if full_size:
                pixels = self._get_all_pixels_as_str(udg_array, scale, trans, flash, attr_map)
            else:
                pixels = self._get_pixels_as_str(udg_array, scale, trans, x, y, width, height, flash, attr_map)
            pixels_lzw = self._compress(pixels, min_code_size)
            p_count = len(pixels_lzw)
            i = 0
            while p_count:
                b_count = min((p_count, 255))
                p_count -= b_count
                data.append(b_count) # This many bytes follow
                data.extend(pixels_lzw[i:i + b_count])
                i += b_count
        else:
            data = bytearray((7,)) # Minimum code size for uncompressed LZW data
            if full_size:
                pixels = self._get_all_pixels(udg_array, scale, trans, flash, attr_map)
            else:
                pixels = self._get_pixels(udg_array, scale, trans, x, y, width, height, flash, attr_map)
            pixels.append(129) # 8-bit STOP code
            p_count = len(pixels)
            i = 0
            while p_count:
                # 127 is the maximum distance between CLEAR codes in an
                # uncompressed LZW stream
                b_count = min((p_count, 126))
                p_count -= b_count
                data.append(b_count + 1) # This many bytes follow
                data.append(128) # 8-bit CLEAR code
                data.extend(pixels[i:i + b_count])
                i += b_count
        data.append(0) # End of image data
        img_file.write(data)
