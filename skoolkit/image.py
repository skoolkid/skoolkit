# -*- coding: utf-8 -*-

# Copyright 2012-2015 Richard Dymond (rjdymond@gmail.com)
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

"""
Defines the :class:`ImageWriter` class.
"""

from skoolkit.gifwriter import GifWriter
from skoolkit.pngwriter import PngWriter

#: Colour name for the transparent colour used in masked images.
TRANSPARENT = 'TRANSPARENT'
#: Colour name for black.
BLACK = 'BLACK'
#: Colour name for blue.
BLUE = 'BLUE'
#: Colour name for red.
RED = 'RED'
#: Colour name for magenta.
MAGENTA = 'MAGENTA'
#: Colour name for green.
GREEN = 'GREEN'
#: Colour name for cyan.
CYAN = 'CYAN'
#: Colour name for yellow.
YELLOW = 'YELLOW'
#: Colour name for white.
WHITE = 'WHITE'
#: Colour name for bright blue.
BRIGHT_BLUE = 'BRIGHT_BLUE'
#: Colour name for bright red.
BRIGHT_RED = 'BRIGHT_RED'
#: Colour name for bright magenta.
BRIGHT_MAGENTA = 'BRIGHT_MAGENTA'
#: Colour name for bright green.
BRIGHT_GREEN = 'BRIGHT_GREEN'
#: Colour name for bright cyan.
BRIGHT_CYAN = 'BRIGHT_CYAN'
#: Colour name for bright yellow.
BRIGHT_YELLOW = 'BRIGHT_YELLOW'
#: Colour name for bright white.
BRIGHT_WHITE = 'BRIGHT_WHITE'

#: Option name that specifies the default image format.
DEFAULT_FORMAT = 'DefaultFormat'
#: Option name that specifies the PNG compression level.
PNG_COMPRESSION_LEVEL = 'PNGCompressionLevel'
#: Option name that specifies the PNG alpha value.
PNG_ALPHA = 'PNGAlpha'
#: Option name that specifies whether to create animated PNGs in APNG format
#: for images that contain flashing cells.
PNG_ENABLE_ANIMATION = 'PNGEnableAnimation'
#: Option name that specifies whether to create animated GIFs for images that
#: contain flashing cells.
GIF_ENABLE_ANIMATION = 'GIFEnableAnimation'
#: Option name that specifies whether to create transparent GIFs for masked
#: images.
GIF_TRANSPARENCY = 'GIFTransparency'

PNG_FORMAT = 'png'
GIF_FORMAT = 'gif'

class ImageWriter:
    """Writes PNG and GIF images.

    :type palette: dict
    :param palette: Colour palette replacements to use.
    :type options: dict
    :param options: Options.
    """
    def __init__(self, palette=None, options=None):
        self.options = self._get_default_options()
        if options:
            for k, v in options.items():
                if k == DEFAULT_FORMAT:
                    self.options[k] = v
                else:
                    try:
                        self.options[k] = int(v)
                    except ValueError:
                        pass
        full_palette = self._get_default_palette()
        if palette:
            full_palette.update(palette)
        self._create_colours(full_palette)
        self._create_attr_index()
        self.default_format = self.options[DEFAULT_FORMAT]
        self.animation = {
            PNG_FORMAT: self.options[PNG_ENABLE_ANIMATION],
            GIF_FORMAT: self.options[GIF_ENABLE_ANIMATION]
        }
        self.masks = {
            0: NoMask(),
            1: OrAndMask(),
            2: AndOrMask()
        }
        self.writers = {
            PNG_FORMAT: PngWriter(self.options[PNG_ALPHA] & 255, self.options[PNG_COMPRESSION_LEVEL], self.masks),
            GIF_FORMAT: GifWriter(self.options[GIF_TRANSPARENCY], self.masks)
        }

    def write_image(self, frames, img_file, img_format):
        use_flash = len(frames) == 1 and self.animation.get(img_format)
        attrs = set()
        colours = set()
        has_trans = False
        for frame in frames:
            f_colours, f_attrs, flash_rect = self._get_colours(frame, use_flash)
            colours.update(f_colours)
            attrs.update(f_attrs)
            has_trans = has_trans or frame.has_trans
        palette, attr_map = self._get_palette(colours, attrs, has_trans)
        self.writers[img_format].write_image(frames, img_file, palette, attr_map, has_trans, flash_rect)

    def _get_default_palette(self):
        return  {
            TRANSPARENT: (0, 254, 0),
            BLACK: (0, 0, 0),
            BLUE: (0, 0, 197),
            RED: (197, 0, 0),
            MAGENTA: (197, 0, 197),
            GREEN: (0, 198, 0),
            CYAN: (0, 198, 197),
            YELLOW: (197, 198, 0),
            WHITE: (205, 198, 205),
            BRIGHT_BLUE: (0, 0, 255),
            BRIGHT_RED: (255, 0, 0),
            BRIGHT_MAGENTA: (255, 0, 255),
            BRIGHT_GREEN: (0, 255, 0),
            BRIGHT_CYAN: (0, 255, 255),
            BRIGHT_YELLOW: (255, 255, 0),
            BRIGHT_WHITE: (255, 255, 255)
        }

    def _get_default_options(self):
        return {
            DEFAULT_FORMAT: PNG_FORMAT,
            PNG_COMPRESSION_LEVEL: 9,
            PNG_ENABLE_ANIMATION: 1,
            PNG_ALPHA: 255,
            GIF_ENABLE_ANIMATION: 1,
            GIF_TRANSPARENCY: 0
        }

    def _create_colours(self, palette):
        colours = []
        colours.append(palette[TRANSPARENT])
        colours.append(palette[BLACK])
        colours.append(palette[BLUE])
        colours.append(palette[RED])
        colours.append(palette[MAGENTA])
        colours.append(palette[GREEN])
        colours.append(palette[CYAN])
        colours.append(palette[YELLOW])
        colours.append(palette[WHITE])
        colours.append(palette[BRIGHT_BLUE])
        colours.append(palette[BRIGHT_RED])
        colours.append(palette[BRIGHT_MAGENTA])
        colours.append(palette[BRIGHT_GREEN])
        colours.append(palette[BRIGHT_CYAN])
        colours.append(palette[BRIGHT_YELLOW])
        colours.append(palette[BRIGHT_WHITE])
        self.colours = colours

    def _create_attr_index(self):
        self.attr_index = {}
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
            self.attr_index[attr] = (paper, ink)

    def _get_colours(self, frame, use_flash=False):
        if not frame.cropped:
            return self._get_all_colours(frame, use_flash)

        udg_array = frame.udgs
        null_mask = frame.mask == 0
        scale = frame.scale
        mask = self.masks[frame.mask]
        x0, y0, width, height = frame.x, frame.y, frame.width, frame.height
        x1 = x0 + width
        y1 = y0 + height
        attrs = set()
        colours = set()
        has_masks = 0
        all_masked = 1
        flashing = False
        inc = 8 * scale
        min_col = x0 // inc
        max_col = x1 // inc
        min_row = y0 // inc
        max_row = y1 // inc
        x0_floor = inc * min_col
        y0_floor = inc * min_row
        x1_floor = inc * max_col
        y1_floor = inc * max_row
        min_x = width
        min_y = height
        max_x = max_y = 0

        y = y0_floor
        for row in udg_array[min_row:max_row + 1]:
            x = x0_floor
            for udg in row[min_col:max_col + 1]:
                attr = udg.attr & 127
                attrs.add(attr)
                paper, ink = self.attr_index[attr]
                udg_flashing = False
                if use_flash and udg.attr & 128:
                    colours.add(ink)
                    if ink != paper:
                        colours.add(paper)
                        flashing = True
                        udg_flashing = True
                if udg.mask:
                    has_masks = 1
                else:
                    all_masked = 0
                if x0 <= x < x1_floor and y0 <= y < y1_floor:
                    # Uncropped UDG
                    for j in range(8):
                        if ink in colours and paper in colours and (null_mask or None in colours):
                            break
                        colours.update(mask.apply(udg, j, paper, ink, None))
                    if udg_flashing:
                        min_x = min(x, min_x)
                        max_x = max(x + inc, max_x)
                        min_y = min(y, min_y)
                        max_y = max(y + inc, max_y)
                else:
                    # Cropped UDG
                    min_k = max(0, (x0 - x) // scale)
                    max_k = min(8, 1 + (x1 - 1 - x) // scale)
                    min_j = max(0, (y0 - y) // scale)
                    max_j = min(8, 1 + (y1 - 1 - y) // scale)
                    for j in range(min_j, max_j):
                        if ink in colours and paper in colours and (null_mask or None in colours):
                            break
                        for pixel in mask.apply(udg, j, paper, ink, None)[min_k:max_k]:
                            colours.add(pixel)
                    if udg_flashing:
                        fx0 = max(x0, x + min_k * scale)
                        fx1 = min(x1, x + max_k * scale)
                        fy0 = max(y0, y + min_j * scale)
                        fy1 = min(y1, y + max_j * scale)
                        min_x = min(fx0, min_x)
                        max_x = max(fx1, max_x)
                        min_y = min(fy0, min_y)
                        max_y = max(fy1, max_y)
                x += inc
            y += inc

        if flashing:
            flash_rect = (min_x - x0, min_y - y0, max_x - min_x, max_y - min_y)
        else:
            flash_rect = None
        if None in colours:
            colours.remove(None)
            frame.has_trans = True
        else:
            frame.has_trans = False
        frame.has_masks = has_masks
        frame.all_masked = all_masked
        return colours, attrs, flash_rect

    def _get_all_colours(self, frame, use_flash=False):
        # Find all the colours in an uncropped image
        udg_array = frame.udgs
        null_mask = frame.mask == 0
        mask = self.masks[frame.mask]
        attrs = set()
        colours = set()
        has_trans = False
        has_masks = 0
        all_masked = 1
        flashing = False
        min_x = len(udg_array[0])
        min_y = len(udg_array)
        max_x = max_y = 0

        y = 0
        for row in udg_array:
            x = 0
            for udg in row:
                attr = udg.attr
                attrs.add(attr & 127)
                paper, ink = self.attr_index[attr & 127]
                has_non_trans = False
                for i in range(8):
                    pixels = mask.apply(udg, i, paper, ink, None)
                    if ink in pixels:
                        colours.add(ink)
                        has_non_trans = True
                    if paper in pixels:
                        colours.add(paper)
                        has_non_trans = True
                    if None in pixels:
                        has_trans = True
                    if ink in colours and paper in colours and (null_mask or has_trans):
                        break
                if use_flash and attr & 128 and ink != paper and has_non_trans:
                    min_x = min(x, min_x)
                    min_y = min(y, min_y)
                    max_x = max(x, max_x)
                    max_y = max(y, max_y)
                    flashing = True
                if udg.mask:
                    has_masks = 1
                else:
                    all_masked = 0
                x += 1
            y += 1

        if flashing:
            flash_rect = (min_x, min_y, max_x - min_x + 1, max_y - min_y + 1)
        else:
            flash_rect = None
        frame.has_trans = has_trans
        frame.has_masks = has_masks
        frame.all_masked = all_masked
        return colours, attrs, flash_rect

    def _get_palette(self, colours, attrs, has_trans):
        colour_map = {}
        palette = []
        i = 0
        if has_trans:
            palette.extend(self.colours[0])
            i += 1
        for colour in colours:
            palette.extend(self.colours[colour])
            colour_map[colour] = i
            i += 1

        attr_map = {}
        for attr in attrs:
            paper, ink = self.attr_index[attr]
            attr_map[attr] = (colour_map.get(paper, 0), colour_map.get(ink, 0))

        return palette, attr_map

class NoMask:
    def apply(self, udg, row, paper, ink, trans):
        udg_byte = udg.data[row]
        pixels = []
        for b in range(8):
            if udg_byte & 128:
                pixels.append(ink)
            else:
                pixels.append(paper)
            udg_byte *= 2
        return pixels

class OrAndMask:
    def apply(self, udg, row, paper, ink, trans):
        udg_byte = udg.data[row]
        if udg.mask:
            mask_byte = udg.mask[row]
        else:
            mask_byte = udg_byte
        pixels = [paper] * 8
        index = 7
        while mask_byte:
            if mask_byte & 1:
                if udg_byte & 1:
                    pixels[index] = ink
                else:
                    pixels[index] = trans
            udg_byte //= 2
            mask_byte //= 2
            index -= 1
        return pixels

    def colours(self, patterns, paper, ink, trans):
        return (
            patterns[paper], # 00
            patterns[trans], # 01
            patterns[paper], # 10
            patterns[ink]    # 11
        )

class AndOrMask:
    def apply(self, udg, row, paper, ink, trans):
        udg_byte = udg.data[row]
        if udg.mask:
            mask_byte = udg.mask[row]
        else:
            mask_byte = udg_byte
        pixels = [paper] * 8
        index = 7
        while udg_byte or mask_byte:
            if udg_byte & 1:
                pixels[index] = ink
            elif mask_byte & 1:
                pixels[index] = trans
            udg_byte //= 2
            mask_byte //= 2
            index -= 1
        return pixels

    def colours(self, patterns, paper, ink, trans):
        return (
            patterns[paper], # 00
            patterns[trans], # 01
            patterns[ink],   # 10
            patterns[ink]    # 11
        )
