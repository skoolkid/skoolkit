# -*- coding: utf-8 -*-

# Copyright 2010-2012 Richard Dymond (rjdymond@gmail.com)
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
from .skoolctl import CtlWriter, BLOCKS, BLOCK_TITLES, BLOCK_DESC, REGISTERS, BLOCK_COMMENTS, SUBBLOCKS, COMMENTS

USAGE = """skool2ctl.py [options] FILE

  Convert a skool file into a control file, written to standard output. FILE
  may be a regular file, or '-' for standard input.

Options:
  -w X  Write only these elements, where X is one or more of:
          {0} = block types and addresses
          {1} = block titles
          {2} = block descriptions
          {3} = registers
          {4} = mid-block comments and block end comments
          {5} = sub-block types and addresses
          {6} = instruction-level comments
  -h    Write addresses in hexadecimal format
  -a    Do not write ASM directives""".format(BLOCKS, BLOCK_TITLES, BLOCK_DESC, REGISTERS, BLOCK_COMMENTS, SUBBLOCKS, COMMENTS)

def parse_args(args):
    elements = BLOCKS + BLOCK_TITLES + BLOCK_DESC + REGISTERS + BLOCK_COMMENTS + SUBBLOCKS + COMMENTS
    write_hex = False
    write_asm_dirs = True
    files = []
    i = 0
    while i < len(args):
        arg = args[i]
        if arg == '-w':
            elements = args[i + 1]
            i += 1
        elif arg == '-h':
            write_hex = True
        elif arg == '-a':
            write_asm_dirs = False
        elif len(arg) > 1 and arg[0] == '-':
            raise UsageError(USAGE)
        else:
            files.append(arg)
        i += 1

    if len(files) != 1:
        raise UsageError(USAGE)
    return files[0], elements, write_hex, write_asm_dirs

def run(skoolfile, elements, write_hex, write_asm_dirs):
    writer = CtlWriter(skoolfile, elements, write_hex, write_asm_dirs)
    writer.write()

def main(args):
    run(*parse_args(args))
