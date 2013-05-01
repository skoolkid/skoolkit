# -*- coding: utf-8 -*-

# Copyright 2009-2013 Richard Dymond (rjdymond@gmail.com)
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

from os.path import isfile

from . import read_bin_file, parse_int_arg, UsageError
from .snaskool import SkoolWriter, generate_ctls, write_ctl
from .snapshot import get_snapshot
from .sftparser import SftParser
from .ctlparser import CtlParser

START = 16384
DEFB_SIZE = 8
DEFM_SIZE = 66

USAGE = """sna2skool.py [options] file

  Convert a binary (raw memory) file or a SNA, SZX or Z80 snapshot into a skool
  file.

Options:
  -c FILE  Use FILE as the control file (default is file.ctl)
  -T FILE  Use FILE as the skool file template (default is file.sft)
  -g FILE  Generate a control file in FILE
  -M FILE  Use FILE as a code execution map when generating the control file
  -h       Write hexadecimal addresses in the generated control file
  -H       Write hexadecimal addresses and operands in the disassembly
  -L       Write the disassembly in lower case
  -s ADDR  Specify the address at which to start disassembling (default={0})
  -o ADDR  Specify the origin address of file.bin (default: 65536 - length)
  -p PAGE  Specify the page (0-7) of a 128K snapshot to map to 49152-65535
  -t       Show ASCII text in the comment fields
  -r       Don't add comments that list entry point referrers
  -n N     Set the max number of bytes per DEFB statement to N (default={1})
  -m M     Group DEFB blocks by addresses that are divisible by M
  -z       Write bytes with leading zeroes in DEFB statements
  -l L     Set the max number of characters per DEFM statement to L (default={2})""".format(START, DEFB_SIZE, DEFM_SIZE)

class Options:
    def __init__(self):
        self.ctlfile = None
        self.sftfile = None
        self.genctl = False
        self.genctlfile = None
        self.code_map = None
        self.ctl_hex = False
        self.asm_hex = False
        self.asm_lower = False
        self.start = START
        self.org = None
        self.page = None
        self.text = False
        self.write_refs = True
        self.defb_size = DEFB_SIZE
        self.defb_mod = 1
        self.defm_width = DEFM_SIZE
        self.zfill = False

def find(fname):
    if isfile(fname):
        return fname

def parse_args(args):
    options = Options()
    files = []
    i = 0
    while i < len(args):
        arg = args[i]
        if arg == '-c':
            options.ctlfile = args[i + 1]
            options.sftfile = None
            i += 1
        elif arg == '-T':
            options.ctlfile = None
            options.sftfile = args[i + 1]
            i += 1
        elif arg == '-g':
            options.genctl = True
            options.genctlfile = args[i + 1]
            i += 1
        elif arg == '-M':
            options.code_map = args[i + 1]
            i += 1
        elif arg == '-h':
            options.ctl_hex = True
        elif arg == '-H':
            options.asm_hex = True
        elif arg == '-L':
            options.asm_lower = True
        elif arg == '-s':
            options.start = parse_int_arg(args[i + 1], arg, 'Start address')
            i += 1
        elif arg == '-o':
            options.org = parse_int_arg(args[i + 1], arg, 'Origin address')
            i += 1
        elif arg == '-p':
            options.page = parse_int_arg(args[i + 1], arg, 'Page')
            i += 1
        elif arg == '-t':
            options.text = True
        elif arg == '-r':
            options.write_refs = False
        elif arg == '-n':
            options.defb_size = parse_int_arg(args[i + 1], arg, 'Max number of bytes per DEFB statement')
            i += 1
        elif arg == '-m':
            options.defb_mod = parse_int_arg(args[i + 1], arg, 'DEFB block address divisor')
            i += 1
        elif arg == '-l':
            options.defm_width = parse_int_arg(args[i + 1], arg, 'Max number of characters per DEFM statement')
            i += 1
        elif arg == '-z':
            options.zfill = True
        elif arg[0] == '-':
            raise UsageError(USAGE)
        else:
            files.append(arg)
        i += 1

    if len(files) != 1 or files[0][-4:].lower() not in ('.bin', '.sna', '.z80', '.szx'):
        raise UsageError(USAGE)
    snafile = files[0]
    prefix = snafile[:-4]
    if not (options.ctlfile or options.sftfile):
        options.sftfile = find('{0}.sft'.format(prefix))
    if not (options.ctlfile or options.sftfile):
        options.ctlfile = find('{0}.ctl'.format(prefix))
    return snafile, options

def run(snafile, options):
    start = options.start

    # Read the snapshot file
    if snafile[-4:] == '.bin':
        ram = read_bin_file(snafile)
        org = 65536 - len(ram) if options.org is None else options.org
        snapshot = [0] * org
        snapshot.extend(ram)
        start = max(org, options.start)
    else:
        snapshot = get_snapshot(snafile, options.page)
    end = len(snapshot)

    # Pad out the end of the snapshot to avoid disassembly errors when an
    # instruction crosses the 64K boundary
    snapshot += [0] * (65539 - len(snapshot))

    if options.sftfile:
        # Use a skool file template
        writer = SftParser(snapshot, options.sftfile, options.zfill, options.asm_hex, options.asm_lower)
        writer.write_skool()
        return

    ctl_parser = CtlParser()
    if options.genctl:
        # Generate a control file
        ctls = generate_ctls(snapshot, start, options.code_map)
        write_ctl(options.genctlfile, ctls, options.ctl_hex)
        ctl_parser.ctls = ctls
    elif options.ctlfile:
        # Use a control file
        ctl_parser.parse_ctl(options.ctlfile)
    else:
        ctls = {start: 'c'}
        if end < 65536:
            ctls[end] = 'i'
        ctl_parser.ctls = ctls
    writer = SkoolWriter(snapshot, ctl_parser, options.defb_size, options.defb_mod, options.zfill, options.defm_width, options.asm_hex, options.asm_lower)
    writer.write_skool(options.write_refs, options.text)

def main(args):
    run(*parse_args(args))
