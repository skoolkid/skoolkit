# -*- coding: utf-8 -*-
import sys
import unittest

from skoolkittest import SkoolKitTestCase
from skoolkit import error, open_file, read_bin_file

ERRNO = 13 if sys.platform == 'win32' else 21

class SkoolKitTest(SkoolKitTestCase):
    def test_error(self):
        message = 'Something went wrong'
        with self.assertRaises(SystemExit) as cm:
            error(message)
        self.assertEqual(cm.exception.args[0], 1)
        self.assertEqual(self.err.getvalue(), 'ERROR: {0}\n'.format(message))

    def test_open_file(self):
        tempdir = self.make_directory()
        with self.assertRaises(IOError) as cm:
            open_file(tempdir)
        self.assertEqual(cm.exception.errno, ERRNO)

    def test_read_bin_file(self):
        tempdir = self.make_directory()
        with self.assertRaises(IOError) as cm:
            read_bin_file(tempdir)
        self.assertEqual(cm.exception.errno, ERRNO)

if __name__ == '__main__':
    unittest.main()
