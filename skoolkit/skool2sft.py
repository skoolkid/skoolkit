# -*- coding: utf-8 -*-

# Copyright 2011-2013 Richard Dymond (rjdymond@gmail.com)
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

from . import VERSION
from .skoolsft import SftWriter

def run(skoolfile, write_hex):
    writer = SftWriter(skoolfile, write_hex)
    writer.write()

def main(args):
    parser = argparse.ArgumentParser(
        usage='skool2sft.py [options] FILE',
        description="Convert a skool file into a skool file template, written to standard output. "
                    "FILE may be a regular file, or '-' for standard input.",
        add_help=False
    )
    parser.add_argument('skoolfile', help=argparse.SUPPRESS, nargs='?')
    group = parser.add_argument_group('Options')
    group.add_argument('-h', '--hex', action='store_true', dest='write_hex',
                       help='Write addresses in hexadecimal format')
    group.add_argument('-V', '--version', action='version', version='SkoolKit {}'.format(VERSION),
                       help='Show SkoolKit version number and exit')
    namespace, unknown_args = parser.parse_known_args(args)
    if unknown_args or namespace.skoolfile is None:
        parser.exit(2, parser.format_help())
    run(namespace.skoolfile, namespace.write_hex)
