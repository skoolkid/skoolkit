# -*- coding: utf-8 -*-

# Copyright 2008-2016 Richard Dymond (rjdymond@gmail.com)
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

# Byte flip table
FLIP = (
    0, 128, 64, 192, 32, 160, 96, 224, 16, 144, 80, 208, 48, 176, 112, 240,
    8, 136, 72, 200, 40, 168, 104, 232, 24, 152, 88, 216, 56, 184, 120, 248,
    4, 132, 68, 196, 36, 164, 100, 228, 20, 148, 84, 212, 52, 180, 116, 244,
    12, 140, 76, 204, 44, 172, 108, 236, 28, 156, 92, 220, 60, 188, 124, 252,
    2, 130, 66, 194, 34, 162, 98, 226, 18, 146, 82, 210, 50, 178, 114, 242,
    10, 138, 74, 202, 42, 170, 106, 234, 26, 154, 90, 218, 58, 186, 122, 250,
    6, 134, 70, 198, 38, 166, 102, 230, 22, 150, 86, 214, 54, 182, 118, 246,
    14, 142, 78, 206, 46, 174, 110, 238, 30, 158, 94, 222, 62, 190, 126, 254,
    1, 129, 65, 193, 33, 161, 97, 225, 17, 145, 81, 209, 49, 177, 113, 241,
    9, 137, 73, 201, 41, 169, 105, 233, 25, 153, 89, 217, 57, 185, 121, 249,
    5, 133, 69, 197, 37, 165, 101, 229, 21, 149, 85, 213, 53, 181, 117, 245,
    13, 141, 77, 205, 45, 173, 109, 237, 29, 157, 93, 221, 61, 189, 125, 253,
    3, 131, 67, 195, 35, 163, 99, 227, 19, 147, 83, 211, 51, 179, 115, 243,
    11, 139, 75, 203, 43, 171, 107, 235, 27, 155, 91, 219, 59, 187, 123, 251,
    7, 135, 71, 199, 39, 167, 103, 231, 23, 151, 87, 215, 55, 183, 119, 247,
    15, 143, 79, 207, 47, 175, 111, 239, 31, 159, 95, 223, 63, 191, 127, 255
)

class Udg(object):
    """Initialise the UDG.

    :param attr: The attribute byte.
    :param data: The graphic data (sequence of 8 bytes).
    :param mask: The mask data (sequence of 8 bytes).
    """
    def __init__(self, attr, data, mask=None):
        self.attr = attr
        self.data = data
        self.mask = mask

    def __repr__(self):
        if self.mask is None:
            return 'Udg({0}, {1})'.format(self.attr, self.data)
        return 'Udg({0}, {1}, {2})'.format(self.attr, self.data, self.mask)

    def __eq__(self, other):
        if type(other) is Udg:
            return self.attr == other.attr and self.data == other.data and self.mask == other.mask
        return False

    def _rotate_tile(self, tile_data):
        rotated = []
        b = 1
        while b < 129:
            rbyte = 0
            for byte in tile_data:
                rbyte //= 2
                if byte & b:
                    rbyte += 128
            rotated.append(rbyte)
            b *= 2
        rotated.reverse()
        return rotated

    # API
    def flip(self, flip=1):
        """Flip the UDG.

        :param flip: 1 to flip horizontally, 2 to flip vertically, or 3 to flip
                     horizontally and vertically.
        """
        if flip & 1:
            for i in range(8):
                self.data[i] = FLIP[self.data[i]]
                if self.mask:
                    self.mask[i] = FLIP[self.mask[i]]
        if flip & 2:
            self.data.reverse()
            if self.mask:
                self.mask.reverse()

    # API
    def rotate(self, rotate=1):
        """Rotate the UDG 90 degrees clockwise.

        :param rotate: The number of rotations to perform.
        """
        for i in range(rotate & 3):
            self.data = self._rotate_tile(self.data)
            if self.mask:
                self.mask = self._rotate_tile(self.mask)

    def copy(self):
        if self.mask:
            return Udg(self.attr, self.data[:], self.mask[:])
        return Udg(self.attr, self.data[:])

class Frame(object):
    """Create a frame of an animated image.

    :param udgs: The two-dimensional array of tiles (instances of
                 :class:`~skoolkit.graphics.Udg`) from which to build the
                 frame, or a function that returns the array of tiles.
    :param scale: The scale of the frame.
    :param mask: The type of mask to apply to the tiles in the frame: 0 (no
                 mask), 1 (OR-AND mask), or 2 (AND-OR mask).
    :param x: The x-coordinate of the top-left pixel to include in the frame.
    :param y: The y-coordinate of the top-left pixel to include in the frame.
    :param width: The width of the frame; if `None`, the maximum width
                  (derived from `x` and the width of the array of tiles) is
                  used.
    :param height: The height of the frame; if `None`, the maximum height
                   (derived from `y` and the height of the array of tiles) is
                   used.
    :param delay: The delay between this frame and the next in 1/100ths of a
                  second.
    :param name: The name of this frame.
    """
    def __init__(self, udgs, scale=1, mask=0, x=0, y=0, width=None, height=None, delay=32, name=''):
        self._udgs = udgs
        self._scale = scale
        self.mask = int(mask)
        self._x = x
        self._y = y
        self._width = width
        self._height = height
        self.delay = delay
        self.name = name

    def swap_colours(self, tx=0, ty=0, tw=None, th=None, x=0, y=0, width=None, height=None):
        # Swap paper and ink in UDGs that are flashing
        t_width = tw or len(self.udgs[0])
        t_height = th or len(self.udgs)
        udgs = [self.udgs[i][tx:tx + t_width] for i in range(ty, ty + t_height)]
        for row in udgs:
            for i in range(len(row)):
                udg = row[i]
                attr = udg.attr
                if attr & 128:
                    new_attr = (attr & 192) + (attr & 7) * 8 + (attr & 56) // 8
                    row[i] = Udg(new_attr, udg.data, udg.mask)
        return Frame(udgs, self.scale, self.mask, x, y, width, height)

    @property
    def udgs(self):
        if callable(self._udgs):
            self._udgs = self._udgs()
        return self._udgs

    @property
    def scale(self):
        return self._scale

    @property
    def x(self):
        return self._x

    @property
    def y(self):
        return self._y

    @property
    def full_width(self):
        return 8 * len(self.udgs[0]) * self.scale

    @property
    def width(self):
        full_width = self.full_width
        return min(self._width or full_width, full_width - self.x)

    @property
    def full_height(self):
        return 8 * len(self.udgs) * self.scale

    @property
    def height(self):
        full_height = self.full_height
        return min(self._height or full_height, full_height - self.y)

    @property
    def cropped(self):
        return self.width != self.full_width or self.height != self.full_height

    @property
    def tiles(self):
        return len(self.udgs[0]) * len(self.udgs)

# API
def flip_udgs(udgs, flip=1):
    """Flip a 2D array of UDGs (instances of :class:`~skoolkit.graphics.Udg`).

    :param udgs: The array of UDGs.
    :param flip: 1 to flip horizontally, 2 to flip vertically, or 3 to flip
                 horizontally and vertically.
    """
    if flip:
        flipped_udgs = set()
        for row in udgs:
            for udg in row:
                if id(udg) not in flipped_udgs:
                    udg.flip(flip)
                    flipped_udgs.add(id(udg))
        if flip & 1:
            for row in udgs:
                row.reverse()
        if flip & 2:
            udgs.reverse()

# API
def rotate_udgs(udgs, rotate=1):
    """
    Rotate a 2D array of UDGs (instances of :class:`~skoolkit.graphics.Udg`)
    90 degrees clockwise.

    :param udgs: The array of UDGs.
    :param rotate: The number of rotations to perform.
    """
    if rotate:
        rotated_udgs = set()
        for row in udgs:
            for udg in row:
                if id(udg) not in rotated_udgs:
                    udg.rotate(rotate)
                    rotated_udgs.add(id(udg))
        if rotate & 3 == 1:
            rotated = []
            for i in range(len(udgs[0])):
                rotated.append([])
                for j in range(len(udgs)):
                    rotated[-1].insert(0, udgs[j][i])
            udgs[:] = rotated
        elif rotate & 3 == 2:
            udgs.reverse()
            for row in udgs:
                row.reverse()
        elif rotate & 3 == 3:
            rotated = []
            for i in range(len(udgs[0])):
                rotated.insert(0, [])
                for j in range(len(udgs)):
                    rotated[0].append(udgs[j][i])
            udgs[:] = rotated
