# -*- coding: utf-8 -*-

# Copyright 2009-2015 Richard Dymond (rjdymond@gmail.com)
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
from os.path import isfile

from skoolkit import info, read_bin_file, VERSION
from skoolkit.ctlparser import CtlParser
from skoolkit.sftparser import SftParser
from skoolkit.snapshot import get_snapshot
from skoolkit.snaskool import SkoolWriter, generate_ctls, write_ctl

START = 16384
END = 65536
DEFB_SIZE = 8
DEFM_SIZE = 66

def find(fname):
    if isfile(fname):
        return fname

def run(snafile, options):
    # Read the snapshot file
    if snafile[-4:].lower() in ('.sna', '.szx', '.z80'):
        snapshot = get_snapshot(snafile, options.page)
        start = max(START, options.start)
    else:
        ram = read_bin_file(snafile)
        if options.org is None:
            org = 65536 - len(ram)
        else:
            org = options.org
        snapshot = [0] * org
        snapshot.extend(ram)
        start = max(org, options.start)
    end = min(options.end, len(snapshot))

    # Pad out the end of the snapshot to avoid disassembly errors when an
    # instruction crosses the 64K boundary
    snapshot += [0] * (65539 - len(snapshot))

    if options.sftfile:
        # Use a skool file template
        info('Using skool file template: {}'.format(options.sftfile))
        writer = SftParser(snapshot, options.sftfile, options.zfill, options.asm_hex, options.asm_lower)
        writer.write_skool(options.start, options.end)
        return

    if options.genctlfile:
        # Generate a control file
        ctls = generate_ctls(snapshot, start, end, options.code_map)
        write_ctl(options.genctlfile, ctls, options.ctl_hex)
        ctl_parser = CtlParser(ctls)
    elif options.ctlfile:
        # Use a control file
        info('Using control file: {}'.format(options.ctlfile))
        ctl_parser = CtlParser()
        ctl_parser.parse_ctl(options.ctlfile, options.start, options.end)
    else:
        ctl_parser = CtlParser({start: 'c', end: 'i'})
    writer = SkoolWriter(snapshot, ctl_parser, options)
    writer.write_skool(options.write_refs, options.text)

def main(args):
    parser = argparse.ArgumentParser(
        usage='sna2skool.py [options] file',
        description="Convert a binary (raw memory) file or a SNA, SZX or Z80 snapshot into a skool file.",
        add_help=False
    )
    parser.add_argument('snafile', help=argparse.SUPPRESS, nargs='?')
    group = parser.add_argument_group('Options')
    group.add_argument('-c', '--ctl', dest='ctlfile', metavar='FILE',
                       help='Use FILE as the control file')
    group.add_argument('-e', '--end', dest='end', metavar='ADDR', type=int, default=END,
                       help='Stop disassembling at this address (default={})'.format(END))
    group.add_argument('-g', '--generate-ctl', dest='genctlfile', metavar='FILE',
                       help='Generate a control file in FILE')
    group.add_argument('-h', '--ctl-hex', dest='ctl_hex', action='store_const', const=1, default=0,
                       help='Write upper case hexadecimal addresses in the generated control file')
    group.add_argument('-H', '--skool-hex', dest='asm_hex', action='store_true',
                       help='Write hexadecimal addresses and operands in the disassembly')
    group.add_argument('-i', '--ctl-hex-lower', dest='ctl_hex', action='store_const', const=-1, default=0,
                       help='Write lower case hexadecimal addresses in the generated control file')
    group.add_argument('-l', '--defm-size', dest='defm_width', metavar='L', type=int, default=DEFM_SIZE,
                       help='Set the maximum number of characters per DEFM statement to L (default={})'.format(DEFM_SIZE))
    group.add_argument('-L', '--lower', dest='asm_lower', action='store_true',
                       help='Write the disassembly in lower case')
    group.add_argument('-m', '--defb-mod', dest='defb_mod', metavar='M', type=int, default=1,
                       help='Group DEFB blocks by addresses that are divisible by M')
    group.add_argument('-M', '--map', dest='code_map', metavar='FILE',
                       help='Use FILE as a code execution map when generating a control file')
    group.add_argument('-n', '--defb-size', dest='defb_size', metavar='N', type=int, default=DEFB_SIZE,
                       help='Set the maximum number of bytes per DEFB statement to N (default={})'.format(DEFB_SIZE))
    group.add_argument('-o', '--org', dest='org', metavar='ADDR', type=int,
                       help='Specify the origin address of a binary (.bin) file (default: 65536 - length)')
    group.add_argument('-p', '--page', dest='page', metavar='PAGE', type=int, choices=list(range(8)),
                       help='Specify the page (0-7) of a 128K snapshot to map to 49152-65535')
    group.add_argument('-r', '--no-erefs', dest='write_refs', action='store_const', const=-1, default=0,
                       help="Don't add comments that list entry point referrers")
    group.add_argument('-R', '--erefs', dest='write_refs', action='store_const', const=1, default=0,
                       help="Always add comments that list entry point referrers")
    group.add_argument('-s', '--start', dest='start', metavar='ADDR', type=int, default=0,
                       help='Start disassembling at this address (default={})'.format(START))
    group.add_argument('-t', '--text', dest='text', action='store_true',
                       help='Show ASCII text in the comment fields')
    group.add_argument('-T', '--sft', dest='sftfile', metavar='FILE',
                       help='Use FILE as the skool file template')
    group.add_argument('-V', '--version', action='version', version='SkoolKit {}'.format(VERSION),
                       help='Show SkoolKit version number and exit')
    group.add_argument('-w', '--line-width', dest='line_width', metavar='W', type=int, default=79,
                       help='Set the maximum line width of the skool file (default: 79)')
    group.add_argument('-z', '--defb-zfill', dest='zfill', action='store_true',
                       help='Pad decimal values in DEFB statements with leading zeroes')

    namespace, unknown_args = parser.parse_known_args(args)
    snafile = namespace.snafile
    if unknown_args or snafile is None:
        parser.exit(2, parser.format_help())
    if snafile[-4:].lower() in ('.bin', '.sna', '.szx', '.z80'):
        prefix = snafile[:-4]
    else:
        prefix = snafile
    if not (namespace.ctlfile or namespace.sftfile):
        namespace.sftfile = find('{}.sft'.format(prefix))
    if not (namespace.ctlfile or namespace.sftfile):
        namespace.ctlfile = find('{}.ctl'.format(prefix))
    run(snafile, namespace)
