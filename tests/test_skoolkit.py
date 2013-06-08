# -*- coding: utf-8 -*-
import sys
import unittest

from skoolkittest import SkoolKitTestCase
from skoolkit import error, open_file, read_bin_file

ERRNO = 13 if sys.platform == 'win32' else 21

class SkoolKitTest(SkoolKitTestCase):
    def test_error(self):
        message = 'Something went wrong'
        try:
            error(message)
            self.fail()
        except SystemExit as e:
            self.assertEqual(e.args[0], 1)
        self.assertEqual(self.err.getvalue(), 'ERROR: {0}\n'.format(message))

    def test_open_file(self):
        tempdir = self.make_directory()
        try:
            open_file(tempdir)
            self.fail()
        except IOError as e:
            self.assertEqual(e.errno, ERRNO)

    def test_read_bin_file(self):
        tempdir = self.make_directory()
        try:
            read_bin_file(tempdir)
            self.fail()
        except IOError as e:
            self.assertEqual(e.errno, ERRNO)

if __name__ == '__main__':
    unittest.main()
