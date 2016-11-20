# -*- coding: utf-8 -*-
import unittest

from skoolkittest import SkoolKitTestCase
from skoolkit.graphics import Udg

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

if __name__ == '__main__':
    unittest.main()
