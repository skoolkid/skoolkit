import sys
import os
from importlib import invalidate_caches

from skoolkittest import SkoolKitTestCase
from skoolkit import error, get_object, open_file, read_bin_file

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

    def test_get_object_with_class_name(self):
        class_name = 'CustomWriter'
        mod = 'class {}:\n    pass'.format(class_name)
        module = self.write_text_file(mod, '{}/custom.py'.format(self.make_directory()))
        invalidate_caches()
        module_path = os.path.dirname(module)
        module_name = os.path.basename(module)[:-3]
        writer_class = get_object('{}:{}.{}'.format(module_path, module_name, class_name), '')
        self.assertEqual(writer_class.__name__, class_name)

    def test_get_object_with_module_name(self):
        module_path = self.make_directory()
        module_name = 'custom'
        mod = 'def foo():\n    pass'
        module = self.write_text_file(mod, '{}/{}.py'.format(module_path, module_name))
        invalidate_caches()
        full_module_name = '{}.{}'.format(module_path, module_name)
        module_obj = get_object(':' + full_module_name)
        self.assertEqual(module_obj.__name__, full_module_name)

    def test_get_object_with_default_path_and_blank_module_path(self):
        class_name = 'CustomWriter'
        mod = 'class {}:\n    pass'.format(class_name)
        module = self.write_text_file(mod, '{}/custom.py'.format(self.make_directory()))
        invalidate_caches()
        default_path = os.path.dirname(module)
        module_name = os.path.basename(module)[:-3]
        writer_class = get_object(':{}.{}'.format(module_name, class_name), default_path)
        self.assertEqual(writer_class.__name__, class_name)
