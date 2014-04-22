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

# http://www.w3.org/Graphics/GIF/spec-gif89a.txt
GIF89A = (71, 73, 70, 56, 57, 97)
AEB = (33, 255, 11, 78, 69, 84, 83, 67, 65, 80, 69, 50, 46, 48, 3, 1, 0, 0, 0)
GIF_TRAILER = 59

BINSTR = [''.join([str((m >> n) & 1) for n in range(11, -1, -1)]) for m in range(4096)]

class GifWriter:
    def __init__(self, transparency, masks):
        self.transparency = transparency
        self.masks = masks
        self.gif_header = bytearray(GIF89A)
        self.aeb = bytearray(AEB)
        self.gif_trailer = bytearray((GIF_TRAILER,))

    def write_image(self, frames, img_file, palette, attr_map, has_trans, flash_rect):
        frame = frames[0]
        width, height = frame.width, frame.height
        transparent = self.transparency and has_trans

        # Header
        img_file.write(self.gif_header)

        # Logical screen descriptor
        data = bytearray()
        data.extend((width % 256, width // 256)) # logical screen width
        data.extend((height % 256, height // 256)) # logical screen height
        img_file.write(data)

        # Global Colour Table
        min_code_size = self._write_gct(img_file, palette)

        # Application Extension block
        if len(frames) > 1 or flash_rect:
            img_file.write(self.aeb)

        if len(frames) == 1:
            udg_array = frame.udgs
            scale = frame.scale
            x, y = frame.x, frame.y
            mask = self.masks[frame.mask]
            full_size = not frame.cropped

            if flash_rect:
                self._write_gce(img_file, frame.delay, transparent)
            elif transparent:
                self._write_gce(img_file, 0, transparent)

            # Frame 1
            self._write_image_descriptor(img_file, width, height)
            self._write_gif_image_data(img_file, udg_array, scale, x, y, width, height, full_size, min_code_size, attr_map, mask)

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
                self._write_gce(img_file, frame.delay, transparent)
                self._write_image_descriptor(img_file, f2_w, f2_h, f2_x, f2_y)
                self._write_gif_image_data(img_file, f2_udg_array, scale, x + f2_x, y + f2_y, f2_w, f2_h, full_size, min_code_size, attr_map, mask, True)
        else:
            for frame in frames:
                x, y, width, height = frame.x, frame.y, frame.width, frame.height
                mask = self.masks[frame.mask]
                full_size = not frame.cropped
                self._write_gce(img_file, frame.delay, transparent)
                self._write_image_descriptor(img_file, width, height)
                self._write_gif_image_data(img_file, frame.udgs, frame.scale, x, y, width, height, full_size, min_code_size, attr_map, mask)

        # GIF trailer
        img_file.write(self.gif_trailer)

    def _get_pixels(self, udg_array, scale, x0, y0, width, height, flash, attr_map, mask):
        pixels = []
        x1 = x0 + width
        y1 = y0 + height
        inc = 8 * scale
        min_col = x0 // inc
        max_col = x1 // inc
        min_row = y0 // inc
        max_row = y1 // inc
        x0_floor = inc * min_col
        x1_floor = inc * max_col
        x1_pixel_floor = scale * (x1 // scale)
        y1_pixel_floor = scale * (y1 // scale)
        trans_pixels = chr(0) * scale

        y = inc * min_row
        for row in udg_array[min_row:max_row + 1]:
            min_k = max(0, (y0 - y) // scale)
            max_k = min(8, 1 + (y1 - 1 - y) // scale)
            y += min_k * scale
            for k in range(min_k, max_k):
                x = x0_floor
                pixel_row = []
                for udg in row[min_col:max_col + 1]:
                    paper, ink = attr_map[udg.attr & 127]
                    if flash and udg.attr & 128:
                        paper, ink = ink, paper
                    if x0 <= x < x1_floor:
                        # Full width UDG
                        pixel_row.extend(mask.apply(udg, k, chr(paper) * scale, chr(ink) * scale, trans_pixels))
                        x += inc
                    else:
                        # UDG cropped on the left or right
                        min_j = max(0, (x0 - x) // scale)
                        max_j = min(8, 1 + (x1 - 1 - x) // scale)
                        x += min_j * scale
                        for pixel in mask.apply(udg, k, chr(paper), chr(ink), chr(0))[min_j:max_j]:
                            if x < x0:
                                cols = x - x0 + scale
                            elif x < x1_pixel_floor:
                                cols = scale
                            else:
                                cols = x1 - x
                            pixel_row.append(pixel * cols)
                            x += scale
                if y < y0:
                    rows = y - y0 + scale
                elif y < y1_pixel_floor:
                    rows = scale
                else:
                    rows = y1 - y
                for i in range(rows):
                    pixels += pixel_row
                y += scale
        return ''.join(pixels)

    def _get_all_pixels(self, udg_array, scale, flash, attr_map, mask):
        # Get all the pixels in an uncropped image
        attr_index = {}
        for attr, (paper, ink) in attr_map.items():
            attr_index[attr] = (chr(paper) * scale, chr(ink) * scale)

        pixels = []
        t = chr(0) * scale
        for row in udg_array:
            for k in range(8):
                pixel_row = []
                for udg in row:
                    paper, ink = attr_index[udg.attr & 127]
                    if flash and udg.attr & 128:
                        paper, ink = ink, paper
                    pixel_row.extend(mask.apply(udg, k, paper, ink, t))
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

    def _write_gif_image_data(self, img_file, udg_array, scale, x, y, width, height, full_size, min_code_size, attr_map, mask, flash=False):
        data = bytearray((min_code_size,))
        if full_size:
            pixels = self._get_all_pixels(udg_array, scale, flash, attr_map, mask)
        else:
            pixels = self._get_pixels(udg_array, scale, x, y, width, height, flash, attr_map, mask)
        pixels_lzw = self._compress(pixels, min_code_size)
        p_count = len(pixels_lzw)
        i = 0
        while p_count:
            b_count = min((p_count, 255))
            p_count -= b_count
            data.append(b_count) # This many bytes follow
            data.extend(pixels_lzw[i:i + b_count])
            i += b_count
        data.append(0) # End of image data
        img_file.write(data)
