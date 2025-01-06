from collections import defaultdict
from unittest.mock import patch, Mock

from skoolkittest import SkoolKitTestCase
from skoolkit import screen

BLACK, BLUE, RED, MAGENTA, GREEN, CYAN, YELLOW, WHITE = range(8)
BRIGHT_BLUE, BRIGHT_RED, BRIGHT_MAGENTA, BRIGHT_GREEN, BRIGHT_CYAN, BRIGHT_YELLOW, BRIGHT_WHITE = range(9, 16)

COLOURS = {
    (0x00, 0x00, 0x00): BLACK,
    (0x00, 0x00, 0xc5): BLUE,
    (0xc5, 0x00, 0x00): RED,
    (0xc5, 0x00, 0xc5): MAGENTA,
    (0x00, 0xc6, 0x00): GREEN,
    (0x00, 0xc6, 0xc5): CYAN,
    (0xc5, 0xc6, 0x00): YELLOW,
    (0xcd, 0xc6, 0xcd): WHITE,
    (0x00, 0x00, 0xff): BRIGHT_BLUE,
    (0xff, 0x00, 0x00): BRIGHT_RED,
    (0xff, 0x00, 0xff): BRIGHT_MAGENTA,
    (0x00, 0xff, 0x00): BRIGHT_GREEN,
    (0x00, 0xff, 0xff): BRIGHT_CYAN,
    (0xff, 0xff, 0x00): BRIGHT_YELLOW,
    (0xff, 0xff, 0xff): BRIGHT_WHITE,
}

QUIT = 1

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

class MockSurface:
    def __init__(self):
        self.pixels = [None] * 49152

    def fill(self, colour, rect):
        x0, y0, w, h = rect
        for x in range(x0, x0 + w):
            for y in range(y0, y0 + h):
                self.pixels[256 * y + x] = colour

class MockPygame:
    def __init__(self, events=()):
        self.init_called = False
        self.Color = lambda r, g, b: COLOURS.get((r, g, b))
        self.display = Mock()
        self.display.get_surface.return_value = MockSurface()
        self.time = Mock()
        self.event = Mock()
        self.event.get.return_value = events
        self.key = Mock()
        self.Rect = lambda x, y, w, h: (x, y, w, h)

    def __getattr__(self, name):
        if name == 'QUIT':
            return QUIT
        if name.startswith('K_'):
            return name[2:]
        raise AttributeError

    def init(self):
        self.init_called = True

class ScreenTest(SkoolKitTestCase):
    def _test_init(self, mock_pygame, scale, caption):
        s = screen.Screen(scale, 50, caption)
        self.assertTrue(mock_pygame.init_called)
        mock_pygame.display.set_mode.assert_called_with((256 * scale, 192 * scale))
        mock_pygame.display.set_caption.assert_called_with(caption)
        mock_pygame.display.get_surface.assert_called_with()
        mock_pygame.time.Clock.assert_called_with()

    @patch.object(screen, 'CELLS', ())
    @patch.object(screen, 'pygame', new_callable=MockPygame)
    def _test_keys(self, keys, extra, mock_pygame):
        s = screen.Screen(1, 50, 'screen')
        scr = [0] * 6912
        keyboard = [0] * 8
        for k, i, b in keys:
            exp_keyboard = [0] * 8
            exp_keyboard[i] = b
            if extra:
                exp_keyboard[extra[0]] |= extra[1]
            mock_pygame.key.get_pressed.return_value = defaultdict(int, {k: 1})
            self.assertTrue(s.draw(scr, 0, keyboard))
            self.assertEqual(exp_keyboard, keyboard)

    @patch.object(screen, 'pygame', new_callable=MockPygame)
    def test_init(self, mock_pygame):
        self._test_init(mock_pygame, 1, 'hello')

    @patch.object(screen, 'pygame', new_callable=MockPygame)
    def test_init_scale_2(self, mock_pygame):
        self._test_init(mock_pygame, 2, 'screen')

    @patch.object(screen, 'pygame', new_callable=MockPygame)
    def test_draw(self, mock_pygame):
        s = screen.Screen(1, 50, 'screen')
        self.assertTrue(s.draw([0] * 6912, 0))
        mock_surface = mock_pygame.display.get_surface()
        self.assertTrue(all(p == BLACK for p in mock_surface.pixels))
        s.clock.tick.assert_called_with(50)
        mock_pygame.display.update.assert_called_with()

    @patch.object(screen, 'pygame', new_callable=MockPygame)
    def test_pixel_change(self, mock_pygame):
        s = screen.Screen(1, 50, 'screen')
        scr = [0] * 0x1800 + [BLUE] * 0x300
        self.assertTrue(s.draw(scr, 0))
        mock_surface = mock_pygame.display.get_surface()
        self.assertTrue(all(p == BLACK for p in mock_surface.pixels))
        scr = scr.copy()
        scr[0] |= 0b10000000
        self.assertTrue(s.draw(scr, 1))
        self.assertEqual(mock_surface.pixels[0], BLUE)

    @patch.object(screen, 'pygame', new_callable=MockPygame)
    def test_attr_change(self, mock_pygame):
        s = screen.Screen(1, 50, 'screen')
        scr = [0] * 0x1800 + [8 * GREEN] * 0x300
        self.assertTrue(s.draw(scr, 0))
        mock_surface = mock_pygame.display.get_surface()
        self.assertTrue(all(p == GREEN for p in mock_surface.pixels))
        scr = scr.copy()
        scr[0x1800] = 8 * YELLOW
        self.assertTrue(s.draw(scr, 1))
        for x in range(8):
            for y in range(8):
                self.assertEqual(mock_surface.pixels[256 * y + x], YELLOW)

    @patch.object(screen, 'pygame', new_callable=MockPygame)
    def test_flash(self, mock_pygame):
        s = screen.Screen(1, 50, 'screen')
        paper, ink = MAGENTA, CYAN
        scr = [0] * 0x1800 + [0x80 + 8 * paper + ink] * 0x300
        self.assertTrue(s.draw(scr, 0x0F))
        mock_surface = mock_pygame.display.get_surface()
        self.assertTrue(all(p == paper for p in mock_surface.pixels))
        self.assertTrue(s.draw(scr.copy(), 0x10))
        self.assertTrue(all(p == ink for p in mock_surface.pixels))
        self.assertTrue(s.draw(scr.copy(), 0x20))
        self.assertTrue(all(p == paper for p in mock_surface.pixels))

    @patch.object(screen, 'pygame', MockPygame([Mock(type=QUIT)]))
    def test_quit(self):
        s = screen.Screen(1, 50, 'screen')
        self.assertFalse(s.draw([0] * 6912, 0))

    def test_keys(self):
        self._test_keys(KEYS, ())

    def test_caps_shift(self):
        self._test_keys(CS_KEYS, (0, 1))

    def test_symbol_shift(self):
        self._test_keys(SS_KEYS, (7, 2))
