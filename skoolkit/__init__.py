# Copyright 2011-2019 Richard Dymond (rjdymond@gmail.com)
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

import argparse
import sys
import os
import posixpath
import textwrap
import importlib

VERSION = '7.2'
PACKAGE_DIR = os.path.dirname(__file__)

BASE_10 = 10
BASE_16 = 16

CASE_LOWER = 1
CASE_UPPER = 2

WRAPPER = textwrap.TextWrapper(break_long_words=False, break_on_hyphens=False)

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
    WRAPPER.width = width
    return WRAPPER.wrap(text)

def is_char(value):
    return 32 <= value < 127 and value not in (94, 96)

def get_int_param(num_str, accept0x=False):
    try:
        return int(num_str)
    except ValueError:
        pass
    if num_str.startswith('$'):
        return int(num_str[1:], 16)
    if accept0x and num_str.startswith('0x'):
        return int(num_str[2:], 16)
    if num_str.startswith('%'):
        return int(num_str[1:], 2)
    if num_str.startswith('"') and num_str.endswith('"'):
        try:
            if num_str.startswith('"\\'):
                return ord(num_str[2:-1])
            return ord(num_str[1:-1])
        except TypeError:
            pass
    raise ValueError

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

def get_class(name_spec, default_path):
    path, sep, name = name_spec.rpartition(':')
    if sep:
        sys.path.insert(0, os.path.expanduser(path) or default_path)
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

def find_file(fname, search_dirs=('',)):
    for f in [os.path.join(d, fname) for d in search_dirs]:
        if os.path.isfile(f):
            return f

def open_file(fname, mode='r'):
    if fname == '-':
        if 'w' in mode:
            return sys.stdout.buffer
        return sys.stdin
    try:
        if 'b' in mode:
            return open(fname, mode)
        return open(fname, mode, encoding='utf-8')
    except IOError as e:
        if e.errno == 2:
            raise SkoolKitError('{0}: file not found'.format(fname))
        raise
    except TypeError:
        # Assume this is already a file-like object
        return fname

def read_bin_file(fname, size=-1):
    if fname == '-':
        return sys.stdin.buffer.read(size)
    try:
        with open(fname, 'rb') as f:
            return f.read(size)
    except IOError as e:
        if e.errno == 2:
            raise SkoolKitError('{0}: file not found'.format(fname))
        raise

def format_template(template__, name__, **fields):
    try:
        return template__.format(**fields)
    except ValueError as e:
        raise SkoolKitError('Failed to format {} template: {}'.format(name__, e.args[0]))
    except KeyError as e:
        raise SkoolKitError("Unknown field '{}' in {} template".format(e.args[0], name__))

def normpath(*paths):
    return posixpath.normpath(posixpath.join(*[p.replace('\\', '/') for p in paths]))

def get_word(data, index):
    return data[index] + 256 * data[index + 1]

def get_word3(data, index):
    return get_word(data, index) + 65536 * data[index + 2]

def get_dword(data, index):
    return get_word3(data, index) + 16777216 * data[index + 3]

def integer(arg):
    try:
        s_arg = arg.strip()
        if s_arg.startswith('0x'):
            return int(s_arg[2:], 16)
        return int(s_arg)
    except ValueError:
        raise argparse.ArgumentTypeError("invalid integer: '{}'".format(arg))

class SkoolKitError(Exception):
    pass

class SkoolParsingError(SkoolKitError):
    pass
