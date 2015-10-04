# -*- coding: utf-8 -*-

# Copyright 2011-2015 Richard Dymond (rjdymond@gmail.com)
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

import sys
import os
import posixpath
import textwrap
import importlib

VERSION = '5.0'
ENCODING = 'utf-8'
PY3 = sys.version_info >= (3,)
PACKAGE_DIR = os.path.dirname(__file__)

def error(msg):
    sys.stderr.write('ERROR: {0}\n'.format(msg))
    sys.exit(1)

def warn(msg):
    sys.stderr.write('WARNING: {0}\n'.format(msg))

def info(msg):
    sys.stderr.write('{0}\n'.format(msg))

def show_package_dir():
    write_line(PACKAGE_DIR)
    sys.exit(0)

def write(text):
    sys.stdout.write(text)
    sys.stdout.flush()

def write_line(text):
    sys.stdout.write('{0}\n'.format(text))

def write_text(text):
    sys.stdout.write(text)

def wrap(text, width):
    return textwrap.wrap(text, width, break_long_words=False, break_on_hyphens=False)

def get_int_param(num_str):
    if num_str.startswith('$'):
        return int(num_str[1:], 16)
    if num_str.startswith('%'):
        return int(num_str[1:], 2)
    if num_str.startswith('"') and num_str.endswith('"'):
        if num_str.startswith('"\\'):
            return ord(num_str[2:-1])
        return ord(num_str[1:-1])
    return int(num_str)

def parse_int(num_str, default=None):
    try:
        return get_int_param(num_str)
    except ValueError:
        return default

def get_address_format(hexadecimal=False, lower=False):
    if hexadecimal:
        if lower:
            return '${:04x}'
        return '${:04X}'
    return '{:05d}'

def get_chr(code):
    return chr(code) if PY3 else unichr(code).encode(ENCODING)

def get_class(name_spec):
    if ':' in name_spec:
        path, name = name_spec.rsplit(':', 1)
        if path not in sys.path:
            sys.path.insert(0, os.path.expanduser(path))
    else:
        name = name_spec
    if '.' not in name:
        raise SkoolKitError("Invalid class name: '{0}'".format(name))
    mod_name, cls_name = name.rsplit('.', 1)
    try:
        m = importlib.import_module(mod_name)
    except ImportError as e:
        raise SkoolKitError("Failed to import class {0}: {1}".format(name, e.args[0]))
    try:
        return getattr(m, cls_name)
    except AttributeError:
        raise SkoolKitError("No class named '{0}' in module '{1}'".format(cls_name, mod_name))

def open_file(fname, mode='r'):
    if fname == '-':
        return sys.stdin
    try:
        return open(fname, mode)
    except IOError as e:
        if e.errno == 2:
            raise SkoolKitError('{0}: file not found'.format(fname))
        raise
    except TypeError:
        # Assume this is already a file-like object
        return fname

def read_bin_file(fname):
    try:
        with open(fname, 'rb') as f:
            return bytearray(f.read()) # PY: 'return f.read()' in Python 3
    except IOError as e:
        if e.errno == 2:
            raise SkoolKitError('{0}: file not found'.format(fname))
        raise

def normpath(*paths):
    return posixpath.normpath(posixpath.join(*[p.replace('\\', '/') for p in paths]))

def get_word(data, index):
    return data[index] + 256 * data[index + 1]

def get_word3(data, index):
    return get_word(data, index) + 65536 * data[index + 2]

def get_dword(data, index):
    return get_word3(data, index) + 16777216 * data[index + 3]

class SkoolKitError(Exception):
    pass

class SkoolParsingError(SkoolKitError):
    pass
