# © 2024-2026 Richard Dymond (rjdymond@gmail.com)
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

with contextlib.redirect_stderr(io.StringIO()):
    with contextlib.redirect_stdout(io.StringIO()) as pygame_io:
        try:
            import pygame
        except ImportError: # pragma: no cover
            pygame = None

CELLS = tuple((x, y, 2048 * (y // 8) + 32 * (y % 8) + x, 6144 + 32 * y + x) for x in range(32) for y in range(24))

class Screen:
    """
    Initialise the screen.

    :param scale: The screen scale factor.
    :param fps: The target frame rate.
    :param caption: Window title bar text.
    :param is128k: Whether to use 128K screen draw timings.
    """
    # Component API
    def __new__(cls, scale, fps, caption, is128k):
        # Return None if pygame is not available
        if pygame:
            return super().__new__(cls)

    def __init__(self, scale, fps, caption, is128k):
        self._init_colours_and_keys()
        pygame.init()
        pygame.display.set_mode((320 * scale, 240 * scale))
        pygame.display.set_caption(caption)
        print(pygame_io.getvalue())
        self.scale = scale
        self.fps = fps
        if is128k:
            self.draw_border = self._draw_border_128k
        else:
            self.draw_border = self._draw_border_48k
        self.pixel_rects = [[pygame.Rect((32 + px) * scale, (24 + py) * scale, scale, scale) for py in range(192)] for px in range(256)]
        self.cell_rects = [[pygame.Rect((32 + px) * scale, (24 + py) * scale, 8 * scale, 8 * scale) for py in range(0, 192, 8)] for px in range(0, 256, 8)]
        self.surface = pygame.display.get_surface()
        self.clock = pygame.time.Clock()
        self.prev_scr = [None] * 6912

    def _init_colours_and_keys(self):
        self.colours = (
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
        ) if pygame else None

        self.keys = (
            (pygame.K_1, 3, 0b00001),
            (pygame.K_2, 3, 0b00010),
            (pygame.K_3, 3, 0b00100),
            (pygame.K_4, 3, 0b01000),
            (pygame.K_5, 3, 0b10000),
            (pygame.K_6, 4, 0b10000),
            (pygame.K_7, 4, 0b01000),
            (pygame.K_8, 4, 0b00100),
            (pygame.K_9, 4, 0b00010),
            (pygame.K_0, 4, 0b00001),
            (pygame.K_q, 2, 0b00001),
            (pygame.K_w, 2, 0b00010),
            (pygame.K_e, 2, 0b00100),
            (pygame.K_r, 2, 0b01000),
            (pygame.K_t, 2, 0b10000),
            (pygame.K_y, 5, 0b10000),
            (pygame.K_u, 5, 0b01000),
            (pygame.K_i, 5, 0b00100),
            (pygame.K_o, 5, 0b00010),
            (pygame.K_p, 5, 0b00001),
            (pygame.K_a, 1, 0b00001),
            (pygame.K_s, 1, 0b00010),
            (pygame.K_d, 1, 0b00100),
            (pygame.K_f, 1, 0b01000),
            (pygame.K_g, 1, 0b10000),
            (pygame.K_h, 6, 0b10000),
            (pygame.K_j, 6, 0b01000),
            (pygame.K_k, 6, 0b00100),
            (pygame.K_l, 6, 0b00010),
            (pygame.K_RETURN, 6, 0b00001),      # ENTER
            (pygame.K_KP_ENTER, 6, 0b00001),    # ENTER
            (pygame.K_LSHIFT, 0, 0b00001),      # CAPS SHIFT
            (pygame.K_z, 0, 0b00010),
            (pygame.K_x, 0, 0b00100),
            (pygame.K_c, 0, 0b01000),
            (pygame.K_v, 0, 0b10000),
            (pygame.K_b, 7, 0b10000),
            (pygame.K_n, 7, 0b01000),
            (pygame.K_m, 7, 0b00100),
            (pygame.K_LCTRL, 7, 0b00010),       # SYMBOL SHIFT
            (pygame.K_SPACE, 7, 0b00001),
        ) if pygame else None

        self.cs_keys = (
            (pygame.K_BACKSPACE, 4, 0b00001),   # CAPS SHIFT + 0
            (pygame.K_LEFT, 3, 0b10000),        # CAPS SHIFT + 5
            (pygame.K_DOWN, 4, 0b10000),        # CAPS SHIFT + 6
            (pygame.K_UP, 4, 0b01000),          # CAPS SHIFT + 7
            (pygame.K_RIGHT, 4, 0b00100),       # CAPS SHIFT + 8
        ) if pygame else None

        self.ss_keys = (
            (pygame.K_QUOTE, 4, 0b01000),       # SYMBOL SHIFT + 7
            (pygame.K_SEMICOLON, 5, 0b00010),   # SYMBOL SHIFT + O
            (pygame.K_MINUS, 6, 0b01000),       # SYMBOL SHIFT + J
            (pygame.K_KP_MINUS, 6, 0b01000),    # SYMBOL SHIFT + J
            (pygame.K_KP_PLUS, 6, 0b00100),     # SYMBOL SHIFT + K
            (pygame.K_EQUALS, 6, 0b00010),      # SYMBOL SHIFT + L
            (pygame.K_SLASH, 0, 0b10000),       # SYMBOL SHIFT + V
            (pygame.K_KP_DIVIDE, 0, 0b10000),   # SYMBOL SHIFT + V
            (pygame.K_KP_MULTIPLY, 7, 0b10000), # SYMBOL SHIFT + B
            (pygame.K_COMMA, 7, 0b01000),       # SYMBOL SHIFT + N
            (pygame.K_PERIOD, 7, 0b00100),      # SYMBOL SHIFT + M
            (pygame.K_KP_PERIOD, 7, 0b00100),   # SYMBOL SHIFT + M
        ) if pygame else None

    def _draw_chunks(self, border, chunks):
        screen = self.surface
        scale = self.scale
        Rect = pygame.Rect

        for c, x, y, t in chunks:
            if 24 <= y < 216 and 32 - t < x < 288:
                if x < 32:
                    # Left border to left edge of main screen
                    screen.fill(c, Rect(x * scale, y * scale, (32 - x) * scale, scale))
                if x + t > 288:
                    # From right edge of main screen into right border
                    screen.fill(c, Rect(288 * scale, y * scale, (x + t - 288) * scale, scale))
            else:
                # Top/bottom/left/right border only
                screen.fill(c, Rect(x * scale, y * scale, t * scale, scale))

        border[:] = [(0, border[-2][1])]

    def _draw_border_48k(self, border):
        colours = self.colours
        chunks = []
        x, y = 20, 0
        for i, (ts, colour) in enumerate(border[:-1]):
            t = (border[i + 1][0] & 0xFFFFC) - (ts & 0xFFFFC)
            c = colours[colour]
            while y < 280:
                x1 = x + t
                t0 = t - max(0, x1 - 224)
                if y >= 40 and 8 - t0 <= x < 168:
                    if x < 8:
                        chunks.append((c, 0, y - 40, (t0 + x - 8) * 2))
                    else:
                        chunks.append((c, (x - 8) * 2, y - 40, t0 * 2))
                if x1 < 224:
                    x = x1
                    break
                x = 0
                y += 1
                t -= t0
        self._draw_chunks(border, chunks)

    def _draw_border_128k(self, border):
        colours = self.colours
        chunks = []
        x, y = 16, 0
        for i, (ts, colour) in enumerate(border[:-1]):
            t = (border[i + 1][0] & 0xFFFFC) - (ts & 0xFFFFC)
            c = colours[colour]
            while y < 279:
                x1 = x + t
                t0 = t - max(0, x1 - 228)
                if y >= 39 and x < 160:
                    chunks.append((c, x * 2, y - 39, t0 * 2))
                if x1 < 228:
                    x = x1
                    break
                x = 0
                y += 1
                t -= t0
        self._draw_chunks(border, chunks)

    # Component API
    def draw(self, scr, frame, border, keyboard=None):
        """
        Draw the screen.

        :param scr: A 6912-element list of byte values from the display file
                    and attribute file.
        :param frame: Frame number (used to determine the state of flashing
                      cells).
        :param border: A log of the output to port 0xFE.
        :param keyboard: A list for capturing the keyboard state.
        :return: `False` if the window has been closed, `True` otherwise.
        """
        screen = self.surface
        pixel_rects = self.pixel_rects
        cell_rects = self.cell_rects
        prev_scr = self.prev_scr
        flash_change = (frame % 16) == 0
        flash_switch = (frame // 16) % 2
        colours = self.colours

        border.append((99999, 0))
        self.draw_border(border)

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
                ink = colours[bright + (attr % 8)]
                paper = colours[bright + ((attr // 8) % 8)]
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

        if keyboard is not None:
            keyboard[:] = (0,) * 8
            pressed = pygame.key.get_pressed()
            for k, i, b in self.keys:
                if pressed[k]:
                    keyboard[i] |= b
            for k, i, b in self.cs_keys:
                if pressed[k]:
                    keyboard[0] |= 1 # CAPS SHIFT
                    keyboard[i] |= b
            for k, i, b in self.ss_keys:
                if pressed[k]:
                    keyboard[7] |= 2 # SYMBOL SHIFT
                    keyboard[i] |= b

        return True
