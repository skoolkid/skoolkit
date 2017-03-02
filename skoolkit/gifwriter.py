# Copyright 2012-2014, 2017 Richard Dymond (rjdymond@gmail.com)
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

BINSTR = [['{:0{}b}'.format(n, width) for n in range(2 ** width)] for width in range(13)]
BITS8 = [[(n >> m) & 1 for m in (7, 6, 5, 4, 3, 2, 1, 0)] for n in range(256)]

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
        min_code_size, gct = self._gct(palette)
        img_file.write(gct)

        # Application Extension block
        if len(frames) > 1 or flash_rect:
            img_file.write(self.aeb)

        if len(frames) == 1:
            if flash_rect:
                img_file.write(self._gce(frame.delay, transparent))
            elif transparent:
                img_file.write(self._gce(0, transparent))

            # Frame 1
            frame.attr_map = attr_map
            img_file.write(self._image_descriptor(width, height))
            img_file.write(self._build_image_data(frame, min_code_size))

            if flash_rect:
                # Frame 2
                f2_x, f2_y, f2_w, f2_h = flash_rect
                f2_frame = frame.swap_colours(frame.x + f2_x, frame.y + f2_y, f2_w, f2_h)
                f2_attr_map = attr_map.copy()
                for attr, (paper, ink) in attr_map.items():
                    new_attr = (attr & 192) + (attr & 7) * 8 + (attr & 56) // 8
                    f2_attr_map[new_attr] = (ink, paper)
                f2_frame.attr_map = f2_attr_map
                img_file.write(self._gce(frame.delay, transparent))
                img_file.write(self._image_descriptor(f2_w, f2_h, f2_x, f2_y))
                img_file.write(self._build_image_data(f2_frame, min_code_size))
        else:
            for frame in frames:
                frame.attr_map = attr_map
                img_file.write(self._gce(frame.delay, transparent))
                img_file.write(self._image_descriptor(frame.width, frame.height))
                img_file.write(self._build_image_data(frame, min_code_size))

        # GIF trailer
        img_file.write(self.gif_trailer)

    def _get_pixels(self, frame):
        pixels = []
        scale = frame.scale
        mask = self.masks[frame.mask]
        x0, y0 = frame.x, frame.y
        width, height = frame.width, frame.height
        y1 = y0 + height
        inc = 8 * scale
        r0, r1 = y0 // inc, y1 // inc + 1
        c0, c1 = x0 // inc, (x0 + width) // inc + 1
        p0 = x0 % inc
        p1 = p0 + width
        trans = chr(0) * scale
        attrs = {attr: (chr(p) * scale, chr(i) * scale) for attr, (p, i) in frame.attr_map.items()}

        k0, k1 = (y0 % inc) // scale, min(8, 1 + (y1 - inc * r0 - 1) // scale)
        y = scale * (y0 // scale)
        rows = min(y - y0 + scale, height)
        for row in frame.udgs[r0:r1]:
            pixel_rows = ([], [], [], [], [], [], [], [])
            for udg in row[c0:c1]:
                paper, ink = attrs[udg.attr & 127]
                for k in range(k0, k1):
                    pixel_rows[k].extend(mask.apply(udg, k, paper, ink, trans))
            pixels.append(''.join(pixel_rows[k0])[p0:p1] * rows)
            y += (k1 - k0) * scale
            if k1 > k0 + 1:
                for i in range(k0 + 1, k1 - 1):
                    pixels.append(''.join(pixel_rows[i])[p0:p1] * scale)
                pixels.append(''.join(pixel_rows[k1 - 1])[p0:p1] * min(scale, y1 - y + scale))
            rows = min(scale, y1 - y)
            k0, k1 = 0, min(8, 1 + (y1 - y - 1) // scale)

        return ''.join(pixels)

    def _get_all_pixels(self, frame):
        # Get all the pixels in an uncropped image
        scale = frame.scale
        attrs = {attr: (chr(p) * scale, chr(i) * scale) for attr, (p, i) in frame.attr_map.items()}
        mask = self.masks[frame.mask]
        trans = chr(0) * scale

        pixels = []
        for row in frame.udgs:
            pixel_rows = ([], [], [], [], [], [], [], [])
            for udg in row:
                paper, ink = attrs[udg.attr & 127]
                for k in range(8):
                    pixel_rows[k].extend(mask.apply(udg, k, paper, ink, trans))
            pixels.extend([''.join(p) * scale for p in pixel_rows])

        return ''.join(pixels)

    def _get_all_pixels_nt(self, frame):
        # Get all the pixels in an uncropped, unmasked image
        scale = frame.scale
        attr_index = {}
        for attr, (paper, ink) in frame.attr_map.items():
            attr_index[attr] = (chr(paper) * scale, chr(ink) * scale)

        pixels = []
        for row in frame.udgs:
            pixel_row0 = []
            pixel_row1 = []
            pixel_row2 = []
            pixel_row3 = []
            pixel_row4 = []
            pixel_row5 = []
            pixel_row6 = []
            pixel_row7 = []
            for udg in row:
                bits = attr_index[udg.attr & 127]
                udg_bytes = udg.data
                b7, b6, b5, b4, b3, b2, b1, b0 = BITS8[udg_bytes[0]]
                pixel_row0.extend((bits[b7], bits[b6], bits[b5], bits[b4], bits[b3], bits[b2], bits[b1], bits[b0]))
                b7, b6, b5, b4, b3, b2, b1, b0 = BITS8[udg_bytes[1]]
                pixel_row1.extend((bits[b7], bits[b6], bits[b5], bits[b4], bits[b3], bits[b2], bits[b1], bits[b0]))
                b7, b6, b5, b4, b3, b2, b1, b0 = BITS8[udg_bytes[2]]
                pixel_row2.extend((bits[b7], bits[b6], bits[b5], bits[b4], bits[b3], bits[b2], bits[b1], bits[b0]))
                b7, b6, b5, b4, b3, b2, b1, b0 = BITS8[udg_bytes[3]]
                pixel_row3.extend((bits[b7], bits[b6], bits[b5], bits[b4], bits[b3], bits[b2], bits[b1], bits[b0]))
                b7, b6, b5, b4, b3, b2, b1, b0 = BITS8[udg_bytes[4]]
                pixel_row4.extend((bits[b7], bits[b6], bits[b5], bits[b4], bits[b3], bits[b2], bits[b1], bits[b0]))
                b7, b6, b5, b4, b3, b2, b1, b0 = BITS8[udg_bytes[5]]
                pixel_row5.extend((bits[b7], bits[b6], bits[b5], bits[b4], bits[b3], bits[b2], bits[b1], bits[b0]))
                b7, b6, b5, b4, b3, b2, b1, b0 = BITS8[udg_bytes[6]]
                pixel_row6.extend((bits[b7], bits[b6], bits[b5], bits[b4], bits[b3], bits[b2], bits[b1], bits[b0]))
                b7, b6, b5, b4, b3, b2, b1, b0 = BITS8[udg_bytes[7]]
                pixel_row7.extend((bits[b7], bits[b6], bits[b5], bits[b4], bits[b3], bits[b2], bits[b1], bits[b0]))
            pixels.append(''.join(pixel_row0) * scale)
            pixels.append(''.join(pixel_row1) * scale)
            pixels.append(''.join(pixel_row2) * scale)
            pixels.append(''.join(pixel_row3) * scale)
            pixels.append(''.join(pixel_row4) * scale)
            pixels.append(''.join(pixel_row5) * scale)
            pixels.append(''.join(pixel_row6) * scale)
            pixels.append(''.join(pixel_row7) * scale)
        return ''.join(pixels)

    def _compress(self, pixels, min_code_size):
        # Initialise the dictionary
        init_d = {chr(i): i for i in range(1 << min_code_size)}

        # Add initial (dummy) STOP and CLEAR codes
        clear_code = 1 << min_code_size
        stop_code = clear_code + 1
        init_d[clear_code] = 0
        init_d[stop_code] = 0

        d = init_d.copy()
        d_size = len(d) - 1
        code_size = min_code_size + 1
        d_limit = 1 << code_size
        output = []
        bit_buf = BINSTR[code_size][clear_code]
        i = 0
        num_p = len(pixels)
        while 1:
            # Check for max dictionary length
            if d_size == 4095:
                # Output a CLEAR code
                bit_buf = BINSTR[-1][clear_code] + bit_buf
                # Initialise the dictionary and reset the code size
                d = init_d.copy()
                code_size = min_code_size + 1
                d_limit = 1 << code_size

            # Find the next substring not yet in the dictionary
            new_substr = ''
            while i < num_p:
                new_substr += pixels[i]
                if new_substr in d:
                    substr = new_substr
                    i += 1
                else:
                    break
            bit_buf = BINSTR[code_size][d[substr]] + bit_buf

            k = len(bit_buf)
            if k > 1023:
                # Flush full bytes in the bit buffer to the output
                while k > 31:
                    value = int(bit_buf[k - 32:k], 2)
                    output.extend((value & 255, (value >> 8) & 255, (value >> 16) & 255, value >> 24))
                    k -= 32
                bit_buf = bit_buf[:k]

            if new_substr not in d:
                d_size = len(d)
                if d_size == d_limit:
                    code_size += 1
                    d_limit *= 2
                # Add the code for the new substring
                d[new_substr] = d_size
            else:
                break

        # Output the STOP code
        bit_buf = BINSTR[code_size][stop_code] + bit_buf

        # Flush any remaining bits from the buffer
        while bit_buf:
            output.append(int(bit_buf[-8:], 2))
            bit_buf = bit_buf[:-8]

        return output

    def _gct(self, palette):
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
        return min_code_size, data

    def _gce(self, delay, transparent):
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
        return data

    def _image_descriptor(self, width, height, x_offset=0, y_offset=0):
        data = bytearray()
        data.append(44) # Image separator
        data.extend((x_offset % 256, x_offset // 256)) # image left position
        data.extend((y_offset % 256, y_offset // 256)) # image top position
        data.extend((width % 256, width // 256)) # image width
        data.extend((height % 256, height // 256)) # image height
        data.append(0) # no local colour table
        return data

    def _build_image_data(self, frame, min_code_size):
        data = bytearray((min_code_size,))
        if frame.cropped:
            pixels = self._get_pixels(frame)
        elif frame.mask:
            pixels = self._get_all_pixels(frame)
        else:
            pixels = self._get_all_pixels_nt(frame)
        pixels_lzw = self._compress(pixels, min_code_size)
        p_count = len(pixels_lzw)
        i = 0
        while p_count:
            b_count = min(p_count, 255)
            p_count -= b_count
            data.append(b_count) # This many bytes follow
            data.extend(pixels_lzw[i:i + b_count])
            i += b_count
        data.append(0) # End of image data
        return data
