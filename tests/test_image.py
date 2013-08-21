# -*- coding: utf-8 -*-
import zlib
import unittest
from collections import deque
from io import BytesIO

from skoolkittest import SkoolKitTestCase, PY3
from skoolkit.image import ImageWriter, PngWriter, DEFAULT_FORMAT, PNG_COMPRESSION_LEVEL, PNG_ENABLE_ANIMATION, PNG_ALPHA, GIF_ENABLE_ANIMATION, GIF_TRANSPARENCY, GIF_COMPRESSION
from skoolkit.skoolhtml import Udg

TRANSPARENT = [0, 254, 0]
BLACK = [0, 0, 0]
BLUE = [0, 0, 197]
RED = [197, 0, 0]
MAGENTA = [197, 0, 197]
GREEN = [0, 198, 0]
CYAN = [0, 198, 197]
YELLOW = [197, 198, 0]
WHITE = [205, 198, 205]
BRIGHT_BLUE = [0, 0, 255]
BRIGHT_RED = [255, 0, 0]
BRIGHT_MAGENTA = [255, 0, 255]
BRIGHT_GREEN = [0, 255, 0]
BRIGHT_CYAN = [0, 255, 255]
BRIGHT_YELLOW = [255, 255, 0]
BRIGHT_WHITE = [255, 255, 255]

PALETTE = [
    TRANSPARENT,
    BLACK,
    BLUE,
    RED,
    MAGENTA,
    GREEN,
    CYAN,
    YELLOW,
    WHITE,
    BRIGHT_BLUE,
    BRIGHT_RED,
    BRIGHT_MAGENTA,
    BRIGHT_GREEN,
    BRIGHT_CYAN,
    BRIGHT_YELLOW,
    BRIGHT_WHITE
]

PNG_SIGNATURE = [137, 80, 78, 71, 13, 10, 26, 10]
IHDR = [73, 72, 68, 82]
PLTE = [80, 76, 84, 69]
TRNS = [116, 82, 78, 83]
ACTL_CHUNK = [0, 0, 0, 8, 97, 99, 84, 76, 0, 0, 0, 2, 0, 0, 0, 0, 243, 141, 147, 112]
FCTL = [102, 99, 84, 76]
FDAT = [102, 100, 65, 84]
IDAT = [73, 68, 65, 84]
IEND_CHUNK = [0, 0, 0, 0, 73, 69, 78, 68, 174, 66, 96, 130]

CRC_MASK = 4294967295

GIF_HEADER = [71, 73, 70, 56, 57, 97]
AEB =  [33, 255, 11, 78, 69, 84, 83, 67, 65, 80, 69, 50, 46, 48, 3, 1, 0, 0, 0]
GIF_FRAME_DELAY = 32
GIF_TRAILER = 59

def create_crc_table():
    crc_table = []
    for n in range(256):
        c = n
        for k in range(8):
            if c & 1:
                c = 3988292384 ^ (c >> 1)
            else:
                c = c >> 1
        crc_table.append(c)
    return crc_table

def create_attr_index():
    attr_index = {}
    for attr in range(128):
        if attr & 64:
            ink = 8 + (attr & 7)
            paper = 8 + (attr & 56) // 8
            if ink == 8:
                ink = 1
            if paper == 8:
                paper = 1
        else:
            ink = 1 + (attr & 7)
            paper = 1 + (attr & 56) // 8
        attr_index[attr] = (paper, ink)
    return attr_index

CRC_TABLE = create_crc_table()
ATTR_INDEX = create_attr_index()

class ImageWriterOptionsTest(SkoolKitTestCase):
    def test_change_option_values(self):
        options = {
            DEFAULT_FORMAT: 'gif',
            PNG_COMPRESSION_LEVEL: 3,
            GIF_TRANSPARENCY: 1
        }
        image_writer = ImageWriter(options=options)
        self.assertEqual(image_writer.options[DEFAULT_FORMAT], 'gif')
        self.assertEqual(image_writer.options[PNG_COMPRESSION_LEVEL], 3)
        self.assertEqual(image_writer.options[GIF_TRANSPARENCY], 1)

    def test_default_option_values(self):
        image_writer = ImageWriter()
        self.assertEqual(image_writer.options[DEFAULT_FORMAT], 'png')
        self.assertEqual(image_writer.options[PNG_COMPRESSION_LEVEL], 9)
        self.assertEqual(image_writer.options[PNG_ENABLE_ANIMATION], 1)
        self.assertEqual(image_writer.options[PNG_ALPHA], 255)
        self.assertEqual(image_writer.options[GIF_ENABLE_ANIMATION], 1)
        self.assertEqual(image_writer.options[GIF_TRANSPARENCY], 0)

    def test_invalid_option_value(self):
        image_writer = ImageWriter(options={PNG_COMPRESSION_LEVEL: 'NaN'})
        self.assertEqual(image_writer.options[PNG_COMPRESSION_LEVEL], 9)

class ImageWriterTest:
    def _get_num(self, stream, index):
        return index + 1, stream[index]

    def _get_dword(self, stream, index):
        return index + 4, 16777216 * stream[index] + 65536 * stream[index + 1] + 256 * stream[index + 2] + stream[index + 3]

    def _get_image_data(self, image_writer, udg_array, img_format, scale=1, mask=False, x=0, y=0, width=None, height=None):
        img_stream = BytesIO()
        image_writer.write_image(udg_array, img_stream, img_format, scale, mask, x, y, width, height)
        if PY3:
            img_bytes = [b for b in img_stream.getvalue()]
        else:
            img_bytes = [ord(c) for c in img_stream.getvalue()]
        img_stream.close()
        return img_bytes

    def _get_pixels_from_udg_array(self, udg_array, scale, mask, x, y, width, height):
        full_width = 8 * len(udg_array[0]) * scale
        full_height = 8 * len(udg_array) * scale
        width = min(width or full_width, full_width - x)
        height = min(height or full_height, full_height - y)

        palette = []
        pixels = []
        pixels2 = []
        has_trans = 0
        all_trans = 1
        y_count = 0
        inc = 8 * scale

        min_x = width
        min_y = height
        max_x = max_y = 0

        for row in udg_array:
            if y_count >= y + height:
                break
            if y_count + inc <= y:
                y_count += inc
                continue
            for j in range(8):
                if y_count + scale <= y:
                    y_count += scale
                    continue
                if y_count >= y:
                    num_lines = min(y + height - y_count, scale)
                else:
                    num_lines = y_count - y + scale
                pixel_row = []
                pixel_row2 = []
                x_count = 0
                for udg in row:
                    if x_count >= x + width:
                        break
                    if x_count + inc <= x:
                        x_count += inc
                        continue
                    attr = udg.attr
                    paper, ink = ATTR_INDEX[attr & 127]
                    flashing = attr & 128 and paper != ink
                    p_rgb = PALETTE[paper]
                    i_rgb = PALETTE[ink]
                    byte = udg.data[j]
                    if mask and udg.mask:
                        mask_byte = udg.mask[j]
                        byte &= mask_byte
                    else:
                        all_trans = 0
                        mask_byte = 0
                    for k in range(8):
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
                        if flashing:
                            min_x = min((len(pixel_row), min_x))
                            max_x = max((len(pixel_row) + num_bits, max_x))
                            min_y = min((len(pixels), min_y))
                            max_y = max((len(pixels) + num_lines, max_y))
                        if byte & 128:
                            pixel_row.extend((i_rgb,) * num_bits)
                            if flashing:
                                pixel_row2.extend((p_rgb,) * num_bits)
                            else:
                                pixel_row2.extend((i_rgb,) * num_bits)
                        elif mask_byte & 128:
                            pixel_row.extend((TRANSPARENT,) * num_bits)
                            pixel_row2.extend((TRANSPARENT,) * num_bits)
                            has_trans = 1
                        else:
                            pixel_row.extend((p_rgb,) * num_bits)
                            if flashing:
                                pixel_row2.extend((i_rgb,) * num_bits)
                            else:
                                pixel_row2.extend((p_rgb,) * num_bits)
                        byte *= 2
                        mask_byte *= 2
                        x_count += scale
                for pixel in pixel_row:
                    if pixel not in palette:
                        palette.append(pixel)
                for pixel in pixel_row2:
                    if pixel not in palette:
                        palette.append(pixel)
                for n in range(num_lines):
                    pixels.append(pixel_row)
                    pixels2.append(pixel_row2)
                y_count += scale

        if pixels2 == pixels:
            pixels2 = frame2_xy = None
        else:
            frame2_xy = (min_x, min_y)
            pixels2 = [pixels2[i][min_x:max_x] for i in range(min_y, max_y)]

        trans = has_trans + all_trans if has_trans else 0

        return palette, trans, pixels, pixels2, frame2_xy

    def test_masked_alpha(self):
        # Masked image, alpha < 255
        iw_args = {'options': self.alpha_option}
        udg = Udg(88, (34,) * 8, (163,) * 8)
        udg_array = [[udg]]
        self._test_image(udg_array, mask=True, iw_args=iw_args)

    def test_masked_bd1_blank_flashing(self):
        # Masked image, single colour, flashing
        udg = Udg(184, (0,) * 8, (255,) * 8)
        udg_array = [[udg]]
        self._test_image(udg_array, mask=True)

    def test_masked_bd1_blank(self):
        # Masked image, single colour, scales 1-2
        udg = Udg(56, (0,) * 8, (255,) * 8)
        udg_array = [[udg]]
        self._test_image(udg_array, mask=True)
        self._test_image(udg_array, scale=2, mask=True)

    def test_masked_bd1_ink(self):
        # Masked image, two colours (trans + ink), >= 4 UDGs
        udg = Udg(49, (136,) * 8, (255,) * 8)
        udg_array = [[udg, udg]] * 2
        self._test_image(udg_array, mask=True)

    def test_masked_bd1_paper(self):
        # Masked image, two colours (trans + paper), >= 4 UDGs
        udg = Udg(8, (0,) * 8, (88,) * 8)
        udg_array = [[udg, udg]] * 2
        self._test_image(udg_array,  mask=True)

    def test_masked_bd2_cropped(self):
        # Masked image, bit depth 2, cropped
        udg = Udg(88, (34,) * 8, (119,) * 8)
        udg_array = [[udg] * 3]
        self._test_image(udg_array, mask=True, width=17)
        self._test_image(udg_array, mask=True, height=3)
        self._test_image(udg_array, mask=True, x=5)
        self._test_image(udg_array, mask=True, y=1)
        self._test_image(udg_array, mask=True, x=2, y=2, width=16, height=4)

    def test_masked_bd2(self):
        # Masked image, bit depth 2
        udg = Udg(88, (34,) * 8, (119,) * 8)
        udg_array = [[udg]]
        self._test_image(udg_array, mask=True)

    def test_masked_bd4_all_bp(self):
        # Masked image, bit depth 4, all bit patterns
        udg1 = Udg(56, (0,) * 8)              # pppppppp
        udg2 = Udg(56, (255,) * 8)            # iiiiiiii
        udg3 = Udg(50, (27,) * 8)             # pp,pi,ip,ii
        udg4 = Udg(50, (0,) * 8, (228,) * 8)  # tt,tp,pt,pp
        udg5 = Udg(50, (27,) * 8, (255,) * 8) # tt,ti,it,ii
        udg6 = Udg(50, (6,) * 8, (246,) * 8)  # tt,tt,pi,ip
        udg_array = [[udg1, udg2, udg3, udg4, udg5, udg6]]
        self._test_image(udg_array, mask=True)

    def test_masked_bd4_all_colours(self):
        # Masked image, 15 colours + trans
        udg1 = Udg(56, (15,) * 8)             # white, black
        udg2 = Udg(10, (15,) * 8)             # blue, red
        udg3 = Udg(28, (15,) * 8)             # magenta, green
        udg4 = Udg(46, (15,) * 8)             # cyan, yellow
        udg5 = Udg(120, (0,) * 8, (240,) * 8) # trans, bright white
        udg6 = Udg(74, (15,) * 8)             # bright blue, bright red
        udg7 = Udg(92, (15,) * 8)             # bright magenta, bright green
        udg8 = Udg(110, (15,) * 8)            # bright cyan, bright yellow
        udg_array = [[udg1, udg2, udg3, udg4, udg5, udg6, udg7, udg8]]
        self._test_image(udg_array, mask=True)

    def test_masked_bd4_flashing(self):
        # Masked image, bit depth 4, flashing
        udg1 = Udg(184, (240,) * 8, (243,) * 8)
        udg2 = Udg(49, (170,) * 8)
        udg3 = Udg(170, (195,) * 8)
        udg_array = [[udg1, udg2, udg3]]
        self._test_image(udg_array, mask=True)

    def test_masked_bd4_cropped(self):
        # Masked image, bit depth 4
        udg1 = Udg(24, (34,) * 8, (119,) * 8)
        udg2 = Udg(57, (170,) * 8)
        udg_array = [[udg1, udg2]]
        self._test_image(udg_array, scale=2, mask=True, x=1, y=3, width=27, height=12)

    def test_masked_cropped_flashing(self):
        # Masked image, cropped, flashing
        udg1 = Udg(184, (240,) * 8, (243,) * 8)
        udg2 = Udg(56, (170,) * 8)
        udg_array = [[udg1, udg2]] * 2
        self._test_image(udg_array, scale=2, mask=True, x=1, y=1, width=29, height=27)

    def test_masked_flashing(self):
        # Masked image, flashing
        udg = Udg(184, (240,) * 8, (243,) * 8)
        udg_array = [[udg]]
        self._test_image(udg_array, mask=True)

    def test_masked_flashing_no_animation(self):
        # Masked image, flashing, no animation
        iw_args = {'options': {self.animation_flag: 0}}
        udg = Udg(184, (240,) * 8, (243,) * 8)
        udg_array = [[udg]]
        self._test_image(udg_array, iw_args=iw_args)

    def test_unmasked_alpha(self):
        # Masked image, alpha < 255
        iw_args = {'options': self.alpha_option}
        udg = Udg(56, (132,) * 8)
        udg_array = [[udg]]
        self._test_image(udg_array, iw_args=iw_args)

    def test_unmasked_bd1_blank(self):
        # Unmasked image, single colour, scales 1-2
        udg = Udg(56, (255,) * 8)
        udg_array = [[udg]]
        self._test_image(udg_array)
        self._test_image(udg_array, scale=2)

    def test_unmasked_bd1_custom_colours(self):
        # Unmasked image, two custom colours
        indigo = [75, 0, 130]
        salmon = [250, 128, 114]
        colours = {'BLUE': indigo, 'RED': salmon}
        iw_args = {'palette': colours}
        udg = Udg(10, (195,) * 8) # 11000011
        udg_array = [[udg]]
        exp_pixels = [[salmon, salmon, indigo, indigo, indigo, indigo, salmon, salmon]] * 8
        self._test_image(udg_array, exp_pixels=exp_pixels, iw_args=iw_args)

    def test_unmasked_bd1_cropped(self):
        # Unmasked image, bit depth 1, cropped
        udg = Udg(30, (240,) * 8)
        udg_array = [[udg] * 2] * 2
        self._test_image(udg_array, width=11)
        self._test_image(udg_array, height=12)
        self._test_image(udg_array, x=5)
        self._test_image(udg_array, y=7)
        self._test_image(udg_array, x=1, y=2, width=9, height=11)

    def test_unmasked_bd1_cropped(self):
        # Unmasked image, bit depth 1, cropped
        udg = Udg(5, (148,) * 8)
        udg_array = [[udg] * 2] * 2
        self._test_image(udg_array, width=11)
        self._test_image(udg_array, height=12)
        self._test_image(udg_array, x=5)
        self._test_image(udg_array, y=7)
        self._test_image(udg_array, x=1, y=2, width=9, height=11)

    def test_unmasked_bd1_flashing(self):
        # Unmasked image, bit depth 1, >3 UDGs
        udg = Udg(177, (164,) * 8)
        udg_array = [[udg] * 4]
        self._test_image(udg_array)

    def test_unmasked_bd1_scaled(self):
        # Unmasked image, bit depth 1, scales 1-2, >3 UDGs
        udg = Udg(49, (164,) * 8)
        udg_array = [[udg] * 4]
        self._test_image(udg_array)
        self._test_image(udg_array, scale=2)
        return udg_array

    def test_unmasked_bd2_cropped(self):
        # Unmasked image, bit depth 2, cropped
        udg1 = Udg(30, (170,) * 8)
        udg2 = Udg(28, (81,) * 8)
        udg_array = [[udg1, udg2]] * 2
        self._test_image(udg_array, height=12)
        self._test_image(udg_array, x=5)
        self._test_image(udg_array, width=11)
        self._test_image(udg_array, y=7)
        self._test_image(udg_array, x=1, y=2, width=10, height=11)

    def test_unmasked_bd2_cropped(self):
        # Unmasked image, bit depth 2, cropped
        udg1 = Udg(30, (170,) * 8)
        udg2 = Udg(28, (81,) * 8)
        udg_array = [[udg1, udg2]] * 2
        self._test_image(udg_array, width=11)
        self._test_image(udg_array, height=12)
        self._test_image(udg_array, x=5)
        self._test_image(udg_array, y=7)
        self._test_image(udg_array, x=1, y=2, width=10, height=11)

    def test_unmasked_bd2_flashing(self):
        # Unmasked image, bit depth 2, flashing, scales 1-2
        udg1 = Udg(56, (93,) * 8)
        udg2 = Udg(177, (162,) * 8)
        udg_array = [[udg1, udg2]]
        self._test_image(udg_array)
        self._test_image(udg_array, scale=2)
        return udg_array

    def test_unmasked_bd2_scaled(self):
        # Unmasked image, bit depth 2, scales 1-2
        udg1 = Udg(56, (93,) * 8)
        udg2 = Udg(49, (162,) * 8)
        udg_array = [[udg1, udg2]]
        self._test_image(udg_array)
        self._test_image(udg_array, scale=2)
        return udg_array

    def test_unmasked_bd4_all_colours_cropped(self):
        # Unmasked image, 15 colours, colours cropped off
        udg1 = Udg(56, (15,) * 8)  # white, black
        udg2 = Udg(10, (15,) * 8)  # blue, red
        udg3 = Udg(28, (15,) * 8)  # magenta, green
        udg4 = Udg(46, (15,) * 8)  # cyan, yellow
        udg5 = Udg(120, (0,) * 8)  # bright white
        udg6 = Udg(74, (15,) * 8)  # bright blue, bright red
        udg7 = Udg(92, (15,) * 8)  # bright magenta, bright green
        udg8 = Udg(110, (15,) * 8) # bright cyan, bright yellow
        udg_array = [[udg1, udg2, udg3, udg4], [udg5, udg6, udg7, udg8]]
        self._test_image(udg_array, scale=2, x=1)
        self._test_image(udg_array, scale=3, x=12)
        self._test_image(udg_array, scale=2, x=20)
        self._test_image(udg_array, scale=2, width=56)
        self._test_image(udg_array, scale=2, width=44)
        self._test_image(udg_array, scale=2, y=1)
        self._test_image(udg_array, scale=2, y=24)
        self._test_image(udg_array, scale=2, height=18)
        self._test_image(udg_array, scale=2, height=14)

    def test_unmasked_bd4_all_colours(self):
        # Unmasked image, 15 colours
        udg1 = Udg(56, (15,) * 8)  # white, black
        udg2 = Udg(10, (15,) * 8)  # blue, red
        udg3 = Udg(28, (15,) * 8)  # magenta, green
        udg4 = Udg(46, (15,) * 8)  # cyan, yellow
        udg5 = Udg(120, (0,) * 8)  # bright white
        udg6 = Udg(74, (15,) * 8)  # bright blue, bright red
        udg7 = Udg(92, (15,) * 8)  # bright magenta, bright green
        udg8 = Udg(110, (15,) * 8) # bright cyan, bright yellow
        udg_array = [[udg1, udg2, udg3, udg4, udg5, udg6, udg7, udg8, udg1]] * 2
        self._test_image(udg_array)

    def test_unmasked_bd4_cropped(self):
        # Unmasked image, bit depth 4, cropped
        udg1 = Udg(30, (170,) * 8)
        udg2 = Udg(28, (81,) * 8)
        udg3 = Udg(5, (129,) * 8)
        udg_array = [[udg1, udg2], [udg3, udg1]]
        self._test_image(udg_array, height=9)
        self._test_image(udg_array, x=3)
        self._test_image(udg_array, width=11)
        self._test_image(udg_array, y=7)
        self._test_image(udg_array, x=2, y=1, width=11, height=9)

    def test_unmasked_bd4_cropped(self):
        # Unmasked image, bit depth 4, cropped
        udg1 = Udg(30, (170,) * 8)
        udg2 = Udg(28, (81,) * 8)
        udg3 = Udg(5, (129,) * 8)
        udg_array = [[udg1, udg2], [udg3, udg1]]
        self._test_image(udg_array, width=11)
        self._test_image(udg_array, height=9)
        self._test_image(udg_array, x=3)
        self._test_image(udg_array, y=7)
        self._test_image(udg_array, x=2, y=1, width=11, height=9)

    def test_unmasked_bd4_flashing(self):
        # Unmasked image, bit depth 4, flashing
        udg1 = Udg(49, (136,) * 8)
        udg2 = Udg(170, (68,) * 8)
        udg3 = Udg(35, (34,) * 8)
        udg_array = [[udg1, udg2, udg3]]
        self._test_image(udg_array)

    def test_unmasked_bd4_scaled(self):
        # Unmasked image, bit depth 4, scales 1-2
        udg1 = Udg(49, (136,) * 8)
        udg2 = Udg(42, (68,) * 8)
        udg3 = Udg(35, (34,) * 8)
        udg_array = [[udg1, udg2, udg3]]
        self._test_image(udg_array)
        self._test_image(udg_array, scale=2)

    def test_unmasked_flashing(self):
        # Unmasked image, flashing
        udg = Udg(184, (240,) * 8)
        udg_array = [[udg]]
        self._test_image(udg_array)

    def test_unmasked_flashing_no_animation(self):
        # Unmasked image, flashing, no animation
        iw_args = {'options': {self.animation_flag: 0}}
        udg = Udg(184, (240,) * 8)
        udg_array = [[udg]]
        self._test_image(udg_array, iw_args=iw_args)

class PngWriterTest(SkoolKitTestCase, ImageWriterTest):
    def setUp(self):
        SkoolKitTestCase.setUp(self)
        self.animation_flag = PNG_ENABLE_ANIMATION
        self.alpha_option = {PNG_ALPHA: 127}

    def _get_word(self, stream, index):
        return index + 2, 256 * stream[index] + stream[index + 1]

    def _get_crc(self, byte_list):
        crc = CRC_MASK
        for b in byte_list:
            crc = CRC_TABLE[(crc ^ b) & 255] ^ (crc >> 8)
        return crc ^ CRC_MASK

    def _get_chunk_type(self, stream, index):
        return index + 4, stream[index:index + 4]

    def _check_signature(self, img_bytes):
        i = len(PNG_SIGNATURE)
        self.assertEqual(img_bytes[:i], PNG_SIGNATURE)
        return i

    def _check_ihdr(self, img_bytes, index, exp_width, exp_height, exp_bit_depth):
        i = index
        i, chunk_length = self._get_dword(img_bytes, i)
        self.assertEqual(chunk_length, 13)
        ihdr_start = i
        i, chunk_type = self._get_chunk_type(img_bytes, i)
        self.assertEqual(chunk_type, IHDR)
        i, image_width = self._get_dword(img_bytes, i)
        self.assertEqual(image_width, exp_width)
        i, image_height = self._get_dword(img_bytes, i)
        self.assertEqual(image_height, exp_height)
        i, bit_depth = self._get_num(img_bytes, i)
        self.assertEqual(bit_depth, exp_bit_depth)
        i, colour_type = self._get_num(img_bytes, i)
        self.assertEqual(colour_type, 3)
        i, compression_method = self._get_num(img_bytes, i)
        self.assertEqual(compression_method, 0)
        i, filter_method = self._get_num(img_bytes, i)
        self.assertEqual(filter_method, 0)
        i, interlace_method = self._get_num(img_bytes, i)
        self.assertEqual(interlace_method, 0)
        ihdr_end = i
        i, ihdr_crc = self._get_dword(img_bytes, i)
        self.assertEqual(ihdr_crc, self._get_crc(img_bytes[ihdr_start:ihdr_end]))
        return i

    def _check_plte(self, img_bytes, index, exp_palette):
        i = index
        i, chunk_length = self._get_dword(img_bytes, i)
        self.assertEqual(chunk_length, len(exp_palette) * 3)
        plte_start = i
        i, chunk_type = self._get_chunk_type(img_bytes, i)
        self.assertEqual(chunk_type, PLTE)
        palette = [img_bytes[j:j + 3] for j in range(i, i + chunk_length, 3)]
        i += chunk_length
        self.assertEqual(sorted(palette), sorted(exp_palette))
        plte_end = i
        i, plte_crc = self._get_dword(img_bytes, i)
        self.assertEqual(plte_crc, self._get_crc(img_bytes[plte_start:plte_end]))
        return i, palette

    def _check_trns(self, img_bytes, index, exp_alpha):
        i = index
        i, chunk_length = self._get_dword(img_bytes, i)
        self.assertEqual(chunk_length, 1)
        trns_start = i
        i, chunk_type = self._get_chunk_type(img_bytes, i)
        self.assertEqual(chunk_type, TRNS)
        alpha = img_bytes[i]
        self.assertEqual(alpha, exp_alpha)
        i += chunk_length
        trns_end = i
        i, trns_crc = self._get_dword(img_bytes, i)
        self.assertEqual(trns_crc, self._get_crc(img_bytes[trns_start:trns_end]))
        return i

    def _check_fctl(self, img_bytes, index, exp_frame_num, exp_width, exp_height, exp_x_offset=0, exp_y_offset=0):
        i = index
        i, chunk_length = self._get_dword(img_bytes, i)
        self.assertEqual(chunk_length, 26)
        fctl_start = i
        i, chunk_type = self._get_chunk_type(img_bytes, i)
        self.assertEqual(chunk_type, FCTL)
        i, frame_num = self._get_dword(img_bytes, i)
        self.assertEqual(frame_num, exp_frame_num)
        i, width = self._get_dword(img_bytes, i)
        self.assertEqual(width, exp_width)
        i, height = self._get_dword(img_bytes, i)
        self.assertEqual(height, exp_height)
        i, x_offset = self._get_dword(img_bytes, i)
        self.assertEqual(x_offset, exp_x_offset)
        i, y_offset = self._get_dword(img_bytes, i)
        self.assertEqual(y_offset, exp_y_offset)
        i, delay_num = self._get_word(img_bytes, i)
        self.assertEqual(delay_num, 8)
        i, delay_den = self._get_word(img_bytes, i)
        self.assertEqual(delay_den, 25)
        dispose_op = img_bytes[i]
        self.assertEqual(dispose_op, 0)
        i += 1
        blend_op = img_bytes[i]
        self.assertEqual(blend_op, 0)
        i += 1
        fctl_end = i
        i, fctl_crc = self._get_dword(img_bytes, i)
        self.assertEqual(fctl_crc, self._get_crc(img_bytes[fctl_start:fctl_end]))
        return i

    def _get_pixels_from_image_data(self, bit_depth, palette, image_data, width):
        if bit_depth == 4:
            scanline_len = (2 if width & 1 else 1) + width // 2
        elif bit_depth == 2:
            scanline_len = (2 if width & 3 else 1) + width // 4
        else:
            scanline_len = (2 if width & 7 else 1) + width // 8
        pixels = []
        for i, byte in enumerate(image_data):
            if i % scanline_len == 0:
                self.assertEqual(byte, 0)
                if i:
                    pixels.append(pixel_row[:width])
                pixel_row = []
            elif bit_depth == 4:
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
        return pixels

    def _check_fdat(self, img_bytes, index, bit_depth, palette, exp_pixels, width):
        i = index
        i, chunk_length = self._get_dword(img_bytes, i)
        fdat_start = i
        i, chunk_type = self._get_chunk_type(img_bytes, i)
        self.assertEqual(chunk_type, FDAT)
        fdat_end = i + chunk_length
        i, seq_num = self._get_dword(img_bytes, i)
        self.assertEqual(seq_num, 2)
        if PY3:
            image_data_z = bytes(img_bytes[i:fdat_end])
            image_data = list(zlib.decompress(image_data_z))
        else:
            image_data_z = ''.join(chr(b) for b in img_bytes[i:fdat_end])
            image_data = [ord(c) for c in zlib.decompress(image_data_z)]
        pixels = self._get_pixels_from_image_data(bit_depth, palette, image_data, width)
        self.assertEqual(len(pixels[0]), len(exp_pixels[0])) # width
        self.assertEqual(len(pixels), len(exp_pixels)) # height
        self.assertEqual(pixels, exp_pixels)
        i, fdat_crc = self._get_dword(img_bytes, fdat_end)
        self.assertEqual(fdat_crc, self._get_crc(img_bytes[fdat_start:fdat_end]))
        return i

    def _check_idat(self, img_bytes, index, bit_depth, palette, exp_pixels, width):
        i = index
        i, chunk_length = self._get_dword(img_bytes, i)
        idat_start = i
        i, chunk_type = self._get_chunk_type(img_bytes, i)
        self.assertEqual(chunk_type, IDAT)
        idat_end = i + chunk_length
        if PY3:
            image_data_z = bytes(img_bytes[i:idat_end])
            image_data = list(zlib.decompress(image_data_z))
        else:
            image_data_z = ''.join(chr(b) for b in img_bytes[i:idat_end])
            image_data = [ord(c) for c in zlib.decompress(image_data_z)]
        pixels = self._get_pixels_from_image_data(bit_depth, palette, image_data, width)
        self.assertEqual(len(pixels[0]), len(exp_pixels[0])) # width
        self.assertEqual(len(pixels), len(exp_pixels)) # height
        self.assertEqual(pixels, exp_pixels)
        i, idat_crc = self._get_dword(img_bytes, idat_end)
        self.assertEqual(idat_crc, self._get_crc(img_bytes[idat_start:idat_end]))
        return i

    def _test_method(self, method_name, udg_array, scale=1, mask=False, flash=0, x=0, y=0, width=None, height=None):
        image_writer = ImageWriter()
        png_writer = image_writer.png_writer
        method = getattr(png_writer, '_build_image_data_{0}'.format(method_name))

        t_width = len(udg_array[0])
        t_height = len(udg_array)
        full_width = 8 * t_width * scale
        full_height = 8 * t_height * scale
        width = min(width or full_width, full_width - x)
        height = min(height or full_height, full_height - y)
        full_size = 1 if width == full_width and height == full_height else 0
        use_flash = image_writer.options[PNG_ENABLE_ANIMATION]
        palette, attr_map, trans, flash_rect = image_writer._get_palette(udg_array, scale, mask, x, y, width, height, full_size, use_flash)
        palette = [palette[i:i + 3] for i in range(0, len(palette), 3)]

        exp_palette, exp_trans, exp_pixels, exp_pixels2, frame2_xy = self._get_pixels_from_udg_array(udg_array, scale, mask, x, y, width, height)
        self.assertEqual(sorted(palette), sorted(exp_palette))
        self.assertEqual(trans, exp_trans)
        self.assertEqual(flash_rect, frame2_xy)

        palette_size = len(palette)
        if palette_size > 4:
            bit_depth = 4
        elif palette_size > 2:
            bit_depth = 2
        else:
            bit_depth = 1
        image_data_z = method(udg_array, scale, attr_map, trans, flash, x, y, width, height, bit_depth)
        if PY3:
            image_data = list(zlib.decompress(image_data_z))
        else:
            image_data = [ord(c) for c in zlib.decompress(bytes(image_data_z))]
        pixels = self._get_pixels_from_image_data(bit_depth, palette, image_data, width)
        self.assertEqual(len(pixels[0]), len(exp_pixels[0])) # width
        self.assertEqual(len(pixels), len(exp_pixels)) # height
        self.assertEqual(pixels, exp_pixels)

    def _test_image(self, udg_array, exp_pixels=None, scale=1, mask=False, x=0, y=0, width=None, height=None, iw_args=None):
        image_writer = ImageWriter(**(iw_args or {}))
        img_bytes = self._get_image_data(image_writer, udg_array, 'png', scale, mask, x, y, width, height)

        exp_pixels2 = None
        if exp_pixels is None:
            exp_palette, has_trans, exp_pixels, exp_pixels2, frame2_xy = self._get_pixels_from_udg_array(udg_array, scale, mask, x, y, width, height)
            if not image_writer.options[PNG_ENABLE_ANIMATION]:
                exp_pixels2 = None
        else:
            exp_palette = []
            for row in exp_pixels:
                for pixel in row:
                    if pixel not in exp_palette:
                        exp_palette.append(pixel)
        palette_size = len(exp_palette)
        if palette_size > 4:
            exp_bit_depth = 4
        elif palette_size > 2:
            exp_bit_depth = 2
        else:
            exp_bit_depth = 1

        # PNG signature
        i = self._check_signature(img_bytes)

        # IHDR
        exp_width = 8 * scale * len(udg_array[0]) - x if width is None else width
        exp_height = 8 * scale * len(udg_array) - y if height is None else height
        i = self._check_ihdr(img_bytes, i, exp_width, exp_height, exp_bit_depth)

        # PLTE
        i, palette = self._check_plte(img_bytes, i, exp_palette)

        # tRNS
        alpha = image_writer.options[PNG_ALPHA]
        if alpha < 255 and has_trans:
            i = self._check_trns(img_bytes, i, alpha)

        # acTL and fcTL
        if exp_pixels2:
            self.assertEqual(img_bytes[i:i + len(ACTL_CHUNK)], ACTL_CHUNK)
            i += len(ACTL_CHUNK)
            i = self._check_fctl(img_bytes, i, 0, exp_width, exp_height)

        # IDAT
        i = self._check_idat(img_bytes, i, exp_bit_depth, palette, exp_pixels, exp_width)

        # fcTL and fdAT
        if exp_pixels2:
            exp_width = len(exp_pixels2[0])
            exp_height = len(exp_pixels2)
            exp_x_offset, exp_y_offset = frame2_xy
            i = self._check_fctl(img_bytes, i, 1, exp_width, exp_height, exp_x_offset, exp_y_offset)
            i = self._check_fdat(img_bytes, i, exp_bit_depth, palette, exp_pixels2, exp_width)

        # IEND
        self.assertEqual(img_bytes[i:], IEND_CHUNK)

    def test_unmasked_bd1_scaled(self):
        # Unmasked image, bit depth 1, scales 1-13, >3 UDGs
        udg_array = ImageWriterTest.test_unmasked_bd1_scaled(self)
        self._test_image(udg_array, scale=3)
        self._test_image(udg_array, scale=4)
        self._test_image(udg_array, scale=5)
        self._test_image(udg_array, scale=6)
        self._test_image(udg_array, scale=7)
        self._test_image(udg_array, scale=8)
        self._test_image(udg_array, scale=9)
        self._test_image(udg_array, scale=10)
        self._test_image(udg_array, scale=11)
        self._test_image(udg_array, scale=12)
        self._test_image(udg_array, scale=13)

    def test_unmasked_bd2_flashing(self):
        # Unmasked image, bit depth 2, flashing, scales 1-5
        udg_array = ImageWriterTest.test_unmasked_bd2_flashing(self)
        self._test_image(udg_array, scale=3)
        self._test_image(udg_array, scale=4)
        self._test_image(udg_array, scale=5)

    def test_unmasked_bd2_scaled(self):
        # Unmasked image, bit depth 2, scales 1-5
        udg_array = ImageWriterTest.test_unmasked_bd2_scaled(self)
        self._test_image(udg_array, scale=3)
        self._test_image(udg_array, scale=4)
        self._test_image(udg_array, scale=5)

    def test_bd4_nt_nf(self):
        udg_array = [[Udg(attr, (15,) * 8) for attr in (1, 19, 37, 55)]]
        method_name = 'bd4_nt_nf'
        self._test_method(method_name, udg_array, scale=1)
        self._test_method(method_name, udg_array, scale=2)
        self._test_method(method_name, udg_array, scale=3)
        self._test_method(method_name, udg_array, scale=4)

    def test_bd2_nt_nf(self):
        udg_array = [[Udg(attr, (85,) * 8) for attr in (1, 19)]]
        method_name = 'bd2_nt_nf'
        self._test_method(method_name, udg_array, scale=1)
        self._test_method(method_name, udg_array, scale=2)
        self._test_method(method_name, udg_array, scale=3)
        self._test_method(method_name, udg_array, scale=4)
        self._test_method(method_name, udg_array, scale=5)

    def test_bd2_at_nf(self):
        udg_array = [[Udg(56, (15,) * 8, (207,) * 8)]]
        method_name = 'bd2_at_nf'
        self._test_method(method_name, udg_array, scale=2, mask=True)
        self._test_method(method_name, udg_array, scale=4, mask=True)

    def test_bd1_nt_nf_1udg(self):
        udg_array = [[Udg(34, (170,) * 8)]]
        method_name = 'bd1_nt_nf_1udg'
        self._test_method(method_name, udg_array, scale=1)
        self._test_method(method_name, udg_array, scale=2)
        self._test_method(method_name, udg_array, scale=4)
        self._test_method(method_name, udg_array, scale=8)

    def test_bd1_method(self):
        iw = PngWriter()
        self.assertEquals(iw._bd1_method(5, 0, 0), iw._build_image_data_bd1)
        self.assertEquals(iw._bd1_method(6, 0, 0), iw._build_image_data_bd1)
        self.assertEquals(iw._bd1_method(4, 2, 0), iw._build_image_data_bd1)
        self.assertEquals(iw._bd1_method(3, 2, 0), iw._build_image_data_bd1)
        self.assertEquals(iw._bd1_method(2, 3, 0), iw._build_image_data_bd_any)

    def test_bd2_at_nf_method(self):
        iw = PngWriter()
        self.assertEquals(iw._bd2_at_nf_method(0, 0, 2), iw._build_image_data_bd2_at_nf)
        self.assertEquals(iw._bd2_at_nf_method(0, 0, 4), iw._build_image_data_bd2_at_nf)
        self.assertEquals(iw._bd2_at_nf_method(0, 0, 8), iw._build_image_data_bd2_at_nf)
        self.assertEquals(iw._bd2_at_nf_method(0, 0, 3), iw._build_image_data_bd2)
        self.assertEquals(iw._bd2_at_nf_method(0, 0, 5), iw._build_image_data_bd2)
        self.assertEquals(iw._bd2_at_nf_method(0, 0, 6), iw._build_image_data_bd2)
        self.assertEquals(iw._bd2_at_nf_method(0, 0, 3), iw._build_image_data_bd2)

    def test_bd4_nt_nf_method(self):
        iw = PngWriter()
        self.assertEquals(iw._bd4_nt_nf_method(35, 5, 1), iw._build_image_data_bd4_nt_nf)
        self.assertEquals(iw._bd4_nt_nf_method(12, 6, 1), iw._build_image_data_bd4)
        self.assertEquals(iw._bd4_nt_nf_method(50, 5, 2), iw._build_image_data_bd4_nt_nf)
        self.assertEquals(iw._bd4_nt_nf_method(16, 6, 2), iw._build_image_data_bd4)
        self.assertEquals(iw._bd4_nt_nf_method(195, 5, 3), iw._build_image_data_bd4_nt_nf)
        self.assertEquals(iw._bd4_nt_nf_method(233, 6, 3), iw._build_image_data_bd4)

class GifWriterTest(ImageWriterTest):
    def setUp(self):
        self.animation_flag = GIF_ENABLE_ANIMATION
        self.alpha_option = {GIF_TRANSPARENCY: 1}

    def _get_word(self, stream, index):
        return index + 2, 256 * stream[index + 1] + stream[index]

    def _check_header(self, img_bytes):
        i = len(GIF_HEADER)
        self.assertEqual(img_bytes[:i], GIF_HEADER)
        return i

    def _check_lsd(self, img_bytes, index, exp_width, exp_height):
        i, width = self._get_word(img_bytes, index)
        self.assertEqual(width, exp_width)
        i, height = self._get_word(img_bytes, i)
        self.assertEqual(height, exp_height)
        return i

    def _check_gct(self, img_bytes, index, exp_palette):
        i, gct_flags = self._get_num(img_bytes, index)
        exp_palette_size = len(exp_palette)
        if exp_palette_size > 8:
            exp_gct_size = 3
        elif exp_palette_size > 4:
            exp_gct_size = 2
        elif exp_palette_size > 2:
            exp_gct_size = 1
        else:
            exp_gct_size = 0
        exp_gct_flags = 240 + exp_gct_size
        self.assertEqual(gct_flags, exp_gct_flags)
        i, bg_index = self._get_num(img_bytes, i)
        self.assertEqual(bg_index, 0)
        i, aspect_ratio = self._get_num(img_bytes, i)
        self.assertEqual(aspect_ratio, 0)
        gct = [img_bytes[j:j + 3] for j in range(i, i + 3 * exp_palette_size, 3)]
        self.assertEqual(sorted(gct), sorted(exp_palette))
        i += 3 * len(gct)
        full_gct_len = 1 << (1 + exp_gct_size)
        for n in range(full_gct_len - len(gct)):
            self.assertEqual(img_bytes[i:i + 3], [0, 0, 0])
            i += 3
        return i, gct

    def _check_gce(self, img_bytes, index, t_flag, delay):
        self.assertEqual(img_bytes[index:index + 8], [33, 249, 4, t_flag, delay, 0, 0, 0])
        return index + 8

    def _check_image_descriptor(self, img_bytes, index, exp_width, exp_height, exp_x_offset=0, exp_y_offset=0):
        i = index
        self.assertEqual(img_bytes[i], 44)
        i += 1
        i, x_offset = self._get_word(img_bytes, i)
        self.assertEqual(x_offset, exp_x_offset)
        i, y_offset = self._get_word(img_bytes, i)
        self.assertEqual(y_offset, exp_y_offset)
        i, width = self._get_word(img_bytes, i)
        self.assertEqual(width, exp_width)
        i, height = self._get_word(img_bytes, i)
        self.assertEqual(height, exp_height)
        i, lct = self._get_num(img_bytes, i)
        self.assertEqual(lct, 0)
        return i

    def _get_pixels_from_image_data(self, lzw_data, min_code_size, palette, width):
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
        output = []
        prefix = None
        while 1:
            if len(lzw_bits) < code_size:
                self.fail('Unexpected end of LZW stream')

            # Collect a code from the LZW stream
            code = 0
            m = 1
            for k in range(code_size):
                code += m * lzw_bits.pop()
                m *= 2

            if code == clear_code:
                # Found a CLEAR code
                d = init_d.copy()
                code_size = min_code_size + 1
                prefix = None
                continue
            elif code == stop_code:
                # Found the STOP code
                break

            # Update the value of the last code added to the dictionary
            out = d[code]
            if out is None:
                out = prefix + prefix[0:1]
                d[code] = out
            elif prefix:
                d[len(d) - 1] = prefix + out[0:1]

            # Increase the code size if necessary
            if len(d) == 1 << code_size and len(lzw_bits) > code_size and code_size < 12:
                code_size += 1

            output.extend(out)
            prefix = out
            d[len(d)] = None

        pixels = [[]]
        for pixel in output:
            if len(pixels[-1]) == width:
                pixels.append([])
            pixels[-1].append(palette[pixel])
        return pixels

    def _check_image_data(self, img_bytes, index, width, height, palette, exp_min_code_size, exp_pixels):
        i, min_code_size = self._get_num(img_bytes, index)
        self.assertEqual(min_code_size, exp_min_code_size)

        lzw_data = []
        while True:
            i, length = self._get_num(img_bytes, i)
            if length == 0:
                break
            lzw_data.extend(img_bytes[i:i + length])
            i += length

        pixels = self._get_pixels_from_image_data(lzw_data, min_code_size, palette, width)
        self.assertEqual(len(pixels[0]), len(exp_pixels[0])) # width
        self.assertEqual(len(pixels), len(exp_pixels)) # height
        self.assertEqual(pixels, exp_pixels)

        return i

    def _test_image(self, udg_array, exp_pixels=None, scale=1, mask=False, x=0, y=0, width=None, height=None, iw_args=None):
        if iw_args is None:
            iw_args = {}
        options = iw_args.setdefault('options', {})
        options.update(self.iw_options)
        image_writer = ImageWriter(**iw_args)
        img_bytes = self._get_image_data(image_writer, udg_array, 'gif', scale, mask, x, y, width, height)

        exp_pixels2 = None
        if exp_pixels is None:
            exp_palette, has_trans, exp_pixels, exp_pixels2, frame2_xy = self._get_pixels_from_udg_array(udg_array, scale, mask, x, y, width, height)
            if not image_writer.options[GIF_ENABLE_ANIMATION]:
                exp_pixels2 = None
        else:
            exp_palette = []
            for row in exp_pixels:
                for pixel in row:
                    if pixel not in exp_palette:
                        exp_palette.append(pixel)
            # Assume that there are transparent bits if mask is True
            has_trans = mask

        t_flag = 1 if image_writer.options[GIF_TRANSPARENCY] and has_trans else 0

        if image_writer.options[GIF_COMPRESSION]:
            palette_size = len(exp_palette)
            if palette_size > 8:
                exp_min_code_size = 4
            elif palette_size > 4:
                exp_min_code_size = 3
            else:
                exp_min_code_size = 2
        else:
            exp_min_code_size = 7

        # GIF header
        i = self._check_header(img_bytes)

        # Logical screen descriptor
        exp_width = 8 * scale * len(udg_array[0]) - x if width is None else width
        exp_height = 8 * scale * len(udg_array) - y if height is None else height
        i = self._check_lsd(img_bytes, i, exp_width, exp_height)

        # Global Colour Table
        i, palette = self._check_gct(img_bytes, i, exp_palette)

        # AEB and GCE (frame 1)
        if exp_pixels2:
            aeb_len = len(AEB)
            self.assertEqual(img_bytes[i:i + aeb_len], AEB)
            i += aeb_len
            i = self._check_gce(img_bytes, i, t_flag, GIF_FRAME_DELAY)
        elif t_flag:
            i = self._check_gce(img_bytes, i, t_flag, 0)

        # Frame 1 image descriptor
        i = self._check_image_descriptor(img_bytes, i, exp_width, exp_height)

        # Frame 1 image data
        i = self._check_image_data(img_bytes, i, exp_width, exp_height, palette, exp_min_code_size, exp_pixels)

        # Frame 2
        if exp_pixels2:
            i = self._check_gce(img_bytes, i, t_flag, GIF_FRAME_DELAY)
            exp_width = len(exp_pixels2[0])
            exp_height = len(exp_pixels2)
            exp_x_offset, exp_y_offset = frame2_xy
            i = self._check_image_descriptor(img_bytes, i, exp_width, exp_height, exp_x_offset, exp_y_offset)
            i = self._check_image_data(img_bytes, i, exp_width, exp_height, palette, exp_min_code_size, exp_pixels2)

        # GIF trailer
        self.assertEqual(img_bytes[i], GIF_TRAILER)

class UncompressedGifWriterTest(SkoolKitTestCase, GifWriterTest):
    def setUp(self):
        SkoolKitTestCase.setUp(self)
        GifWriterTest.setUp(self)
        self.iw_options = {GIF_COMPRESSION: 0}

class CompressedGifWriterTest(SkoolKitTestCase, GifWriterTest):
    def setUp(self):
        SkoolKitTestCase.setUp(self)
        GifWriterTest.setUp(self)
        self.iw_options = {GIF_COMPRESSION: 1}

    def _bin_digits(self, n):
        digits = str(n & 1)
        n >>= 1
        while n:
            digits = str(n & 1) + digits
            n >>= 1
        return digits

    def test_lzw_clear_code(self):
        pixels = ''
        for n in range(3510):
            pixels += self._bin_digits(n)
        pixels += '0' * (64 - (len(pixels) & 63))
        num_udgs = len(pixels) // 64
        udgs = []
        for i in range(num_udgs):
            udg_data = []
            for j in range(8):
                index = 8 * (i + num_udgs * j)
                udg_data.append(int(pixels[index:index + 8], 2))
            udgs.append(Udg(56, udg_data))
        self._test_image([udgs])

if __name__ == '__main__':
    unittest.main()
