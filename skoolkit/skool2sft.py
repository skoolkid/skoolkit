# -*- coding: utf-8 -*-

# Copyright 2011-2012 Richard Dymond (rjdymond@gmail.com)
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

from . import UsageError
from .skoolsft import SftWriter

USAGE = """skool2sft.py [options] FILE

  Convert a skool file into a skool file template, written to standard output.
  FILE may be a regular file, or '-' for standard input.

Options:
  -h  Write addresses in hexadecimal format"""

def parse_args(args):
    write_hex = False
    files = []
    i = 0
    while i < len(args):
        arg = args[i]
        if arg == '-h':
            write_hex = True
        elif len(arg) > 1 and arg[0] == '-':
            raise UsageError(USAGE)
        else:
            files.append(arg)
        i += 1

    if len(files) != 1:
        raise UsageError(USAGE)
    return files[0], write_hex

def run(skoolfile, write_hex):
    writer = SftWriter(skoolfile, write_hex)
    writer.write()

def main(args):
    run(*parse_args(args))
