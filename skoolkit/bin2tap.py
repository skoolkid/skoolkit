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

from . import read_bin_file, parse_int_arg, UsageError

USAGE = """bin2tap.py [options] FILE.bin

  Convert a binary snapshot file into a TAP file.

Options:
  -o ORG      Set the origin (default: 65536 - length of FILE.bin)
  -s START    Set the start address to JP to (default: ORG)
  -p STACK    Set the stack pointer (default: ORG)
  -t TAPFILE  Set the TAP filename (default: FILE.tap)"""

def get_str(chars):
    return [ord(c) for c in chars]

def get_word(word):
    return (word % 256, word // 256)

def get_parity(data):
    parity = 0
    for b in data[2:]:
        parity ^= b
    return parity

def get_basic_loader(title):
    header = []
    header.extend(get_word(19))                  # Length of header block
    header.append(0)                             # Header block marker
    header.append(0)                             # BASIC program follows
    header.extend(get_str(title[:10].ljust(10))) # Title padded with spaces
    header.extend(get_word(27))                  # Length of entire data block
    header.extend(get_word(10))                  # RUN 10 after LOADing
    header.extend(get_word(27))                  # Length of BASIC program only
    header.append(get_parity(header))

    data = []
    data.extend(get_word(29))     # Length of data block
    data.append(255)              # Data block marker
    data.extend((0, 10))          # Line 10
    data.extend(get_word(5))      # Length of line 10
    data.append(239)              # LOAD
    data.extend((34, 34))         # ""
    data.append(175)              # CODE
    data.append(13)               # ENTER
    data.extend((0, 20))          # Line 20
    data.extend(get_word(14))     # Length of line 20
    data.append(249)              # RANDOMIZE
    data.append(192)              # USR
    data.extend(get_str("23296")) # 23296
    data.append(14)               # Floating-point number marker
    data.extend((0, 0))           # 23296 in
    data.extend(get_word(23296))  # floating-point
    data.append(0)                # form
    data.append(13)               # ENTER
    data.append(get_parity(data))

    return header + data

def get_data_loader(title, org, length, start, stack):
    data = []
    data.append(255)                            # Data block marker
    data.extend((221, 33))                      # LD IX,ORG
    data.extend(get_word(org))
    data.append(17)                             # LD DE,LENGTH
    data.extend(get_word(length))
    data.append(55)                             # SCF
    data.append(159)                            # SBC A,A
    data.append(49)                             # LD SP,STACK
    data.extend(get_word(stack))
    data.append(1)                              # LD BC,START
    data.extend(get_word(start))
    data.append(197)                            # PUSH BC
    data.extend((195, 86, 5))                   # JP 1366
    data = list(get_word(len(data) + 1)) + data # Prepend length of data block
    data.append(get_parity(data))

    header = []
    header.extend(get_word(19))                  # Length of header block
    header.append(0)                             # Header block marker
    header.append(3)                             # CODE block follows
    header.extend(get_str(title[:10].ljust(10))) # Title padded with spaces
    header.extend(get_word(len(data) - 4))       # Length of data in data block
    header.extend(get_word(23296))               # Start address
    header.extend(get_word(0))                   # Unused
    header.append(get_parity(header))

    return header + data

def parse_args(args):
    org = None
    start = None
    stack = None
    tapfile = None
    files = []

    i = 0
    while i < len(args):
        arg = args[i]
        if arg == '-o':
            org = parse_int_arg(args[i + 1], arg, 'ORG')
            i += 1
        elif arg == '-s':
            start = parse_int_arg(args[i + 1], arg, 'START')
            i += 1
        elif arg == '-p':
            stack = parse_int_arg(args[i + 1], arg, 'STACK')
            i += 1
        elif arg == '-t':
            tapfile = args[i + 1]
            i += 1
        elif arg.startswith('-'):
            raise UsageError(USAGE)
        else:
            files.append(arg)
        i += 1

    if len(files) != 1:
        raise UsageError(USAGE)
    binfile = files[0]
    ram = read_bin_file(binfile)
    length = len(ram)
    org = org or 65536 - length
    if tapfile is None:
        suffix = '.bin'
        if binfile.endswith(suffix):
            prefix = binfile[:-len(suffix)]
        else:
            prefix = binfile
        tapfile = prefix + ".tap"
    return ram, org, start or org, stack or org, binfile, tapfile

def run(ram, org, start, stack, binfile, tapfile):
    length = len(ram)

    stack_contents = get_word(1343) + get_word(start)
    stack_size = len(stack_contents)
    index = stack - org - stack_size
    if -stack_size < index < length:
        # If the main data block overwrites the stack, make sure that SA/LD-RET
        # (1343) and the start address are ready to be popped off the stack
        # when loading has finished
        for byte in stack_contents:
            if 0 <= index < length:
                ram[index] = byte
                index += 1

    data = []
    data.extend(get_word(length + 2)) # Length of main data block
    data.append(255)                  # Data block marker
    data.extend(ram)                  # Data
    data.append(get_parity(data))

    tap_data = get_basic_loader(binfile)
    tap_data.extend(get_data_loader(binfile, org, length, start, stack))
    tap_data.extend(data)

    with open(tapfile, 'wb') as f:
        f.write(bytearray(tap_data))

def main(args):
    ram, org, start, stack, binfile, tapfile = parse_args(args)
    run(ram, org, start, stack, binfile, tapfile)
