from argparse import ArgumentTypeError
import os
import unittest
from importlib import invalidate_caches

from skoolkittest import SkoolKitTestCase
from skoolkit import (SkoolKitError, address, byteval, error, get_object,
                      makedirs, open_file, read_bin_file)

class SkoolKitTest(SkoolKitTestCase):
    def test_error(self):
        message = 'Something went wrong'
        with self.assertRaises(SystemExit) as cm:
            error(message)
        self.assertEqual(cm.exception.args[0], 1)
        self.assertEqual(self.err.getvalue(), 'ERROR: {0}\n'.format(message))

    def test_makedirs_file_exists(self):
        fname = 'this-is-a-regular-file.txt'
        with open(fname, 'w') as f:
            f.write('Hello')
        with self.assertRaises(SkoolKitError) as cm:
            makedirs(fname)
        self.assertEqual(cm.exception.args[0], f"Failed to create directory '{fname}': file already exists")

    def test_makedirs_permission_denied(self):
        path = os.path.join('not-allowed', 'nope')
        self.output_directory_permission_denied(makedirs, path, path=path)

    def test_makedirs_parent_directory_is_a_regular_file(self):
        fname = 'regular-file'
        with open(fname, 'w') as f:
            f.write('Hi')
        dname = os.path.join(fname, 'subdir')
        err_prefix = f"Failed to create directory '{dname}': "
        with self.assertRaises(SkoolKitError) as cm:
            makedirs(dname)
        self.assertEqual(cm.exception.args[0][:len(err_prefix)], err_prefix)

    def test_open_file_file_not_found(self):
        fname = 'non-existent'
        self.input_file_not_found(open_file, fname, 'r', fname=fname)

    def test_open_file_is_a_directory(self):
        dname = 'somedir'
        self.input_file_is_a_directory(open_file, dname, 'r', dname=dname)

    def test_open_file_for_reading_permission_denied(self):
        fname = 'not-allowed'
        self.input_file_permission_denied(open_file, fname, 'r', fname=fname)

    def test_open_file_for_writing_permission_denied(self):
        path = os.path.join('not-allowed', 'nope')
        self.output_file_permission_denied(open_file, path, 'w', path=path)

    def test_open_file_name_too_long(self):
        fname = 'a' * 300
        err_prefix = f"Failed to open '{fname}': "
        with self.assertRaises(SkoolKitError) as cm:
            open_file(fname, 'w')
        self.assertEqual(cm.exception.args[0][:len(err_prefix)], err_prefix)

    def test_read_bin_file_file_not_found(self):
        self.input_file_not_found(read_bin_file, 'non-existent')

    def test_read_bin_file_is_a_directory(self):
        self.input_file_is_a_directory(read_bin_file, 'somedir')

    def test_read_bin_file_permission_denied(self):
        self.input_file_permission_denied(read_bin_file, 'not-allowed')

    def test_read_bin_file_name_too_long(self):
        fname = 'a' * 300
        err_prefix = f"Failed to open '{fname}': "
        with self.assertRaises(SkoolKitError) as cm:
            read_bin_file(fname)
        self.assertEqual(cm.exception.args[0][:len(err_prefix)], err_prefix)

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

    def test_address_value_out_of_range(self):
        for arg in ('-1', '65536'):
            with self.assertRaises(ArgumentTypeError) as cm:
                address(arg)
            self.assertEqual(cm.exception.args[0], f"address out of range: '{arg}'")

    def test_byteval_value_out_of_range(self):
        for arg in ('-1', '256'):
            with self.assertRaises(ArgumentTypeError) as cm:
                byteval(arg)
            self.assertEqual(cm.exception.args[0], f"byte value out of range: '{arg}'")
