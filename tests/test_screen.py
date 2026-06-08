from collections import defaultdict
from unittest.mock import patch, Mock

from skoolkittest import BLACK, BLUE, RED, MAGENTA, GREEN, CYAN, YELLOW, QUIT, MockPygame, SkoolKitTestCase
from skoolkit import screen

KEYS = (
    ('1', 3, 0b00001),
    ('2', 3, 0b00010),
    ('3', 3, 0b00100),
    ('4', 3, 0b01000),
    ('5', 3, 0b10000),
    ('6', 4, 0b10000),
    ('7', 4, 0b01000),
    ('8', 4, 0b00100),
    ('9', 4, 0b00010),
    ('0', 4, 0b00001),
    ('q', 2, 0b00001),
    ('w', 2, 0b00010),
    ('e', 2, 0b00100),
    ('r', 2, 0b01000),
    ('t', 2, 0b10000),
    ('y', 5, 0b10000),
    ('u', 5, 0b01000),
    ('i', 5, 0b00100),
    ('o', 5, 0b00010),
    ('p', 5, 0b00001),
    ('a', 1, 0b00001),
    ('s', 1, 0b00010),
    ('d', 1, 0b00100),
    ('f', 1, 0b01000),
    ('g', 1, 0b10000),
    ('h', 6, 0b10000),
    ('j', 6, 0b01000),
    ('k', 6, 0b00100),
    ('l', 6, 0b00010),
    ('RETURN', 6, 0b00001),      # ENTER
    ('KP_ENTER', 6, 0b00001),    # ENTER
    ('LSHIFT', 0, 0b00001),      # CAPS SHIFT
    ('z', 0, 0b00010),
    ('x', 0, 0b00100),
    ('c', 0, 0b01000),
    ('v', 0, 0b10000),
    ('b', 7, 0b10000),
    ('n', 7, 0b01000),
    ('m', 7, 0b00100),
    ('LCTRL', 7, 0b00010),       # SYMBOL SHIFT
    ('SPACE', 7, 0b00001),
)

CS_KEYS = (
    ('BACKSPACE', 4, 0b00001),   # CAPS SHIFT + 0
    ('LEFT', 3, 0b10000),        # CAPS SHIFT + 5
    ('DOWN', 4, 0b10000),        # CAPS SHIFT + 6
    ('UP', 4, 0b01000),          # CAPS SHIFT + 7
    ('RIGHT', 4, 0b00100),       # CAPS SHIFT + 8
)

SS_KEYS = (
    ('QUOTE', 4, 0b01000),       # SYMBOL SHIFT + 7
    ('SEMICOLON', 5, 0b00010),   # SYMBOL SHIFT + O
    ('MINUS', 6, 0b01000),       # SYMBOL SHIFT + J
    ('KP_MINUS', 6, 0b01000),    # SYMBOL SHIFT + J
    ('KP_PLUS', 6, 0b00100),     # SYMBOL SHIFT + K
    ('EQUALS', 6, 0b00010),      # SYMBOL SHIFT + L
    ('SLASH', 0, 0b10000),       # SYMBOL SHIFT + V
    ('KP_DIVIDE', 0, 0b10000),   # SYMBOL SHIFT + V
    ('KP_MULTIPLY', 7, 0b10000), # SYMBOL SHIFT + B
    ('COMMA', 7, 0b01000),       # SYMBOL SHIFT + N
    ('PERIOD', 7, 0b00100),      # SYMBOL SHIFT + M
    ('KP_PERIOD', 7, 0b00100),   # SYMBOL SHIFT + M
)

class ScreenTest(SkoolKitTestCase):
    def _test_init(self, mock_pygame, scale, caption, is128k=False):
        s = screen.Screen(scale, 50, caption, is128k)
        self.assertTrue(mock_pygame.init_called)
        mock_pygame.display.set_mode.assert_called_with((320 * scale, 240 * scale))
        mock_pygame.display.set_caption.assert_called_with(caption)
        mock_pygame.display.get_surface.assert_called_with()
        mock_pygame.time.Clock.assert_called_with()

    @patch.object(screen, 'CELLS', ())
    @patch.object(screen, 'pygame', new_callable=MockPygame)
    def _test_keys(self, keys, extra, mock_pygame):
        s = screen.Screen(1, 50, 'screen', False)
        scr = [0] * 6912
        keyboard = [0] * 8
        border = [(0, YELLOW)]
        for k, i, b in keys:
            exp_keyboard = [0] * 8
            exp_keyboard[i] = b
            if extra:
                exp_keyboard[extra[0]] |= extra[1]
            mock_pygame.key.get_pressed.return_value = defaultdict(int, {k: 1})
            self.assertTrue(s.draw(scr, 0, border, keyboard))
            self.assertEqual(exp_keyboard, keyboard)

    @patch.object(screen, 'pygame', new_callable=MockPygame)
    def test_init(self, mock_pygame):
        self._test_init(mock_pygame, 1, 'hello')

    @patch.object(screen, 'pygame', new_callable=MockPygame)
    def test_init_scale_2(self, mock_pygame):
        self._test_init(mock_pygame, 2, 'screen')

    @patch.object(screen, 'pygame', new_callable=MockPygame)
    def test_draw(self, mock_pygame):
        s = screen.Screen(1, 50, 'screen', False)
        self.assertTrue(s.draw([0] * 6912, 0, [(0, BLACK)]))
        mock_surface = mock_pygame.display.get_surface()
        self.assertTrue(all(p == BLACK for p in mock_surface.pixels))
        s.clock.tick.assert_called_with(50)
        mock_pygame.display.update.assert_called_with()

    @patch.object(screen, 'pygame', new_callable=MockPygame)
    def test_pixel_change(self, mock_pygame):
        s = screen.Screen(1, 50, 'screen', False)
        scr = [0] * 0x1800 + [BLUE] * 0x300
        self.assertTrue(s.draw(scr, 0, [(0, BLACK)]))
        mock_surface = mock_pygame.display.get_surface()
        self.assertTrue(all(p == BLACK for p in mock_surface.pixels))
        scr = scr.copy()
        scr[0] |= 0b10000000
        self.assertTrue(s.draw(scr, 1, [(0, BLACK)]))
        self.assertEqual(mock_surface.get_pixel(0, 0), BLUE)

    @patch.object(screen, 'pygame', new_callable=MockPygame)
    def test_attr_change(self, mock_pygame):
        s = screen.Screen(1, 50, 'screen', False)
        scr = [0] * 0x1800 + [8 * GREEN] * 0x300
        self.assertTrue(s.draw(scr, 0, [(0, GREEN)]))
        mock_surface = mock_pygame.display.get_surface()
        self.assertTrue(all(p == GREEN for p in mock_surface.pixels))
        scr = scr.copy()
        scr[0x1800] = 8 * YELLOW
        self.assertTrue(s.draw(scr, 1, [(0, BLACK)]))
        for x in range(8):
            for y in range(8):
                self.assertEqual(mock_surface.get_pixel(x, y), YELLOW)

    @patch.object(screen, 'pygame', new_callable=MockPygame)
    def test_flash(self, mock_pygame):
        s = screen.Screen(1, 50, 'screen', False)
        paper, ink = MAGENTA, CYAN
        scr = [0] * 0x1800 + [0x80 + 8 * paper + ink] * 0x300
        self.assertTrue(s.draw(scr, 0x0F, [(0, paper)]))
        mock_surface = mock_pygame.display.get_surface()
        self.assertTrue(all(p == paper for p in mock_surface.pixels))
        self.assertTrue(s.draw(scr.copy(), 0x10, [(0, ink)]))
        self.assertTrue(all(p == ink for p in mock_surface.pixels))
        self.assertTrue(s.draw(scr.copy(), 0x20, [(0, paper)]))
        self.assertTrue(all(p == paper for p in mock_surface.pixels))

    @patch.object(screen, 'pygame', new_callable=MockPygame)
    def test_border_colours_48k(self, mock_pygame):
        s = screen.Screen(1, 50, 'screen', False)
        scr = [0] * 0x1800 + [8 * CYAN] * 0x300
        border = [
            (0, MAGENTA),         # 64 scanlines (top border)
            (64 * 224, GREEN),    # Invisible left border (8 T-states)
            (64 * 224 + 8, BLUE), # 192 scanlines (main screen)
            (256 * 224, RED),     # 56 scanlines (bottom border)
        ]
        self.assertTrue(s.draw(scr, 0, border))
        mock_surface = mock_pygame.display.get_surface()
        self.assertEqual(mock_surface.get_abs_pixel(0, 0), MAGENTA)
        self.assertEqual(mock_surface.get_abs_pixel(319, 23), MAGENTA)
        for y in (24, 215):
            for x in (0, 31, 288, 319):
                self.assertEqual(mock_surface.get_abs_pixel(x, y), BLUE)
            for x in (32, 287):
                self.assertEqual(mock_surface.get_abs_pixel(x, y), CYAN)
        self.assertEqual(mock_surface.get_abs_pixel(0, 216), RED)
        self.assertEqual(mock_surface.get_abs_pixel(319, 239), RED)

    @patch.object(screen, 'pygame', new_callable=MockPygame)
    def test_border_colours_128k(self, mock_pygame):
        s = screen.Screen(1, 50, 'screen', True)
        scr = [0] * 0x1800 + [8 * GREEN] * 0x300
        border = [
            (0, YELLOW),       # 63 scanlines (top border)
            (63 * 228, CYAN),  # 192 scanlines (main screen)
            (255 * 228, BLUE), # 56 scanlines (bottom border)
        ]
        self.assertTrue(s.draw(scr, 0, border))
        mock_surface = mock_pygame.display.get_surface()
        self.assertEqual(mock_surface.get_abs_pixel(0, 0), YELLOW)
        self.assertEqual(mock_surface.get_abs_pixel(319, 23), YELLOW)
        for y in (24, 215):
            for x in (0, 31, 288, 319):
                self.assertEqual(mock_surface.get_abs_pixel(x, y), CYAN)
            for x in (32, 287):
                self.assertEqual(mock_surface.get_abs_pixel(x, y), GREEN)
        self.assertEqual(mock_surface.get_abs_pixel(0, 216), BLUE)
        self.assertEqual(mock_surface.get_abs_pixel(319, 239), BLUE)

    @patch.object(screen, 'pygame', MockPygame([Mock(type=QUIT)]))
    def test_quit(self):
        s = screen.Screen(1, 50, 'screen', False)
        self.assertFalse(s.draw([0] * 6912, 0, [(0, BLACK)]))

    def test_keys(self):
        self._test_keys(KEYS, ())

    def test_caps_shift(self):
        self._test_keys(CS_KEYS, (0, 1))

    def test_symbol_shift(self):
        self._test_keys(SS_KEYS, (7, 2))
