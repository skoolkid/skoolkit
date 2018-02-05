# Copyright 2008-2018 Richard Dymond (rjdymond@gmail.com)
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

    def _rotate_tile(self, tile_data, backwards=0):
        rotated = []
        if backwards:
            b = 1
            while b < 129:
                rbyte = 0
                for byte in tile_data:
                    rbyte *= 2
                    if byte & b:
                        rbyte += 1
                rotated.append(rbyte)
                b *= 2
        else:
            b = 128
            while b:
                rbyte = 0
                for byte in tile_data:
                    rbyte //= 2
                    if byte & b:
                        rbyte += 128
                rotated.append(rbyte)
                b //= 2
        return rotated

    # API
    def flip(self, flip=1):
        """Flip the UDG.

        :param flip: 1 to flip horizontally, 2 to flip vertically, or 3 to flip
                     horizontally and vertically.
        """
        if flip & 1:
            self.data = [FLIP[b] for b in self.data]
            if self.mask:
                self.mask = [FLIP[b] for b in self.mask]
        if flip & 2:
            self.data.reverse()
            if self.mask:
                self.mask.reverse()

    # API
    def rotate(self, rotate=1):
        """Rotate the UDG 90 degrees clockwise.

        :param rotate: The number of rotations to perform.
        """
        if rotate & 1:
            self.data = self._rotate_tile(self.data, rotate & 2)
            if self.mask:
                self.mask = self._rotate_tile(self.mask, rotate & 2)
        elif rotate & 2:
            self.flip(3)

    def copy(self):
        if self.mask:
            return Udg(self.attr, self.data[:], self.mask[:])
        return Udg(self.attr, self.data[:])

class Frame(object):
    """Create a frame of a still or animated image.

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

    def swap_colours(self, x, y, width, height):
        # Swap paper and ink in UDGs that are flashing
        if self.cropped:
            udgs = [row[:] for row in self.udgs]
        else:
            inc = 8 * self.scale
            tx, ty, tw, th = x // inc, y // inc, width // inc, height // inc
            udgs = [row[tx:tx + tw] for row in self.udgs[ty:ty + th]]
            x, y, width, height = 0, 0, None, None
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
            for i in range(max([len(r) for r in udgs])):
                rotated.append([])
                for j in range(len(udgs)):
                    if i < len(udgs[j]):
                        rotated[-1].insert(0, udgs[j][i])
            udgs[:] = rotated
        elif rotate & 3 == 2:
            udgs.reverse()
            for row in udgs:
                row.reverse()
        elif rotate & 3 == 3:
            rotated = []
            for i in range(max([len(r) for r in udgs])):
                rotated.insert(0, [])
                for j in range(len(udgs)):
                    if i < len(udgs[j]):
                        rotated[0].append(udgs[j][i])
            udgs[:] = rotated

def adjust_udgs(udgs, flip, rotate):
    flip_udgs(udgs, flip)
    rotate_udgs(udgs, rotate)
    return udgs

def build_udg(snapshot, addr, attr, step, inc, flip, rotate, mask, mask_addr, mask_step):
    udg_bytes = [(snapshot[addr + n * step] + inc) % 256 for n in range(8)]
    mask_bytes = None
    if mask and mask_addr is not None:
        mask_bytes = snapshot[mask_addr:mask_addr + 8 * mask_step:mask_step]
    udg = Udg(attr, udg_bytes, mask_bytes)
    udg.flip(flip)
    udg.rotate(rotate)
    return udg

def font_udgs(snapshot, address, attr, message):
    udgs = []
    for c in message:
        a = address + 8 * (ord(c) - 32)
        udgs.append(Udg(attr, snapshot[a:a + 8]))
    return [udgs]

def scr_udgs(snapshot, x, y, w, h, df_addr=16384, af_addr=22528):
    width = min((w, 32 - x))
    height = min((h, 24 - y))
    scr_udgs = []
    for r in range(y, y + height):
        attr_addr = af_addr + 32 * r + x
        addr = df_addr + 2048 * (r // 8) + 32 * (r % 8) + x
        scr_udgs.append([Udg(snapshot[attr_addr + i], snapshot[addr + i:addr + i + 2048:256]) for i in range(width)])
    return scr_udgs
