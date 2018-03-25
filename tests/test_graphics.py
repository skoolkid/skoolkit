from skoolkittest import SkoolKitTestCase
from skoolkit.graphics import Udg, flip_udgs, rotate_udgs, font_udgs

class UdgTest(SkoolKitTestCase):
    def test_flip(self):
        udg = Udg(0, [1, 2, 4, 8, 16, 32, 64, 128], [1, 2, 4, 8, 16, 32, 64, 128])
        udg.flip(0)
        self.assertEqual(udg.data, [1, 2, 4, 8, 16, 32, 64, 128])
        self.assertEqual(udg.mask, [1, 2, 4, 8, 16, 32, 64, 128])

        udg = Udg(0, [1, 2, 4, 8, 16, 32, 64, 128], [1, 2, 4, 8, 16, 32, 64, 128])
        udg.flip(1)
        self.assertEqual(udg.data, [128, 64, 32, 16, 8, 4, 2, 1])
        self.assertEqual(udg.mask, [128, 64, 32, 16, 8, 4, 2, 1])

        udg = Udg(0, [1, 2, 3, 4, 5, 6, 7, 8], [2, 4, 6, 8, 10, 12, 14, 16])
        udg.flip(2)
        self.assertEqual(udg.data, [8, 7, 6, 5, 4, 3, 2, 1])
        self.assertEqual(udg.mask, [16, 14, 12, 10, 8, 6, 4, 2])

        udg = Udg(0, [1, 2, 3, 4, 5, 6, 7, 8], [8, 7, 6, 5, 4, 3, 2, 1])
        udg.flip(3)
        self.assertEqual(udg.data, [16, 224, 96, 160, 32, 192, 64, 128])
        self.assertEqual(udg.mask, [128, 64, 192, 32, 160, 96, 224, 16])

    def test_rotate(self):
        udg = Udg(0, [1, 2, 4, 8, 16, 32, 64, 128], [1, 2, 4, 8, 16, 32, 64, 128])
        udg.rotate(0)
        self.assertEqual(udg.data, [1, 2, 4, 8, 16, 32, 64, 128])
        self.assertEqual(udg.mask, [1, 2, 4, 8, 16, 32, 64, 128])

        udg = Udg(0, [1, 2, 4, 8, 16, 32, 64, 128], [1, 2, 4, 8, 16, 32, 64, 128])
        udg.rotate(1)
        self.assertEqual(udg.data, [128, 64, 32, 16, 8, 4, 2, 1])
        self.assertEqual(udg.mask, [128, 64, 32, 16, 8, 4, 2, 1])

        udg = Udg(0, [1, 2, 3, 4, 5, 6, 7, 8], [8, 7, 6, 5, 4, 3, 2, 1])
        udg.rotate(2)
        self.assertEqual(udg.data, [16, 224, 96, 160, 32, 192, 64, 128])
        self.assertEqual(udg.mask, [128, 64, 192, 32, 160, 96, 224, 16])

        udg = Udg(0, [1, 2, 3, 4, 5, 6, 7, 8], [255, 254, 253, 252, 251, 250, 249, 248])
        udg.rotate(3)
        self.assertEqual(udg.data, [170, 102, 30, 1, 0, 0, 0, 0])
        self.assertEqual(udg.mask, [170, 204, 240, 255, 255, 255, 255, 255])

    def test_copy(self):
        udg = Udg(23, [1] * 8)
        replica = udg.copy()
        self.assertEqual(udg.attr, replica.attr)
        self.assertEqual(udg.data, replica.data)
        self.assertEqual(udg.mask, replica.mask)
        self.assertFalse(udg.data is replica.data)

        udg = Udg(47, [2] * 8, [3] * 8)
        replica = udg.copy()
        self.assertEqual(udg.attr, replica.attr)
        self.assertEqual(udg.data, replica.data)
        self.assertEqual(udg.mask, replica.mask)
        self.assertFalse(udg.data is replica.data)
        self.assertFalse(udg.mask is replica.mask)

    def test_eq(self):
        udg1 = Udg(1, [7] * 8)
        udg2 = Udg(1, [7] * 8)
        udg3 = Udg(2, [7] * 8)
        self.assertTrue(udg1 == udg2)
        self.assertFalse(udg1 == udg3)
        self.assertFalse(udg1 == 1)

    def test_repr(self):
        udg1 = Udg(1, [2, 3, 4, 5, 6, 7, 8, 9])
        self.assertEqual(repr(udg1), 'Udg(1, [2, 3, 4, 5, 6, 7, 8, 9])')

        udg2 = Udg(1, [2] * 8, [3, 4, 5, 6, 7, 8, 9, 10])
        self.assertEqual(repr(udg2), 'Udg(1, [2, 2, 2, 2, 2, 2, 2, 2], [3, 4, 5, 6, 7, 8, 9, 10])')

    def test_flip_udgs(self):
        udg1 = Udg(0, [1, 2, 4, 8, 16, 32, 64, 128], [1, 2, 4, 8, 16, 32, 64, 128])
        udg2 = Udg(0, [1, 2, 3, 4, 5, 6, 7, 8], [2, 4, 6, 8, 10, 12, 14, 16])
        udg3 = Udg(0, [1, 2, 3, 4, 5, 6, 7, 8], [8, 7, 6, 5, 4, 3, 2, 1])
        udg4 = Udg(0, [8, 7, 6, 5, 4, 3, 2, 1], [255, 254, 253, 252, 251, 250, 249, 248])

        udgs = [[udg1.copy(), udg2.copy()], [udg3.copy(), udg4.copy()]]
        flip_udgs(udgs, 0)
        self.assertEqual(udgs, [[udg1, udg2], [udg3, udg4]])

        udgs = [[udg1.copy(), udg2.copy()], [udg3.copy(), udg4.copy()]]
        flip_udgs(udgs, 1)
        udg1_f, udg2_f, udg3_f, udg4_f = udg1.copy(), udg2.copy(), udg3.copy(), udg4.copy()
        udg1_f.flip(1)
        udg2_f.flip(1)
        udg3_f.flip(1)
        udg4_f.flip(1)
        self.assertEqual(udgs, [[udg2_f, udg1_f], [udg4_f, udg3_f]])

        udgs = [[udg1.copy(), udg2.copy()], [udg3.copy(), udg4.copy()]]
        flip_udgs(udgs, 2)
        udg1_f, udg2_f, udg3_f, udg4_f = udg1.copy(), udg2.copy(), udg3.copy(), udg4.copy()
        udg1_f.flip(2)
        udg2_f.flip(2)
        udg3_f.flip(2)
        udg4_f.flip(2)
        self.assertEqual(udgs, [[udg3_f, udg4_f], [udg1_f, udg2_f]])

        udgs = [[udg1.copy(), udg2.copy()], [udg3.copy(), udg4.copy()]]
        flip_udgs(udgs, 3)
        udg1_f, udg2_f, udg3_f, udg4_f = udg1.copy(), udg2.copy(), udg3.copy(), udg4.copy()
        udg1_f.flip(3)
        udg2_f.flip(3)
        udg3_f.flip(3)
        udg4_f.flip(3)
        self.assertEqual(udgs, [[udg4_f, udg3_f], [udg2_f, udg1_f]])

    def test_flip_udgs_with_duplicates(self):
        base_udg = Udg(1, [2, 3, 5, 7, 11, 13, 17, 19])
        udg = base_udg.copy()

        udgs = [[udg, udg]]
        flip_udgs(udgs, 1)
        udg_f = base_udg.copy()
        udg_f.flip(1)
        self.assertEqual([[udg_f, udg_f]], udgs)

    def test_rotate_udgs(self):
        udg1 = Udg(0, [1, 2, 4, 8, 16, 32, 64, 128], [1, 2, 4, 8, 16, 32, 64, 128])
        udg2 = Udg(0, [1, 2, 3, 4, 5, 6, 7, 8], [2, 4, 6, 8, 10, 12, 14, 16])
        udg3 = Udg(0, [1, 2, 3, 4, 5, 6, 7, 8], [8, 7, 6, 5, 4, 3, 2, 1])
        udg4 = Udg(0, [8, 7, 6, 5, 4, 3, 2, 1], [255, 254, 253, 252, 251, 250, 249, 248])

        udgs = [[udg1.copy(), udg2.copy()], [udg3.copy(), udg4.copy()]]
        rotate_udgs(udgs, 0)
        self.assertEqual(udgs, [[udg1, udg2], [udg3, udg4]])

        udgs = [[udg1.copy(), udg2.copy()], [udg3.copy(), udg4.copy()]]
        rotate_udgs(udgs, 1)
        udg1_r, udg2_r, udg3_r, udg4_r = udg1.copy(), udg2.copy(), udg3.copy(), udg4.copy()
        udg1_r.rotate(1)
        udg2_r.rotate(1)
        udg3_r.rotate(1)
        udg4_r.rotate(1)
        self.assertEqual(udgs, [[udg3_r, udg1_r], [udg4_r, udg2_r]])

        udgs = [[udg1.copy(), udg2.copy()], [udg3.copy(), udg4.copy()]]
        rotate_udgs(udgs, 2)
        udg1_r, udg2_r, udg3_r, udg4_r = udg1.copy(), udg2.copy(), udg3.copy(), udg4.copy()
        udg1_r.rotate(2)
        udg2_r.rotate(2)
        udg3_r.rotate(2)
        udg4_r.rotate(2)
        self.assertEqual(udgs, [[udg4_r, udg3_r], [udg2_r, udg1_r]])

        udgs = [[udg1.copy(), udg2.copy()], [udg3.copy(), udg4.copy()]]
        rotate_udgs(udgs, 3)
        udg1_r, udg2_r, udg3_r, udg4_r = udg1.copy(), udg2.copy(), udg3.copy(), udg4.copy()
        udg1_r.rotate(3)
        udg2_r.rotate(3)
        udg3_r.rotate(3)
        udg4_r.rotate(3)
        self.assertEqual(udgs, [[udg2_r, udg4_r], [udg1_r, udg3_r]])

    def test_rotate_udgs_with_duplicates(self):
        base_udg = Udg(1, [2, 3, 5, 7, 11, 13, 17, 19])
        udg = base_udg.copy()

        udgs = [[udg, udg]]
        rotate_udgs(udgs, 1)
        udg_r = base_udg.copy()
        udg_r.rotate(1)
        self.assertEqual([[udg_r], [udg_r]], udgs)

    def test_rotate_udgs_with_rows_of_different_sizes(self):
        base_udg1 = Udg(1, [170] * 8)
        base_udg2 = Udg(2, [85] * 8)

        udg1 = base_udg1.copy()
        udg2 = base_udg2.copy()
        udg1_r1 = Udg(1, [255, 0] * 4)
        udg2_r1 = Udg(2, [0, 255] * 4)
        udgs = [[udg1], [udg2, udg1]]
        rotate_udgs(udgs, 1)
        self.assertEqual([[udg2_r1, udg1_r1], [udg1_r1]], udgs)

        udg1 = base_udg1.copy()
        udg2 = base_udg2.copy()
        udg1_r3 = Udg(1, [0, 255] * 4)
        udg2_r3 = Udg(2, [255, 0] * 4)
        udgs = [[udg1, udg2], [udg2]]
        rotate_udgs(udgs, 3)
        self.assertEqual([[udg2_r3], [udg1_r3, udg2_r3]], udgs)

class GraphicsTest(SkoolKitTestCase):
    def test_font_udgs(self):
        snapshot = [0] * 65536
        char1 = [1, 2, 3, 4, 5, 6, 7, 8]
        char2 = [8, 7, 6, 5, 4, 3, 2, 1]
        chars = [char1, char2]
        char_data = []
        for char in chars:
            char_data.extend(char)
        address = 32768
        snapshot[address:address + sum(len(c) for c in chars)] = char_data
        attr = 56
        message = ''.join([chr(n) for n in range(32, 32 + len(chars))])
        font_udg_array = font_udgs(snapshot, address, attr, message)
        self.assertEqual(len(font_udg_array[0]), len(chars))
        for i, udg in enumerate(font_udg_array[0]):
            self.assertEqual(udg.attr, attr)
            self.assertEqual(udg.data, chars[i])
