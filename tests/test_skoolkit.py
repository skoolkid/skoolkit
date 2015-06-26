# -*- coding: utf-8 -*-
import sys
import os
import unittest
try:
    from importlib import invalidate_caches
except ImportError:
    invalidate_caches = lambda: None

from skoolkittest import SkoolKitTestCase
from skoolkit import error, get_class, open_file, read_bin_file

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

    def test_get_class(self):
        class_name = 'CustomWriter'
        mod = 'class {}:\n    pass'.format(class_name)
        module = self.write_text_file(mod, '{}/custom.py'.format(self.make_directory()))
        invalidate_caches()
        module_path = os.path.dirname(module)
        module_name = os.path.basename(module)[:-3]
        writer_class = get_class('{}:{}.{}'.format(module_path, module_name, class_name))
        self.assertEqual(writer_class.__name__, class_name)

if __name__ == '__main__':
    unittest.main()
