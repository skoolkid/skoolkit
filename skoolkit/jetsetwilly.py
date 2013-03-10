# -*- coding: utf-8 -*-

# Copyright 2012 Richard Dymond (rjdymond@gmail.com)
#
# This program is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.

from .skoolhtml import HtmlWriter, Udg

class JetSetWillyHtmlWriter(HtmlWriter):
    def init(self):
        self.font = {}
        for b, h in self.get_dictionary('Font').items():
            self.font[b] = [int(h[i:i + 2], 16) for i in range(0, 16, 2)]
        start = 41984 + self.snapshot[41983]
        self.items = {}
        for a in range(start, 42240):
            b1 = self.snapshot[a]
            b2 = self.snapshot[a + 256]
            room_num = b1 & 63
            x = b2 & 31
            y = 8 * (b1 >> 7) + b2 // 32
            self.items.setdefault(room_num, []).append((x, y))

    def expand_room(self, text, index, cwd):
        # #ROOMaddr[,scale][(fname)]
        img_path_id = 'ScreenshotImagePath'
        end, img_path, crop_rect, address, scale = self.parse_image_params(text, index, 2, (2,), img_path_id)
        if img_path is None:
            room_name = ''.join([chr(b) for b in self.snapshot[address + 128:address + 160]])
            fname = room_name.strip().lower().replace(' ', '_')
            img_path = self.image_path(fname, img_path_id)
        if self.need_image(img_path):
            self.write_image(img_path, self._get_room_udgs(address), crop_rect, scale)
        return end, self.img_element(cwd, img_path)

    def _get_room_udgs(self, addr):
        # Collect block graphics
        block_graphics = []
        for a in range(addr + 160, addr + 196, 9):
            attr = self.snapshot[a]
            block_graphics.append(Udg(attr, self.snapshot[a + 1:a + 9]))

        # Build the room UDG array
        udg_array = []
        for a in range(addr, addr + 128):
            if a % 8 == 0:
                udg_array.append([])
            b = self.snapshot[a]
            for block_id in (b >> 6, (b >> 4) & 3, (b >> 2) & 3, b & 3):
                udg_array[-1].append(block_graphics[block_id])

        # Room name
        name_udgs = [Udg(70, self.font[b]) for b in self.snapshot[addr + 128:addr + 160]]
        udg_array.append(name_udgs)

        # Items
        item_udg_data = self.snapshot[addr + 225:addr + 233]
        room_num = addr // 256 - 192
        ink = 3
        for x, y in self.items.get(room_num, ()):
            attr = (udg_array[y][x].attr & 248) + ink
            udg_array[y][x] = Udg(attr, item_udg_data)
            ink += 1
            if ink == 7:
                ink = 3

        # Ramp
        direction, p1, p2, length = self.snapshot[addr + 218:addr + 222]
        if length:
            attr = self.snapshot[addr + 196]
            ramp_udg = Udg(attr, self.snapshot[addr + 197:addr + 205])
            direction = direction * 2 - 1
            x = p1 & 31
            y = 8 * (p2 & 1) + (p1 & 224) // 32
            for i in range(length):
                udg_array[y][x] = ramp_udg
                y -= 1
                x += direction

        # Conveyor
        p1, p2, length = self.snapshot[addr + 215:addr + 218]
        if length:
            attr = self.snapshot[addr + 205]
            # Simulate the 'Cell-Graphics' bug that affects conveyors
            # http://webspace.webring.com/people/ja/andrewbroad/bugs.html
            b = addr + 160
            while b < addr + 205 and self.snapshot[b] != attr:
                b += 1
            conveyor_udg = Udg(attr, self.snapshot[b + 1:b + 9])
            x = p1 & 31
            y = 8 * (p2 & 1) + (p1 & 224) // 32
            for i in range(x, x + length):
                udg_array[y][i] = conveyor_udg

        # Guardians
        for a in range(addr + 240, addr + 256, 2):
            num, start = self.snapshot[a:a + 2]
            if num == 255:
                break
            def_addr = 40960 + num * 8
            guardian_def = self.snapshot[def_addr:def_addr + 8]
            guardian_type = guardian_def[0] & 7
            if guardian_type & 3 in (1, 2):
                # Horizontal and vertical guardians
                x = start & 31
                y0 = guardian_def[3]
                y = (y0 & 240) // 16
                y_delta = (y0 & 14) // 2
                b1 = guardian_def[1]
                bright = 8 * (b1 & 8)
                ink = b1 & 7
                attr = bright + ink
                sprite_addr = 256 * guardian_def[5] + (start & 224)
                sprite = self._get_graphic(sprite_addr)
                self._place_graphic(udg_array, sprite, x, y, attr, y_delta)
            elif guardian_type & 3 == 3:
                # Rope
                x = start & 31
                length = guardian_def[4] + 1
                rope_udg_data = []
                i = j = 0
                while i < length:
                    if j % 3:
                        rope_udg_data.append(0)
                    else:
                        rope_udg_data.append(128)
                        i += 1
                    j += 1
                rope_udg_data += [0] * (8 - (len(rope_udg_data) & 7))
                rope_udg_array = []
                for i in range(0, len(rope_udg_data), 8):
                    rope_udg_array.append([Udg(0, rope_udg_data[i:i + 8])])
                self._place_graphic(udg_array, rope_udg_array, x, 0)
            elif guardian_type == 4:
                # Arrow; first get the display file address at which the middle
                # of the arrow will be drawn
                df_addr = self.snapshot[start + 33280] + 256 * (self.snapshot[start + 33281] - 32)
                # Draw the arrow only if the JSW engine would draw it in the
                # upper two-thirds of the screen (unlike the first arrow in The
                # Attic!)
                if 16384 <= df_addr < 20480:
                    y = ((df_addr // 256 - 64) & 24) + (df_addr % 256) // 32
                    y_delta = (df_addr // 256) & 7
                    x = guardian_def[4] & 31
                    arrow_udg_data = [0] * (y_delta - 1) + [guardian_def[6], 255, guardian_def[6]] + [0] * (6 - y_delta)
                    arrow_udg = Udg(0, arrow_udg_data)
                    self._place_graphic(udg_array, [[arrow_udg]], x, y, 7)

        if addr == 57600:
            # Toilet in the bathroom
            toilet = self._get_graphic(42496)
            self._place_graphic(udg_array, toilet, 28, 13, 7)
        elif addr == 58112:
            # Maria in the master bedroom
            maria = self._get_graphic(40064)
            self._place_graphic(udg_array, [maria[0]], 14, 11, 69)
            self._place_graphic(udg_array, [maria[1]], 14, 12, 7)

        return udg_array

    def _get_graphic(self, addr, attr=0):
        # Build a 16x16 graphic
        udgs = []
        for offsets in ((0, 1), (16, 17)):
            o1, o2 = offsets
            udgs.append([])
            for a in (addr + o1, addr + o2):
                udgs[-1].append(Udg(attr, self.snapshot[a:a + 16:2]))
        return udgs

    def _place_graphic(self, udg_array, graphic, x, y, ink=None, y_delta=0):
        if y_delta == 0:
            for row in graphic:
                for i, udg in enumerate(row):
                    bg_udg = udg_array[y][x + i]
                    new_udg_attr = (bg_udg.attr & 56) + ink if ink is not None else bg_udg.attr
                    new_udg_data = [b1 | b2 for b1, b2 in zip(bg_udg.data, udg.data)]
                    udg_array[y][x + i] = Udg(new_udg_attr, new_udg_data)
                y += 1
            return

        blank_udg = Udg(0, [0] * 8)
        width = len(graphic[0])
        prev_row = [blank_udg] * width
        for row in graphic + [[blank_udg] * width]:
            for i, udg in enumerate(row):
                bg_udg = udg_array[y][x + i]
                new_udg_attr = (bg_udg.attr & 56) + ink if ink is not None else bg_udg.attr
                shifted_udg_data = prev_row[i].data[-y_delta:] + udg.data[:-y_delta]
                new_udg_data = [b1 | b2 for b1, b2 in zip(bg_udg.data, shifted_udg_data)]
                udg_array[y][x + i] = Udg(new_udg_attr, new_udg_data)
                prev_row[i] = udg
            y += 1
