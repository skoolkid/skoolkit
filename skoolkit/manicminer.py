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

class ManicMinerHtmlWriter(HtmlWriter):
    def init(self):
        self.font = {}
        for b, h in self.get_dictionary('Font').items():
            self.font[b] = [int(h[i:i + 2], 16) for i in range(0, 16, 2)]

    def cavern(self, cwd, address, scale=2, fname=None):
        if fname is None:
            cavern_name = ''.join([chr(b) for b in self.snapshot[address + 512:address + 544]])
            fname = cavern_name.strip().lower().replace(' ', '_')
        img_path = self.image_path(fname, 'ScreenshotImagePath')
        if self.need_image(img_path):
            self.write_image(img_path, self._get_cavern_udgs(address), scale=scale)
        return self.img_element(cwd, img_path)

    def _get_cavern_udgs(self, addr):
        # Collect block graphics
        block_graphics = {}
        bg_attr = self.snapshot[addr + 544]
        bg_udg = Udg(bg_attr, self.snapshot[addr + 545:addr + 553])
        block_graphics[bg_udg.attr] = bg_udg
        for a in range(addr + 553, addr + 616, 9):
            attr = self.snapshot[a]
            block_graphics[attr] = Udg(attr, self.snapshot[a + 1:a + 9])

        # Build the cavern UDG array
        udg_array = []
        for a in range(addr, addr + 512, 32):
            udg_array.append([block_graphics.get(attr, bg_udg) for attr in self.snapshot[a:a + 32]])
        if addr == 64512:
            # The Final Barrier (top half)
            udg_array[:8] = self.screenshot(h=8, df_addr=40960, af_addr=64512)

        # Cavern name
        name_udgs = [Udg(48, self.font[b]) for b in self.snapshot[addr + 512:addr + 544]]
        udg_array.append(name_udgs)

        # Items
        item_udg_data = self.snapshot[addr + 692:addr + 700]
        for a in range(addr + 629, addr + 653, 5):
            attr = self.snapshot[a]
            if attr in (0, 255):
                break
            x, y = self._get_coords(a + 1)
            udg_array[y][x] = Udg(attr, item_udg_data)

        has_vertical_guardians = self.snapshot[addr + 733] < 255

        # Horizontal guardians
        for a in range(addr + 702, addr + 730, 7):
            attr = self.snapshot[a]
            if attr in (0, 255):
                break
            sprite_index = self.snapshot[a + 4]
            if has_vertical_guardians:
                sprite_index |= 4
            sprite = self._get_graphic(addr + 768 + 32 * sprite_index, attr)
            x, y = self._get_coords(a + 1)
            self._place_graphic(udg_array, sprite, x, y)

        if addr == 49152:
            # Eugene
            attr = (bg_attr & 248) + 7
            sprite = self._get_graphic(addr + 736, attr)
            self._place_graphic(udg_array, sprite, 15, 0)
        elif has_vertical_guardians:
            # Vertical guardians (except Eugene's Lair)
            for a in range(addr + 733, addr + 761, 7):
                attr = self.snapshot[a]
                if attr == 255:
                    break
                sprite_index = self.snapshot[a + 1]
                sprite = self._get_graphic(addr + 768 + 32 * sprite_index, attr)
                y = (self.snapshot[a + 2] & 120) // 8
                y_delta = self.snapshot[a + 2] & 7
                x = self.snapshot[a + 3]
                self._place_graphic(udg_array, sprite, x, y, y_delta)

        # Miner Willy
        attr = (bg_attr & 248) + 7
        sprite_index = self.snapshot[addr + 617]
        direction = self.snapshot[addr + 618]
        willy = self._get_graphic(33280 + 128 * direction + 32 * sprite_index, attr)
        x, y = self._get_coords(addr + 620)
        self._place_graphic(udg_array, willy, x, y)

        # Portal
        attr = self.snapshot[addr + 655]
        portal_udgs = self._get_graphic(addr + 656, attr)
        x, y = self._get_coords(addr + 688)
        self._place_graphic(udg_array, portal_udgs, x, y)

        return udg_array

    def _get_graphic(self, addr, attr):
        # Build a 16x16 graphic
        udgs = []
        for offsets in ((0, 1), (16, 17)):
            o1, o2 = offsets
            udgs.append([])
            for a in (addr + o1, addr + o2):
                udgs[-1].append(Udg(attr, self.snapshot[a:a + 16:2]))
        return udgs

    def _get_coords(self, addr):
        p1, p2 = self.snapshot[addr:addr + 2]
        x = p1 & 31
        y = 8 * (p2 & 1) + (p1 & 224) // 32
        return x, y

    def _place_graphic(self, udg_array, graphic, x, y, y_delta=0):
        if y_delta == 0:
            udg_array[y][x:x + 2] = graphic[0]
            udg_array[y + 1][x:x + 2] = graphic[1]
            return

        udg1, udg2 = graphic[0]
        udg3, udg4 = graphic[1]
        attr = udg1.attr
        new_udg1 = Udg(attr, [0] * y_delta + udg1.data[:-y_delta])
        new_udg2 = Udg(attr, [0] * y_delta + udg2.data[:-y_delta])
        new_udg3 = Udg(attr, udg1.data[-y_delta:] + udg3.data[:-y_delta])
        new_udg4 = Udg(attr, udg2.data[-y_delta:] + udg4.data[:-y_delta])
        new_udg5 = Udg(attr, udg3.data[-y_delta:] + [0] * (8 - y_delta))
        new_udg6 = Udg(attr, udg4.data[-y_delta:] + [0] * (8 - y_delta))

        udg_array[y][x:x + 2] = [new_udg1, new_udg2]
        udg_array[y + 1][x:x + 2] = [new_udg3, new_udg4]
        udg_array[y + 2][x:x + 2] = [new_udg5, new_udg6]
