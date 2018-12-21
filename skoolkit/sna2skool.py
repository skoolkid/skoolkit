# Copyright 2009-2015, 2017, 2018 Richard Dymond (rjdymond@gmail.com)
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
import glob

from skoolkit import find_file, info, integer, VERSION
from skoolkit.config import get_config, show_config, update_options
from skoolkit.ctlparser import CtlParser
from skoolkit.sftparser import SftParser
from skoolkit.snapshot import make_snapshot
from skoolkit.snaskool import SkoolWriter

END = 65536

def run(snafile, options, config):
    snapshot, start, end = make_snapshot(snafile, options.org, options.start, options.end, options.page)

    if options.sftfile:
        # Use a skool file template
        info('Using skool file template: {}'.format(options.sftfile))
        writer = SftParser(snapshot, options.sftfile, config['DefbZfill'], options.base == 16, options.case == 1)
        writer.write_skool(options.start, options.end)
        return

    if options.ctlfiles:
        # Use control file(s)
        if len(options.ctlfiles) > 1:
            suffix = 's'
        else:
            suffix = ''
        info('Using control file{}: {}'.format(suffix, ', '.join(options.ctlfiles)))
        ctl_parser = CtlParser()
        ctl_parser.parse_ctls(options.ctlfiles, options.start, options.end)
    else:
        ctl_parser = CtlParser({start: 'c', end: 'i'})
    writer = SkoolWriter(snapshot, ctl_parser, options, config)
    writer.write_skool(config['ListRefs'], config['Text'])

def main(args):
    config = get_config('sna2skool')
    parser = argparse.ArgumentParser(
        usage='sna2skool.py [options] FILE',
        description="Convert a binary (raw memory) file or a SNA, SZX or Z80 snapshot into a skool file. "
                    "FILE may be a regular file, or '-' for standard input.",
        add_help=False
    )
    parser.add_argument('snafile', help=argparse.SUPPRESS, nargs='?')
    group = parser.add_argument_group('Options')
    group.add_argument('-c', '--ctl', dest='ctlfiles', metavar='FILE', action='append', default=[],
                       help="Use FILE as a control file (may be '-' for standard input). This option may be used multiple times.")
    group.add_argument('-e', '--end', dest='end', metavar='ADDR', type=integer, default=END,
                       help='Stop disassembling at this address (default={}).'.format(END))
    group.add_argument('-H', '--hex', dest='base', action='store_const', const=16, default=config['Base'],
                       help='Write hexadecimal addresses and operands in the disassembly.')
    group.add_argument('-I', '--ini', dest='params', metavar='p=v', action='append', default=[],
                       help="Set the value of the configuration parameter 'p' to 'v'. This option may be used multiple times.")
    group.add_argument('-l', '--lower', dest='case', action='store_const', const=1, default=config['Case'],
                       help='Write the disassembly in lower case.')
    group.add_argument('-o', '--org', dest='org', metavar='ADDR', type=integer,
                       help='Specify the origin address of a binary (.bin) file (default: 65536 - length).')
    group.add_argument('-p', '--page', dest='page', metavar='PAGE', type=int, choices=list(range(8)),
                       help='Specify the page (0-7) of a 128K snapshot to map to 49152-65535.')
    group.add_argument('--show-config', dest='show_config', action='store_true',
                       help="Show configuration parameter values.")
    group.add_argument('-s', '--start', dest='start', metavar='ADDR', type=integer, default=0,
                       help='Start disassembling at this address (default=16384).')
    group.add_argument('-T', '--sft', dest='sftfile', metavar='FILE',
                       help="Use FILE as the skool file template (may be '-' for standard input).")
    group.add_argument('-V', '--version', action='version', version='SkoolKit {}'.format(VERSION),
                       help='Show SkoolKit version number and exit.')
    group.add_argument('-w', '--line-width', dest='line_width', metavar='W', type=int, default=config['LineWidth'],
                       help='Set the maximum line width of the skool file (default: {}).'.format(config['LineWidth']))

    namespace, unknown_args = parser.parse_known_args(args)
    if namespace.show_config:
        show_config('sna2skool', config)
    snafile = namespace.snafile
    if unknown_args or snafile is None:
        parser.exit(2, parser.format_help())
    if snafile[-4:].lower() in ('.bin', '.sna', '.szx', '.z80'):
        prefix = snafile[:-4]
    else:
        prefix = snafile
    if not (namespace.ctlfiles or namespace.sftfile):
        namespace.sftfile = find_file(prefix + '.sft')
    if not (namespace.ctlfiles or namespace.sftfile):
        namespace.ctlfiles.extend(sorted(glob.glob(prefix + '*.ctl')))
    update_options('sna2skool', namespace, namespace.params, config)
    run(snafile, namespace, config)
