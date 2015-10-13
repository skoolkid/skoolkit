# -*- coding: utf-8 -*-

# Copyright 2015 Richard Dymond (rjdymond@gmail.com)
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

from skoolkit.skoolhtml import HtmlWriter, Udg

class HungryHoraceHtmlWriter(HtmlWriter):
    def init(self):
        self.maze_tiles = [Udg(61, self.snapshot[a:a + 8]) for a in range(31735, 31815, 8)]
        self.maze_tiles[2].attr = 60 # flower
        self.maze_tiles[3].attr = 56 # arrow

    def maze(self, cwd, address, fname, scale=2):
        img_path = self.image_path(fname, 'ScreenshotImagePath')
        if self.need_image(img_path):
            self.write_image(img_path, self._get_maze_udgs(address), scale=scale)
        return self.img_element(cwd, img_path)

    def _get_maze_udgs(self, address):
        return [[self.maze_tiles[i] for i in self.snapshot[a:a + 32]] for a in range(address, address + 768, 32)]
