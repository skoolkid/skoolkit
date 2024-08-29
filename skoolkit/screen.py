# Copyright 2024 Richard Dymond (rjdymond@gmail.com)
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

import contextlib
import io

with contextlib.redirect_stdout(io.StringIO()) as pygame_io:
    try:
        import pygame
    except ImportError: # pragma: no cover
        pygame = None

if pygame: # pragma: no cover
    COLOURS = (
        pygame.Color(0x00, 0x00, 0x00), # Black
        pygame.Color(0x00, 0x00, 0xc5), # Blue
        pygame.Color(0xc5, 0x00, 0x00), # Red
        pygame.Color(0xc5, 0x00, 0xc5), # Magenta
        pygame.Color(0x00, 0xc6, 0x00), # Green
        pygame.Color(0x00, 0xc6, 0xc5), # Cyan
        pygame.Color(0xc5, 0xc6, 0x00), # Yellow
        pygame.Color(0xcd, 0xc6, 0xcd), # White
        pygame.Color(0x00, 0x00, 0x00), # Bright black
        pygame.Color(0x00, 0x00, 0xff), # Bright blue
        pygame.Color(0xff, 0x00, 0x00), # Bright red
        pygame.Color(0xff, 0x00, 0xff), # Bright magenta
        pygame.Color(0x00, 0xff, 0x00), # Bright green
        pygame.Color(0x00, 0xff, 0xff), # Bright cyan
        pygame.Color(0xff, 0xff, 0x00), # Bright yellow
        pygame.Color(0xff, 0xff, 0xff), # Bright white
    )

CELLS = tuple((x, y, 2048 * (y // 8) + 32 * (y % 8) + x, 6144 + 32 * y + x) for x in range(32) for y in range(24))

class Screen: # pragma: no cover
    def __init__(self, scale, fps, caption):
        pygame.init()
        pygame.display.set_mode((256 * scale, 192 * scale))
        pygame.display.set_caption(caption)
        self.pygame_msg = pygame_io.getvalue()
        self.fps = fps
        self.pixel_rects = [[pygame.Rect(px * scale, py * scale, scale, scale) for py in range(192)] for px in range(256)]
        self.cell_rects = [[pygame.Rect(px * scale, py * scale, 8 * scale, 8 * scale) for py in range(0, 192, 8)] for px in range(0, 256, 8)]
        self.surface = pygame.display.get_surface()
        self.clock = pygame.time.Clock()
        self.prev_scr = [None] * 6912

    def draw(self, scr, frame):
        screen = self.surface
        pixel_rects = self.pixel_rects
        cell_rects = self.cell_rects
        prev_scr = self.prev_scr
        flash_change = (frame % 16) == 0
        flash_switch = (frame // 16) % 2

        for (x, y, df_addr, af_addr) in CELLS:
            update = False
            attr = scr[af_addr]
            for a in range(df_addr, df_addr + 2048, 256):
                if scr[a] != prev_scr[a]:
                    update = True
                    break
            else:
                update = attr != prev_scr[af_addr] or (flash_change and attr & 0x80)
            if update:
                bright = (attr & 64) // 8
                ink = COLOURS[bright + (attr % 8)]
                paper = COLOURS[bright + ((attr // 8) % 8)]
                if attr & 0x80 and flash_switch:
                    ink, paper = paper, ink
                py = 8 * y
                screen.fill(paper, cell_rects[x][y])
                for addr in range(df_addr, df_addr + 2048, 256):
                    b = scr[addr]
                    px = 8 * x
                    while b % 256:
                        if b & 0x80:
                            screen.fill(ink, pixel_rects[px][py])
                        b *= 2
                        px += 1
                    py += 1

        self.prev_scr = scr
        if self.fps > 0:
            self.clock.tick(self.fps)

        pygame.display.update()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
        return True
